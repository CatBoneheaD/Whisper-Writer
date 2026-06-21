import os
from audioplayer import AudioPlayer
from utils import ConfigManager

DEFAULT_SOUND = os.path.join('assets', 'sounds', 'soft.wav')


def play_completion_sound(path=None, volume=None, block=True):
    """Play the completion sound at the given volume (0-100). Falls back to config."""
    if path is None:
        path = ConfigManager.get_config_value('misc', 'completion_sound') or DEFAULT_SOUND
    if volume is None:
        volume = ConfigManager.get_config_value('misc', 'completion_volume')
    if volume is None:
        volume = 35
    if not os.path.exists(path):
        path = DEFAULT_SOUND
    try:
        player = AudioPlayer(path)
        try:
            player.volume = float(volume)
        except Exception:
            pass
        player.play(block=block)
        return player
    except Exception as e:
        ConfigManager.console_print(f'Sound play failed: {e}')
        return None
