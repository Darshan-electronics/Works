import subprocess
from ..config import WORKSPACE
ALLOWED={'system_info':['uname','-a'],'python_version':['python3','--version'],'git_status':['git','status','--short'],'git_log':['git','log','--oneline','-10'],'iverilog_version':['iverilog','-V'],'verilator_version':['verilator','--version'],'yosys_version':['yosys','-V'],'ss_listening':['ss','-lntup']}
def run(tool):
    if tool not in ALLOWED: raise ValueError('Tool is not allowed')
    try:
        p=subprocess.run(ALLOWED[tool],cwd=WORKSPACE,capture_output=True,text=True,timeout=30)
        return {'ok':p.returncode==0,'stdout':p.stdout[-10000:],'stderr':p.stderr[-10000:],'code':p.returncode}
    except FileNotFoundError:return {'ok':False,'error':f'{ALLOWED[tool][0]} is not installed'}
