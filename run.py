import os
import sys
import multiprocessing


def _setup_cuda_path(base):
    """Make CUDA DLLs (cuBLAS / cuDNN bundled in the venv) discoverable regardless
    of how the app is launched (console, pythonw, .vbs shortcut)."""
    nvidia = os.path.join(base, 'venv', 'Lib', 'site-packages', 'nvidia')
    for sub in (os.path.join(nvidia, 'cublas', 'bin'),
                os.path.join(nvidia, 'cudnn', 'bin')):
        if os.path.isdir(sub):
            os.environ['PATH'] = sub + os.pathsep + os.environ.get('PATH', '')


if __name__ == '__main__':
    # On Windows, multiprocessing uses 'spawn', which re-executes this file in
    # child processes. The __main__ guard + freeze_support() ensure those children
    # do NOT start a second copy of the app (which caused duplicated typing).
    multiprocessing.freeze_support()

    from dotenv import load_dotenv

    _base = os.path.dirname(os.path.abspath(__file__))
    _setup_cuda_path(_base)
    os.chdir(_base)
    sys.path.insert(0, os.path.join(_base, 'src'))
    load_dotenv()

    from main import WhisperWriterApp

    app = WhisperWriterApp()
    app.run()
