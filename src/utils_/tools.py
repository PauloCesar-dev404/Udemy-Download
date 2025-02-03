import os
from pathlib import Path
import requests
import yt_dlp
from colorama import Fore, Style
from udemy_userAPI.api import HEADERS_USER


class MPDExtractor:
    def __init__(self):
        self.session = requests.session()
        self.headers = HEADERS_USER

    def extract_mpd(self, url, out_path, lecture_id):
        _temp = []

        file_name = f"index_{lecture_id}.mpd"
        mpd_path = Path(out_path, file_name)

        # Certifique-se de que o diretório de saída existe
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

            # Filtra apenas os formatos de vídeo, organiza por resolução e guarda o maior
            video_formats = [f for f in formats if "video" in f.get("format_note")]
            best_video_format = max(video_formats, key=lambda x: x.get("height", 0), default=None)

            if best_video_format:
                format_id = best_video_format.get("format_id")
                extension = best_video_format.get("ext")
                height = best_video_format.get("height")
                width = best_video_format.get("width")
                init_url = best_video_format.get("fragments")[0]["url"]

                _temp.append(
                    {
                        "type": "dash",
                        "height": str(height),
                        "width": str(width),
                        "format_id": f"{format_id},{best_audio_format_id}",
                        "extension": extension,
                        "download_url": best_video_format.get("manifest_url"),
                        "init_url": init_url
                    }
                )

        except Exception as e:
            raise Exception(f"erro ao obter MPD: {e}")
        return _temp, str(mpd_path)


def save_external_links(url, title, output_path):
    """
    Salva um link em um arquivo .txt.
    :param url: O URL a ser salvo.
    :param title: O título que será usado como nome do arquivo.
    :param output_path: O caminho do diretório onde o arquivo será salvo.
    """
    filename = f'{title}.txt'
    output_path_file = os.path.join(output_path, filename)
    if os.path.exists(output_path_file):
        return

    try:
        # Verifica se o diretório de saída existe e cria, se necessário
        os.makedirs(output_path, exist_ok=True)

        # Abrir o arquivo em modo de escrita e salvar o link (substitui o conteúdo existente)
        with open(output_path_file, 'w', encoding='utf-8') as file:
            file.write(f"{url}\n")
    except Exception as e:
        raise Exception(f"Ocorreu um erro ao salvar o link: {e}")


def download_files(file_url, title, download_path):
    """
    Faz o download de arquivos a partir de uma lista de dicionários.

    :param title:
    :param file_url:
    :param self:
    :param download_path: Caminho onde os arquivos serão salvos.
    """
    try:
        file_path = os.path.join(download_path, title)
        if os.path.exists(file_path):
            return
        response = requests.get(file_url, stream=True, headers=HEADERS_USER)
        response.raise_for_status()  # Verifica erros na requisição

        # Caminho do arquivo para salvar
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
        # Fazer o download do arquivo
        res = requests.get(url, headers=HEADERS_USER, stream=True)
        res.raise_for_status()  # Levanta exceção se houver falha no download

        # Nome do arquivo local
        segment_file = os.path.join(dir_save, name)

        # Salvar o conteúdo como texto
        with open(segment_file, 'wt', encoding='utf-8') as f:
            for chunk in res.iter_content(chunk_size=8192):
                # Decodificar o chunk para texto antes de escrever
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

    :param article: O conteúdo do artigo a ser salvo.
    :param output_file: O caminho do arquivo onde o artigo será salvo.
    :return: Retorna uma mensagem indicando se o arquivo foi salvo ou já existia.
    """
    try:
        if os.path.exists(output_file):
            return

        # Salva o artigo no arquivo
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(article)
        print(f"\n\t==> AULA: {Fore.GREEN}{output_name} Baixada!{Style.RESET_ALL}")

    except Exception as e:
        return f"Erro ao salvar o artigo: {e}"


def baixar_video(url_video, output_file, animation, output_name):
    try:
        response = requests.get(url_video, stream=True, headers=HEADERS_USER)
        response.raise_for_status()  # Verifica se houve algum erro na requisição
        downloaded_size = 0

        with open(output_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):  # Baixa em pedaços de 8 KB
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
        animation.stop()
        print(f"\n\t==> AULA: {Fore.GREEN}{output_name} Baixada!{Style.RESET_ALL}")

    except requests.exceptions.RequestException as e:
        raise Exception(f"Erro ao baixar o vídeo: {e}")
