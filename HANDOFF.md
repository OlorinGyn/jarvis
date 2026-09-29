# Contexto para continuar o J.A.R.V.I.S. noutra máquina

Este arquivo existe para uma sessão nova do Claude Code pegar o fio sem repetir
o que já foi decidido e descartado. **Leia isto primeiro**, depois
`docs/ARQUITETURA.md`.

> **Precisa de mais contexto?** `CONTEXTO.md` traz o histórico completo do
> projeto: todas as decisões com seus porquês, os bugs já corrigidos que não
> devem voltar, as medições de referência, as limitações aceitas e os próximos
> passos planejados.

Apague este arquivo quando o problema descrito na seção 4 estiver resolvido.

---

## 1. O que é o projeto

Sistema de vigilância doméstica: duas câmeras TP-Link Tapo externas (C310) via
RTSP. Detecta movimento, decide se é pessoa ou animal, grava o evento em vídeo,
reconhece rostos e permite cadastrar nomes.

Interface OpenCV com três abas: **Live**, **Records** (gravações, com
calendário e rolagem) e **People** (rostos, com cadastro de nome).

Tudo funciona na máquina de desenvolvimento.

## 2. Como trabalhamos aqui (siga isto)

Três regras que o usuário estabeleceu e que devem ser mantidas:

**O código não tem comentários.** Nenhum. Toda explicação vive em `docs/`.
Docstrings de uma linha são aceitas. Verifique com:

```bat
uv run python -c "import tokenize,pathlib; print(sum(sum(1 for t in tokenize.generate_tokens(tokenize.open(f).readline) if t.type==tokenize.COMMENT) for f in pathlib.Path('.').glob('*.py')))"
```

**Toda mudança termina em commit + documentação atualizada.** Mensagens de
commit explicam o *porquê*, não só o quê. Docs em português; código e
identificadores em inglês.

**Antes de cada commit, confira que `.env` não entrou.** Ele tem as senhas
reais das câmeras. Já vazou uma vez em exemplos da documentação e foi corrigido.

O usuário está aprendendo Python e OpenCV — explique o que o código faz, não só
o resultado. Ele vem de Java/C#; `docs/PYTHON.md` cobre as diferenças.

## 3. Decisões já tomadas — não desfaça sem motivo novo

| Decisão | Por quê |
|---|---|
| **Python, não C++** | Bindings do OpenCV chamam o mesmo C++; o ecossistema é Python |
| **ffmpeg, não `cv2.VideoCapture`** | O VideoCapture obriga a recodificar. Hoje o vídeo salvo é cópia byte a byte dos pacotes da câmera |
| **Sem PyTorch** | O Smart App Control do Windows 11 bloqueia as DLLs sem assinatura do torch (`WinError 4551`). Desligá-lo é **irreversível**. O YOLO roda por `cv2.dnn` sobre ONNX |
| **Sem compactar os vídeos** | Medido: zip economiza 0,2% em H.264. Duas tentativas pioram o arquivo |
| **Uma conexão RTSP por câmera** | A Tapo aceita só uma. Um ffmpeg por câmera serve duas saídas: segmentos `-c copy` e frames de análise |
| **Rosto roda no clipe, não ao vivo** | Um rosto de 60px em 1080p vira 30px nos frames de análise de 960x540 |

Detalhes e medições em `docs/ARQUITETURA.md`, seções 5.1, 7.11, 8.7 e 10.1.

## 4. O PROBLEMA ATUAL

**Nesta máquina (Lenovo ThinkCentre M900, i5 Skylake 4 núcleos, Windows 11) o
ffmpeg conecta nas câmeras mas nunca entrega frames de análise.**

Sintoma: `FALHOU - nenhum frame recebido` no terminal, painel em "sem sinal",
**sem nenhuma mensagem de erro do ffmpeg**.

### O que já foi descartado

| Hipótese | Como foi descartada |
|---|---|
| Rede, credenciais ou RTSP | `uv run probe_rtsp.py <ip> <user> <senha> stream1` passa nos três estágios com RTP fluindo |
| Duas instâncias competindo pela câmera | O usuário confirmou que não estavam rodando juntas |
| Código quebrado | O mesmo commit funciona na máquina de desenvolvimento |
| Parâmetros do comando ffmpeg | `uv run diagnostico.py Front` testa cinco variantes. **Todas falharam aqui**; todas entregam 118-176 frames na máquina de desenvolvimento |
| Visual C++ Redistributable ausente | Instalado pelo `instalar.bat` |

A falha de **todas** as variantes, inclusive a que não grava segmentos e só
decodifica, aponta para o decode em si ou para o pipe — não para a câmera nem
para os parâmetros.

### Próximos testes sugeridos

**1. Os segmentos são gravados?** É a pergunta que separa tudo. A coluna
`segmentos` do `diagnostico.py` responde. Se sim, o ffmpeg conecta e escreve
vídeo, e só o decode falha. Se não, ele não conecta de verdade.

**2. O ffmpeg decodifica alguma coisa nesta máquina?** Isola decode de rede,
sem envolver câmera nenhuma:

```bat
uv run diagnostico.py --local
```

Ele gera um vídeo 1920x1080 H.264 com o próprio ffmpeg e tenta decodificar para
rawvideo 960x540, exatamente como o programa faz. Na máquina de desenvolvimento
imprime `recebido 7776000 bytes, esperado 7776000`.

Se aqui der 0, o problema **não tem relação com as câmeras** — é o ffmpeg desta
máquina, e as suspeitas passam a ser o binário do `imageio-ffmpeg`, antivírus
ou política do Windows.

**3. Log completo do ffmpeg.** Rode o comando de captura à mão com
`-loglevel debug` e leia tudo. O `diagnostico.py` usa `warning`; pode estar
escondendo a pista.

**4. Suspeitas em aberto**
- Antivírus ou política do Windows interferindo no pipe do processo filho
- O binário do `imageio-ffmpeg` exigindo instrução de CPU ausente no Skylake
- Diferença de build do Windows

## 5. Comandos úteis

```bat
jarvis.bat                                   iniciar o programa
uv run diagnostico.py Front                  testar variantes de captura
uv run probe_rtsp.py <ip> <user> <senha> stream1    testar RTSP puro
tasklist | findstr ffmpeg                    procurar ffmpeg orfao
```

Constantes de ajuste: `capture.py` (`ANALYSIS_FPS`, `HWACCEL`, `SEGMENT_SECONDS`),
`people.py` (`MIN_INTERVAL`, `MIN_PERSON_HEIGHT_FRACTION`), `motion.py`
(`MIN_AREA`, `CONFIRM_FRAMES`).

## 6. Estado do repositório

Tudo commitado e funcionando na máquina de desenvolvimento. Os modelos
(`models/*.onnx`, ~95 MB) e o `.env` não são versionados: o `instalar.bat`
baixa os modelos e cria o `.env` a partir do `.env.example`.

Últimos commits relevantes ao problema:

```
d360797  diagnostico que testa variantes de captura
5f52e2a  expor o motivo do "sem sinal" em vez de descartar
a9dfc1c  janela congelava porque o laco bloqueava no pipe
6aa5fe9  remover PyTorch, YOLO via cv2.dnn
```
