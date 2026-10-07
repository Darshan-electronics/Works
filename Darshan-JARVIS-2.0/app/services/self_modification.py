from __future__ import annotations

import hashlib
import json
import subprocess
import time
import uuid
from pathlib import Path

from ..config import WORKSPACE
from ..memory import audit

PROPOSAL_DIR = Path(WORKSPACE) / "data" / "code_change_proposals"
PROPOSAL_DIR.mkdir(parents=True, exist_ok=True)

# HARD RULE:
# No code modification is allowed without an explicit approval recorded by the user.
# This applies to tiny changes as well as large changes.
ALLOWED_ROOT = Path(WORKSPACE).resolve()


def _safe_path(relative_path: str) -> Path:
    p = (ALLOWED_ROOT / relative_path).resolve()
    if ALLOWED_ROOT != p and ALLOWED_ROOT not in p.parents:
        raise ValueError("Path is outside the JARVIS workspace")
    if p.suffix not in {".py", ".json", ".toml", ".yaml", ".yml", ".md", ".sh", ".kt", ".kts", ".js", ".css", ".html"}:
        raise ValueError("File type is not approved for self-modification")
    return p


def create_proposal(relative_path: str, new_content: str, reason: str = ""):
    path = _safe_path(relative_path)
    old = path.read_text(encoding="utf-8") if path.exists() else ""
    proposal_id = uuid.uuid4().hex
    payload = {
        "id": proposal_id,
        "status": "PENDING_APPROVAL",
        "path": relative_path,
        "reason": reason,
        "old_sha256": hashlib.sha256(old.encode()).hexdigest(),
        "new_sha256": hashlib.sha256(new_content.encode()).hexdigest(),
        "old_content": old,
        "new_content": new_content,
        "created_at": time.time(),
    }
    (PROPOSAL_DIR / f"{proposal_id}.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    audit("code_change_proposed", "CRITICAL", "awaiting_user_approval", relative_path)
    return {
        "id": proposal_id,
        "status": payload["status"],
        "path": relative_path,
        "reason": reason,
        "old_sha256": payload["old_sha256"],
        "new_sha256": payload["new_sha256"],
        "requires_explicit_user_approval": True,
    }


def get_proposal(proposal_id: str):
    p = PROPOSAL_DIR / f"{proposal_id}.json"
    if not p.exists():
        raise FileNotFoundError("Code-change proposal not found")
    return json.loads(p.read_text(encoding="utf-8"))


def apply_proposal(proposal_id: str, approved: bool):
    payload = get_proposal(proposal_id)
    if payload["status"] != "PENDING_APPROVAL":
        raise ValueError(f"Proposal is already {payload['status']}")

    if not approved:
        payload["status"] = "REJECTED"
        payload["rejected_at"] = time.time()
        (PROPOSAL_DIR / f"{proposal_id}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        audit("code_change", "CRITICAL", "rejected", payload["path"])
        return {"id": proposal_id, "status": "REJECTED", "changed": False}

    path = _safe_path(payload["path"])
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    current_sha = hashlib.sha256(current.encode()).hexdigest()
    if current_sha != payload["old_sha256"]:
        raise RuntimeError("File changed since proposal was created; refusing to overwrite it.")

    # Create a local backup before every approved change.
    backup = path.with_suffix(path.suffix + f".bak.{proposal_id}")
    if path.exists():
        backup.write_text(current, encoding="utf-8")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload["new_content"], encoding="utf-8")

    # Syntax-check Python changes before reporting success.
    if path.suffix == ".py":
        check = subprocess.run(
            ["python3", "-m", "py_compile", str(path)],
            cwd=str(ALLOWED_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if check.returncode != 0:
            path.write_text(current, encoding="utf-8")
            payload["status"] = "ROLLED_BACK"
            payload["error"] = check.stderr[-4000:]
            (PROPOSAL_DIR / f"{proposal_id}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
            audit("code_change", "CRITICAL", "rolled_back_validation_failure", payload["path"])
            return {"id": proposal_id, "status": "ROLLED_BACK", "changed": False, "error": check.stderr[-4000:]}

    payload["status"] = "APPLIED"
    payload["approved_at"] = time.time()
    payload["backup"] = str(backup) if path.exists() else None
    (PROPOSAL_DIR / f"{proposal_id}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    audit("code_change", "CRITICAL", "applied_after_explicit_approval", payload["path"])
    return {"id": proposal_id, "status": "APPLIED", "changed": True, "path": payload["path"]}


def list_pending():
    items = []
    for p in sorted(PROPOSAL_DIR.glob("*.json")):
        try:
            x = json.loads(p.read_text(encoding="utf-8"))
            if x.get("status") == "PENDING_APPROVAL":
                items.append({
                    "id": x["id"],
                    "path": x["path"],
                    "reason": x.get("reason", ""),
                    "created_at": x["created_at"],
                    "old_sha256": x["old_sha256"],
                    "new_sha256": x["new_sha256"],
                })
        except Exception:
            continue
    return items
