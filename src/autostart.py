"""Windows autostart toggle via the HKCU Run registry key (no extra deps)."""
import os
import winreg

_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_APP_NAME = "WhisperWriter"


def _base_dir():
    # src/autostart.py -> project root
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _command():
    """Silent launch command (wscript runs launch.vbs with no console window)."""
    vbs = os.path.join(_base_dir(), 'launch.vbs')
    return f'wscript.exe "{vbs}"'


def is_enabled():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY) as key:
            value, _ = winreg.QueryValueEx(key, _APP_NAME)
            return bool(value)
    except OSError:
        return False


def enable():
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, _RUN_KEY) as key:
        winreg.SetValueEx(key, _APP_NAME, 0, winreg.REG_SZ, _command())


def disable():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, _APP_NAME)
    except OSError:
        pass


def set_enabled(flag):
    enable() if flag else disable()
