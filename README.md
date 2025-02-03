<div align="center">
  <h1>
    <img src="assets/favicon.ico" alt="Logo" width="280"><br>
    Udemy Download
  </h1>
  <p align="center">
  O Udemy Download é uma ferramenta de código aberto que permite aos usuários salvar cursos adquiridos na plataforma Udemy para acesso offline. Este aplicativo utiliza métodos semelhantes aos dos navegadores para obter e salvar conteúdos de cursos, garantindo que apenas os cursos adquiridos oficialmente sejam baixados.</p>

  <p align="center">
    <img src="https://img.shields.io/badge/Version-1.0.0.7-orange?style=flat-square" alt="Version">
    <img src="https://img.shields.io/badge/Status-Active-success?style=flat-square" alt="Status">
    <a href="https://github.com/PauloCesar-dev404/Udemy-Download/raw/refs/heads/main/versions/win-amd64-SETUP.exe" target="_blank">
      <img src="https://img.shields.io/badge/Download-latest-blue?style=flat-square" alt="Download">
    </a>
  </p>
  </p>
</div>

> ⚠️ **Atenção**  
Não pratique pirataria. Compartilhar cursos baixados é contra os termos de uso da plataforma e é considerado ilegal. Este aplicativo é apenas uma ferramenta destinada a salvar dados adquiridos oficialmente pelo usuário. Todas as ações realizadas com esta ferramenta são de total responsabilidade do usuário.

## Requisitos versão compilada
- Sistema operacional: Windows 10 ou superior
- Arquitetura: AMD64

---

## Instalação

1. Baixe o instalador em: [Download do Instalador](https://github.com/PauloCesar-dev404/Udemy-Download/raw/refs/heads/main/versions/win-amd64-SETUP.exe)
2. Execute o instalador, clique em "Instalar" e aguarde a conclusão da instalação.
3. Após a instalação, abra um novo terminal e execute o programa diretamente, pois ele estará disponível no PATH do sistema.

---

## 🚀 Como Usar

Digite o comando `--help` para ver os comandos disponíveis:

```bash
udemy_download --help
```

### 🔑 Login

Após o download e instalação concluída, você deve iniciar uma sessão. Existem **duas maneiras de login**: por código OTP (One Time Password) ou por e-mail e senha.

#### 🔐 Login via OTP
```bash
udemy_download --auth-code
```
1. Digite seu e-mail.  
2. Aguarde um código de 6 dígitos, que será enviado para sua caixa de entrada.  
3. O código será válido por 15 minutos.

#### ✉️ Login via E-mail e Senha
```bash
udemy_download --auth-credentials 
```
1. Forneça seu e-mail e senha cadastrados na Udemy.  
2. Após a autenticação, sua sessão será ativa.

---

### 🎬 Download de Cursos

Depois de efetuar login, inicie sua sessão ativa com o comando:

```bash
udemy_download --my-section
```

- O programa carregará os cursos nos quais você está inscrito.
- Você poderá escolher abrir os cursos no navegador (mais fácil de visualizar) ou exibi-los no console.

Cada curso possui um **identificador único**. Copie o ID do curso desejado, cole no terminal e aguarde o download das aulas. Fique atento ao terminal para acompanhar o progresso e eventuais erros.

### Local de Salvamento dos Seus Cursos

Os cursos serão salvos no seguinte diretório em seu computador: **C:\Users\SEU-USUARIO\Udemy\Meus Cursos**

### ERROS
- Se o app não abrir ao digitar comandos, abra uma nova guia no PowerShell e tente novamente. Caso persista, abra uma issue especificando: `versão do sistema`, `qual terminal está usando`, `comando utilizado`.

---
### Integridade

SHA256: ` 03BB840C362450F001A6AC461901481BE9B253AEE742BCDD3BD7687DF35069AF`

versão: 1.0.0.7
---
## ❤️ Apoie o Projeto

Se você gostou deste projeto e deseja [apoiar](https://paulocesar-dev404.github.io/me-apoiando-online/), sua contribuição será muito bem-vinda!

---
