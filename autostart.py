"""Windows current-user startup registration for TodoSimple."""
import os
import sys
from pathlib import Path


class AutoStart:
    APP_NAME = "TodoSimple"
    RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"

    def __init__(self):
        self._supported = os.name == "nt"

    def _command(self) -> str:
        if getattr(sys, "frozen", False):
            return f'"{sys.executable}"'
        script = Path(sys.argv[0]).resolve()
        return f'"{sys.executable}" "{script}"'

    def is_enabled(self) -> bool:
        if not self._supported:
            return False
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.RUN_KEY) as key:
                value, _ = winreg.QueryValueEx(key, self.APP_NAME)
            return bool(value)
        except OSError:
            return False

    def set_enabled(self, enabled: bool) -> bool:
        if not self._supported:
            return False
        try:
            import winreg
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, self.RUN_KEY, 0, winreg.KEY_SET_VALUE
            ) as key:
                if enabled:
                    winreg.SetValueEx(key, self.APP_NAME, 0, winreg.REG_SZ, self._command())
                else:
                    try:
                        winreg.DeleteValue(key, self.APP_NAME)
                    except FileNotFoundError:
                        pass
            return True
        except OSError:
            return False
