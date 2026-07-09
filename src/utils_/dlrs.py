import os
import re
import shutil
import time
import traceback
from .animation import Fore, Style
from yt_dlp import YoutubeDL
from ffmpeg_for_python import FFmpeg
import logging

from . import deletar_arquivos_em_pasta
from .constants import DEBUG_DEV
logging.disable(logging.CRITICAL)

class NoLogger:
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        pass

def handle_segments(url, format_id, lecture_id, path_frags):
    """
    Faz o download de segmentos de vídeo e áudio usando yt-dlp diretamente como biblioteca.
    """
    from .animation import AnimationConsole

    video_filepath_enc = os.path.join(path_frags, f"{lecture_id}.encrypted.mp4")
    audio_filepath_enc = os.path.join(path_frags, f"{lecture_id}.encrypted.m4a")

    ydl_opts = {
        "format": format_id,
        "outtmpl": os.path.join(path_frags, f"{lecture_id}.encrypted.%(ext)s"),
        "allow_unplayable_formats": True,
        "concurrent_fragment_downloads": 10,
        "fixup": "never",
        "downloader": "aria2c",
        "downloader_args": {
            "aria2c": ["--disable-ipv6", "--quiet", "--console-log-level=error", "--summary-interval=0"]
        },
        "noprogress": True,
        "quiet": True,
        "force_generic_extractor": True,
        "enable_file_urls": True,
        "merge_output_format": None,
        "logger": NoLogger()
    }

    animation = AnimationConsole(text="Baixando Segmentos", color_frame=Fore.LIGHTCYAN_EX)

    try:
        animation.start()
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        animation.stop()

        if os.path.exists(video_filepath_enc) or os.path.exists(audio_filepath_enc):
            return {
                "video_filepath": video_filepath_enc,
                "audio_filepath": audio_filepath_enc
            }
        else:
            raise Exception("Não foi possível obter segmentos!")

    except Exception as e:
        animation.stop()
        raise Exception(f"Erro durante o download dos segmentos: {e}")

def mux_process(mpd_path,
                frags_dir,
                video_filepath,
                audio_filepath,
                video_title: str,
                audio_key: str,
                video_key: str,
                output_dir):
    from .utils import generate_temp_file_path
    from .animation import AnimationConsole
    ffmpeg = FFmpeg()

    try:
        ffmpeg.reset_ffmpeg()
        if not os.path.exists(audio_filepath):
            raise Exception(f'audio não encontrado...')
        if not os.path.exists(video_filepath):
            raise Exception(f'video não encontrado...')
        if not os.path.exists(mpd_path):
            raise Exception("mpd não encontrado...")
        if not os.path.exists(output_dir):
            raise Exception("Dir de saída não existe!")
        path_temp = generate_temp_file_path(suffix='video_', extension='mp4', output_dir=frags_dir)
        final_path = os.path.join(output_dir, video_title)
        if DEBUG_DEV:
            print(f"TEMP_PATH: {path_temp}\n"
                  f"FINAL_PATH: {final_path}\n")
        codec = "hevc_nvenc"
        transcode = "-hwaccel cuda -hwaccel_output_format cuda"
        audio_decryption_arg = f"-decryption_key {audio_key}"
        video_decryption_arg = f"-decryption_key {video_key}"

        animation = AnimationConsole(text='Gerando Vídeo',
                                     color_frame=Fore.LIGHTCYAN_EX,
                                     color=Fore.LIGHTMAGENTA_EX)
        command = [
            *transcode.split(),
            "-y",
            "-hide_banner",
            "-loglevel", "error",
            *video_decryption_arg.split(),
            "-i", video_filepath,
            *audio_decryption_arg.split(),
            "-i", audio_filepath,
            "-c:v", codec,
            "-vtag", "hvc1",
            "-crf", "28",
            "-preset", "medium",
            "-c:a", "copy",
            "-fflags", "+bitexact",
            "-shortest",
            "-map_metadata", "-1",
            path_temp
        ]
        process = ffmpeg.args(command).run()

        animation.start()
        for line in process:
            ...
        animation.stop()
        a = AnimationConsole(text='Finalizando', animation_type='spinner')
        time.sleep(3)
        a.stop()
        print(f"\n\t==> AULA: {Fore.GREEN}{video_title} Baixada!{Style.RESET_ALL}")

        ffmpeg.reset_ffmpeg()

        shutil.move(path_temp, final_path)
        deletar_arquivos_em_pasta(frags_dir)
    except Exception as e:
        if 'animation' in locals():
            animation.stop()
        if DEBUG_DEV:
            e = traceback.format_exc()
        raise Exception(e)

def extrair_numero(nome_arquivo):
    """Extrai o número de um nome de arquivo, ou retorna infinito se não encontrar."""
    match = re.search(r'(\d+)', nome_arquivo)
    return int(match.group(1)) if match else float('inf')

def ffmpeg_concatener(output_name: str, output_save, course_id, extension: str, dir_segments: str):
    """
    Concatena segmentos de vídeo em um único arquivo.

    Args:
        output_name: Nome do vídeo final.
        output_save: Diretório onde salvar o vídeo final.
        course_id: ID do curso.
        extension: Extensão dos arquivos de segmento.
        dir_segments: Diretório onde estáo os segmentos.
    """
    from .utils import generate_temp_file_path
    from .animation import AnimationConsole
    ffmpeg = FFmpeg()
    arquivo_lista = os.path.join(dir_segments, 'list.txt')
    final_path = os.path.join(output_save, output_name)
    path_temp = generate_temp_file_path(suffix='video_', extension='mp4', output_dir=dir_segments)
    animation = AnimationConsole(text='Gerando Vídeo', color_frame=Fore.LIGHTCYAN_EX, color=Fore.LIGHTMAGENTA_EX)

    if DEBUG_DEV:
        print(f"TEMP_PATH: {path_temp}\nFINAL_PATH: {final_path}\n")

    try:

        with open(arquivo_lista, 'w') as f:

            arquivos_ts = [arquivo for arquivo in os.listdir(dir_segments) if
                           arquivo.endswith(f'.{extension}') and str(course_id) in arquivo]

            arquivos_ts.sort(key=extrair_numero)

            for arquivo in arquivos_ts:
                caminho_absoluto = os.path.abspath(os.path.join(dir_segments, arquivo))
                f.write(f"file '{caminho_absoluto}'\n")

        command = [
            '-f', 'concat',
            '-safe', '0',
            '-i', arquivo_lista,
            '-c', 'copy',
            '-hide_banner',
            '-loglevel', 'error',
            path_temp
        ]
        animation.start()
        for i in ffmpeg.args(command).run():
            ...
        animation.stop()

        a = AnimationConsole(text='Finalizando', animation_type='spinner')
        time.sleep(3)
        a.stop()
        print(f"\n\t==> AULA: {Fore.GREEN}{output_name} Baixada!{Style.RESET_ALL}")

        shutil.move(path_temp, final_path)
        ffmpeg.reset_ffmpeg()

        deletar_arquivos_em_pasta(dir_segments)

    except Exception as e:
        raise Exception(e)

def gerar_html_exercicio(assessment_data, output_name, output_path="exercicio_view.html", content_extra=None):

    titulo = assessment_data.get('title', 'Conteúdo da Aula')
    instrucoes = assessment_data['prompt'].get('instructions', '') if 'prompt' in assessment_data else ""
    objetivo = assessment_data['prompt'].get('learning_objective', 'N/A') if 'prompt' in assessment_data else ""

    display_content = content_extra if content_extra else instrucoes

    html_template = f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <style>
            body {  font-family: 'Udemy Sans', Arial, sans-serif; background: #f7f9fa; padding: 20px; }
            .problem-container--problem-container--vhRvv {  background: white; border: 1px solid #dcdfe2; padding: 20px; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .ud-heading-lg {  font-size: 1.5rem; font-weight: 700; margin-bottom: 15px; }
            .ud-text-md {  font-size: 1rem; line-height: 1.5; color: #1c1d1f; }
        </style>
    </head>
    <body>
        <div class="problem-container--problem-container--vhRvv">
            <div class="ud-heading-lg">{titulo}</div>
            <div class="ud-text-md">{display_content}</div>
        </div>
    </body>
    </html>
    """
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_template)
    print(f"\n\t==> AULA: {Fore.GREEN}{output_name} Baixada!{Style.RESET_ALL}")

def sv_exer_local(assessment_data, output_name, pasta_base="exercicios"):
    path = pasta_base
    os.makedirs(path, exist_ok=True)

    tipo = assessment_data.get('assessment_type')

    if tipo == 'coding-problem':

        for categoria in ['initial_files', 'solution_files', 'test_files']:
            for file_obj in assessment_data['prompt'].get(categoria, []):
                file_path = os.path.join(path, categoria, file_obj['file_name'])
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(file_obj['content'])
        gerar_html_exercicio(assessment_data, output_name, output_path=os.path.join(path, "instrucoes.html"))

    elif tipo == 'multiple-choice':

        html_quiz = generate_quiz({"results": [assessment_data]})
        with open(os.path.join(path, "quiz.html"), "w", encoding="utf-8") as f:
            f.write(html_quiz)
        print(f"\n\t==> QUIZ: {Fore.CYAN}{output_name} Baixado!{Style.RESET_ALL}")

def generate_quiz(quiz_data: dict) -> str:

    html = '''<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <style>
        :root {
            --applied-background-default: oklch(100% 0 0deg);
            --applied-text-default: oklch(29.74% 0.0362 281.74deg);
            --applied-border-default: oklch(86.72% 0.0192 282.72deg);
            --applied-border-positive: oklch(44.49% 0.0863 157.92deg);
            --applied-border-negative: oklch(55.73% 0.2161 29.71deg);
        }
        body { font-family: 'Udemy Sans', Roboto, sans-serif; background-color: var(--applied-background-default); color: var(--applied-text-default); padding: 20px; }
        .quiz-view--container { max-width: 800px; margin: auto; }
        .mc-quiz-question--container { background: #fff; border: 1px solid var(--applied-border-default); padding: 24px; border-radius: 8px; margin-bottom: 24px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        .mc-quiz-question--question-prompt { font-weight: 600; margin-bottom: 15px; font-size: 1.1rem; }
        .ud-unstyled-list { list-style: none; padding: 0; }
        .mc-quiz-answer--answer { display: flex; padding: 12px; border: 1px solid var(--applied-border-default); margin: 8px 0; border-radius: 4px; cursor: pointer; transition: 0.2s; }
        .mc-quiz-answer--answer:hover { background-color: #f1f2f3; }
        .mc-quiz-answer--correct { background-color: oklch(97.23% 0.0176 170.1deg); border-color: var(--applied-border-positive) !important; }
        .mc-quiz-answer--incorrect { background-color: oklch(95.79% 0.0208 21.17deg); border-color: var(--applied-border-negative) !important; }
        .code-block { background: #282c34; color: #abb2bf; padding: 10px; border-radius: 4px; font-family: monospace; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="quiz-view--container">
    '''

    for i, q in enumerate(quiz_data.get('results', []), 1):
        prompt = q.get('prompt', {})
        question_text = prompt.get('question', '').replace('<pre', '<div class="code-block"><pre').replace('</pre>',
                                                                                                           '</pre></div>')

        gabarito_letra = q.get('correct_response', [''])[0].lower()
        idx_gabarito = ord(gabarito_letra) - ord('a') if gabarito_letra.isalpha() else -1
        answers = prompt.get('answers', [])

        text_gabarito = answers[idx_gabarito] if 0 <= idx_gabarito < len(answers) else ""

        text_gabarito_clean = text_gabarito.replace('<p>', '').replace('</p>', '').strip()

        html += f'''
        <div class="mc-quiz-question--container">
            <div class="mc-quiz-question--question-prompt">Pergunta {i}: {question_text}</div>
            <ul class="ud-unstyled-list">
        '''

        for ans in answers:

            ans_clean = ans.replace('<p>', '').replace('</p>', '').strip()

            html += f'''
                <li class="mc-quiz-answer--answer" onclick="selectAnswer(this, '{text_gabarito_clean.replace("'", "\\'")}')">
                    {ans}
                </li>
            '''
        html += '</ul></div>'

    html += '''</div>
<script>
    function selectAnswer(element, correctText) {
        const parent = element.parentElement;
        const items = parent.querySelectorAll('.mc-quiz-answer--answer');

        // Remove seleções anteriores e feedbacks existentes para evitar duplicação
        items.forEach(item => {
            item.classList.remove('mc-quiz-answer--correct', 'mc-quiz-answer--incorrect');
            const feedback = item.querySelector('.mc-quiz-answer--checked-feedback--nSDoi');
            if (feedback) feedback.remove();
        });

        // Marca a escolha do usuário
        const userChoice = element.innerText.trim();
        const isCorrect = userChoice === correctText.trim();

        if (isCorrect) {
            element.classList.add('mc-quiz-answer--correct');
            addFeedback(element);
        } else {
            element.classList.add('mc-quiz-answer--incorrect');
            // Destaca a correta e adiciona o feedback nela
            items.forEach(item => {
                if (item.innerText.trim() === correctText.trim()) {
                    item.classList.add('mc-quiz-answer--correct');
                    addFeedback(item);
                }
            });
        }
    }

    function addFeedback(element) {
        // Cria a div de feedback com o HTML que você forneceu
        const feedbackHTML = `
            <div class="mc-quiz-answer--checked-feedback--nSDoi mc-quiz-answer--positive--8eUCV">
                <p class="ud-text-xs"><strong>Correto</strong></p>
                <svg aria-label="false" role="img" focusable="false" class="ud-icon ud-icon-medium ud-icon-color-positive" style="width:24px; height:24px;">
                    <use xlink:href="#icon-success">✅</use>
                </svg>
            </div>`;

        // Adiciona ao final da div interna do item clicado
        const inner = element.querySelector('.mc-quiz-answer--answer-inner--Uz9E8') || element;
        inner.insertAdjacentHTML('beforeend', feedbackHTML);
    }
</script>
</body>
</html>'''
    return html

def download_captions(captions: list, details_lecture, path_save):
    """Salva todas as legendas e retorna uma lista com seus caminhos.

    Para cada legenda na lista, tenta baixar e salvar até 5 vezes.
    Se a legenda não puder ser baixada após 5 tentativas, ela é ignorada.
    """
    files_paths = []
    for lang in captions:
        locale_id = lang.get('locale_id')
        attempts = 0
        success = False
        while attempts < 5 and not success:
            try:
                caption_obj = details_lecture.get_captions.get_lang(locale_id)
                if not caption_obj:

                    break
                filename = f'{caption_obj.locale}.srt'
                file_path = os.path.join(path_save, filename)
                with open(file_path, mode='w', encoding='utf-8') as f:
                    f.write(caption_obj.content)
                files_paths.append(file_path)
                success = True
            except Exception as e:
                attempts += 1

                time.sleep(1)

    return files_paths
