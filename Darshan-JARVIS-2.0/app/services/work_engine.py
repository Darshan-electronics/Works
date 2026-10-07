from pathlib import Path

WORK_ROOT = Path('jarvis_projects')

def project_path(name: str) -> Path:
    return WORK_ROOT / name
