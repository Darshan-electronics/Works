from enum import IntEnum
from .config import CONFIRM_MEDIUM,CONFIRM_HIGH,CONFIRM_CRITICAL
class Risk(IntEnum): LOW=0; MEDIUM=1; HIGH=2; CRITICAL=3
def needs_confirmation(risk):
    r=Risk[risk.upper()]
    return {Risk.LOW:False,Risk.MEDIUM:CONFIRM_MEDIUM,Risk.HIGH:CONFIRM_HIGH,Risk.CRITICAL:CONFIRM_CRITICAL}[r]
