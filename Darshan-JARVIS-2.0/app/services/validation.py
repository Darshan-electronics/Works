import shutil
import subprocess
from pathlib import Path

def _run(cmd, cwd=None, timeout=120):
    try:
        p=subprocess.run(cmd,cwd=cwd,capture_output=True,text=True,timeout=timeout)
        return {"ok":p.returncode==0,"code":p.returncode,"stdout":p.stdout[-12000:],"stderr":p.stderr[-12000:]}
    except FileNotFoundError:
        return {"ok":False,"code":127,"stdout":"","stderr":cmd[0]+" is not installed"}
    except Exception as exc:
        return {"ok":False,"code":1,"stdout":"","stderr":str(exc)}

def validate_project(folder: str):
    root=Path(folder)
    report={"checks":[]}
    kicad=shutil.which("kicad-cli")
    board=next(root.glob("*.kicad_pcb"),None)
    schematic=next(root.glob("*.kicad_sch"),None)
    if board and kicad:
        drc=_run([kicad,"pcb","drc","--severity-all","--exit-code-violations","-o",str(root/"drc_report.rpt"),str(board)])
        report["checks"].append({"name":"KiCad DRC","status":"PASS" if drc["ok"] else "FAIL","details":drc})
    elif board:
        report["checks"].append({"name":"KiCad DRC","status":"SKIPPED","details":"kicad-cli not installed"})
    if schematic and kicad:
        erc=_run([kicad,"sch","erc","--severity-all","--exit-code-violations","-o",str(root/"erc_report.rpt"),str(schematic)])
        report["checks"].append({"name":"KiCad ERC","status":"PASS" if erc["ok"] else "FAIL","details":erc})
    elif schematic:
        report["checks"].append({"name":"KiCad ERC","status":"SKIPPED","details":"kicad-cli not installed"})
    report["checks"].append({"name":"Artifact presence","status":"PASS" if (root/"project_plan.json").exists() else "FAIL","details":"project plan"})
    report["passed"]=sum(x["status"]=="PASS" for x in report["checks"])
    report["total"]=len(report["checks"])
    (root/"validation_report.json").write_text(__import__("json").dumps(report,indent=2),encoding="utf-8")
    return report
