import os
import shutil
from pathlib import Path
import requests
import yt_dlp
from .animation import Fore, Style
from udemy_userAPI.api import HEADERS_USER

class MPDExtractor:
    def __init__(self):
        self.session = requests.session()
        self.headers = HEADERS_USER

    def extract_mpd(self, url, out_path, lecture_id):
        _temp = []

        file_name = f"index_{lecture_id}.mpd"
        mpd_path = Path(out_path, file_name)

        mpd_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(mpd_path, "wb") as f:
                r = self.session.get(url, headers=self.headers)
                r.raise_for_status()
                f.write(r.content)

            mpd_uri = mpd_path.resolve().as_uri()
            ytdl = yt_dlp.YoutubeDL(
                {"quiet": True, "no_warnings": True, "allow_unplayable_formats": True, "enable_file_urls": True}
            )
            results = ytdl.extract_info(mpd_uri, download=False, force_generic_extractor=True)
            formats = results.get("formats")

            format_id = results.get("format_id")
            best_audio_format_id = format_id.split("+")[1]

            video_formats = [f for f in formats if "video" in f.get("format_note")]
            best_video_format = max(video_formats, key=lambda x: x.get("height", 0), default=None)

            if best_video_format:
                format_id = best_video_format.get("format_id")
                extension = best_video_format.get("ext")
                height = best_video_format.get("height")
                width = best_video_format.get("width")
                fragments = best_video_format.get("fragments", [{}])
                init_url = fragments[0].get("url") or fragments[0].get("path", "")

                _temp.append(
                    {
                        "type": "dash",
                        "height": str(height),
                        "width": str(width),
                        "format_id": f"{format_id},{best_audio_format_id}",
                        "extension": extension,
                        "download_url": url,
                        "init_url": init_url
                    }
                )

        except Exception as e:
            raise Exception(f"erro ao obter MPD: {e}")
        return _temp, str(mpd_path)

def save_external_links(url, title, output_path):
    """
    Salva um link em um arquivo .txt.

    Args:
        url: O URL a ser salvo.
        title: O título que será usado como nome do arquivo.
        output_path: O caminho do diretório onde o arquivo será salvo.
    """
    filename = f'{title}.txt'
    output_path_file = os.path.join(output_path, filename)
    if os.path.exists(output_path_file):
        return

    try:

        os.makedirs(output_path, exist_ok=True)

        with open(output_path_file, 'w', encoding='utf-8') as file:
            file.write(f"{url}\n")
    except Exception as e:
        raise Exception(f"Ocorreu um erro ao salvar o link: {e}")

def download_files(file_url, title, download_path):
    """
    Faz o download de arquivos a partir de uma lista de dicionários.

    Args:
        title:
        file_url:
        self:
        download_path: Caminho onde os arquivos serão salvos.
    """
    try:
        file_path = os.path.join(download_path, title)
        if os.path.exists(file_path):
            return
        response = requests.get(file_url, stream=True, headers=HEADERS_USER)
        response.raise_for_status()

        with open(file_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

    except requests.exceptions.RequestException as e:
        raise Exception(f"Erro ao baixar {title}: {e}")

def get_files_uris(data_file):
    file_url = data_file['File'][0]['file']
    return file_url

def get_init_url(url_mpd, output_path, lecture_id):
    mpd_extractor = MPDExtractor()
    mpd_data, mpd_dir = mpd_extractor.extract_mpd(url=url_mpd, out_path=output_path, lecture_id=lecture_id)
    format_id = mpd_data[0].get('format_id', None)
    url = mpd_data[0].get('download_url', None)
    init_url = mpd_data[0].get("init_url")
    return {'format_id': format_id, 'download_url': url, 'init_url': init_url, 'mpd_dir': mpd_dir}

def get_file(url, name, dir_save):
    try:

        os.makedirs(dir_save, exist_ok=True)

        res = requests.get(url, headers=HEADERS_USER, stream=True)
        res.raise_for_status()

        segment_file = os.path.join(dir_save, name)

        with open(segment_file, 'wt', encoding='utf-8') as f:
            for chunk in res.iter_content(chunk_size=8192):

                f.write(chunk.decode('utf-8'))

        return segment_file
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Erro ao baixar o arquivo {name}: {e}")
    except UnicodeDecodeError as e:
        raise ConnectionError(f"Erro de decodificação no arquivo {name}: {e}")
    except Exception as e:
        raise Exception(f"Erro ao obter 'MPD': {e}")

def save_article(article, output_file,output_name):
    """
    Salva o artigo no arquivo especificado se ele ainda não existir.

    Args:
        article: O conteúdo do artigo a ser salvo.
        output_file: O caminho do arquivo onde o artigo será salvo.

    Returns:
        Retorna uma mensagem indicando se o arquivo foi salvo ou já existia.
    """
    try:
        if os.path.exists(output_file):
            return

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(article)
        print(f"\n\t==> AULA: {Fore.GREEN}{output_name} Baixada!{Style.RESET_ALL}")

    except Exception as e:
        return f"Erro ao salvar o artigo: {e}"

def baixar_video(url_video, output_file, animation, output_name):
    try:
        response = requests.get(url_video, stream=True, headers=HEADERS_USER)
        response.raise_for_status()
        downloaded_size = 0

        try:
            with open(output_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
        finally:
            animation.stop()

        print(f"\n\t==> AULA: {Fore.GREEN}{output_name} Baixada!{Style.RESET_ALL}")

    except requests.exceptions.RequestException as e:
        animation.stop()
        raise Exception(f"Erro ao baixar o vídeo: {e}")

def del_path(path_dir):
    """
    Deleta um diretório com todo o seu conteúdo de forma segura.

    Args:
        path_dir (str): O caminho (path) do diretório a ser deletado.
    """

    if not os.path.exists(path_dir):
        return

    if not os.path.isdir(path_dir):
        return

    try:
        shutil.rmtree(path_dir)
    except Exception as e:
        return
def deletar_arquivos_em_pasta(caminho_da_pasta):
    """
    Deleta todos os arquivos dentro de uma pasta, sem apagar a pasta em si.
    """
    try:

        if not os.path.exists(caminho_da_pasta):
            return

        for nome_do_item in os.listdir(caminho_da_pasta):
            caminho_completo_do_item = os.path.join(caminho_da_pasta, nome_do_item)

            if os.path.isfile(caminho_completo_do_item):
                os.remove(caminho_completo_do_item)

            elif os.path.isdir(caminho_completo_do_item):
                shutil.rmtree(caminho_completo_do_item)
    except Exception as e:
        raise Exception(f"Falha ao remover cache....de downloads!\n\n~> {e}")
