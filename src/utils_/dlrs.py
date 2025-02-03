import os
import re
import shutil
import time
import traceback
from colorama import Fore, Style
from yt_dlp import YoutubeDL
from ffmpeg_for_python import FFmpeg
import logging
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
    # Caminhos dos arquivos de saída
    video_filepath_enc = os.path.join(path_frags, f"{lecture_id}.encrypted.mp4")
    audio_filepath_enc = os.path.join(path_frags, f"{lecture_id}.encrypted.m4a")

    # Configurações do yt-dlp
    ydl_opts = {
        "format": format_id,
        "outtmpl": os.path.join(path_frags, f"{lecture_id}.encrypted.%(ext)s"),
        "allow_unplayable_formats": True,
        "concurrent_fragment_downloads": 10,
        "fixup": "never",
        "downloader": "aria2c",
        "downloader_args": {
            "aria2c": ["--disable-ipv6"]
        },
        "noprogress": True,
        "quiet": True,
        "force_generic_extractor": True,
        "enable_file_urls": True,
        "merge_output_format": None,
        "logger": NoLogger()
    }

    # Animação de progresso
    animation = AnimationConsole(text="Baixando Segmentos", color_frame=Fore.LIGHTCYAN_EX)

    try:
        animation.start()
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        animation.stop()

        # Verifica se os arquivos foram baixados corretamente
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
        path_temp = generate_temp_file_path(suffix='video_', extension='mp4', output_dir=output_dir)
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
        # Captura a saída do ffmpeg em tempo real
        animation.start()
        for line in process:
            ...
        animation.stop()
        a = AnimationConsole(text='Finalizando', animation_type='spinner')
        time.sleep(3)
        a.stop()
        print(f"\n\t==> AULA: {Fore.GREEN}{video_title} Baixada!{Style.RESET_ALL}")

        ffmpeg.reset_ffmpeg()
        ## mover o file agora com o nome original
        shutil.move(path_temp, final_path)
    except Exception as e:
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

    :param output_name: Nome do vídeo final.
    :param output_save: Diretório onde salvar o vídeo final.
    :param course_id: ID do curso.
    :param extension: Extensão dos arquivos de segmento.
    :param dir_segments: Diretório onde estão os segmentos.
    """
    from .utils import generate_temp_file_path
    from .animation import AnimationConsole
    ffmpeg = FFmpeg()
    arquivo_lista = os.path.join(dir_segments, 'lista.txt')
    final_path = os.path.join(output_save, output_name)
    path_temp = generate_temp_file_path(suffix='video_', extension='mp4', output_dir=output_save)
    animation = AnimationConsole(text='Gerando Vídeo', color_frame=Fore.LIGHTCYAN_EX, color=Fore.LIGHTMAGENTA_EX)

    if DEBUG_DEV:
        print(f"TEMP_PATH: {path_temp}\nFINAL_PATH: {final_path}\n")

    try:
        # Abre o arquivo lista.txt para escrita
        with open(arquivo_lista, 'w') as f:
            # Lista todos os arquivos no diretório e filtra apenas os arquivos com a extensão correta
            arquivos_ts = [arquivo for arquivo in os.listdir(dir_segments) if
                           arquivo.endswith(f'.{extension}') and str(course_id) in arquivo]
            # Ordena os arquivos com base no número extraído
            arquivos_ts.sort(key=extrair_numero)
            # Escreve cada arquivo no lista.txt
            for arquivo in arquivos_ts:
                caminho_absoluto = os.path.abspath(os.path.join(dir_segments, arquivo))
                f.write(f"file '{caminho_absoluto}'\n")

        cmd = ['-y', '-f', 'concat', '-safe', '0', '-i', arquivo_lista, '-c', 'copy', f'{path_temp}']
        animation.start()
        for i in ffmpeg.args(cmd).run():
            ...
        animation.stop()

        a = AnimationConsole(text='Finalizando', animation_type='spinner')
        time.sleep(3)
        a.stop()
        print(f"\n\t==> AULA: {Fore.GREEN}{output_name} Baixada!{Style.RESET_ALL}")

        # Mover o arquivo agora com o nome original
        shutil.move(path_temp, final_path)
        ffmpeg.reset_ffmpeg()

    except Exception as e:
        raise Exception(e)


def generate_quiz(quiz_data: dict) -> str:
    results = quiz_data.get('results', [])
    questions = []

    for d in results:
        question_text = d.get('prompt', {}).get('question', '')
        id_question = d.get('id', '')

        # Obter a resposta correta
        if d.get('correct_response'):
            correct_index = ord(d['correct_response'][0].lower()) - ord('a')
            answers = d.get('prompt', {}).get('answers', [])
            correct_text = answers[correct_index] if 0 <= correct_index < len(answers) else ""
        else:
            correct_text = ""

        answers = d.get('prompt', {}).get('answers', [])
        questions.append({
            'id': id_question,
            'question': question_text,
            'correct': correct_text,
            'answers': answers
        })

    # Geração do HTML
    html_content = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quiz</title>
    <style>
        body {
            font-family: 'Roboto', Arial, sans-serif;
            background-color: #eef2f5;
            margin: 0;
            padding: 0;
            color: #333;
            line-height: 1.6;
        }
        .container {
            width: 90%;
            max-width: 900px;
            margin: 30px auto;
            background: #fff;
            padding: 20px;
            box-shadow: 0 6px 12px rgba(0,0,0,0.1);
            border-radius: 8px;
        }
        h2 {
            text-align: center;
            color: #2c3e50;
        }
        .question {
            margin-bottom: 30px;
            padding: 15px;
            border: 1px solid #dcdcdc;
            border-radius: 8px;
            background-color: #fafafa;
        }
        .question h3 {
            margin-top: 0;
            color: #2c3e50;
            font-size: 1.2rem;
        }
        .question ul {
            list-style: none;
            padding: 0;
        }
        .question li {
            padding: 10px;
            margin: 8px 0;
            background-color: #f7f7f7;
            border: 1px solid #ddd;
            border-radius: 4px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        .question li:hover {
            background-color: #eaeaea;
        }
        .question li.selected {
            background-color: #d0e4f5;
        }
        .question li.correct {
            background-color: #27ae60;
            color: #fff;
        }
        .question li.incorrect {
            background-color: #e74c3c;
            color: #fff;
        }
        .btn {
            display: block;
            margin: 20px auto;
            background-color: #1e74b8;
            color: #fff;
            padding: 12px 25px;
            border: none;
            border-radius: 5px;
            font-size: 1rem;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        .btn:hover {
            background-color: #15689a;
        }
        .btn:disabled {
            background-color: #ccc;
            cursor: not-allowed;
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>Quiz</h2>
    '''

    for question in questions:
        html_content += f'''
        <div class="question" id="question-{question['id']}">
            <h3>{str(question.get('id', '')).strip()} {question.get('question', '')}</h3>
            <ul>
        '''
        for answer in question["answers"]:
            safe_answer = answer.replace("'", "\\'")
            html_content += f'''
                <li onclick="selectAnswer(this, '{question["id"]}', '{safe_answer}')">{answer}</li>
            '''
        html_content += '''
            </ul>
        </div>
        '''

    html_content += '''
        <button class="btn" id="submit-btn" onclick="submitQuiz()" disabled>Finalizar Quiz</button>
        <button class="btn" id="download-btn" onclick="downloadAnswerKey()" disabled>Baixar Gabarito</button>
    </div>
    <script>
        let selectedAnswers = {};
        let correctAnswers = {}; 
        const totalQuestions = ''' + str(len(questions)) + ''';

        function selectAnswer(element, questionId, answerText) {
            const parent = element.parentElement;
            const items = parent.getElementsByTagName("li");
            for (let i = 0; i < items.length; i++) {
                items[i].classList.remove("selected", "correct", "incorrect");
            }
            element.classList.add("selected");
            selectedAnswers[questionId] = answerText;
            checkAllAnswered();
        }

        function checkAllAnswered() {
            const submitBtn = document.getElementById("submit-btn");
            if (Object.keys(selectedAnswers).length === totalQuestions) {
                submitBtn.disabled = false;
            } else {
                submitBtn.disabled = true;
            }
        }

        function submitQuiz() {
            let total = 0;
            let correctCount = 0;
            correctAnswers = {
            '''

    correct_answers_js = ""
    for question in questions:
        safe_correct = question["correct"].replace("'", "\\'")
        correct_answers_js += f"'{question['id']}': '{safe_correct}',\n"

    html_content += correct_answers_js
    html_content += '''
            };

            for (const questionId in correctAnswers) {
                total++;
                const correctAnswer = correctAnswers[questionId].trim();
                const questionDiv = document.getElementById("question-" + questionId);
                const options = questionDiv.getElementsByTagName("li");
                const userAnswer = (selectedAnswers[questionId] || "").trim();

                for (let i = 0; i < options.length; i++) {
                    const optionText = options[i].innerText.trim();
                    if (optionText === correctAnswer) {
                        options[i].classList.add("correct");
                    }
                    if (optionText === userAnswer && userAnswer !== correctAnswer) {
                        options[i].classList.add("incorrect");
                    }
                }
                if (userAnswer === correctAnswer) {
                    correctCount++;
                }
            }

            let percentCorrect = ((correctCount / total) * 100).toFixed(2);
            let percentIncorrect = (100 - percentCorrect).toFixed(2);
            alert("Você acertou " + correctCount + " de " + total + " perguntas.\\n" +
                  "Acertou: " + percentCorrect + "%\\n" +
                  "Errou: " + percentIncorrect + "%");
            document.getElementById("download-btn").disabled = false;
        }

        function downloadAnswerKey() {
            let answerKeyHTML = '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Gabarito</title>';
            answerKeyHTML += '<style>body { font-family: Arial, sans-serif; background-color: #eef2f5; padding: 20px; }';
            answerKeyHTML += 'h2 { color: #2c3e50; } ul { list-style: none; padding: 0; } li { padding: 10px; margin-bottom: 8px; background: #fff; border: 1px solid #ddd; border-radius: 4px; }</style>';
            answerKeyHTML += '</head><body><h2>Gabarito</h2><ul>';

            for (const questionId in correctAnswers) {
                answerKeyHTML += '<li>Question ' + questionId + ': <strong>' + correctAnswers[questionId] + '</strong></li>';
            }
            answerKeyHTML += '</ul></body></html>';
            const blob = new Blob([answerKeyHTML], { type: 'text/html' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'gabarito.html';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }
    </script>
</body>
</html>
'''
    return html_content


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
                    # Se não houver legenda para este idioma, encerra as tentativas
                    break
                filename = f'{caption_obj.locale}.srt'
                file_path = os.path.join(path_save, filename)
                with open(file_path, mode='w', encoding='utf-8') as f:
                    f.write(caption_obj.content)
                files_paths.append(file_path)
                success = True
            except Exception as e:
                attempts += 1
                # Aguarda 1 segundo antes de tentar novamente
                time.sleep(1)
        # Se não conseguir baixar após 5 tentativas, simplesmente passa para a próxima legenda
    return files_paths
