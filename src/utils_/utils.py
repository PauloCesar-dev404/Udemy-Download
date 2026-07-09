import os
import platform
import re
import subprocess
import uuid
import unicodedata
from .animation import Fore, Style

def oculte_comands_your_system() -> dict:
    """Identifica o sistema do usuário e cria um dicionário de parâmetros para ocultar saídas de janelas e do
    terminal."""
    system_user = platform.system()
    startupinfo_options = {}

    if system_user == "Windows":

        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        startupinfo_options['startupinfo'] = startupinfo

        startupinfo_options['stdout'] = subprocess.DEVNULL
        startupinfo_options['stderr'] = subprocess.DEVNULL
        startupinfo_options['stdin'] = subprocess.DEVNULL

    elif system_user in ["Linux", "Darwin"]:

        startupinfo_options['stdout'] = subprocess.DEVNULL
        startupinfo_options['stderr'] = subprocess.DEVNULL
        startupinfo_options['stdin'] = subprocess.DEVNULL

    else:

        raise NotImplementedError(f"O sistema {system_user} não é suportado para ocultação de comandos.")

    return startupinfo_options

def generate_temp_file_path(output_dir, extension="mp4", prefix="", suffix=""):
    """
    Gera um caminho único para um arquivo temporário.

    Args:
        output_dir: Diretório onde o arquivo será salvo.
        extension: Extensão do arquivo (padrão: "mp4").
        prefix: Prefixo opcional para o nome do arquivo.
        suffix: Sufixo opcional para o nome do arquivo (antes da extensão).

    Returns:
        Caminho completo para o arquivo temporário.
    """
    try:

        unique_id = uuid.uuid4()

        filename = f"{prefix}{unique_id}{suffix}.{extension}"

        return os.path.join(output_dir, filename)
    except Exception as e:
        raise ValueError(f"Erro ao gerar caminho de arquivo temporário: {e}")

def sanitize_filename(filename: str) -> str:
    """Sanitiza um nome de arquivo, removendo caracteres não permitidos, emojis e caracteres binários."""

    def remove_emojis_and_binary_chars(text):
        return ''.join(c for c in text if c.isprintable() and unicodedata.category(c) != 'So')

    filename = re.sub(r'[<>:"/\\|?*+&%$@!,=¨\'\s]+', ' ', filename)

    filename = remove_emojis_and_binary_chars(filename)

    filename = filename.strip()

    return filename

def filter_resolution(resolutions: list[str]) -> str:
    """
    Filtra e retorna a maior resolução da lista.

    Args:
        resolutions: Lista de resoluções no formato 'larguraXaltura'.

    Returns:
        A maior resolução no formato 'larguraXaltura'.
    """

    def parse_resolution(res):
        width, height = map(int, res.split('x'))
        return width, height

    largest_resolution = max(resolutions, key=lambda res: parse_resolution(res)[0] * parse_resolution(res)[1])

    return largest_resolution

def organize_streams(streams):
    organized_streams = {
        'dash': [],
        'hls': [],
        'mp4': []
    }

    best_video = None

    for stream in streams:

        if stream['type'] == 'application/dash+xml':
            organized_streams['dash'].append({
                'src': stream['src'],
                'label': stream.get('label', 'unknown')
            })

        elif stream['type'] == 'application/x-mpegURL':
            organized_streams['hls'].append({
                'src': stream['src'],
                'label': stream.get('label', 'auto')
            })

        elif stream['type'] == 'video/mp4':

            if best_video is None or int(stream['label']) > int(best_video['label']):
                best_video = {
                    'src': stream['src'],
                    'label': stream['label']
                }

    if best_video:
        organized_streams['mp4'].append(best_video)

    return organized_streams

def banner(title, section_lecture,lecture_id,captions, tyype: str = 'Video'):
    size = 0
    if len(title) > len(section_lecture):
        size = len(title)
    else:
        size = len(section_lecture)
    line = (size + 8) * '_'
    print(line,
          f'\n{Fore.LIGHTBLUE_EX}AULA{Style.RESET_ALL}: {Fore.LIGHTWHITE_EX}{title}{Style.RESET_ALL}\n'
          f'{Fore.LIGHTBLUE_EX}SEÇÃO{Style.RESET_ALL}: {Fore.LIGHTWHITE_EX}{section_lecture}'
          f'{Style.RESET_ALL}\n'
          f'{Fore.LIGHTBLUE_EX}TIPO{Style.RESET_ALL}: {Fore.LIGHTWHITE_EX}{tyype}{Style.RESET_ALL}\n'
          f'{Fore.LIGHTBLUE_EX}LEGENDAS{Style.RESET_ALL}: [ {Fore.LIGHTWHITE_EX}{captions}{Style.RESET_ALL} ]\n'
          f'{Fore.LIGHTBLUE_EX}ID DA AULA{Style.RESET_ALL}: {Fore.LIGHTWHITE_EX}{lecture_id}{Style.RESET_ALL}\n'
          )

def create_directory(base_dir, section_order, section_name):
    """
    Cria um diretório organizado com base no número da seção e nome da seção.
    """
    sanitized_section_name = sanitize_filename(section_name)
    section_order = f'Seção {section_order} {sanitized_section_name}' if section_order and section_order != 'None' else 'Conteúdos'

    dir_path = os.path.join(base_dir, f'{section_order}')
    os.makedirs(dir_path, exist_ok=True)

    return dir_path

def filter_by_id(lecture_id, data: list):
    """Obtém os dados de uma aula específica com base no lecture_id"""
    filtered_data = []
    if not isinstance(data, list):
        return
    for item in data:

        if item.get('lecture_id') == lecture_id:
            filtered_data.append(item)

    return filtered_data

def parser_captions(captions_data: list) -> str:
    """
    Recebe uma lista de dicionários contendo dados de legendas e retorna uma
    string com os códigos de idioma ('locale') de cada legenda, separados por vírgula.

    Se o valor de 'locale' contiver um colchete '[', apenas a parte anterior a ele será considerada.
    Além disso, a cada 4 itens, é inserida uma quebra de linha.

    Args:
        captions_data (list): Lista de dicionários com dados de legendas.

    Returns:
        str: String com os códigos de idioma separados por vírgula e com quebras de linha a cada 4 itens.
    """
    locales = []
    for entry in captions_data:

        locale_str = str(entry.get('locale', '')).split('[', 1)[0].strip()
        if locale_str:
            locales.append(locale_str)

    lines = []
    for i in range(0, len(locales), 4):
        group = locales[i:i + 4]
        lines.append(", ".join(group))

    return "\n".join(lines)
