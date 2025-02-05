<div align="center">
  <h1>
    <img src="assets/favicon.ico" alt="Logo" width="280"><br>
    Udemy Download
  </h1>
  <p align="center">

  O **Udemy Download** é uma ferramenta de código aberto que permite aos usuários salvarem para acesso offline **apenas os cursos adquiridos oficialmente** na plataforma Udemy. Ele utiliza métodos semelhantes aos dos navegadores para capturar e armazenar o conteúdo dos cursos, respeitando as políticas da plataforma.</p>

  <p align="center">
    <img src="https://img.shields.io/badge/Version-1.0.0.7-orange?style=flat-square" alt="Version">
    <a href="https://github.com/PauloCesar-dev404/Udemy-Download/raw/refs/heads/main/versions/win-amd64-SETUP.exe" target="_blank">
      <img src="https://img.shields.io/badge/Download-Windows-blue?style=flat-square" alt="Download Windows">
    </a>
  <a href="https://github.com/PauloCesar-dev404/Udemy-Download/raw/refs/heads/main/versions/linux-x86_64-SETUP.deb" target="_blank">
      <img src="https://img.shields.io/badge/Download-Linux-blue?style=flat-square" alt="Download Linux">
    </a>
  </p>
</div>



---

## ⚠️ Aviso Legal e Termos de Uso  

O uso desta ferramenta **deve respeitar as leis de direitos autorais** e os **termos de serviço da Udemy**.  

- **Não pratique pirataria!** O compartilhamento, redistribuição ou venda de cursos baixados com este software é ilegal e pode acarretar punições legais.  
- **Este software não contorna ou quebra proteções DRM (Digital Rights Management)**. Ele **utiliza os mesmos métodos que os navegadores modernos** para acessar os conteúdos, respeitando os mecanismos de segurança existentes.  
- **Todas as ações realizadas com esta ferramenta são de responsabilidade exclusiva do usuário.** O desenvolvedor **não se responsabiliza** por qualquer uso inadequado do programa.  

---

## ✅ Requisitos para versão compilada 

### Windows 

- **Sistema operacional:** Windows 10 ou superior  
- **Arquitetura:** AMD64  
### Linux
- **Sistema operacional:** Debian ou baseados no mesmo.  
- **Arquitetura:** x86_64
---

## 🔧 Instalação Windows

1. Baixe o instalador: [Download do Instalador](https://github.com/PauloCesar-dev404/Udemy-Download/raw/refs/heads/main/versions/win-amd64-SETUP.exe)  
2. Execute o instalador, clique em **"Instalar"** e aguarde a conclusão.  
3. Após a instalação, abra um **novo terminal** e execute o programa.  

## 🔧 Instalação Linux

1. Baixe o pacote: [Download do pacote .deb](https://github.com/PauloCesar-dev404/Udemy-Download/raw/refs/heads/main/versions/linux-x86_64-SETUP.deb)  
2. Insatale:
```bash
apt install ./linux-x86_64-SETUP.deb
```
3. Após a instalação,e execute o programa `udemy_download`.  


---

## 🚀 Como Usar  

Para ver os comandos disponíveis, utilize:  
```bash
udemy_download --help
```

🔑 Login

✅ Login via OTP (Código Temporário) maneira mais segura!
```bash
udemy_download --auth-code
```

Insira seu e-mail cadastrado na Udemy.
![receber o código otp](<assets/Captura de tela 2025-02-04 194402.png>)

Digite o código de 6 dígitos recebido na sua caixa de entrada.O código expira em 15 minutos.
![inserir o código](<assets/Captura de tela 2025-02-04 194500.png>)

---

🎬 Download de Cursos

Depois de realizar o login, liste seus cursos adquiridos com:
```bash
udemy_download --my-section
```
![my courses](<assets/Captura de tela 2025-02-04 194546.png>)


abra no navegador e reinicie o app passando id do curso desejado se você desejar salvar legendas...ou se não apenas digite o id assim como o app solicitará após abrir os cursos.


📌 Os cursos serão salvos em:

C:\Users\SEU-USUARIO\Udemy\Meus Cursos


---

❗ Possíveis Erros e Soluções

- Erro ao abrir o app? Tente executar o programa via PowerShell ou prompt de comando (CMD).

- O comando não é reconhecido? Reinicie o terminal e tente novamente.

- erro no login mesmo digitando e-mail e senhas corretos? Use login via otp


<br>
<br><br><br>

>Caso persista, crie uma issue informando:
> Versão do sistema operacional
> 
>Terminal utilizado (PowerShell, CMD, etc.)
>Comando digitado e mensagem de erro



---

❤️ Apoie o Projeto

Se este projeto foi útil para você, considere apoiar para que ele continue evoluindo!



