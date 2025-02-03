import os
import sys
import time
import traceback
import webbrowser
import requests
import udemy_userAPI
from colorama import Style, Fore
from ffmpeg_for_python import FFmpeg
from m3u8_analyzer import Wrapper
from udemy_userAPI.api import HEADERS_USER
from utils_ import (filter_resolution, ffmpeg_concatener, sanitize_filename, banner, filter_by_id, get_file,
                    get_files_uris,
                    handle_segments, download_files, save_article, save_external_links, download_captions,
                    create_directory,
                    baixar_video, parser_captions, mux_process, get_init_url, organize_streams, generate_quiz,
                    AnimationConsole,
                    Colors, DEBUG_DEV, segments_dir, frags_dir, downloads_dir, apoio,version
                    )


color = Colors()
auth = udemy_userAPI.UdemyAuth()
ffmpeg = FFmpeg()
if DEBUG_DEV:
    print(color.GRAY,f'MODO DEBUG - {color.SUCCESS}ATIVO{color.RESET}\n')
class M3u8Downloader:
    def __init__(self, output_save_dir, course_id):
        self._dir_cache = segments_dir
        os.makedirs(self._dir_cache, exist_ok=True)
        self._course_id = course_id
        self._output_save_dir = output_save_dir

    def download_m3u8_video(self,
                            media_src,
                            output_name_video,
                            course_id,
                            animation):
        try:
            w = Wrapper()
            infor = w.parsing_m3u8(url=media_src)
            max_reso = filter_resolution(infor.get_resolutions())
            max_uri = infor.filter_resolution(filtering=max_reso)
            uris = w.parsing_m3u8(url=max_uri).uris()
            # count = w.parsing_m3u8(url=max_uri).number_segments()
            self.download_segments(uris=uris,
                                   dir_cache=self._dir_cache,
                                   course_id=self._course_id,
                                   animation=animation)

            ffmpeg_concatener(output_name=output_name_video,
                              output_save=self._output_save_dir,
                              extension='ts',
                              dir_segments=self._dir_cache,
                              course_id=course_id)
        except Exception as e:
            raise Exception(f'Não foi possível baixar o vídeo! erro -> "{e}"')

    def download_segments(self, uris, dir_cache, course_id, animation):
        for index, link in enumerate(uris):
            output_path = os.path.join(dir_cache, f'segmento_{str(index)}_{str(course_id)}.ts')
            self.baixar_segmento(url_segmento=link[1], output_path=output_path, headers=HEADERS_USER)
        animation.stop()

    def baixar_segmento(self, url_segmento: str, output_path: str, headers: dict = None):
        """
        Baixa um segmento de vídeo de uma URL e o salva no diretório especificado.

        Args:
            url_segmento (str): URL do segmento de vídeo a ser baixado.
            output_path (str): Caminho completo onde o segmento será salvo, incluindo o nome do arquivo.
            headers (dict, opcional): Cabeçalhos HTTP adicionais para a requisição (opcional).

        Raises:
            M3u8FileError: Erros relacionados ao arquivo ou diretório.
            M3u8NetworkingError: Erros relacionados à conexão de rede.
        """
        try:
            # Garantir que o diretório de destino exista
            output_dir = os.path.dirname(output_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)  # Cria o diretório, se não existir

            if os.path.exists(output_path):
                return  # O arquivo já existe, nada a fazer

            # Baixa o segmento do vídeo
            resposta = requests.get(url_segmento, headers=headers, stream=True)
            chunk_size = 1024  # Tamanho do chunk (1 KB)
            total_bytes = 0
            # Salva o segmento no arquivo de saída
            with open(output_path, 'wb') as arquivo_segmento:
                for chunk in resposta.iter_content(chunk_size=chunk_size):
                    if chunk:
                        arquivo_segmento.write(chunk)
                        total_bytes += len(chunk)
        except FileNotFoundError:
            raise FileNotFoundError(f"Arquivo ou diretório '{output_path}' não encontrado.")
        except PermissionError:
            raise PermissionError(f"Permissão negada ao tentar acessar '{output_path}'.")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Não foi possível se conectar ao servidor. Detalhes: {e}")
        except Exception as e:
            raise NotImplementedError(f"Erro inesperado ao manipular arquivo: {e}")


class Auth:
    def __init__(self):
        self._password = None
        self._email = None
        self._auth = udemy_userAPI.UdemyAuth()

    def is_loggin(self) -> bool:
        return self._auth.verif_login()

    def remove_data(self):
        self._auth.remove_cookies()

    def login(self, credentials: dict, anima):
        self._email = credentials.get('email')
        self._password = credentials.get('password', '')
        time.sleep(3)
        anima.stop()
        if self._password:
            self._auth.login(email=self._email, password=self._password)
            animate2 = AnimationConsole(text='Autenticando...')
            animate2.start()
            if self._auth.verif_login():
                animate2.stop()
                return True
            else:
                animate2.stop()
                return False
        else:
            self._auth.login_passwordless(email=self._email)
        animate2 = AnimationConsole(text='Autenticando...')
        animate2.start()
        if self._auth.verif_login():
            animate2.stop()
            return True
        else:
            animate2.stop()
            return False


class UdemyDownloader:
    def __init__(self,
                 cache_saved_courses: str,
                 course_id: int,
                 lecture_title: str = '',
                 captions:bool = False):
        anima = AnimationConsole(text='Obtendo informações do curso')
        anima.start()
        self._captions = captions
        self._lecture_title_continue = lecture_title
        self._course_id = str(course_id)
        self._details_course = None
        self._title_course = ''
        self._instance_udemy = udemy_userAPI.Udemy()
        self._lectures = []
        self._details_course = self._instance_udemy.get_details_course(course_id)
        self.load_details_course()
        self._additional_files = self._details_course.get_additional_files
        self.lectures_data = []
        self._cache_saved_courses = os.path.join(cache_saved_courses, sanitize_filename(self._title_course))
        os.makedirs(self._cache_saved_courses, exist_ok=True)
        anima.stop()


    def load_details_course(self):
        try:

            self._title_course = self._details_course.title_course
            self._lectures = self._details_course.get_lectures
        except Exception as e:
            raise Exception(f"Erro '{e}' ao tentar obter curso....")

    def download_lectures(self):
        """
        Processa os detalhes das aulas, salvando vídeos, artigos e recursos associados em diretórios organizados.
        Em caso de falha, tenta novamente até o máximo de tentativas permitido.
        """
        max_attempts = 20  # Número máximo de tentativas para cada aula
        index = 0
        titles = []
        ids = []
        print(f"\t\t{color.INFO} Baixando o Curso:{color.RESET}{self._title_course}\n\n")
        for aule in self._lectures:
            index += 1
            attempt = 0
            success = False
            lecture_id = str(aule.get('lecture_id',''))
            titles.append(sanitize_filename(aule.get('title')))
            ids.append(lecture_id)
            if DEBUG_DEV:
                print(f"PORCESSANDO-AULA: {index}.{sanitize_filename(aule.get('title'))}")
            if self._lecture_title_continue:
                if (self._lecture_title_continue not in f"{index}.{sanitize_filename(aule.get('title'))}" and
                        str(self._lecture_title_continue) != lecture_id):
                    continue
            while attempt < max_attempts and not success:
                try:
                    attempt += 1
                    # Coleta de informações da aula
                    lecture_id = aule.get('lecture_id')
                    section_lecture = sanitize_filename(aule.get('section'))
                    title = f"{index}.{sanitize_filename(aule.get('title'))}"
                    lecture_title_origin = aule.get('title')
                    section_order = aule.get('section_order')
                    # Criar diretórios de saída
                    output_save_dir = create_directory(
                        base_dir=self._cache_saved_courses,
                        section_order=section_order,
                        section_name=section_lecture,
                    )
                    # Obter detalhes da aula
                    details_lecture = self._details_course.get_details_lecture(lecture_id=lecture_id)
                    output_save_dir_files = os.path.join(output_save_dir, 'Recursos')
                    # Obter arquivos e status DRM
                    files_course = details_lecture.get_resources
                    is_drm = details_lecture.course_is_drmed().get_key_for_lesson()
                    # Processar tipo de conteúdo
                    if details_lecture.get_asset_type.lower() == 'video':
                        streams_data = organize_streams(details_lecture.get_media_sources)
                        self._process_video(
                            streams_data=streams_data,
                            is_drm=is_drm,
                            title=title,
                            section_lecture=section_lecture,
                            section_order=section_order,
                            files_course=files_course,
                            details_lecture=details_lecture,
                            output_save_dir_files=output_save_dir_files,
                            output_save_dir=output_save_dir,
                            lecture_id=lecture_id
                        )
                        # Se chegou aqui, a tentativa foi bem-sucedida
                        success = True
                    elif details_lecture.get_asset_type.lower() == 'article':
                        banner(
                            title=title,
                            section_lecture=section_lecture,
                            section_order=section_order,
                            tyype='Artigo',
                            lecture_id=lecture_id,
                            captions=''
                        )
                        article_name = f'{title}.html'
                        output_file = os.path.join(output_save_dir, article_name)
                        # Verifica se existem arquivos adicionais associados
                        if self._additional_files:
                            if isinstance(self._additional_files, list):
                                files_da_aula = filter_by_id(lecture_id, self._additional_files)
                                self.download_files(
                                    files_course=files_da_aula,
                                    output_save_dir_files=output_save_dir_files,
                                    title_lecture=title
                                )
                            elif isinstance(self._additional_files, dict):
                                lecture_title = self._additional_files.get('lecture_title')
                                if lecture_title_origin == lecture_title:
                                    files_da_aula = self._additional_files
                                    self.download_files(
                                        files_course=files_da_aula,
                                        output_save_dir_files=output_save_dir_files,
                                        title_lecture=title
                                    )
                        # Salva o artigo no formato HTML
                        if os.path.exists(output_file):
                            print(f"\t==>{color.WARNING}Essa aula já existe! {color.RESET}")
                            break
                        save_article(article=details_lecture.get_articles, output_file=output_file,
                                     output_name=article_name)
                        # Se chegou aqui, a tentativa foi bem-sucedida
                        success = True
                    elif details_lecture.get_asset_type.lower() == 'quiz':
                        banner(
                            title=title,
                            section_lecture=section_lecture,
                            section_order=section_order,
                            tyype='Quiz',
                            lecture_id=lecture_id,
                            captions=''
                        )
                        quiz_name = f'{title}.html'
                        output_file = os.path.join(output_save_dir, quiz_name)
                        # Salva o artigo no formato HTML
                        if os.path.exists(output_file):
                            print(f"\t==>{color.WARNING}Essa aula já existe! {color.RESET}")
                            break
                        quiz_object = details_lecture.quiz_object().content()
                        quiz_html = generate_quiz(quiz_object)
                        save_article(article=quiz_html,
                                     output_file=output_file,
                                     output_name=quiz_name)
                        # Se chegou aqui, a tentativa foi bem-sucedida
                        success = True
                    else:
                        raise Warning(
                            f"\n\t{color.ERROR}Aulas do tipo `{details_lecture.get_asset_type.lower()}` ainda não"
                              f" consigo baixar! contate o desenvolvedor...{color.RESET}\n"
                        )

                except KeyboardInterrupt:
                    print(f"\n\t{color.ERROR}Downloads Interrompidos!{color.RESET}")
                    sys.exit()
                except Exception as e:
                    import traceback
                    if DEBUG_DEV:
                        e = traceback.format_exc()
                        print(e)
                        sys.exit(1)

                    print(f'Ocorreu um erro ao processar a aula'
                          f' "{aule.get('title')}"\n'
                          f'Detalhes: {e}\n\n,'
                          f'tentando novamente...')
                    time.sleep(10)
                    if attempt >= max_attempts:
                        print(f"Falha ao processar a aula '{aule.get('title')}'"
                              f" após {max_attempts} tentativas.\nTente novamente!"
                              f"\n\nDetalhes do erro: {e}")
                        sys.exit(1)
            # time.sleep(random.randint(1, 5))
        if self._lecture_title_continue:
            if str(self._lecture_title_continue) not in titles and str(self._lecture_title_continue) not in ids:
                print(f"Aula '{self._lecture_title_continue}' não encontrada! no curso {self._title_course}")
                sys.exit(1)
        print(f"\n{color.SUCCESS}O Curso {color.INFO}{self._title_course}{color.RESET}"
              f"{color.SUCCESS} Foi baixado com sucesso!{color.RESET}\n\n\n\n"
              f"\t{color.WARNING}considere um apoio ao desenvolvedor:{color.RESET}{apoio}")

    def _process_video(self,
                       streams_data,
                       is_drm,
                       title,
                       section_order,
                       section_lecture,
                       files_course,
                       output_save_dir,
                       output_save_dir_files,
                       lecture_id,
                       details_lecture
                       ):
        dash_stream = streams_data.get('dash', [])
        m3u8_stream = streams_data.get('hls', [])
        mp4_streams = streams_data.get('mp4', [])
        if DEBUG_DEV:
            print("\nSTREAM-DATA-DA-AULA:", streams_data, '\n')
            print("\nRECURSOS-DA-AULA:", files_course, '\n')
        if len(m3u8_stream) > 0 and not is_drm and len(dash_stream) < 1:
            if DEBUG_DEV:
                print("m3u8-FILE!!")
            banner(title=title,
                   section_order=section_order,
                   section_lecture=section_lecture,
                   lecture_id=lecture_id,
                   captions=parser_captions(details_lecture.get_captions.languages()))
            filename = f'{title}.mp4'
            final = os.path.join(output_save_dir, filename)
            if files_course:
                # baixar recursos
                self.download_files(files_course=files_course,
                                    output_save_dir_files=output_save_dir_files,
                                    title_lecture=title)
            if os.path.exists(final):
                print(f"\t==>{color.WARNING}Essa aula já existe! {color.RESET}")
                return
            if self._captions:
                captions_path = os.path.join(output_save_dir, 'Legendas', title)
                os.makedirs(captions_path, exist_ok=True)
                anime = AnimationConsole(text="Baixando legendas")
                anime.start()
                captions_aule = details_lecture.get_captions.languages()
                if captions_aule:
                    download_captions(captions=captions_aule,
                                      details_lecture=details_lecture,
                                      path_save=captions_path)
                    time.sleep(1)
                    anime.update_message(new_text='Salvando todas legendas disponíveis...')
                time.sleep(0.5)
                anime.stop()
            hls = streams_data['hls'][0].get('src')
            m3u8 = M3u8Downloader(course_id=self._course_id,
                                  output_save_dir=output_save_dir)
            animation = AnimationConsole(text='Baixando Segmentos')
            animation.start()
            m3u8.download_m3u8_video(media_src=hls,
                                     output_name_video=filename,
                                     course_id=self._course_id,
                                     animation=animation)
        elif len(dash_stream) > 0 and is_drm:
            if DEBUG_DEV:
                print("DASH-FILE!!")
            banner(title=title,
                   section_order=section_order,
                   section_lecture=section_lecture,
                   captions=parser_captions(details_lecture.get_captions.languages()),
                   lecture_id=lecture_id)
            filename = f'{title}.mp4'
            final = os.path.join(output_save_dir, filename)
            if files_course:
                # baixar recursos
                self.download_files(files_course=files_course,
                                    output_save_dir_files=output_save_dir_files,
                                    title_lecture=title)
            if os.path.exists(final):
                print(f"\t==>{color.WARNING}Essa aula já existe! {color.RESET}")
                return
            if self._captions:
                captions_path = os.path.join(output_save_dir, 'Legendas', title)
                os.makedirs(captions_path, exist_ok=True)
                anime = AnimationConsole(text="Baixando legendas")
                anime.start()
                captions_aule = details_lecture.get_captions.languages()
                if captions_aule:
                    download_captions(captions=captions_aule,
                                      details_lecture=details_lecture,
                                      path_save=captions_path)
                    time.sleep(1)
                    anime.update_message(new_text='Salvando todas legendas disponíveis...')
                time.sleep(0.5)
                anime.stop()
            url_mpd = streams_data['dash'][0].get('src')
            mpd_path = get_file(url=url_mpd, name=f'mpd_{lecture_id}.mpd', dir_save=frags_dir)

            infor_mpd = get_init_url(url_mpd=url_mpd,
                                     output_path=frags_dir,
                                     lecture_id=lecture_id)
            key = details_lecture.course_is_drmed().get_key_for_lesson().split(':')[1]
            p = handle_segments(url=infor_mpd.get('download_url'),
                                format_id=infor_mpd.get('format_id'),
                                lecture_id=str(lecture_id),
                                path_frags=frags_dir)
            mux_process(mpd_path=mpd_path,
                        video_title=filename,
                        audio_key=key,
                        video_key=key,
                        output_dir=output_save_dir,
                        audio_filepath=p.get('audio_filepath'),
                        video_filepath=p.get('video_filepath'))
        elif len(mp4_streams) > 0 and not is_drm:
            if DEBUG_DEV:
                print("MP4-FILE!!")
            banner(title=title,
                   section_order=section_order,
                   section_lecture=section_lecture,
                   lecture_id=lecture_id,
                   captions=parser_captions(details_lecture.get_captions.languages()))
            filename = f'{title}.mp4'
            final = os.path.join(output_save_dir, filename)
            if files_course:
                # baixar recursos
                self.download_files(files_course=files_course,
                                    output_save_dir_files=output_save_dir_files,
                                    title_lecture=title)
            if os.path.exists(final):
                print(f"\t==>{color.WARNING}Essa aula já existe! {color.RESET}")
                return
            if self._captions:
                captions_path = os.path.join(output_save_dir, 'Legendas', title)
                os.makedirs(captions_path, exist_ok=True)
                anime = AnimationConsole(text="Baixando legendas")
                anime.start()
                captions_aule = details_lecture.get_captions.languages()
                if captions_aule:
                    download_captions(captions=captions_aule,
                                      details_lecture=details_lecture,
                                      path_save=captions_path)
                    time.sleep(1)
                    anime.update_message(new_text='Salvando todas legendas disponíveis...')
                time.sleep(0.5)
                anime.stop()
            hls = streams_data['mp4'][0].get('src')
            output_file = os.path.join(output_save_dir, filename)
            animation = AnimationConsole(text='Baixando Vídeo')
            animation.start()
            baixar_video(url_video=hls, output_file=output_file, animation=animation, output_name=title)

    @staticmethod
    def download_files(files_course, output_save_dir_files, title_lecture):
        try:
            output_path = os.path.join(output_save_dir_files, title_lecture.strip())
            # Iniciando a animação para o download
            animation = AnimationConsole(text='Baixando Recursos da Aula')
            animation.start()
            # Verificando se a entrada é um único arquivo ou uma lista de arquivos
            if isinstance(files_course, dict):
                files_course = [files_course]
            # Iterando sobre os arquivos para fazer o download
            for file_course in files_course:
                external_link = file_course.get('external_link', False)
                if external_link:
                    title_file = sanitize_filename(file_course.get('title-file', ''))
                    file_url = file_course.get('data-file')
                    file_pth_title = title_file
                    file_pth = os.path.join(str(output_path), file_pth_title)
                    if os.path.exists(file_pth):
                        animation.update_message(new_text='Recursos existentes....')
                        time.sleep(1)
                        animation.stop()
                        return
                    else:
                        # Chama a função para salvar links externos
                        os.makedirs(output_path, exist_ok=True)
                        save_external_links(title=title_file, output_path=output_path, url=file_url)
                        # Atualizando a animação
                        animation.update_message(new_text='Salvando recursos baixados')
                        time.sleep(3)
                else:
                    # Obtém os arquivos para download, caso não seja um link externo
                    file_url = get_files_uris(file_course.get('data-file'))
                    title_file = sanitize_filename(file_course.get('title-file', ''))
                    file_pth_title = title_file
                    file_pth = os.path.join(str(output_path), file_pth_title)
                    if os.path.exists(file_pth):
                        animation.update_message(new_text='Recursos existentes....')
                        time.sleep(1)
                        animation.stop()
                        return
                    # Chama a função para fazer o download do arquivo
                    os.makedirs(output_path, exist_ok=True)
                    # Atualizando a animação
                    download_files(file_url, title_file, output_path)
                    animation.update_message(new_text='Salvando recursos baixados')
                    time.sleep(3)
            animation.stop()
        except Exception as e:
            if DEBUG_DEV:
                e = traceback.format_exc()
            raise Exception(f"Falha ao obter recursos da aula! -> {e}")


def logo():
    # Definindo as informações
    ascii_art = f'''{Fore.LIGHTBLACK_EX}   
██╗   ██╗██████╗ ███████╗███╗   ███╗██╗   ██╗    ██████╗  ██████╗ ██╗    ██╗███╗   ██╗██╗      ██████╗  █████╗ ██████╗ 
██║   ██║██╔══██╗██╔════╝████╗ ████║╚██╗ ██╔╝    ██╔══██╗██╔═══██╗██║    ██║████╗  ██║██║     ██╔═══██╗██╔══██╗██╔══██╗
██║   ██║██║  ██║█████╗  ██╔████╔██║ ╚████╔╝     ██║  ██║██║   ██║██║ █╗ ██║██╔██╗ ██║██║     ██║   ██║███████║██║  ██║
██║   ██║██║  ██║██╔══╝  ██║╚██╔╝██║  ╚██╔╝      ██║  ██║██║   ██║██║███╗██║██║╚██╗██║██║     ██║   ██║██╔══██║██║  ██║
╚██████╔╝██████╔╝███████╗██║ ╚═╝ ██║   ██║       ██████╔╝╚██████╔╝╚███╔███╔╝██║ ╚████║███████╗╚██████╔╝██║  ██║██████╔╝
 ╚═════╝ ╚═════╝ ╚══════╝╚═╝     ╚═╝   ╚═╝       ╚═════╝  ╚═════╝  ╚══╝╚══╝ ╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═════╝ 
                                                                                                                                                                                                                                                                                                                            
{Style.RESET_ALL}'''
    art = f"""

                            {ascii_art}
{Fore.BLUE}"(...A curiosidade é a chave para abrir portas que você nem sabia que existiam...)"

{Fore.LIGHTYELLOW_EX}~{Style.RESET_ALL} {Fore.LIGHTBLACK_EX}>{Style.RESET_ALL} v{version}
{Fore.LIGHTYELLOW_EX}~{Style.RESET_ALL} {Fore.LIGHTBLACK_EX}>{Style.RESET_ALL} by: PauloCesar-Dev404
Digite o comando {Fore.LIGHTBLACK_EX}--help{Style.RESET_ALL} para ver os comandos disponíveis.
"""

    print(art)


def open_browser(output_file):
    try:
        # Tenta abrir o arquivo com o navegador configurado no sistema
        webbrowser.open(output_file)
        return True
    except webbrowser.Error as e:
        # Caso ocorra um erro, significa que não há navegador configurado
        print("Erro: Nenhum navegador disponível para abrir o arquivo.")
        return None


def save_html(courses):
    """
    Cria um HTML para exibir os cursos do usuário com a imagem e um botão.
    O botão copia o ID do curso ao ser clicado.
    :param courses: Lista de cursos com dados como id, título e imagem.
    """
    # Gera o HTML
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Meus Cursos</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f9f9f9;
            }
            .course {
                border: 1px solid #ddd;
                border-radius: 5px;
                margin: 15px 0;
                padding: 15px;
                display: flex;
                align-items: center;
                background-color: #fff;
            }
            .course img {
                max-width: 150px;
                margin-right: 20px;
                border-radius: 5px;
            }
            .course-info {
                flex: 1;
            }
            .course-info h3 {
                margin: 0;
                color: #333;
            }
            .copy-button {
                padding: 10px 20px;
                background-color: #007bff;
                color: #fff;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }
            .copy-button:hover {
                background-color: #0056b3;
            }
            .copy-button:disabled {
                background-color: #aaa;
                cursor: not-allowed;
            }
        </style>
    </head>
    <body>
        <h1>Meus Cursos</h1>
        <h2>Copie o ID e cole no terminal para baixar</h2>
    """
    for course in courses:
        course_id = course.get('id')
        title = course.get('title')
        image = course.get('image_240x135')
        html_content += f"""
        <div class="course">
            <img src="{image}" alt="Imagem de {title}">
            <div class="course-info">
                <h3>{title}</h3>
                <button class="copy-button" onclick="copyToClipboard('{course_id}', this)">Copiar ID</button>
            </div>
        </div>
        """
    html_content += """
    <script>
        function copyToClipboard(id, button) {
            navigator.clipboard.writeText(id).then(() => {
                const originalText = button.innerText;
                button.innerText = 'Copiado!';
                button.disabled = true;

                setTimeout(() => {
                    button.innerText = originalText;
                    button.disabled = false;
                }, 3000);
            }).catch(err => {
                alert('Falha ao copiar o ID: ' + err);
            });
        }
    </script>
    </body>
    </html>
    """
    # Salva o HTML em um arquivo
    output_file = os.path.join(downloads_dir, "my_courses.html")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(html_content)

    # Lógica para exibir no terminal
    # Calcula o comprimento do maior título
    max_title_length = max(len(course.get('title', '')) for course in courses)
    separator_line = f"{Fore.LIGHTWHITE_EX}{'_._' * ((max_title_length // 3) + 3)}{Style.RESET_ALL}"

    while True:
        open_web = input('Abrir seus cursos no navegador? (s/n): ')
        if open_web.lower() == 's':
            open_browser(output_file)
            break
        elif open_web.lower() == 'n':
            for course in courses:
                course_id = course.get('id')
                title = course.get('title')
                print(f"{Fore.LIGHTMAGENTA_EX}Curso:{Style.RESET_ALL} {Fore.LIGHTWHITE_EX}{title}{Style.RESET_ALL}")
                print(f"{Fore.LIGHTMAGENTA_EX}ID:{Style.RESET_ALL} {Fore.LIGHTWHITE_EX}{course_id}{Style.RESET_ALL}")
                print(f"{Fore.LIGHTWHITE_EX}{separator_line}{Style.RESET_ALL}")
            break
        else:
            print(f"{Fore.LIGHTRED_EX}Resposta inválida! Responda com {Fore.LIGHTYELLOW_EX}'s'{Style.RESET_ALL} "
                  f"{Fore.LIGHTRED_EX}para sim ou {Fore.LIGHTYELLOW_EX}'n'{Style.RESET_ALL} para não.{Style.RESET_ALL}")


def get_image(courses: list, course_id):
    """
    Baixa a imagem de um curso especificado pelo id
    :param courses: lista de cursos (dict)
    :param course_id: id do curso
    :return: caminho do arquivo (filepath)
    """

    for course in courses:
        current_course_id = course.get('id')
        if str(current_course_id) == str(course_id):
            title = course.get('title')
            image_url = course.get('image_240x135', '')
            if not image_url:
                return None

            sanitized_title = sanitize_filename(title)
            filepath_dir = os.path.join(downloads_dir, sanitized_title)
            os.makedirs(filepath_dir, exist_ok=True)

            filepath_name = f'{sanitized_title}.jpg'
            filepath = os.path.join(filepath_dir, filepath_name)

            try:
                response = requests.get(image_url, stream=True)
                response.raise_for_status()  # Garante que status 4xx/5xx levante uma exceção

                with open(filepath, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        file.write(chunk)
                return filepath
            except requests.exceptions.RequestException as e:
                return None
            except IOError as e:
                return None


def menu(captions:bool = False):
    """
    Exibe um menu para o usuário e gera um HTML com os cursos.
    """
    try:
        logo()
        udemy = udemy_userAPI.Udemy()
        anima = AnimationConsole(text='Carregando seus cursos ')
        anima.start()
        mycourses = udemy.my_subscribed_courses()
        if not mycourses:
            anima.stop()
            print(f"Não encontrei nenhum curso,verique se você estar inscrito em algum e tente novamente!")
            sys.exit(1)
        anima.stop()

        save_html(mycourses)  # Gera o HTML com os cursos

        max_attempts = 3  # Número máximo de tentativas
        attempts = 0  # Contador de tentativas

        while attempts < max_attempts:
            try:
                course_id = input(
                    f"\n\n{Fore.LIGHTYELLOW_EX}Digite o {Fore.LIGHTRED_EX}id{Style.RESET_ALL}{Fore.LIGHTYELLOW_EX} "
                    f"do curso desejado{Style.RESET_ALL}\n\t=>  ").strip()
                # Verificar se a entrada está vazia
                if not course_id:
                    anima.update_message(new_text="Entrada vazia! Tentando novamente...")
                    anima.start()
                    time.sleep(1)
                    anima.stop()
                    attempts += 1
                    continue

                # Tentar converter para inteiro
                if course_id.isnumeric():
                    course_id = int(course_id)
                else:
                    anima.update_message(new_text="Somente números! Tentando novamente...")
                    anima.start()
                    time.sleep(1)
                    anima.stop()
                    attempts += 1
                    continue
                if course_id < 1:
                    anima.update_message(new_text="ID inválido! Tentando novamente...")
                    anima.start()
                    time.sleep(1)
                    anima.stop()
                    attempts += 1
                    continue
                get_image(courses=mycourses, course_id=course_id)
                dw = UdemyDownloader(course_id=course_id,
                                     cache_saved_courses=downloads_dir,
                                     captions=captions)
                dw.download_lectures()
                break  # Sai do loop se o download for bem-sucedido

            except ValueError as ve:
                anima.update_message(f"Erro: {ve}, tentando de novo...")
                anima.start()
                time.sleep(2)
                anima.stop()
                attempts += 1
            except Exception as e:
                anima.update_message(f"Erro inesperado: {e}, tentando de novo...")
                anima.start()
                time.sleep(2)
                anima.stop()
                attempts += 1

            if attempts >= max_attempts:
                print(
                    f"\nLimite de tentativas alcançado. Por favor, verifique e tente novamente mais tarde.")
                break
    except Exception as e:
        if DEBUG_DEV:
            e = traceback.format_exc()
        raise Exception(f'Erro: {e}')


def menu_user(course_id: str = '',
              lecture_title: str = '',
              captions:bool = False,
              caption_lang:str = ''):
    """
    Exibe um menu para o usuário e gera um HTML com os cursos.
    :param course_id: id do curso
    :param lecture_title: id da aula
    :param captions: salvar legendas
    :param caption_lang: parametro futuro....para salvar apenas 01 idioma
    :return:
    """
    try:
        if not auth.verif_login():
            print(f"{Fore.LIGHTRED_EX}Sessão expirada!")
            sys.exit(1)
        logo()
        udemy = udemy_userAPI.Udemy()
        anima = AnimationConsole(text='Carregando...')
        anima.start()
        mycourses = udemy.my_subscribed_courses()
        idds = []
        if mycourses:
            for c in mycourses:
                course_idd = str(c.get('id', 0))
                idds.append(course_idd)

        if course_id not in idds:
            anima.stop()
            print(f"{Fore.LIGHTRED_EX}Não encontrei nenhum curso relacionado ao id"
                  f" '{Fore.LIGHTBLACK_EX}{course_id}{Fore.LIGHTRED_EX}',verique se você estar inscrito"
                  f" no mesmo e tente novamente!{Style.RESET_ALL}")
            sys.exit(1)
        anima.stop()
        max_attempts = 3  # Número máximo de tentativas
        attempts = 0  # Contador de tentativas
        while attempts < max_attempts:
            try:
                get_image(courses=mycourses, course_id=course_id)
                dw = UdemyDownloader(course_id=int(course_id),
                                     cache_saved_courses=downloads_dir,
                                     lecture_title=lecture_title,
                                     captions=captions)
                dw.download_lectures()
                break  # Sai do loop se o download for bem-sucedido

            except ValueError as ve:
                anima.update_message(f"Erro: {ve}, tentando de novo...")
                anima.start()
                time.sleep(2)
                anima.stop()
                attempts += 1
            except Exception as e:
                anima.update_message(f"Erro inesperado: {e}, tentando de novo...")
                anima.start()
                time.sleep(2)
                anima.stop()
                attempts += 1

            if attempts >= max_attempts:
                print(
                    f"\nLimite de tentativas alcançado. Por favor, verifique e tente novamente mais tarde.")
                break
    except Exception as e:
        if DEBUG_DEV:
            e = traceback.format_exc()
        raise Exception(f'Erro: {e}')


def panel(logintype: str = 'auth'):
    # Exibe o logotipo
    logo()
    credentials = None
    # Instanciando o sistema de autenticação
    oauth = Auth()
    # Verifica se o usuário já está logado
    if not oauth.is_loggin():
        # Solicita as credenciais do usuário
        print(f"\t\t{Fore.LIGHTMAGENTA_EX}Login na sua conta da Udemy{Style.RESET_ALL}\n")
        email = input("Digite seu e-mail: ").strip()

        # Validações básicas das entradas
        if not email:
            print("E-mail e senha não podem estar vazios. Tente novamente.")
            return
        if "@" not in email or "." not in email:
            print("Por favor, insira um e-mail válido.")
            return

        # Solicita a senha dependendo do tipo de autenticação
        if logintype == 'auth':
            password = input("Digite sua senha: ")
            credentials = {'email': email, 'password': password}
        elif logintype == 'code':
            credentials = {'email': email, 'password': ''}  # Não pede senha no caso de autenticação por código

        anima = AnimationConsole(text='Verificando...')
        anima.start()

        # Tenta fazer o login
        try:
            if oauth.login(credentials=credentials, anima=anima):
                anima.update_message(new_text='Salvando sua sessão...')
                time.sleep(3)
                anima.stop()
                print(f"{Fore.GREEN}Login efetuado com sucesso!\n\n\t-> Sessão ATIVA{Style.RESET_ALL}")
            else:
                anima.stop()
                print("Falha no login. Verifique suas credenciais e tente novamente.")
        except KeyboardInterrupt:
            sys.exit()
        except Exception as e:
            if DEBUG_DEV:
                e = traceback.format_exc()
            print(f"Erro: {e}")
    else:
        menu()


def commands():
    """
    Exibe os comandos disponíveis com suas descrições.
    """
    logo()
    grey = Fore.LIGHTBLACK_EX
    yellow = Fore.LIGHTYELLOW_EX
    reset = Style.RESET_ALL
    cmds = f"""
        {yellow}COMANDOS DISPONÍVEIS{reset}

        {grey}--remove-data{reset}        - Remove todo o cache de sessão do usuário.

        {grey}--auth-code{reset}          - Realiza login utilizando o código de autorização enviado por e-mail.

        {grey}--auth-credentials{reset}   - Realiza login utilizando e-mail e senha.

        {grey}--my-section{reset}         - Inicia o aplicativo com uma sessão ativa.

        {grey}--help{reset}               - Exibe os comandos disponíveis.

        {yellow}OPÇÕES DO COMANDO {grey}--my-section{reset}

        {yellow}ESPECIFICANDO UM CURSO:{reset}  
          {grey}--course_id <COURSE-ID>{reset}          - Inicia o download do curso com o identificador especificado. Recomendado para evitar copiar e colar o ID toda vez.
                Exemplo01: {grey}udemy_download --my-section --course_id https://www.udemy.com/course-dashboard-redirect/?course_id=12345{reset}
                Exemplo02: {grey}udemy_download --my-section --course_id 12345{reset}
        
        {yellow}ESPECIFICANDO UMA AULA PARA INICIAR A PARTIR DELA:{reset}
          {grey}--course_id <COURSE-ID>{reset} {grey}--lecture_title <TITLE>{reset} - Inicia o download do curso a partir da aula com o título especificado. Recomendado para continuar o progresso.
            Exemplo: {grey}udemy_download --my-section --course_id 12345 --lecture_title "Introdução"{reset}
                    
          {grey}--course_id <COURSE-ID ou URL-DO-CURSO>{reset} {grey}--lecture_id <ID>{reset} - Inicia o download do curso a partir da aula com o id especificado. Recomendado para continuar o progresso.
            Exemplo01: {grey}udemy_download --my-section --course_id 12345 --lecture_id 123456{reset}
    
        {yellow}OPÇÕES DO COMANDO {grey}--course_id{reset} {reset}
        
                {grey}--save-captions{reset} - Salva todas faixas de legendas com os seus idiomas disponíveis de uma aula, em um diretório do seu capítulo. O nome do diretório é o mesmo nome da aula.
    
    """
    print(cmds)


def main():
    captions = None
    try:
        args = sys.argv[1:]  # Captura os argumentos da linha de comando, excluindo o nome do script
        if "--remove-data" in args[:12]:
            a = AnimationConsole(text="Removendo cache... ")
            a.start()
            auth = Auth()
            auth.remove_data()
            time.sleep(2)
            a.stop()
            sys.exit(0)
        elif '--auth-credentials' in args[:18]:
            panel(logintype='auth')
        elif '--auth-code' in args[:12]:
            panel(logintype='code')
        elif '--help' in args[:6] or '--h' in args[:6]:
            commands()
        elif '--my-section' in args[:12] and '--course_id' not in args:
            if '--save-captions' in args:
                captions = True
            atth = Auth()
            if not atth.is_loggin():
                print(f"{Fore.LIGHTRED_EX}Você não possui uma Sessão ativa!{Style.RESET_ALL}")
                sys.exit(1)
            else:
                if '--save-captions' in args:
                    captions = True
                menu(captions)
        elif '--my-section' in args[:12] and '--course_id' in args[:25]:
            course_id_index = args.index('--course_id') + 1
            lecture_title = ''
            lecture_id = ''
            if '--lecture_title' in args and not '--lecture_id' in args:
                lecture_id_index = args.index('--lecture_title') + 1
                if lecture_id_index < len(args):
                    lecture_title = args[lecture_id_index]
                else:
                    print(
                        f"{Fore.LIGHTRED_EX}'--lecture_title' está sem valor!"
                        f"{Style.RESET_ALL}")
                    sys.exit(1)
            if '--lecture_id' in args and not '--lecture_title' in args:
                lecture_id_index = args.index('--lecture_id') + 1
                if lecture_id_index < len(args):
                    lecture_title = args[lecture_id_index]
                else:
                    print(
                        f"{Fore.LIGHTRED_EX}'--lecture_id' está sem valor!"
                        f"{Style.RESET_ALL}")
                    sys.exit(1)
            if course_id_index < len(args):
                if '--save-captions' in args:
                    captions = True
                course_id = args[course_id_index]
                if course_id.startswith('https://'):
                    course_id = course_id.split('course_id=')
                    if len(course_id) > 1:
                        course_id = course_id[1]
                atth = Auth()
                if not atth.is_loggin():
                    print(f"{Fore.LIGHTRED_EX}Você não possui uma Sessão ativa!{Style.RESET_ALL}")
                    sys.exit(1)
                else:
                    menu_user(course_id, lecture_title,captions=captions)
            else:
                print(f'{Fore.LIGHTRED_EX}Não foi fornecido um course_id após --course_id!{Style.RESET_ALL}')
        else:
            print(f"{Fore.LIGHTRED_EX}Comando inválido!{Style.RESET_ALL}"
                  f"\n\t\t{Fore.LIGHTBLACK_EX}--help{Style.RESET_ALL}"
                  f" {Fore.LIGHTRED_EX}para ver todos comandos disponíveis!{Style.RESET_ALL}")

    except KeyboardInterrupt:
        sys.exit()
    except Exception as e:
        print(f'{Fore.LIGHTRED_EX}Não foi possível iniciar!{Style.RESET_ALL} {e}')
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit()
    except Exception as e:
        sys.exit(1)
