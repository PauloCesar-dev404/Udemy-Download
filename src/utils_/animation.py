import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    import os
    os.system('color')

class Style:
    RESET_ALL = "\033[0m"

class Fore:
    GREEN = "\033[38;2;28;157;80m"
    BLUE = "\033[38;2;86;36;208m"
    CYAN = "\033[38;2;41;180;248m"
    RED = "\033[38;2;179;45;15m"
    YELLOW = "\033[38;2;244;193;80m"
    MAGENTA = "\033[38;2;86;36;208m"
    WHITE = "\033[38;2;255;255;255m"
    BLACK = "\033[38;2;28;29;31m"
    LIGHTBLACK_EX = "\033[38;2;106;111;115m"
    LIGHTYELLOW_EX = "\033[38;2;244;193;80m"
    LIGHTMAGENTA_EX = "\033[38;2;164;53;240m"
    LIGHTWHITE_EX = "\033[38;2;247;249;250m"
    LIGHTRED_EX = "\033[38;2;236;82;82m"
    LIGHTCYAN_EX = "\033[38;2;41;180;248m"
    LIGHTBLUE_EX = "\033[38;2;86;36;208m"
    INFO = "\033[38;2;164;53;240m"
    SUCCESS = "\033[38;2;28;157;80m"
    WARNING = "\033[38;2;244;193;80m"
    ERROR = "\033[38;2;236;82;82m"

class Cursor:
    HIDE = "\033[?25l"
    SHOW = "\033[?25h"

class Colors:
    ERROR = "\033[38;2;236;82;82m"
    WARNING = "\033[38;2;244;193;80m"
    SUCCESS = "\033[38;2;28;157;80m"
    INFO = "\033[38;2;164;53;240m"
    RESET = "\033[0m"
    GRAY = "\033[38;2;106;111;115m"

class AnimationConsole:
    def __init__(self, text="Loading", color: str = Colors.GRAY, animation_type='material',
                 color_frame: str = Colors.INFO):
        """
        Animação de loading em thread usando print nativo e ANSI puro.
        """
        self._text = text
        self._color = color
        self._color_frame = color_frame
        self._running = False
        self._thread = None

        if animation_type == 'spinner':
            self._frames = ['-', '\\', '|', '/']
        else:

            self._frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']

    def _animate(self):
        sys.stdout.write(Cursor.HIDE)
        for frame in itertools.cycle(self._frames):
            if not self._running:
                break

            output = f"\r{self._color_frame}{frame} {self._color}{self._text}{Style.RESET_ALL} "
            print(output, end="", flush=True)
            time.sleep(0.08)

        sys.stdout.write(f"\r\033[K")
        sys.stdout.write(Cursor.SHOW)
        sys.stdout.flush()

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join()

    def update_message(self, new_text, new_color=None):
        self._text = new_text
        if new_color:
            self._color = new_color


import time
import threading
import itertools

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    import os
    os.system('color')

class Style:
    RESET_ALL = "\033[0m"

class Fore:
    GREEN = "\033[38;2;28;157;80m"
    BLUE = "\033[38;2;86;36;208m"
    CYAN = "\033[38;2;41;180;248m"
    RED = "\033[38;2;179;45;15m"
    YELLOW = "\033[38;2;244;193;80m"
    MAGENTA = "\033[38;2;86;36;208m"
    WHITE = "\033[38;2;255;255;255m"
    BLACK = "\033[38;2;28;29;31m"
    LIGHTBLACK_EX = "\033[38;2;106;111;115m"
    LIGHTYELLOW_EX = "\033[38;2;244;193;80m"
    LIGHTMAGENTA_EX = "\033[38;2;164;53;240m"
    LIGHTWHITE_EX = "\033[38;2;247;249;250m"
    LIGHTRED_EX = "\033[38;2;236;82;82m"
    LIGHTCYAN_EX = "\033[38;2;41;180;248m"
    LIGHTBLUE_EX = "\033[38;2;86;36;208m"
    INFO = "\033[38;2;164;53;240m"
    SUCCESS = "\033[38;2;28;157;80m"
    WARNING = "\033[38;2;244;193;80m"
    ERROR = "\033[38;2;236;82;82m"

class Cursor:
    HIDE = "\033[?25l"
    SHOW = "\033[?25h"

class Colors:
    ERROR = "\033[38;2;236;82;82m"
    WARNING = "\033[38;2;244;193;80m"
    SUCCESS = "\033[38;2;28;157;80m"
    INFO = "\033[38;2;164;53;240m"
    RESET = "\033[0m"
    GRAY = "\033[38;2;106;111;115m"

class AnimationConsole:
    def __init__(self, text="Loading", color: str = Colors.GRAY, animation_type='material',
                 color_frame: str = Colors.INFO):
        """
        Animação de loading em thread usando print nativo e ANSI puro.
        """
        self._text = text
        self._color = color
        self._color_frame = color_frame
        self._running = False
        self._thread = None

        if animation_type == 'spinner':
            self._frames = ['-', '\\', '|', '/']
        else:

            self._frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']

    def _animate(self):
        sys.stdout.write(Cursor.HIDE)
        for frame in itertools.cycle(self._frames):
            if not self._running:
                break

            output = f"\r{self._color_frame}{frame} {self._color}{self._text}{Style.RESET_ALL} "
            print(output, end="", flush=True)
            time.sleep(0.08)

        sys.stdout.write(f"\r\033[K")
        sys.stdout.write(Cursor.SHOW)
        sys.stdout.flush()

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join()

    def update_message(self, new_text, new_color=None):
        self._text = new_text
        if new_color:
            self._color = new_color
