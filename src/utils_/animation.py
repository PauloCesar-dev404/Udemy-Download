import sys
import time
import threading


class Cursor:
    HIDE = "\u001b[?25l"  # Esconde o cursor
    SHOW = "\u001b[?25h"  # Mostra o cursor
    MOVE_UP = "\u001b[{n}A"  # Move o cursor para cima n linhas
    MOVE_DOWN = "\u001b[{n}B"  # Move o cursor para baixo n linhas
    MOVE_RIGHT = "\u001b[{n}C"  # Move o cursor para a direita n colunas
    MOVE_LEFT = "\u001b[{n}D"  # Move o cursor para a esquerda n colunas
    MOVE_TO = "\u001b[{x};{y}H"  # Move o cursor para a posição (x, y)

    @staticmethod
    def move_to(x: int, y: int) -> str:
        """Retorna a sequência para mover o cursor para (x, y)."""
        return f"\u001b[{x};{y}H"


class Colors:
    ERROR = "\u001b[31m"  # Vermelho
    WARNING = "\u001b[33m"  # Amarelo
    SUCCESS = "\u001b[32m"  # Verde
    INFO = "\u001b[34m"  # Azul
    RESET = "\u001b[0m"  # Resetar cor para padrão
    GRAY = "\u001b[90m"  # Cinza


class AnimationConsole:
    def __init__(self, text="Loading", color: str = Colors.GRAY, animation_type='circle',
                 color_frame: str = Colors.INFO):
        """
        Cria uma animação de loading com uma mensagem colorida no console.
        :param text: Texto inicial da mensagem de loading.
        :param color: Cor do texto, usando Fore do colorama.
        :param animation_type: Tipo de animação ('spinner' ou 'circle').
        """
        self._text = text
        self._color = color
        self._color_frame = color_frame
        self._animation_type = animation_type
        self._running = False
        self._animation_thread = None

        if animation_type == 'spinner':
            self._frames = ["-", "\\", "|", "/"]
        elif animation_type == 'circle':
            self._frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

        else:
            raise ValueError("Tipo de animação desconhecido. Use 'spinner' ou 'circle'.")

        self._index = 0

    def start(self):
        """
        Inicia a animação no console.
        """
        if self._running:
            return  # Previne múltiplas execuções
        self._running = True
        self._animation_thread = threading.Thread(target=self._animate, daemon=True)
        self._animation_thread.start()

    def stop(self):
        """
        Para a animação no console.
        """
        self._running = False
        if self._animation_thread:
            self._animation_thread.join()
        sys.stdout.write("\r" + " " * (len(self._text) + 20) + "\r")  # Limpa a linha
        sys.stdout.flush()

    def update_message(self, new_text, new_color=None):
        """
        Atualiza a mensagem exibida junto à animação.
        :param new_text: Novo texto a ser exibido.
        :param new_color: Nova cor para o texto (opcional).
        """
        self._text = new_text
        if new_color:
            self._color = new_color

    def _animate(self):
        """
        Animação interna do console.
        """
        while self._running:
            frame = self._frames[self._index]
            self._index = (self._index + 1) % len(self._frames)
            sys.stdout.write(
                f"\r{self._color}{self._text}{Colors.RESET} {self._color_frame}{frame}{Colors.RESET}{Cursor.HIDE}")
            sys.stdout.flush()
            time.sleep(0.1)
