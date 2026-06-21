import os
import sys
import time
import ctypes
from audioplayer import AudioPlayer
from PyQt5.QtCore import QObject, QProcess, QThread, QSharedMemory, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction

ICON_PATH = os.path.join('assets', 'ww-logo.ico')
APP_ID = 'WhisperWriter.VoiceTyping'
SINGLETON_KEY = 'WhisperWriter-singleton-v1'

from key_listener import KeyListener
from result_thread import ResultThread
from ui.dashboard_window import DashboardWindow
from ui.status_window import StatusWindow
from transcription import create_local_model
from input_simulation import InputSimulator
from history import HistoryStore
from utils import ConfigManager


class ModelLoadThread(QThread):
    """Loads (or reloads) the local Whisper model off the UI thread."""
    loaded = pyqtSignal(object)

    def run(self):
        try:
            model = create_local_model()
        except Exception as e:
            ConfigManager.console_print(f'Model load failed: {e}')
            model = None
        self.loaded.emit(model)


class WhisperWriterApp(QObject):
    def __init__(self):
        super().__init__()
        # Make Windows treat this as its own app (own taskbar icon, not pythonw's).
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
        except Exception:
            pass

        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self.app.setApplicationName('WhisperWriter by CatBoneheaD')
        self._app_icon = QIcon(ICON_PATH)
        self.app.setWindowIcon(self._app_icon)

        # Single-instance guard: if another copy is already running, bail out so we
        # don't get two key listeners typing the same text twice.
        self._shared = QSharedMemory(SINGLETON_KEY)
        if not self._shared.create(1):
            print('WhisperWriter is already running. Exiting this instance.')
            sys.exit(0)

        ConfigManager.initialize()
        self.history = HistoryStore()

        self._rec_start = 0.0
        self._rec_duration = 0.0
        self.model_loader = None

        self.initialize_components()

    def initialize_components(self):
        """Initialize the components of the application."""
        self.input_simulator = InputSimulator()

        self.key_listener = KeyListener()
        self.key_listener.add_callback("on_activate", self.on_activation)
        self.key_listener.add_callback("on_deactivate", self.on_deactivation)

        model_options = ConfigManager.get_config_section('model_options')
        self.local_model = create_local_model() if not model_options.get('use_api') else None

        self.result_thread = None
        self.target_window = None

        self.dashboard = DashboardWindow(self.history)
        self.dashboard.setWindowIcon(self._app_icon)
        self.dashboard.recordToggle.connect(self.on_activation)
        self.dashboard.modelChanged.connect(self.change_model)
        self.dashboard.settingsSaved.connect(self.restart_app)

        if not ConfigManager.get_config_value('misc', 'hide_status_window'):
            self.status_window = StatusWindow()
            self.status_window.setWindowIcon(self._app_icon)
        else:
            self.status_window = None

        self.create_tray_icon()
        self.key_listener.start()
        self.dashboard.show()

    def create_tray_icon(self):
        """Create the system tray icon and its context menu."""
        self.tray_icon = QSystemTrayIcon(self._app_icon, self.app)
        self.tray_icon.setToolTip('WhisperWriter by CatBoneheaD')

        tray_menu = QMenu()

        show_action = QAction('Открыть WhisperWriter', self.app)
        show_action.triggered.connect(self.show_dashboard)
        tray_menu.addAction(show_action)

        settings_action = QAction('Настройки', self.app)
        settings_action.triggered.connect(self.dashboard.open_settings)
        tray_menu.addAction(settings_action)

        tray_menu.addSeparator()

        exit_action = QAction('Выход', self.app)
        exit_action.triggered.connect(self.exit_app)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.show_dashboard()

    def show_dashboard(self):
        self.dashboard.show()
        self.dashboard.raise_()
        self.dashboard.activateWindow()

    def change_model(self, name, path):
        """Switch the active local model (loaded off the UI thread)."""
        if ConfigManager.get_config_value('model_options', 'local', 'model') == name and \
           ConfigManager.get_config_value('model_options', 'local', 'model_path') == path:
            return
        ConfigManager.set_config_value(name, 'model_options', 'local', 'model')
        if path:
            ConfigManager.set_config_value(path, 'model_options', 'local', 'model_path')
        ConfigManager.save_config()

        self.dashboard.set_status('loading')
        self.model_loader = ModelLoadThread()
        self.model_loader.loaded.connect(self._on_model_loaded)
        self.model_loader.start()

    def _on_model_loaded(self, model):
        if model is not None:
            self.local_model = model
            self.dashboard.set_status('idle')
        else:
            self.dashboard.set_status('error')

    def cleanup(self):
        if getattr(self, 'key_listener', None):
            self.key_listener.stop()
        if getattr(self, 'input_simulator', None):
            self.input_simulator.cleanup()
        # Release the single-instance lock so a restart can re-acquire it.
        if getattr(self, '_shared', None) and self._shared.isAttached():
            self._shared.detach()

    def exit_app(self):
        """Exit the application."""
        self.cleanup()
        self.tray_icon.hide()
        QApplication.quit()

    def restart_app(self):
        """Restart the application to apply the new settings."""
        self.cleanup()
        self.tray_icon.hide()
        QApplication.quit()
        QProcess.startDetached(sys.executable, sys.argv)

    def on_activation(self):
        """Called when the activation key combination is pressed."""
        if self.result_thread and self.result_thread.isRunning():
            recording_mode = ConfigManager.get_config_value('recording_options', 'recording_mode')
            if recording_mode == 'press_to_toggle':
                self.result_thread.stop_recording()
            elif recording_mode == 'continuous':
                self.stop_result_thread()
            return

        self.target_window = ctypes.windll.user32.GetForegroundWindow()
        self.start_result_thread()

    def on_deactivation(self):
        """Called when the activation key combination is released."""
        if ConfigManager.get_config_value('recording_options', 'recording_mode') == 'hold_to_record':
            if self.result_thread and self.result_thread.isRunning():
                self.result_thread.stop_recording()

    def start_result_thread(self):
        """Start the result thread to record audio and transcribe it."""
        if self.result_thread and self.result_thread.isRunning():
            return

        self.result_thread = ResultThread(self.local_model)
        self.result_thread.statusSignal.connect(self.on_status_update)
        if self.status_window:
            self.result_thread.statusSignal.connect(self.status_window.updateStatus)
            self.result_thread.audioLevelSignal.connect(self.status_window.updateAudioLevel)
            self.status_window.closeSignal.connect(self.stop_result_thread)
        self.result_thread.resultSignal.connect(self.on_transcription_complete)
        self.result_thread.start()

    def stop_result_thread(self):
        """Stop the result thread."""
        if self.result_thread and self.result_thread.isRunning():
            self.result_thread.stop()

    def on_status_update(self, status):
        """Reflect recording status in the dashboard and measure duration."""
        if status == 'recording':
            self._rec_start = time.time()
        elif status == 'transcribing':
            self._rec_duration = time.time() - self._rec_start
        self.dashboard.set_status(status)

    def on_transcription_complete(self, result):
        """When transcription is complete, save it, type it, and resume listening."""
        if result:
            model_name = ConfigManager.get_config_value('model_options', 'local', 'model') or ''
            self.history.add(result, self._rec_duration, model_name)
            if self.dashboard.isVisible():
                self.dashboard.refresh_history()

        self.input_simulator.typewrite(result, self.target_window)
        self.target_window = None

        if ConfigManager.get_config_value('misc', 'noise_on_completion'):
            AudioPlayer(os.path.join('assets', 'beep.wav')).play(block=True)

        if ConfigManager.get_config_value('recording_options', 'recording_mode') == 'continuous':
            self.start_result_thread()
        else:
            self.key_listener.start()

    def run(self):
        """Start the application."""
        sys.exit(self.app.exec_())


if __name__ == '__main__':
    app = WhisperWriterApp()
    app.run()
