# J.A.R.V.I.S. — Arquitetura

Documentação de como o sistema funciona e, principalmente, **por que** cada
decisão foi tomada. O código não tem comentários; todo o raciocínio está aqui.

Para aspectos de linguagem e bibliotecas, veja [PYTHON.md](PYTHON.md).

---

## 1. O que o sistema faz

Monitora câmeras Tapo pela rede local, identifica quando há **movimento**,
decide se esse movimento é uma **pessoa ou um animal**, grava um **vídeo** do
evento e, quando há pessoa, procura **rostos** e diz de quem são.

A detecção de pessoa é deliberadamente independente do rosto: alguém de
máscara, capacete ou de costas continua sendo detectado como humano e
gravado. O rosto é uma camada a mais, que roda depois, sobre o clipe (seção 10).

## 2. Pipeline

```
     RTSP (rede)
         │
         ▼
   ┌────────────┐
   │ capture.py │  um ffmpeg por câmera, duas saídas
   └──┬──────┬──┘
      │      └── -c copy ──► segmentos de 4 s (pacotes originais)
      │                                    │
      │ frames 960x540 (bgr24 via pipe)    │
      ▼                                    │
   ┌───────────┐                           │
   │ motion.py │  MOG2 + confirmação       │
   └─────┬─────┘                           │
         │ caixas de movimento             │
         ▼                                 │
   ┌───────────┐                           │
   │ people.py │  YOLO11: pessoa/animal    │
   └─────┬─────┘                           │
         │ Detection(x,y,w,h,conf,label)   │
         ▼                                 ▼
   ┌───────────────────────────────────────────────┐
   │ clips.py   concat -c copy + miniatura + JSON  │
   └────────────┬──────────────────┬───────────────┘
                │ clipe 1080p      │ metadados
                ▼                  │
         ┌───────────┐             │
         │ faces.py  │  YuNet +    │
         │           │  SFace      │
         └─────┬─────┘             │
               │ galeria           │
               ▼                   ▼
         ┌─────────────────────────────────┐
         │  ui.py   Live | Records | People│
         └─────────────────────────────────┘
```

O vídeo salvo **nunca passa pelo Python**: ele vai dos pacotes da câmera direto
para o disco. O Python só vê frames pequenos, para decidir quando gravar.

A lógica central é **funil de custo**: cada camada é mais cara que a anterior
e só roda se a anterior encontrou algo.

| Camada | Custo | Frequência |
|---|---|---|
| Captura + decode | baixo | todo frame |
| MOG2 + filtro de luz | ~3 ms | todo frame |
| YOLO11 | 50–62 ms (dev) | só com movimento, no máximo 4×/s por câmera |
| Gravação | ~2 ms | só com pessoa ou animal |
| Rostos | 9–17 s por clipe (M900) | só em clipe com pessoa, fora do laço ao vivo |

## 3. Estrutura de arquivos

```
jarvis/
├── src/jarvis/           o programa, como pacote Python
│   ├── __init__.py       ROOT: a raiz do projeto, base de todo caminho
│   ├── __main__.py       permite `python -m jarvis`
│   ├── cameras.py        Core (vigilância) + run_window / run_headless (seção 15)
│   ├── capture.py        ffmpeg por câmera: segmentos originais + frames
│   ├── motion.py         camada 1: detecção de movimento
│   ├── people.py         camada 2: detecção de pessoas e animais
│   ├── clips.py          camada 3: eventos, montagem sem perda, metadados
│   ├── faces.py          camada 4: detecção de rosto, embedding, galeria
│   ├── archive.py        camada 5: move para o HD externo (seção 11)
│   ├── notify.py         aviso no celular pelo Telegram (seção 12)
│   ├── settings.py       config.json, ajustes que mudam com o programa rodando
│   ├── ui.py             janela OpenCV: Live, Records, People e Ajustes
│   ├── web.py            interface web: servidor FastAPI (seção 17)
│   ├── static/           a página da interface web: HTML, CSS e JavaScript
│   ├── log.py            logging to the console and logs/jarvis.log (18.7)
│   └── geometry.py       tipo Detection e utilitários de caixas (IoU)
├── tools/                ferramentas, fora do programa
│   ├── production.ps1    install, update, status, stop, start production (18.7)
│   ├── check_data.py     reads every file on disk with the current code (19.4)
│   ├── diagnostico.py    variantes do comando de captura; --local sem câmera
│   ├── probe_rtsp.py     RTSP puro (DESCRIBE → SETUP → PLAY)
│   ├── refazer_rostos.py reconstrói faces/ a partir dos clipes
│   ├── verificar_clipes.py dano de imagem vindo das câmeras
│   ├── gerar_epub.py     junta os .md num EPUB para e-reader
│   ├── gerar_icone.py    desenha o ícone (seção 14)
│   └── criar_atalho.ps1  atalho na Área de Trabalho com o ícone
├── assets/               jarvis.ico e uma prévia em PNG (gerados, versionados)
├── docs/
│   ├── ARQUITETURA.md    como funciona e por quê
│   ├── INSTALACAO.md     como instalar e operar numa máquina nova
│   ├── PYTHON.md         Python e bibliotecas, para quem vem de Java/C#
│   └── CONTEXTO.md       histórico, decisões, caminhos descartados
├── instalar.bat          instalação em máquina nova (roda uma vez)
├── jarvis.bat            inicia com janela (o atalho da Área de Trabalho aponta para ele)
├── jarvis_vigilancia.bat inicia sem janela: só grava, avisa e serve a página web
├── CLAUDE.md             regras de trabalho, lidas por toda sessão do Claude Code
├── HANDOFF.md            developer to architect, emptied after each review
├── README.md             apresentação e links para docs/
├── .env.example          modelo de configuração, versionado
│
│   ── daqui para baixo, nada é versionado ──
├── .env                  IP e credenciais das câmeras
├── config.json           ajustes e token do Telegram (cada máquina tem o seu)
├── models/               ONNX do YOLO, YuNet e SFace (~73 MB, baixados)
├── clips/                gravações
│   ├── _buffer/          segmentos rotativos por câmera, apagados sozinhos
│   └── Front/2026-09-26/19-17-30.{mp4,jpg,json}
├── faces/                rostos e galeria
│   ├── gallery.json      pessoas conhecidas e desconhecidas
│   └── 2026-09-28/21-42-00_a1b2c3.{jpg,json}
├── backups/              cópias que as ferramentas fazem antes de mexer em dados
├── logs/                 jarvis.log and its rotations (19.2)
└── HOLD                  only while production is held (18.7)
```

Production is a second clone, `C:\JARVIS`, with this same layout (18.7).

Na raiz ficam só o que o usuário abre ou edita (os `.bat`, o `.env`), a porta
de entrada da documentação (`README.md`, `CLAUDE.md`) e o que as ferramentas
exigem ali (`pyproject.toml`, `uv.lock`, `.python-version`, `.gitignore`).

Dados gerados pelo programa ficam em pastas próprias, nunca soltos na raiz.
Por isso `tools/refazer_rostos.py` guarda o `faces/` antigo em
`backups/faces_<data-hora>/`, e `tools/diagnostico.py` grava seus segmentos de
teste numa pasta temporária do sistema, que some quando ele termina.

### 3.1 O projeto é um pacote instalável

`pyproject.toml` declara um `[build-system]` com o `uv_build` e um comando:

```toml
[project.scripts]
jarvis = "jarvis.cameras:main"
```

O `uv sync` instala o pacote em **modo editável**: o `.venv` aponta para
`src/jarvis/` em vez de copiar os arquivos, então editar o código vale na hora,
sem reinstalar. `uv run jarvis` executa `main()` de `cameras.py`.

Os módulos se importam pelo nome do pacote (`from jarvis.capture import
FFmpegCamera`), igual a um `namespace` em C# ou um `package` em Java. Ver
PYTHON.md.

**Isso reverte uma decisão antiga, com motivo.** Até setembro de 2026 havia
`package = false`, porque o backend que o `uv init` escolheu **reconstruía e
reinstalava o `jarvis` a cada `uv run`**. Com o `uv_build` isso não acontece
mais: medido no M900, o segundo `uv run` diz `Requirement already installed` e
não constrói nada. Com os módulos soltos na raiz, cada script dependia de ser
executado a partir da pasta certa, e a raiz acumulava arquivos de naturezas
diferentes — código, ferramentas, histórico.

`link-mode = "copy"` resolve o outro sintoma antigo: na máquina de
desenvolvimento o cache do `uv` fica no C: e o projeto no D:, e hardlink não
atravessa volumes.

### 3.2 Caminhos partem da raiz, não da pasta atual

`jarvis/__init__.py` define `ROOT = Path(__file__).resolve().parents[2]`: o
arquivo está em `src/jarvis/`, dois níveis abaixo da raiz. `models/`,
`clips/`, `faces/` e `.env` são sempre `ROOT / ...`.

Antes eram relativos (`Path("clips")`), o que significa "relativo à pasta de
onde o comando foi executado". Rodar de outra pasta criava um `clips/` novo no
lugar errado ou não achava o `.env`.

Os caminhos **gravados** nos JSON de rostos continuam relativos à raiz
(`faces\2026-09-28\...`), para a pasta do projeto poder mudar de lugar.

## 4. Configuração — `.env`

Uma câmera = três linhas. O nome do rótulo vira o nome exibido e a pasta dos
clipes.

```
CAM_FRONT_IP=192.168.0.116
CAM_FRONT_USER=<usuario-da-conta-da-camera>
CAM_FRONT_PASSWORD=<senha-da-conta-da-camera>
```

`build_camera_list()` varre as chaves procurando o padrão `CAM_<X>_IP` e monta
a URL RTSP. Adicionar uma terceira câmera não exige mudança de código.

O `.env.example` traz `ip-da-camera` no lugar do IP, e `build_camera_list()`
encerra o programa com uma instrução se encontrar esse texto. Antes o modelo
trazia IPs de aparência real (`.10`, `.11`); no M900 eles ficaram no `.env`
sem ninguém perceber, e o sintoma foi um "nenhum frame recebido" sem erro
(5.7). Sem a checagem, o texto de exemplo daria só `I/O error`.

A senha passa por `urllib.parse.quote()` porque caracteres como `@ : / #` são
estruturais numa URL e quebrariam o parsing.

---

## 5. Camada de captura — `capture.py`

### 5.1 Por que o ffmpeg e não o OpenCV

Esta camada foi reescrita em 26/09/2026. A versão anterior usava
`cv2.VideoCapture`, o que obrigava a recodificar o vídeo para salvá-lo — o
OpenCV entrega frames decodificados, nunca os pacotes originais.

Medição que motivou a troca, 10 s da câmera Back:

| O que era gravado | Tamanho | Qualidade |
|---|---|---|
| **Stream original da câmera** | **579 KB** | **perfeita** |
| Pipeline antigo (mp4v → H.264 CRF 26) | 725 KB | 3 gerações de perda |
| Recodificado em alta qualidade (CRF 18) | 1919 KB | quase perfeita |
| H.264 sem perda (lossless) | 5089 KB | perfeita |

O arquivo antigo era **25% maior que o original e com pior qualidade**. Gastava
CPU para piorar as duas coisas: a câmera já entrega H.264 a 463 kbps com
encoder de hardware, e material já comprimido resiste a comprimir de novo.

**Sobre compactar tipo zip:** não compensa. No stream original, que é o que se
grava hoje, o ganho medido é de 0,2% — e dois dos três métodos deixam o
arquivo maior. Ver 8.7, inclusive por que uma medição antiga dizia 5–11%.

### 5.2 Uma conexão, duas saídas

A câmera aceita **apenas uma sessão RTSP**. Testado: com o OpenCV conectado, um
segundo cliente recebe `406 Not Acceptable` e não abre nada.

Isso força a arquitetura: um único processo ffmpeg por câmera tem que servir
aos dois propósitos ao mesmo tempo.

```
                    ┌─ -c copy ──────────► segmentos de 4 s em disco
RTSP ──► ffmpeg ────┤                       (pacotes originais, sem tocar)
                    └─ rawvideo 960x540 ──► pipe:1 ──► Python (análise)
```

É a arquitetura que NVRs reais usam; o Frigate faz exactamente isso.

Vantagens sobre a versão anterior:

| | Antes | Agora |
|---|---|---|
| Qualidade em disco | 3 gerações de perda | idêntica à câmera |
| Tamanho | 72 KB/s | **48 KB/s** |
| Decodificação 1080p | em Python | só no ffmpeg, uma vez |
| RAM por câmera | ~180 MB (buffer de frames) | ~0 |
| Pré-gravação | frames em memória | segmentos já em disco |

Os ganhos de CPU e RAM são justamente o que o M900 precisa.

### 5.3 Frames de análise

`ANALYSIS_WIDTH/HEIGHT = 960x540` e `ANALYSIS_FPS = 10`. O ffmpeg redimensiona
e entrega em `bgr24`, que é exatamente o layout que o numpy e o OpenCV esperam:

```python
frame = np.frombuffer(data, np.uint8).reshape(ANALYSIS_HEIGHT, ANALYSIS_WIDTH, 3)
```

Cada frame tem `960 * 540 * 3 = 1.555.200` bytes, e o leitor pede exatamente
essa quantidade. Medido na prática: ~8 fps, porque o laço gasta tempo entre
leituras.

`np.frombuffer` devolve um array **somente leitura** (aponta para os bytes do
pipe), por isso há um `.copy()` — sem ele, qualquer desenho no frame falharia.

**Implicação para a camada de rosto:** 960x540 é suficiente para movimento e
para o YOLO, mas um rosto que tem 60 px em 1080p fica com 30 px aqui, pouco
para o reconhecedor. Por isso os rostos são procurados no **clipe gravado**, em
1080p, e não nos frames de análise (10.1).

### 5.4 Leitura em thread: a interface nunca espera

A primeira versão lia o pipe dentro do laço da interface. O `read()` de um pipe
**bloqueia** até o frame inteiro chegar, e no arranque o ffmpeg leva alguns
segundos para negociar o RTSP e encher o buffer.

Medido: **o primeiro frame demora 2,45 s**. Durante esse tempo o `waitKey` não
era chamado, e o Windows marcava a janela como **"Não Responde"**, mostrando um
retângulo cinza que nunca era desenhado.

Agora cada câmera tem uma **thread leitora** que consome o pipe sem parar e
guarda o frame mais recente. O laço da interface pega o que estiver pronto:

```python
def read(self):
    """Return the newest frame not yet analysed, or None. Never blocks."""
    with self._lock:
        frame, self._pending = self._pending, None
    return frame
```

O detalhe importante é o `_pending` virar `None` na leitura. Sem isso o mesmo
frame seria analisado várias vezes, inflando o aquecimento do MOG2 e a contagem
de confirmação temporal com frames repetidos. `_latest` guarda o último frame
separadamente, para desenho.

Como o GIL é liberado durante a leitura do pipe, essa thread realmente roda em
paralelo — é o caso descrito em PYTHON.md 14.1.

Resultado medido depois da mudança, incluindo o arranque:

| | |
|---|---|
| Intervalo mediano do laço | 19,9 ms |
| Pior intervalo | 88,8 ms |
| Limite do "Não Responde" | ~5000 ms |

### 5.5 Buffer rotativo de segmentos

Os segmentos têm nome de horário (`-strftime 1`), o que torna a seleção
trivial. `covering(start, end)` devolve os segmentos **inteiros** que
intersectam a janela pedida:

```python
following = found[index + 1][0] if index + 1 < len(found) else datetime.max
if following > start and stamp < end:
```

Como se guardam segmentos inteiros, a pré-gravação sai de graça: o segmento
anterior ao evento já contém a aproximação da pessoa. Em troca, o clipe tem até
4 s extras em cada ponta, o que é justamente o que se quer.

`prune()` apaga segmentos com mais de `BUFFER_SECONDS = 240`, **nunca o mais
recente** — o ffmpeg ainda está escrevendo nele. Enquanto um evento está aberto,
`protect_from` impede que os segmentos dele sejam apagados. Medido em
30/09/2026 no M900: 6 a 8 MB por câmera, cerca de 60 segmentos.

### 5.6 Decode por hardware

`HWACCEL` insere `-hwaccel <valor>` no comando do ffmpeg. Vem vazio, porque o
valor certo depende da máquina.

Importa só para a **saída de análise**: a gravação copia pacotes e nunca
decodifica. No M900, com Quick Sync do Skylake, `"dxva2"` ou `"qsv"` tira o
decode de 1080p da CPU. Ver INSTALACAO.md seção 6.

### 5.7 Erros do ffmpeg viram texto na tela

A primeira versão mandava o `stderr` do ffmpeg para `DEVNULL`. Consequência: uma
câmera que **nunca conectava** ficava idêntica a uma câmera apenas quieta — o
painel dizia "sem sinal" e o motivo era descartado.

Isso apareceu na implantação: no M900 as duas câmeras diziam `ok` no arranque e
depois ficavam em "no signal" para sempre, sem nenhuma pista. A causa era a
máquina de desenvolvimento estar rodando ao mesmo tempo e ocupando as sessões.

Três mudanças:

**O `stderr` é capturado** por uma thread que guarda as últimas linhas. É
preciso drenar continuamente: um pipe de erro cheio bloquearia o ffmpeg.

**O `ok` do arranque virou honesto.** Antes ele checava `process.poll()` logo
depois do `Popen`, o que é sempre verdadeiro — o processo ainda não teve tempo
de falhar. Agora `wait_ready()` espera o **primeiro frame** de verdade, até
`STARTUP_SECONDS`, e devolve o motivo quando não vem.

**As mensagens são traduzidas.** O ffmpeg diz `Server returned 4XX Client Error,
but not one of 40{0,1,3,4}`, que é o 406 e não ajuda ninguém. `TRANSLATIONS`
mapeia os casos conhecidos para instruções:

| ffmpeg | Texto exibido |
|---|---|
| `401` | Credenciais incorretas, confira a Conta da Camera |
| `not one of 40` / `406` | Camera ocupada, aceita uma conexao RTSP por vez |
| `Connection refused` | Confira o IP e se a camera esta ligada |
| `timed out` | Confira a rede e o IP |
| `Error number -138` | Confira a rede e o IP, o roteador pode ter trocado o IP |

Erro desconhecido passa cru, em vez de virar uma mensagem genérica que esconde
informação.

**Toda conexão tem prazo: `-timeout`.** Sem ele, um IP onde não existe nada
deixa o ffmpeg esperando a conexão TCP para sempre, **sem escrever nenhum
erro**. Foi o que aconteceu no M900: as câmeras estão em `.116` e `.42`, e o
`.env` de lá apontava para `.10` e `.11` — os valores de exemplo do
`.env.example`, de onde o `instalar.bat` cria o `.env`. O painel dizia só
"nenhum frame recebido", e a investigação foi atrás de decode, pipe e antivírus
antes de alguém rodar `Test-NetConnection`. A única linha do log, mesmo em
`-loglevel verbose`, era `Starting connection attempt`.

Com `-timeout` (em microssegundos, `SOCKET_TIMEOUT_SECONDS` no `capture.py`) o
ffmpeg desiste em ~6 s. No Windows o erro sai como `Error number -138`, que é o
`ETIMEDOUT` da biblioteca C, sem as palavras "timed out" — por isso a linha
própria na tabela. O mesmo prazo vale para leituras: câmera que para de mandar
dados por 5 s derruba o processo, e o reinício automático (5.8) reconecta.

O painel "sem sinal" mostra esse texto quebrado em linhas, então o motivo fica
visível sem abrir o terminal.

### 5.8 Reinício automático

Se o ffmpeg morrer (queda de rede, câmera reiniciando), `read()` devolve `None`
e o processo é recriado após `RESTART_SECONDS`. O painel continua mostrando o
último frame nesse intervalo, e a aplicação não cai. "Sem sinal" só aparece se
a câmera nunca entregou frame nenhum.

Como o OpenCV não faz mais captura, a variável de ambiente
`OPENCV_FFMPEG_CAPTURE_OPTIONS` desapareceu, junto com a fragilidade de ter uma
atribuição obrigatória antes do `import cv2` (PYTHON.md 2.2). O transporte TCP
agora é um argumento explícito do ffmpeg (`-rtsp_transport tcp`). A única
variável que resta é `OPENCV_LOG_LEVEL`, e ela só silencia um aviso (10.11).

---

## 6. Camada de movimento — `motion.py`

### 6.1 Por que MOG2

| Algoritmo | Avaliação |
|---|---|
| Diferença de frames | Simples, mas pega só as **bordas** do que se move e dispara com qualquer variação de luz. |
| **MOG2** | **Escolhido.** Aprende o fundo e se adapta. Marca sombras separadamente, o que importa muito em ambiente externo. Rápido e já vem no OpenCV. |
| KNN | Equivalente, segundo lugar. Troca de uma linha se o MOG2 falhar. |
| GSOC | Melhor com fundos agitados, porém muito mais lento e exige `opencv-contrib-python`. |

**Como o MOG2 funciona:** ele não guarda uma imagem de fundo. Para cada pixel
guarda várias distribuições estatísticas ("misturas de gaussianas"), então um
pixel pode ter mais de uma aparência normal — uma folha que balança, por
exemplo. Pixel que não combina com nenhuma delas é movimento.

### 6.2 Os passos de `detect()`

1. **Reduz para 640 px de largura.** Movimento não precisa de resolução total;
   a imagem menor é ~9× mais barata.
2. **Desfoque gaussiano.** Sem ele, ruído de sensor e artefatos de compressão
   viram milhares de pixels "em movimento".
3. **`subtractor.apply()`** compara com o modelo **e atualiza o modelo**. Por
   isso precisa rodar em todo frame, inclusive durante o aquecimento — senão o
   modelo nunca aprende.
4. **Limiar em 200.** A máscara usa 255 para movimento, 127 para sombra, 0 para
   fundo. O corte em 200 descarta as sombras.
5. **Apaga o relógio da câmera.** A Tapo escreve data e hora no canto superior
   esquerdo, e os dígitos mudam a cada segundo. `OVERLAY_BOX` (frações da
   imagem) zera essa faixa da máscara.
6. **Descarta o frame se mais de 50% "mudou".** Isso não é um objeto se
   movendo: é nuvem, sol ou a câmera entrando em modo noturno.
7. **Abertura e dilatação.** A abertura apaga pontos isolados; a dilatação
   cresce o que sobrou, unindo os fragmentos de uma mesma pessoa num só blob.
   É também por isso que a caixa fica um pouco maior que o objeto.
8. **Contornos + `boundingRect`.** Blobs com área menor que `MIN_AREA` são
   ignorados. As coordenadas voltam para a escala do frame original.
9. **Filtro de luz.** Blob cujo conteúdo ainda se parece com o fundo é luz
   mudando, não objeto. Ver 6.7.
10. **Confirmação temporal.** Ver 6.3 — nada é reportado antes de persistir.

### 6.3 Confirmação temporal (o filtro contra insetos)

O problema real medido em campo: à noite o infravermelho ilumina insetos
próximos à lente, que viram blobs **grandes e brilhantes**. Medição de 30 s na
câmera Front mostrou 12 blobs com área acima de 3200 — maiores que uma pessoa
distante. Ou seja, **aumentar `MIN_AREA` nunca resolveria**: tamanho não separa
inseto de pessoa.

O que separa é **persistência**. Uma pessoa continua aproximadamente no mesmo
lugar por vários frames; um inseto aparece, salta e some.

`_confirm()` implementa um mini-rastreador:

- Cada blob vira um `_Candidate` com contador de acertos (`hits`) e falhas
  (`misses`).
- A cada frame, os blobs novos são casados com os candidatos existentes por
  **maior sobreposição**. Quem casa ganha `hits += 1`.
- Candidato que não casa ganha `misses += 1` e é descartado após
  `FORGET_FRAMES`.
- Só é reportado quem atingiu `CONFIRM_FRAMES` acertos.

Custo: uma pessoa é reportada 3 frames (~0,3 s) depois de aparecer. Como o
clipe começa `PRE_SECONDS` (6 s) antes do evento (8.2), nada de útil se perde
no vídeo.

**Limitação conhecida:** um inseto que fique pairando exatamente no mesmo ponto
por vários frames acaba confirmado. O YOLO rejeita esse caso.

Este também é o embrião do *tracking* que virá depois.

### 6.4 Aquecimento

`WARMUP_FRAMES = 60` (~6 s a 10 fps). Antes disso tudo é "novidade" e o detector
reportaria a cena inteira. O painel mostra `learning background`.

### 6.5 Ajustes

| Constante | Efeito |
|---|---|
| `MIN_AREA` | Aumentar ignora objetos pequenos/distantes. |
| `CONFIRM_FRAMES` | Aumentar exige mais persistência: menos ruído, mais atraso. |
| `FORGET_FRAMES` | Quanto tempo um candidato sobrevive sumindo (oclusão). |
| `OPEN_ITERATIONS` | Aumentar apaga mais pontos isolados. |
| `varThreshold` | Aumentar deixa menos sensível a variação. |
| `DETECT_WIDTH` | Aumentar melhora objetos distantes, custa CPU. |
| `MAX_MOTION_FRACTION` | Tolerância a mudanças globais de iluminação. |
| `LIGHTING_CORRELATION` | Baixar descarta mais mudanças de luz, mas começa a perder pessoa (6.7). |
| `OVERLAY_BOX` | Região do relógio da câmera, ignorada. |

**Para ficar ainda menos sensível:** suba `CONFIRM_FRAMES` para 5. Para
recuperar pessoas distantes, baixe `MIN_AREA` de volta para 400 — a confirmação
temporal já segura o ruído sozinha.

### 6.6 Resultados medidos

Teste A/B sobre **exatamente os mesmos frames ao vivo**, 404 frames por câmera,
à noite:

| Câmera | Frames com movimento (antes) | Depois | Redução |
|---|---|---|---|
| Back | 2,5% | 1,2% | 50% |
| Front | 8,7% | 1,5% | **83%** |

Caixas totais na Front: **54 → 6**.

Como o YOLO só roda quando há movimento, isso significa cerca de **6× menos
inferências** na Front. Reduzir a sensibilidade aqui não custa desempenho: ela
o melhora.

### 6.7 Luz do sol não é movimento

**O problema, medido de dia no M900.** A Front mostrava caixas amarelas sem
ninguém na cena. Em 4 minutos de buffer, 99 de 2671 frames tinham movimento,
quase todos numa rajada de 12 s com até 15 caixas espalhadas por parede, portão
e chão. O brilho médio da imagem mal mudou (89 → 92): não era a cena inteira
escurecendo, e sim **manchas de sol** aparecendo e se intensificando em partes
da parede, mais a sombra das folhas balançando no chão. O passo 6 não pega isso,
porque a área total mudada fica bem abaixo de 50%.

O MOG2 marca como movimento qualquer pixel que ficou diferente do fundo. Ele não
sabe distinguir "outra coisa apareceu aqui" de "a mesma coisa ficou mais clara".

**A ideia.** Luz muda o brilho, mas não o conteúdo: as bordas, a textura do
reboco, o desenho do portão continuam no mesmo lugar. Uma pessoa troca o
conteúdo. A **correlação cruzada normalizada** mede exatamente isso:

```python
a = a - a.mean()
b = b - b.mean()
correlation = (a * b).sum() / sqrt((a * a).sum() * (b * b).sum())
```

Subtrair a média remove o "mais claro ou mais escuro"; dividir pelas normas
remove o "mais contraste ou menos". O que sobra é 1,0 para o mesmo desenho e
perto de 0 para desenhos sem relação. Em Java seria um laço sobre dois arrays;
com NumPy cada linha opera sobre o patch inteiro de uma vez (PYTHON.md).

Para cada blob, `_raw_boxes()` compara o frame atual com
`subtractor.getBackgroundImage()` — a imagem de fundo que o próprio MOG2
aprendeu — e descarta o blob se a correlação passar de `LIGHTING_CORRELATION`.

**Só os pixels que mudaram.** A primeira versão comparava o retângulo inteiro.
Mas o retângulo de uma pessoa é em boa parte fundo intacto, que puxa a
correlação para cima, e a pessoa era descartada junto com a luz. A versão atual
compara só os pixels que a máscara marcou como mudados, antes da dilatação
(`changed`).

**Medição** sobre os mesmos frames: 4 minutos da Front sem ninguém, e os 10
clipes gravados com pessoa (273 frames em que o YOLO vê a pessoa):

| Versão | Frames com movimento sem ninguém | Pessoa coberta por movimento |
|---|---|---|
| Sem filtro | 99 | 262 |
| Retângulo inteiro, 0,75 | 1 | 216 |
| Só pixels mudados, 0,85 | 39 | 261 |
| Só pixels mudados, 0,75 | 22 | 259 |
| **Só pixels mudados, 0,65** | **15** | **258** |
| Só pixels mudados, 0,55 | 14 | 245 |

0,65 corta 85% do falso movimento e perde 4 de 273 frames de pessoa. Abaixo
disso o ganho acaba e a perda cresce. Todos os clipes continuam disparando
gravação.

O fundo só é calculado quando existe algum blob, então frame parado não paga
nada a mais.

---

## 7. Camada de sujeitos — `people.py`

### 7.1 O que o YOLO faz aqui

YOLO11 foi treinado com corpos inteiros: forma, postura, membros, proporções.
**Ele não tem noção de rosto.** Por isso máscara, capacete, capuz ou pessoa de
costas continuam sendo detectados.

O COCO tem 80 classes. Vigiamos estas:

```python
PERSON_CLASS = 0
CLASS_NAMES = {0: "person", 14: "bird", 15: "cat", 16: "dog",
               17: "horse", 18: "sheep", 19: "cow"}
```

Ou seja: `person`, `bird`, `cat`, `dog`, `horse`, `sheep`, `cow`. Bear, elephant
e zebra existem no COCO e foram deixados de fora por serem implausíveis aqui —
incluí-los só criaria falsos positivos exóticos.

Animais usam um limiar de confiança mais alto (`ANIMAL_CONFIDENCE = 0.45` contra
`CONFIDENCE = 0.35`), porque objetos de cena são confundidos com animais com
mais facilidade que com pessoas.

**Observado em 30/09/2026, ainda não tratado:** eventos rotulados `cat`, `cow`,
`sheep` e `bird` numa casa onde há cachorro e gente. Provavelmente é o YOLO
hesitando entre espécies para o mesmo cachorro, de frame em frame. Como
`labels` acumula tudo que apareceu no evento (8.4), uma única hesitação já
entra no rótulo. Não muda o que é gravado, só o texto do cartão.

### 7.2 O tipo `Detection`

Detecções deixaram de ser tuplas anônimas e viraram um `NamedTuple` em
`geometry.py`:

```python
Detection(x, y, w, h, confidence, label)
```

Continua sendo uma tupla (indexável, desempacotável), então `d[:4]` ainda é a
caixa, mas agora carrega o rótulo e expõe `d.is_person`. Foi o que permitiu o
mesmo pipeline tratar pessoas e animais sem duplicar código.

`drop_duplicates` só funde caixas **do mesmo rótulo** — um cachorro ao lado de
uma pessoa se sobrepõe muito, e antes um dos dois seria descartado.

### 7.3 Saber que é um cachorro, não qual cachorro

| Objetivo | Situação |
|---|---|
| Detectar que existe um cachorro | Funciona (COCO classe 16) |
| Saber *qual* cachorro | Não feito; a camada de rosto não serve (10.8) |
| Saber *qual* pessoa | Camada de rosto, YuNet + SFace (seção 10) |

### 7.4 Decisão de projeto: frame inteiro, não recorte

A primeira versão recortava o frame na região do movimento e rodava o YOLO só
nesse recorte. Teste revelou a falha:

- Recorte de 192×192, pessoa ocupando quase a imagem toda.
- O YOLO acertou "pessoa", mas **a caixa retornada ficou limitada ao recorte**:
  153×115 em vez do corpo inteiro.

Isso é um teto estrutural, não questão de ajuste. Pior: se o movimento pegar só
as pernas, a caixa recortada **nunca** conterá a cabeça — e a camada de rosto
usa justamente a caixa do corpo para confirmar que um rosto é de uma pessoa
(10.9).

**Solução:** YOLO roda no frame inteiro. O movimento serve como (a) gatilho e
(b) filtro de relevância. Reteste com o mesmo blob minúsculo: caixa completa
`120,202 → 1109,712`, confiança 0.92, batendo com o *ground truth*.

### 7.5 Throttle

O YOLO custa 50 a 62 ms por inferência na máquina de desenvolvimento (7.11).
Rodar em todo frame comeria o orçamento e travaria o vídeo. `MIN_INTERVAL =
0.25` limita a 4 execuções por segundo por câmera, **reaproveitando a resposta
anterior** no intervalo.

Evidência de que funciona, medida ainda com o PyTorch: a taxa de frames ficou
em 12,7 fps antes e depois de adicionar o YOLO. No M900 o número a acompanhar é
o uso de CPU com as duas câmeras em movimento ao mesmo tempo.

### 7.6 Filtro de sobreposição

`REQUIRE_MOTION_OVERLAP = True` descarta pessoas detectadas que não encostam em
nenhuma caixa de movimento. Isso amarra a resposta ao evento que a disparou.

**Limitação conhecida:** quem parar de se mover é absorvido pelo modelo de
fundo e deixa de ser reportado. A solução é *tracking*, próxima camada.

### 7.7 `drop_duplicates` e IoU

Duas caixas podem descrever a mesma pessoa. "Mesma" é medido por **IoU**
(*Intersection over Union*): área compartilhada dividida pela área combinada.
0 = sem sobreposição, 1 = idênticas. Acima de 0.5, tratamos como uma só e
mantemos a de maior confiança.

A função `iou()` vive em `geometry.py`, compartilhada com o rastreador de
movimento, que usa `overlap_area()` do mesmo módulo para casar candidatos entre
frames.

### 7.8 Supressão de cenário estático

**O problema observado em campo (2026-09-26):** a câmera Front gravou dois
clipes marcados como `person left`. Reanalisando os vídeos, o YOLO apontava
pessoa em 100% dos frames, com confiança 0,80 — e **exatamente a mesma caixa**
nos dois clipes, gravados com 90 s de diferença: 68×82 px em (1391, 311).

Era um objeto fixo na parede. Um segundo ponto em (364, 285) fazia o mesmo.

O detalhe revelador: **nos clipes diurnos do mesmo enquadramento o YOLO não
detecta pessoa alguma.** O falso positivo é específico do infravermelho, que
transforma o objeto numa silhueta escura contra a parede clara.

**A solução:** um objeto de cenário não se move; uma pessoa sim. `_reject_scenery`
mantém uma lista de pontos onde detecções continuam surgindo:

- Duas caixas são "o mesmo lugar" quando os centros estão a até
  `STATIC_CENTRE_TOLERANCE` px e os tamanhos diferem menos de
  `STATIC_SIZE_TOLERANCE`. Casar por centro (e não por IoU) foi necessário
  porque a caixa do segundo objeto **oscilava de tamanho** — 73×65, 68×68,
  71×74 — e nunca atingia IoU alto, embora o centro ficasse parado.
- A contagem é **consecutiva**: qualquer ciclo em que o ponto não reaparece
  zera `hits`. Sem isso, alguém que fica parado, anda e volta acabaria somando
  acertos ao longo do tempo.
- Ao atingir `STATIC_HITS` ciclos seguidos, o ponto vira cenário e é ignorado.
- Pontos somem da lista após `STATIC_TTL` sem aparecer.

**Resultado no clipe real:** os dois objetos foram aprendidos como dois pontos
e silenciados a partir do ciclo 49. Uma pessoa que se mexe a cada 10 ciclos
continua detectada.

**Custo consciente:** alguém absolutamente imóvel por ~12 s (50 ciclos a 4/s) é
suprimido. É aceitável porque o clipe já capturou a chegada dessa pessoa, e
qualquer movimento a libera no mesmo instante. Para ser mais conservador, suba
`STATIC_HITS`.

**Custo no arranque:** a lista nasce vazia a cada execução, então o programa
grava um clipe do objeto estático antes de aprendê-lo. Persistir a lista em
disco resolveria isso e é um próximo passo natural.

### 7.9 Altura mínima para pessoa

Na noite de 26/09/2026 a câmera Front gravou **19 eventos**, dos quais só 3 eram
pessoas de verdade. Os outros 16 eram caixinhas na parede acima do carro, com
confiança entre 0,36 e 0,79 — alta o bastante para passar pelo limiar.

A supressão de cenário estático (7.8) **não pega esse caso**: os falsos
positivos aparecem separados por minutos, então a contagem consecutiva zera
entre um evento e outro e nunca chega aos 50 ciclos.

A medição das caixas de todas as 18 miniaturas resolveu:

| | Altura da caixa | Razão alt/larg |
|---|---|---|
| **Pessoas reais** (3) | 294–306 px | 1,55–2,32 |
| **Falsos positivos** (15) | **36–86 px** | 0,91–1,59 |

A altura separa os dois grupos com folga de **3,4×** (86 contra 294). A razão
largura/altura se sobrepõe (1,59 contra 1,55) e por isso foi descartada como
critério.

```python
MIN_PERSON_HEIGHT_FRACTION = 0.20
```

Fração da altura do frame, não pixels absolutos, para sobreviver a mudanças de
`ANALYSIS_HEIGHT`. A 540 px isso dá 108 px: 26% acima do maior falso positivo e
2,7× abaixo da menor pessoa real.

**Verificado contra as 18 gravações reais: 18 acertos, 0 erros.**

Duas ressalvas honestas:

- **É específico da cena.** Numa cena onde pessoas apareçam pequenas ao longe,
  108 px descartaria gente de verdade. Aqui a garagem é estreita e mesmo no
  fundo uma pessoa passa dos 150 px.
- **Só vale para `person`.** Animais são naturalmente mais baixos que largos, e
  aplicar o mesmo piso rejeitaria um cachorro legítimo. Ainda não há dados de
  detecção real de animais para calibrar um limiar próprio.

### 7.10 Um modelo, várias câmeras

`@lru_cache(maxsize=1)` em `load_model()` garante uma única instância do YOLO
para o laço ao vivo, compartilhada pelas câmeras. É o oposto do
`MotionDetector`:

| Componente | Estado | Instâncias |
|---|---|---|
| `MotionDetector` | modelo de fundo daquela câmera | **uma por câmera** |
| `SubjectDetector` | throttle, último resultado e cenário estático | uma por câmera |
| Rede YOLO do laço ao vivo (`load_model`) | buffers internos | **uma, só na thread principal** |
| Rede YOLO de fundo (`load_background_model`) | buffers internos | uma, só na varredura de rostos |

Compartilhar entre câmeras funciona porque todas rodam na mesma thread, uma
depois da outra. Compartilhar entre **threads** derrubou o programa: ver 10.9.

### 7.11 Por que OpenCV e não PyTorch

O YOLO roda pelo `cv2.dnn` sobre o export ONNX, não pelo `ultralytics`. A troca
foi forçada por um problema de implantação, em 29/09/2026.

**O sintoma:** na máquina de destino, e horas depois também na de
desenvolvimento, o PyTorch parou de carregar:

```
OSError: [WinError 4551] An Application Control policy has blocked this
file. Error loading "...\torch\lib\shm.dll"
```

**A causa:** o **Smart App Control** do Windows 11, que bloqueia binários sem
assinatura reconhecida pela Microsoft. As DLLs do PyTorch não são assinadas.
Confirmado pelo registro:

```
HKLM\SYSTEM\CurrentControlSet\Control\CI\Policy
    VerifiedAndReputablePolicyState = 1    (ligado, bloqueando)
```

**Por que não desligar o Smart App Control:** ele é **irreversível**. Uma vez
desligado, só volta reinstalando o Windows. Trocar a segurança do sistema por
uma dependência é um preço alto e permanente.

**A saída:** o Ultralytics publica o `yolo11s.onnx` oficial no mesmo release de
onde já vinha o `.pt`, e o OpenCV — cujas DLLs são assinadas e passam — executa
esse ONNX sem PyTorch nenhum.

Ganhos além de destravar:

| | Antes | Depois |
|---|---|---|
| Dependências | opencv, ultralytics, torch, torchvision + 38 | **opencv, imageio-ffmpeg** |
| Peso | ~2,5 GB | ~90 MB |
| Inferência (dev) | 24 ms | **50-62 ms** |

O custo é real: cerca de 2x mais lento. Com o portão de movimento e o
`MIN_INTERVAL` de 0,25 s isso não apareceu nos testes, mas é o número a
acompanhar no M900. O `cv2.dnn` aceita backend OpenVINO, que já era o plano
para aquela máquina, então há caminho de volta para a velocidade.

**O que foi preciso escrever à mão.** O `ultralytics` fazia pré e
pós-processamento por baixo dos panos; agora são explícitos:

- `_letterbox()` encaixa o frame num quadrado de 640 sem distorcer, guardando a
  escala para desfazer depois
- A saída é `(1, 84, 8400)`: 8400 caixas candidatas, cada uma com 4 números de
  geometria e 80 de pontuação por classe. Transpor e percorrer dá as detecções
- `cv2.dnn.NMSBoxes` elimina as caixas sobrepostas da mesma detecção

Foi exatamente o trabalho apontado, no começo do projeto, como o custo de usar
C++ em vez de Python. Ele apareceu de qualquer forma — só que por um motivo que
ninguém previu.

**Os nomes das classes** vinham de `model.names`. Sem o ultralytics, o
`CLASS_NAMES` lista apenas as sete que interessam, e a filtragem por classe usa
esse mesmo dicionário.

---

## 8. Camada de gravação — `clips.py`

### 8.1 Nada é recodificado

O clipe é montado concatenando **segmentos inteiros** do buffer com o
`concat` do ffmpeg em modo `-c copy`:

```
ffmpeg -f concat -safe 0 -i lista.txt -c copy -movflags +faststart saida.mp4
```

`-c copy` significa "copie os pacotes, não decodifique nem recodifique". O
resultado é bit a bit o que a câmera produziu — não existe qualidade melhor
possível, porque a câmera já é a fonte.

**Verificado:** o clipe montado sai em **1920x1080, h264, 270 frames em 18 s**,
enquanto a análise roda em 960x540. Se houvesse recodificação a partir dos
frames de análise, o vídeo sairia em 960x540.

### 8.2 Quando o evento começa e termina

- Começa no primeiro frame com sujeito detectado. Nesse instante a **miniatura**
  é salva e o horário é registrado.
- `POST_SECONDS = 5.0` — o evento fecha após 5 s sem ninguém. A detecção oscila,
  e parar na hora fragmentaria um evento em dezenas de arquivos.
- `MAX_SECONDS = 60.0` — teto rígido.
- `PRE_SECONDS = 6.0` — quanto se pede para trás ao selecionar segmentos.

### 8.3 Atraso de montagem

O ffmpeg só finaliza um segmento quando começa o próximo. Montar o clipe
imediatamente pegaria o último segmento incompleto, então a montagem roda numa
**thread** que espera `ASSEMBLY_DELAY = SEGMENT_SECONDS + 2` segundos antes de
concatenar.

Os metadados, porém, são escritos **na hora**, para a gravação aparecer na tela
Records imediatamente. O vídeo materializa poucos segundos depois; por isso
`reveal()` cai para a pasta do dia se o `.mp4` ainda não existir.

`wait_for_jobs()` é chamado na saída para nenhuma montagem ficar pela metade.

### 8.4 Três arquivos por evento

```
19-17-30.mp4     vídeo, montado dos segmentos originais
19-17-30.jpg     o primeiro frame em que o sujeito apareceu
19-17-30.json    metadados
```

A miniatura vem do frame de análise (960x540) reduzido para `THUMB_WIDTH = 480`
— nenhuma perda prática, já que ela é sempre exibida pequena.

O `.json` existe para que a tela Records **nunca precise abrir um vídeo**:

```json
{
  "camera": "Front",
  "started_at": "2026-09-26T19:52:06",
  "time": "19:52:06",
  "seconds": 12.1,
  "labels": ["dog", "person"],
  "best_confidence": 0.88,
  "video": "19-52-06.mp4",
  "thumbnail": "19-52-06.jpg",
  "reason": "subject left"
}
```

`labels` acumula tudo que apareceu durante o evento, não só no primeiro frame.

Um JSON por clipe é deliberadamente simples e inspecionável — o passo seguinte
é SQLite, quando houver busca por pessoa e por período.

### 8.5 A miniatura é a única que leva caixas desenhadas

O **vídeo** nunca é tocado, então não há como sujá-lo. A **miniatura** recebe as
caixas de propósito, porque a função dela é ser folheada por um humano.

Esse era um cuidado explícito na versão antiga (o gravador recebia o frame
limpo); agora é consequência da arquitetura, o que é melhor: não depende de
ninguém lembrar.

### 8.6 Armazenamento

A taxa depende do que a câmera está vendo: cena parada comprime muito, cena com
gente e luz do dia comprime pouco. Duas medições:

| Medição | Taxa |
|---|---|
| Clipe noturno de 18 s, dev, 26/09 | ~48 KB/s |
| **Todos os clipes de 30/09 no M900** (dia e noite) | **~120 KB/s** |

O dia 30/09 é a referência realista: **102 eventos, 41 minutos de clipe,
303 MB**. Nesse ritmo:

| Período | Espaço |
|---|---|
| Por dia | ~300 MB |
| Por mês | ~9 GB |
| Por ano | **~110 GB** |

Uma estimativa anterior desta seção dizia ~5 GB/ano. Ela usava a taxa noturna e
supunha 5 minutos de atividade por dia; a casa real tem 8 vezes mais. Com esse
volume, **retenção automática** (8.7) deixou de ser opcional.

O buffer rotativo custa à parte e não cresce: 6 a 8 MB por câmera (5.5).

### 8.7 Arquivamento em zip: implementado, medido e removido

Os clipes ficam em disco como `.mp4` soltos. **Não há compactação**, e isso é
uma decisão medida, não um esquecimento.

Em 26/09/2026 o arquivamento em zip foi implementado por completo — empacotar o
clipe, apagar o `.mp4`, descompactar no acesso, selo `ZIP` no cartão — e então
removido, porque a medição no arquivo real mostrou que não serve para nada:

| Método | 1302 KB de mp4 vira | Ganho |
|---|---|---|
| deflate | 1299 KB | **0,2%** |
| bzip2 | 1304 KB | **−0,2%** (maior) |
| lzma | 1313 KB | **−0,9%** (maior) |

**Por que:** H.264 já é codificado por entropia. A redundância que um
compactador de uso geral procura foi removida pelo codec. Dois dos três métodos
produzem arquivo **maior**, porque o overhead do container supera a economia.

O custo era real: perder o duplo clique para assistir, e `.mp4` extraídos se
acumulando ao lado dos `.zip`. Em troca de 2,6 KB por gravação.

**Cuidado com números antigos.** Uma medição anterior indicava 5–11%, e estava
correta **para o formato antigo**: aquele arquivo era recodificado em CRF 26 e
ainda tinha folga. Os arquivos atuais vêm do encoder de hardware da câmera e
estão muito mais apertados. A conclusão mudou junto com o formato — se o
formato mudar de novo, remeça antes de concluir.

**O que realmente reduz disco** neste projeto, em ordem de impacto:

1. Não gravar o que não é evento — feito (movimento, filtro de luz,
   confirmação temporal, supressão de cenário estático).
2. Não recodificar — feito (seção 5.1). O arquivo antigo era 25% maior que o
   original e pior.
3. **Retenção automática** — não feito, e é o único lever grande que resta.
   Com ~300 MB/dia (8.6), os 394 GB livres do M900 (30/09/2026) acabam em
   cerca de 3 anos e meio — antes, se houver mais câmeras ou mais movimento.
4. Compactar — 0,2%, descartado.

---

## 9. Interface — `ui.py`

A janela inteira é uma única imagem numpy, montada assim:

```
┌──────────┬──────────────────────────┬──────────┐
│ J.A.R.V. │                          │ 09/2026  │
│          │   Live (letterbox)       │ D S T Q  │
│ ▸ Live   │   ou grade de gravações  │  1 2 3 4 │
│   Records│   ou grade de rostos     │  5 6 7 8 │
│   People │                          │          │
└──────────┴──────────────────────────┴──────────┘
  190 px                                 250 px
                                (só em Records e People)
```

O HighGUI do OpenCV **não tem widgets**: não existe botão, lista, scroll nem
gerenciador de layout. Tudo é retângulo e texto desenhados à mão.

### 9.1 Proporção ao redimensionar a janela

**Problema:** esticar a janela esticava o vídeo, deformando a imagem.

A causa é que o backend do HighGUI escala a imagem recebida para preencher a
janela, sem respeitar proporção. A flag que deveria resolver não serve:

```python
cv2.WINDOW_KEEPRATIO   # vale 0 — idêntico a WINDOW_NORMAL
cv2.WINDOW_FREERATIO   # vale 256
```

`WINDOW_KEEPRATIO` ser `0` significa que combiná-la com `WINDOW_NORMAL` não
muda nada; ela só tem efeito no backend Qt, e aqui o backend é o Win32.

**Solução:** perguntar o tamanho da janela e devolver uma imagem **exatamente
daquele tamanho**. Se a imagem já tem a dimensão da janela, não há nada para o
backend escalar:

```python
_, _, width, height = cv2.getWindowImageRect(WINDOW)
```

Dentro dessa tela, `letterbox()` desenha o vídeo na maior escala que couber
preservando a proporção, centralizado, com barras escuras nas sobras:

```python
scale = min(area_w / w, area_h / h)
```

Medido: numa janela 1000×900, o vídeo de proporção 3,554 é desenhado como
810×227 — proporção 3,568, a diferença vindo só do arredondamento a pixel
inteiro.

**Benefício colateral importante:** como a imagem tem o tamanho exato da
janela, as coordenadas do mouse passam a mapear 1:1 com o que é desenhado. Sem
isso, os cliques sairiam deslocados sempre que a janela fosse redimensionada.

`getWindowImageRect` devolve valores inválidos antes da janela existir, então
`window_size()` cai para o tamanho natural do layout nesse caso.

### 9.2 Só redesenha quando vale a pena

As câmeras entregam ~10 frames por segundo, mas o laço gira a cada ~20 ms. A
maioria das voltas não tem frame novo, e redesenhar a tela inteira nelas seria
desperdício puro — num M900 de quatro núcleos, desperdício caro.

O redesenho acontece quando **alguma câmera trouxe frame novo**, ou quando
passaram `REDRAW_SECONDS = 0.15` sem nada. O segundo caso existe para a
interface continuar viva: o cursor do campo de nome pisca, e a tela Records
precisa reler a pasta de tempos em tempos.

O `cv2.waitKey(15)` continua sendo chamado em **toda** volta, com frame novo ou
sem. É ele que mantém a janela respondendo (PYTHON.md 16), e os 15 ms também
evitam que o laço gire a mil por segundo sem fazer nada.

Os painéis ficam guardados por câmera num dicionário. Câmera sem frame novo
reaproveita o painel anterior, em vez de virar "sem sinal" a cada volta.

### 9.3 Modo imediato: nada persiste

Vindo de Swing, WinForms ou WPF, o instinto é criar controles uma vez e deixar
o framework mantê-los. Aqui é o oposto — é o modelo que jogos usam:

**A cada volta do laço a janela é redesenhada do zero.** Não existe objeto
"botão" guardado em lugar algum; existe apenas um array numpy que nasce, recebe
pixels e é jogado na tela. No frame seguinte, outro array.

`render()` cria a tela como um array do tamanho exato da janela, preenchido com
a cor de fundo, e pinta cada parte por cima:

```python
canvas = np.full((height, width, 3), BACKGROUND, dtype=np.uint8)
self._draw_sidebar(canvas, height)
```

O conteúdo à direita do menu é a tela Live, a Records ou a People. As
primitivas são todas chamadas do `cv2` sobre o array: `rectangle` (com espessura
`-1` para preenchido), `putText`, `line`, `circle`. Na Live, os painéis das
câmeras são colados lado a lado com `np.hstack` antes de irem para a tela.

Consequência prática: **não há estado de interface para dessincronizar**. O que
aparece é função direta dos dados daquele instante. Em troca, tudo é
recalculado várias vezes por segundo — daí os cuidados de cache da seção 9.6.

### 9.4 Cliques: coordenadas cruas e uma pegadinha

`cv2.setMouseCallback(WINDOW, interface.on_mouse)` entrega `(event, x, y,
flags, param)`. Nenhum elemento "sabe" que foi clicado: chega o pixel e você
mesmo descobre o que há ali.

Passar um **método ligado** (`interface.on_mouse`, não uma função solta) é o
truque que evita variável global: o `self` já carrega todo o estado da tela.

Com menu, calendário e cartões, o teste de clique por aritmética não escala.
A `Interface` usa então **regiões de clique registradas no desenho** — o padrão
clássico de interface em modo imediato:

```python
self._region((x, y, x + card_w, bottom), "open", entry["video_path"])
```

Cada elemento, ao ser desenhado, grava seu retângulo e a ação correspondente.
A lista é zerada a cada frame, no início do `render()`, e o clique percorre as
regiões procurando a primeira que o contém. Medido: a tela Records registra
**41 regiões** (2 do menu, 2 setas de mês, 30 dias, 7 cartões).

As ações são pares `(tipo, payload)`:

| Ação | Efeito |
|---|---|
| `view` | Troca entre Live, Records e People |
| `day` | Seleciona o dia exibido |
| `month` | Avança ou volta um mês no calendário |
| `open` | Abre o arquivo no Explorer |
| `name` | Abre o campo de nome para aquele rosto (10.7) |

A vantagem é que layout e interação nunca saem de sincronia: quem move um
cartão move automaticamente sua área clicável, porque é a mesma linha de código
que faz as duas coisas.

### 9.5 Tela Live

`make_panel()` redimensiona cada frame para 480 px de altura e desenha por
cima. As caixas chegam em pixels do frame original, então são multiplicadas
por `scale` para caber no painel.

| Elemento | Significado |
|---|---|
| Retângulo amarelo fino | Algo se moveu |
| Retângulo verde grosso | Pessoa, com confiança |
| Retângulo ciano grosso | Animal, com espécie e confiança |
| Ponto vermelho + `REC` | Gravando |

`np.hstack` cola os painéis lado a lado e **exige altura idêntica** — é a única
razão de `make_panel` redimensionar.

### 9.6 Tela Records

Abre nas gravações **de hoje**, lendo apenas os `.json` e os `.jpg`. Nenhum
vídeo é aberto ou decodificado, o que era o requisito.

Cada cartão mostra:

| Campo | Onde |
|---|---|
| **Hora de início** (`HH:MM:SS`) | em destaque, fonte maior |
| Câmera | à direita, na mesma linha |
| Rótulos (`person`, `dog`) | verde para pessoa, ciano para animal |
| Duração em segundos | ao lado dos rótulos |

**Clicar num cartão abre o arquivo no Explorer**, já selecionado na pasta:

```python
subprocess.Popen(f'explorer /select,"{target}"')
```

O `/select` faz o Explorer abrir a pasta **com o arquivo destacado**, em vez de
apenas abrir o diretório. É preciso caminho absoluto, daí o `resolve()`. O
Explorer retorna código de saída 1 mesmo quando funciona, então usamos `Popen`
e ignoramos o retorno em vez de `run(check=True)`.

**A string aqui é obrigatória, e a lista não funciona.** A primeira versão
usava a forma de lista, que é a recomendada em geral, e o clique abria a pasta
Documentos em vez do arquivo. A razão:

```python
subprocess.list2cmdline(["explorer", f"/select,{alvo}"])
# explorer "/select,D:\Personal Projects\...\19-17-30.mp4"
```

No Windows o `subprocess` monta a linha de comando com `list2cmdline`, que
envolve em aspas qualquer argumento contendo espaço. Como o caminho tem
espaço ("Personal Projects"), **o `/select,` foi para dentro das aspas**. O
Explorer não reconhece a opção assim, desiste e abre a pasta padrão.

O Explorer precisa de `explorer /select,"<caminho>"` — só o caminho entre
aspas. Passar uma string ao `Popen` no Windows a entrega ao `CreateProcess`
sem reformatação, que é o que resolve. Ver PYTHON.md seção 19.

Se o `.mp4` ainda não existir — a montagem roda em thread e leva alguns
segundos depois do fim do evento (8.3) —, `reveal()` abre a pasta do dia.

### 9.7 Calendário e grade de cartões

À direita, 250 px fixos, para alcançar dias anteriores:

- Setas `<` e `>` navegam meses. `shift_month()` faz a conta em meses absolutos
  para atravessar a virada de ano corretamente — testado: 01/2026 menos 1 dá
  12/2025, e 12/2026 mais 1 dá 01/2027.
- Semana começa no **domingo** (`calendar.Calendar(firstweekday=6)`), seguindo
  a convenção brasileira. `monthdayscalendar()` devolve as semanas já com zeros
  no lugar dos dias de fora do mês.
- **Dia selecionado:** preenchido em verde.
- **Hoje:** contorno azul.
- **Dias com gravação:** número em branco, negrito, com um ponto verde abaixo.
  Os demais ficam apagados.

`available_days()` conta **os arquivos `.json`**, não as pastas. Isso é
deliberado: clipes gravados antes do formato de metadados existir deixariam a
pasta do dia no disco, o calendário marcaria o dia como tendo gravação, e ao
clicar a tela apareceria vazia.

**Colar uma imagem dentro de outra é atribuição de slice**, não uma API de
blit:

```python
canvas[y:y + thumb_h, x:x + card_w] = self._thumbnail(entry, card_w, thumb_h)
```

O numpy exige que as formas coincidam exatamente, e é justamente por isso que
`_thumbnail` redimensiona para `(card_w, thumb_h)` antes de devolver. Lembre
que a indexação é `[linha, coluna]`, ou seja `y` antes de `x`.

**O grid sai de aritmética simples.** Primeiro, quantas colunas cabem com o
cartão na largura mínima; depois a largura real, dividindo o espaço pelas
colunas e descontando os vãos — para 5 colunas há 6 vãos (um em cada borda
mais os internos):

```python
columns = max((width - CARD_GAP) // (MIN_CARD_WIDTH + CARD_GAP), 1)
card_w = (width - CARD_GAP * (columns + 1)) // columns
thumb_h = int(card_w * 9 / 16)
```

Assim os cartões esticam para ocupar a largura toda, e uma coluna a mais
aparece quando a janela cresce o bastante.

A posição de cada cartão vem de `divmod`, que devolve quociente e resto numa
só chamada — o 8º cartão (índice 7) com 5 colunas cai em linha 1, coluna 2:

```python
row, column = divmod(index, columns)
x = x0 + CARD_GAP + column * (card_w + CARD_GAP)
y = top + row * (card_h + CARD_GAP)
```

A tela People usa a mesma grade, com cartões quadrados de largura fixa
(`FACE_CARD = 150`).

O número de linhas sai da altura disponível, então o grid se adapta se a janela
mudar de tamanho.

**Rolagem.** Uma noite movimentada produz mais gravações do que cabem — 19 num
único dia, contra 10 visíveis. A tela rola com a **roda do mouse**.

O OpenCV expõe o evento `EVENT_MOUSEWHEEL`, mas **não** expõe o
`getMouseWheelDelta` ao Python. O delta vem empacotado nos 16 bits altos de
`flags` e precisa ser desempacotado à mão, com correção de sinal:

```python
delta = flags >> 16
if delta > 32767:
    delta -= 65536
```

O estado é uma variável só, `self.scroll`, medida **em linhas** e não em pixels,
o que dispensa qualquer conta de posição parcial:

```python
total_rows = -(-len(self.entries) // columns)
self.max_scroll = max(0, total_rows - rows)
first = self.scroll * columns
```

`-(-a // b)` é divisão com arredondamento **para cima** usando só inteiros:
como `//` arredonda para baixo (PYTHON.md 22.1), negar duas vezes inverte o
sentido do arredondamento.

Os cartões também encolheram (`MIN_CARD_WIDTH` de 210 para 168), então mais
gravações cabem antes de precisar rolar.

A barra à direita **não é clicável**: indica apenas posição e proporção, e seu
tamanho reflete quanto do total está visível.

**A ordem de desenho importa:** os cartões são desenhados **antes** do
cabeçalho, porque é `_draw_cards` que calcula `max_scroll`, e o cabeçalho
precisa desse valor para decidir se mostra a dica "roda do mouse para rolar".

**Dois cuidados de desempenho**, porque isso é redesenhado várias vezes por
segundo (9.2):

- **Cache de miniaturas.** Decodificar JPEG a cada frame seria absurdo; as
  imagens já redimensionadas ficam num dicionário indexado por caminho **e
  tamanho** — o tamanho entra na chave porque redimensionar a janela muda
  `card_w` e invalidaria as imagens antigas.
- **Rescan periódico.** A pasta só é relida a cada `RESCAN_SECONDS = 2.0`, não
  a cada frame.

**As câmeras continuam sendo processadas enquanto a tela Records está aberta.**
Detecção e gravação não param por causa da navegação; só a imagem exibida muda.

### 9.8 Limitação: `cv2.putText` é só ASCII

As fontes Hershey do OpenCV não têm acentuação. Escrever `"gravação"` renderiza
caracteres quebrados, e por isso todo texto da interface está **sem acento** de
propósito ("gravacao", "Nenhuma gravacao neste dia").

Acentos exigiriam desenhar texto com o Pillow e converter para numpy, e eu
descartei isso por ser "dependência nova". **Foi viés** (CONTEXTO seção 11): o
Pillow é padrão da indústria e você nunca pediu aplicação pequena. O resultado
foi uma interface inteira escrita errado em português.

Não vale mais corrigir aqui, porque a interface web (backlog, item 3) resolve
de graça — o navegador desenha acento sem ninguém pedir. Fica registrado como
exemplo do custo: o viés não cobrou uma dependência, cobrou a grafia de tudo
que o usuário lê.

### 9.9 Fechar a janela no X

O HighGUI do OpenCV não tem evento de fechamento. Ao clicar no X a janela é
destruída, mas o `imshow` seguinte **cria outra**. Por isso perguntamos a cada
frame se ela ainda existe:

```python
if cv2.getWindowProperty(WINDOW, cv2.WND_PROP_VISIBLE) < 1:
    break
```

A verificação precisa vir **depois** de `cv2.waitKey(15)`, porque é o `waitKey`
que processa a fila de eventos da interface — inclusive o clique no X.

---

## 10. Camada de rostos — `faces.py`

### 10.1 Roda no clipe, não no ao vivo

Um rosto que tem 60 px no 1080p original fica com 30 px nos frames de análise de
960x540. O reconhecedor quer ~112 px. Reconhecer rosto nos frames de análise
simplesmente não funciona.

Por isso `scan_clip()` roda **no clipe já montado**, dentro da mesma thread que
faz a montagem (seção 8.3). Ganhos:

- Resolução original, a melhor disponível
- Fora do caminho crítico: não rouba CPU do ao vivo
- Só roda quando o evento teve `person` entre os rótulos

O custo é o rosto aparecer na tela People alguns segundos após o evento.

### 10.2 YuNet e SFace

São bons modelos para CPU, e o OpenCV já traz os dois embutidos — conveniência
real, não mérito de contagem de dependências:

| Papel | Modelo | Tamanho |
|---|---|---|
| Detectar rosto | `cv2.FaceDetectorYN` (YuNet) | 227 KB |
| Gerar embedding | `cv2.FaceRecognizerSF` (SFace) | 37 MB |

Os `.onnx` são baixados do repositório oficial `opencv/opencv_zoo` para
`models/`, que não é versionado. `alignCrop()` já devolve o recorte alinhado em
112x112 — exatamente o que o SFace espera — usando os 5 pontos faciais que o
YuNet retorna junto com a caixa.

O embedding tem **128 dimensões**. A comparação é por cosseno.

Medido com rostos nítidos:

| Comparação | Similaridade |
|---|---|
| Mesmo rosto | **1.000** |
| Rostos diferentes | **0.045** |

`MATCH_THRESHOLD = 0.363` é o valor recomendado pela documentação do OpenCV
para o SFace com cosseno.

### 10.3 Um rosto por pessoa por evento

Um clipe tem dezenas de frames da mesma pessoa. `_group()` junta as observações
pela própria similaridade dos embeddings (`SAME_FACE_THRESHOLD = 0.40`) e
guarda, de cada grupo, a **melhor** visão — a de maior `largura x score`, já que
rosto maior e mais confiante gera embedding melhor.

Se dois grupos do mesmo clipe casarem com a mesma pessoa da galeria, só o de
maior peso vira aparição (`seen_here`). E `list_sightings()` mostra um cartão
por pessoa por clipe, porque depois de uma junção (10.4) dois cartões antigos
podem passar a apontar para a mesma pessoa.

Resultado: um evento com uma pessoa gera uma aparição, não trinta.

### 10.4 O nome é uma referência, não um rótulo

O objetivo da tela People: **nomear uma pessoa uma vez e ela ser reconhecida
sozinha dali em diante.**

`faces/gallery.json` guarda as pessoas, cada uma com uma lista de embeddings
(as "visões" de referência). Cada aparição vira um par `.jpg` + `.json` em
`faces/<data>/` que aponta para a pessoa pelo `person_id`. O nome é resolvido
na hora de exibir, então nomear uma pessoa renomeia **todas** as aparições
dela, passadas e futuras.

**Como era, e por que não funcionava.** Medido no M900 em 15 minutos de uso:
**14 "pessoas"**, cada uma com **uma** visão, para 3 pessoas reais. Três causas:

1. Todo rosto que não casava com ninguém virava uma pessoa nova — inclusive
   perfis, nucas e um braço (10.9).
2. Dar o mesmo nome a dois cartões criava **duas** pessoas com o mesmo nome;
   cada uma continuava só com a sua visão.
3. A pessoa só aprendia visões novas com rostos de 80 px ou mais, e as
   câmeras entregam 40 a 60 px. Na prática ninguém aprendia nada.

**Como é hoje.**

| Momento | O que acontece |
|---|---|
| Rosto novo que não casa com ninguém | Vira desconhecido **só se apareceu em 2+ frames** do clipe (`MIN_VIEWS_FOR_NEW`), já com até 4 visões |
| Rosto que casa (≥ `MATCH_THRESHOLD` 0.363) | A aparição recebe aquela pessoa. Se a semelhança passa de `LEARN_THRESHOLD` (0.45), a visão é **aprendida** |
| Casa com um nomeado e um desconhecido | O **nomeado** vence: o nome é o que o usuário pediu para o sistema aprender |
| Usuário nomeia um cartão | `rename()` dá o nome e **absorve** todo desconhecido parecido (≥ 0.45) |
| Usuário dá um nome que já existe | As duas pessoas **viram uma**, somando as visões |

Absorver e juntar (`_merge`) move as visões para a pessoa nomeada e reescreve
o `person_id` das aparições antigas. Até `MAX_EMBEDDINGS = 40` visões por
pessoa.

Medido no mesmo conjunto de clipes, com o pipeline novo: **3 pessoas**. Nomear
um cartão da senhora absorveu a outra identidade dela e pôs o nome em 3
cartões; nomear um cartão do Gustavo nomeou também o da outra câmera.

`LEARN_THRESHOLD` é mais alto que o de casamento de propósito: o limiar de
0.363 do OpenCV vale para rostos de 112 px nítidos. Com rostos de 40 px, uma
semelhança de 0.37 pode ser acaso, e **aprender** com acaso contaminaria a
referência de todo mundo dali para frente. Exibir um nome errado é corrigível;
aprender errado se propaga.

**Duas instâncias da galeria.** A interface e a thread que varre clipes têm
cada uma o seu `Gallery`. Se uma salvasse a cópia que carregou antes, apagaria
o que a outra fez — um nome recém-dado sumiria. Toda escrita agora recarrega o
arquivo sob `_GALLERY_LOCK` antes de mudar.

**Limitação:** não há como desfazer uma junção pela tela. Um nome dado ao cartão
errado junta duas pessoas; hoje a saída é rodar `tools/refazer_rostos.py`, que
guarda o `faces/` atual de lado e reconstrói tudo a partir dos clipes — os nomes
precisam ser dados de novo, um cartão por pessoa.

### 10.5 A realidade do infravermelho noturno

Testado no clipe noturno real, onde o YOLO detecta a pessoa com 0,92:

| Medida | Valor |
|---|---|
| Rosto encontrado pelo YuNet | **44 px de largura** |
| Largura desejável para o SFace | ~112 px |

O rosto é detectado, mas um embedding tirado de 44 px é pouco confiável. A
solução foi não descartar e sim **marcar**:

```python
MIN_FACE_WIDTH = 36     # abaixo disso nem entra
GOOD_FACE_WIDTH = 80    # abaixo disso aparece com a largura em vermelho
```

Rostos pequenos aparecem na tela People com a largura em vermelho e podem ser
nomeados. Até setembro de 2026 eles **nunca** entravam nas referências, para não
contaminar a galeria. Na prática isso impedia qualquer aprendizado, porque de
dia as câmeras também entregam 40 a 60 px (10.4). Hoje o que protege a galeria
é o filtro de qualidade (10.9) e o `LEARN_THRESHOLD`, não a largura.

Expectativa honesta: identificação boa de dia e a curta distância; à noite o
sistema detecta que *há* um rosto, mas dizer de quem é será instável.

### 10.6 Dois bugs que o teste revelou

**Amostragem no lugar errado.** A primeira versão lia os primeiros frames do
clipe. Como existe pré-gravação (seção 8.2), o começo do clipe é justamente
**antes** da pessoa chegar — e o resultado era zero rostos num clipe que
claramente tinha uma pessoa. Agora o passo é calculado a partir do total de
frames, espalhando as amostras pelo clipe inteiro:

```python
step = max(total // MAX_SAMPLES, SAMPLE_EVERY)
```

**Piso alto demais.** `MIN_FACE_WIDTH` estava em 55 e descartava silenciosamente
o rosto de 44 px. O detector estava certo; o filtro é que estava errado.

### 10.7 Cadastro de nome sem widget

O HighGUI não tem campo de texto. O prompt é desenhado à mão e as teclas chegam
pelo `waitKey` do laço principal, que as encaminha para a interface enquanto
`interface.capturing` for verdadeiro:

```python
key = cv2.waitKey(15) & 0xFF
if interface.capturing:
    interface.on_key(key)
elif key == ord("q"):
    break
```

Repare que o `q` deixa de encerrar o programa durante a digitação — senão seria
impossível escrever um nome com a letra q. Enter salva, Esc cancela, Backspace
apaga, e só caracteres imprimíveis (32 a 126) entram no texto.

### 10.8 Animais: por que não dá com esta camada

O SFace é treinado exclusivamente em faces humanas. Um cachorro não tem rosto
detectável pelo YuNet, e mesmo que tivesse, o embedding não teria significado.

Identificar *qual* cachorro exigiria outra camada, de *animal re-ID*, sobre o
**corpo inteiro** e não sobre o rosto. Dois caminhos:

| Caminho | Precisão | Custo |
|---|---|---|
| Classificador treinado com fotos dos próprios cães | Boa para poucos cães conhecidos | ~50-100 recortes por cão |
| Embedding genérico de re-ID animal (MegaDescriptor) | Menor | Só baixar o modelo |

O padrão da tela People — cartões com recorte, nome dado uma vez, junção de
identidades — serviria igual para cães, trocando o recorte do rosto pelo do
corpo inteiro que o YOLO já entrega.

Ressalva: à noite, um cachorro escuro vira silhueta no infravermelho. A precisão
será sempre bem menor que a de rostos humanos.

### 10.9 Só rosto de frente, e só em cima de uma pessoa

Uma folha com as 19 aparições dos primeiros 15 minutos no M900 mostrou que
várias **nem eram rosto**: um braço (106 px, marcado como confiável), perfis,
nucas. Um embedding de perfil não descreve ninguém — e cada um virava uma
"pessoa" nova.

Foram medidos 72 rostos detectados nos 10 clipes gravados, com três números
tirados da própria detecção do YuNet, que devolve 5 pontos: olhos, ponta do
nariz e cantos da boca.

| Medida | Rosto de frente | Perfil, nuca, espelho do carro, mancha de sol |
|---|---|---|
| Confiança do YuNet | 0,81 a 0,92 | muitas vezes 0,6 a 0,7 |
| Nariz fora do centro dos olhos (÷ distância entre olhos) | até 0,3 | 0,5 a 2,3 |
| Distância entre olhos ÷ largura da caixa | 0,38 a 0,50 | 0,1 a 0,33 |

`is_frontal()` exige os três: confiança ≥ `IDENTITY_SCORE` (0,75), nariz a no
máximo `MAX_NOSE_OFFSET` (0,35) e olhos abertos pelo menos `MIN_EYE_SPREAD`
(0,38). Num perfil o nariz sai para o lado e os olhos quase se sobrepõem.

Sobraram quatro falsos na Front, pequenos (36 a 42 px), que passavam nos três
critérios — um deles era uma mancha de sol no chão. Por isso, nos frames em que
aparece um rosto de frente, `scan_clip()` roda também o YOLO
(`people.person_boxes()`) e só aceita o rosto se o centro dele estiver **na
metade de cima do corpo de uma pessoa**. O YOLO só roda nesses poucos frames,
então o custo é pequeno: cada clipe leva 9 a 17 s no M900, fora do caminho
crítico.

**Uma rede por thread, uma varredura por vez.** Na primeira versão
`person_boxes()` usava `load_model()`, a mesma rede do laço ao vivo. A
varredura roda na thread que monta o clipe (8.3), então as duas threads
chamavam `net.forward()` no mesmo objeto ao mesmo tempo. Um `cv2.dnn.Net`
guarda buffers internos entre chamadas e não pode fazer isso: o programa caiu
com `buf.shape() == m.shape()` no meio do ao vivo, logo depois de um evento.

Correção: `load_background_model()` carrega uma **segunda cópia** da rede
(~40 MB a mais de memória), usada só fora do laço principal. E `scan_clip()`
roda sob `_SCAN_LOCK`: cada evento monta o clipe na própria thread, e dois
eventos seguidos disputariam também o YuNet e o SFace, que são compartilhados.
As varreduras ficam em fila, o que também evita duas varreduras pesadas ao
mesmo tempo na CPU do M900.

Testado com o laço principal fazendo inferências enquanto 4 varreduras rodam
em paralelo: o código antigo reproduz o erro exato; o novo passa sem erros.

Em C# a situação seria a mesma de um objeto que não é *thread-safe*
compartilhado sem `lock`. Python tem o GIL, mas ele só protege o interpretador:
o OpenCV solta o GIL dentro do código C++, e duas chamadas rodam de verdade em
paralelo.

`MAX_SAMPLES` subiu de 30 para 60 frames por clipe: com o filtro, sobram menos
rostos por frame, e mais amostras dão mais chance de uma visão boa e de chegar
às 2 que um desconhecido exige.

### 10.10 A foto do cartão

A miniatura era o recorte alinhado de 112 px que o SFace usa, ampliado para 160.
Esse recorte serve para o reconhecedor, não para uma pessoa olhar: é cortado
rente (sem cabelo nem queixo) e, de um rosto de 45 px, já vem ampliado uma vez —
a ampliação para o cartão borrava pela segunda vez.

Hoje `context_crop()` recorta direto do frame original um quadrado de
`THUMB_CONTEXT` (2,2) vezes o tamanho do rosto, com cabelo e ombros, e grava a
300 px com interpolação cúbica. A tela reduz para 150 px com `INTER_AREA`, a
interpolação certa para diminuir. O embedding continua saindo do recorte
alinhado; só a foto mudou.

### 10.11 O clipe é lido pelo ffmpeg, não pelo OpenCV

`scan_clip()` lia o clipe com `cv2.VideoCapture`. O OpenCV traz um ffmpeg
próprio dentro dele, e esse decodificador imprime direto no terminal cada bloco
danificado que encontra (`[h264 @ ...] error while decoding MB 52 20`). Num dia
com o Wi-Fi da Back ruim, o terminal se encheu dessas linhas, que parecem erro
do programa mas são só o vídeo da câmera com defeito (INSTALACAO seção 8).

A variável `OPENCV_FFMPEG_LOGLEVEL`, que deveria silenciar isso, **não tem
efeito** no OpenCV 5.0 — testado. Então a leitura passou para o **nosso**
ffmpeg, o mesmo de `capture.py`, com `-loglevel quiet`:

```
ffmpeg -i clipe.mp4 -vf "select=not(mod(n\,STEP))" -fps_mode passthrough
       -frames:v 60 -pix_fmt bgr24 -f rawvideo pipe:1
```

O filtro `select` deixa passar só um a cada `STEP` frames (`n` é o número do
frame, `mod` o resto da divisão). O `-fps_mode passthrough` impede o ffmpeg de
duplicar frames para "preencher" os que foram descartados. A barra em `\,`
existe porque a vírgula separa filtros na linguagem do `-vf`.

Ganho de bônus: o `VideoCapture` decodificava e entregava **todos** os frames
para o Python descartar a maioria; o ffmpeg descarta antes do pipe. Medido no
clipe de 577 frames: **3,3 s → 1,6 s**, com os mesmos 60 frames (diferença
média de 2 em 255 por pixel, da conversão de cor feita por outra biblioteca). A
varredura dos clipes de 29/09 deu as mesmas 3 pessoas com as mesmas
similaridades.

Tamanho e número de frames vêm de `_describe()`, que roda `ffmpeg -i clipe` sem
saída: ele imprime o cabeçalho do vídeo e para, sem decodificar nada. Abrir com
`VideoCapture` só para perguntar o tamanho já decodificava o começo e imprimia
o dano dali.

O aviso `setPreferableTarget ... not supported by the new graph engine`, que o
OpenCV imprime ao carregar o detector de rosto, é silenciado por
`OPENCV_LOG_LEVEL=ERROR` em `jarvis/__init__.py`. Esse arquivo roda antes de
qualquer `import cv2` do programa, que é quando o OpenCV lê a variável.

---

## 11. Armazenamento em camadas — `archive.py`

### 11.1 Três camadas, deleção por último

```
clips/ (disco do programa)  --30 dias-->  HD externo  --só se lotar-->  apaga o mais antigo
```

**Nada é apagado de `clips/`.** O que foi gravado sai de lá apenas movido para o
arquivo morto. A exclusão existe só no HD externo, do evento mais antigo, e
somente quando o espaço livre cai abaixo do limite.

A alternativa descartada era apagar por idade direto da gravação. Com ~300 MB/dia
o disco encheria, mas apagar material recente para resolver isso troca um
problema por outro pior.

### 11.2 Copiar, conferir, então apagar

Mover entre discos não é atômico. `_move_event()` copia todos os arquivos do
evento, **confere o tamanho de cada um**, e só então remove os originais.

Uma cópia interrompida — HD desconectado no meio — deixa o original intacto e
apaga o que já tinha ido. Melhor sobrar duplicado que faltar.

Testado simulando falha na segunda cópia de um evento: o original permanece.

### 11.3 HD desconectado

É o caso normal, não a exceção: um HD externo passa a maior parte do tempo fora.
`destination_state()` responde se dá para escrever agora, e todas as operações
param na hora se não der, sem apagar nada e explicando o motivo na tela.

### 11.4 Configuração na interface

A aba **Ajustes** mostra as três camadas com números reais — quantos eventos,
quanto ocupam, quanto sobra em cada disco — e os botões para escolher a pasta,
arquivar na hora e remover a configuração.

O seletor de pasta é o nativo do Windows, via `tkinter`, que vem na biblioteca
padrão. O HighGUI não tem diálogo de arquivo, e digitar caminho à mão seria
ruim justamente para um HD externo, cuja letra muda.

As escolhas ficam em `config.json` na raiz, **não** no `.env`. A separação é
proposital: o `.env` guarda credenciais escritas uma vez à mão, enquanto isto
muda em tempo de execução pela interface. O `config.json` não é versionado.

| Chave | Padrão | O que faz |
|---|---|---|
| `archive_path` | vazio | Pasta do HD externo; vazio desliga o arquivamento |
| `archive_after_days` | 30 | Idade para mover |
| `archive_min_free_gb` | 10 | Abaixo disso, apaga o mais antigo do HD |

### 11.5 Quando roda

`Housekeeper.tick()` é chamado no laço principal e só age a cada
`CHECK_SECONDS = 1800`. Eventos com menos de `PROTECT_MINUTES = 10` nunca são
tocados, porque a montagem do clipe acontece numa thread e pode ainda estar em
andamento.

---

## 12. Notificação — `notify.py`

### 12.1 Por que Telegram

Sem aviso, o sistema responde *"quem esteve aqui?"* e nunca *"tem alguém aí
agora"* — é um gravador, não uma vigilância.

| | Telegram | E-mail | Toast do Windows |
|---|---|---|---|
| Chega no celular | push imediato | caixa de entrada | não |
| Manda a miniatura | sim | anexo | não |
| Dependência nova | nenhuma | SMTP + senha de app | — |
| Expõe a máquina | não | não | — |

A API é HTTP comum e o envio usa `requests`. A primeira versão usava `urllib`
da biblioteca padrão e montava o `multipart/form-data` da foto à mão, em vinte
linhas, para não trazer dependência nova. Foi um erro — veja a seção 12.5 e a
seção 11 do `CONTEXTO.md`.

### 12.2 Avisa no começo do evento, não no fim

O aviso dispara em `_start()`, no primeiro frame com sujeito detectado — não
quando o clipe fecha. A diferença importa: fechar o evento espera a pessoa sair
mais `POST_SECONDS`, e depois a montagem leva mais alguns segundos. Avisando no
começo, a mensagem chega enquanto a pessoa ainda está lá.

O custo é não ter o nome do rosto, que só sai da varredura pós-evento. Para
"tem alguém aí", saber na hora vale mais que saber quem. O "quem" chega depois,
numa segunda mensagem (12.7).

### 12.3 Silêncio é obrigatório

Duas travas impedem a enxurrada que tornaria o recurso insuportável:

- **Filtro por rótulo.** `notify_labels` vem com `["person"]`. Animal não avisa,
  senão cada gato de madrugada viraria uma mensagem.
- **Intervalo mínimo por câmera.** `notify_cooldown = 120` segundos, contado
  **por câmera**: alguém circulando na frente não gera vinte avisos, mas um
  evento na Back durante o silêncio da Front ainda passa.

### 12.4 Nunca trava a captura

O envio roda numa thread. Uma rede lenta ou o Telegram fora do ar não podem
segurar o laço de captura, e toda falha volta como `(False, motivo)` em vez de
exceção.

### 12.5 A raiz de certificado que faltava

Na primeira tentativa de validar o token, isto:

```
[SSL: CERTIFICATE_VERIFY_FAILED] self-signed certificate in certificate chain
```

Parecia antivírus interceptando HTTPS. **Não era.** O `github.com` e o
`google.com` verificavam normalmente — só o Telegram falhava.

A cadeia que o `api.telegram.org` apresenta termina em **"Go Daddy Root
Certificate Authority - G2"**, e o repositório desta máquina tinha apenas
raízes **Starfield**. A raiz Go Daddy G2 não estava instalada.

O navegador funciona porque o **Windows baixa raízes faltantes sob demanda**,
pela própria CryptoAPI. O Python não aciona esse mecanismo: o
`ssl.enum_certificates` só enxerga o que já está em cache local. Carregar o
repositório inteiro do Windows levou de 39 para 52 CAs e continuou falhando,
porque a raiz simplesmente não estava lá para ser carregada.

A correção é o `certifi`, o conjunto de raízes da Mozilla — 121 certificados,
incluindo a Go Daddy G2. É um arquivo de dados, não código, e garante o mesmo
comportamento nas duas máquinas em vez de depender do que cada Windows resolveu
baixar.

**Duas lições, e a segunda é mais importante que a primeira.**

A primeira: erro de SSL não significa necessariamente interceptação. Vale
testar outro site antes de culpar antivírus.

A segunda: **este problema nunca deveria ter chegado a existir.** O `requests`
já depende do `certifi` e o usa por padrão — `requests.utils.DEFAULT_CA_BUNDLE_PATH`
aponta para `certifi.where()`. O bug só apareceu porque a primeira versão
evitava o `requests` para manter a contagem de dependências baixa, e essa
contagem nunca foi uma decisão do usuário. O custo real daquela economia não
foram as vinte linhas de `multipart` — foi uma sessão inteira de depuração de
TLS para reinstalar, à mão, uma garantia que a biblioteca dá de graça. O envio
hoje usa `requests` e não importa `certifi` diretamente.

### 12.6 Configuração


O token tem ~46 caracteres e o HighGUI não tem como colar. Por isso a aba
Ajustes abre o `config.json` no editor em vez de pedir digitação:

1. **Abrir config.json** — cole o token do `@BotFather` em `notify_token`
2. Mande qualquer mensagem para o bot no Telegram
3. **Descobrir conversa** — lê o `chat_id` da última mensagem e grava sozinho
4. **Enviar teste** — confirma que chega no celular

O `config.json` não é versionado, e o token é uma credencial: quem o tiver pode
mandar mensagens pelo seu bot.

### 12.7 Segunda mensagem: o rosto e o nome

Pedido do usuário em 09/10/2026: além da miniatura do evento, a foto do rosto
isolado e, se a pessoa for conhecida, o nome na mensagem.

O rosto só existe depois do evento — o clipe precisa fechar, ser montado e
varrido (10.1), uns 20 a 40 s depois de a pessoa aparecer. Por isso não dá para
pôr na primeira mensagem sem atrasá-la, e 12.2 continua valendo. Fica assim:

| Mensagem | Quando | Foto | Texto |
|---|---|---|---|
| 1ª | no primeiro frame com pessoa | miniatura do evento, com a caixa | `Back: person` e a hora |
| 2ª | depois da varredura de rostos | recorte do rosto (10.10) | `Back 15:20:54: Gustavo Henrique Gomes reconhecido` ou `rosto desconhecido` |

Uma foto por pessoa encontrada no clipe, no máximo `MAX_FACES = 3`.

**O caminho.** `EventRecorder._start()` guarda o que `notify.event()` devolveu
em `self.notified`, e esse valor viaja junto para a thread de montagem:

```python
found = faces.scan_clip(destination, camera.label, start)
...
if notified and found:
    notify.faces_seen(camera.label, start, found)
```

`scan_clip()` passou a devolver, além do que grava no JSON da aparição, o
caminho da foto (`thumbnail_path`) e o nome atual da pessoa (`name`, vazio se
ninguém deu nome). O nome vem da galeria na hora, então quem foi nomeado
ontem aparece com nome hoje.

**A segunda segue a primeira.** Só sai se a primeira saiu. Quando o intervalo de
120 s por câmera (12.3) segurou o aviso do evento, segura também o do rosto —
senão alguém andando pelo quintal geraria uma foto de rosto a cada evento,
justamente a enxurrada que 12.3 existe para evitar.

**Não trava nada.** `faces_seen()` roda na thread de montagem do clipe, que já
é de fundo e já espera a varredura; o laço de captura nunca vê a rede.

Testado em 09/10/2026 com dois clipes de 29/09 e uma cópia da galeria: as duas
mensagens chegaram, uma com "Gustavo Henrique Gomes reconhecido" e outra com
"Izabel reconhecido", cada uma com o recorte do rosto.

### 12.8 A person who arrives after an animal, and other changes (09/10/2026)

**The bug (review 1, R1).** The notification was attempted only on an event's
first frame, with that frame's labels. An event that began with a dog was not
announced — only `person` notifies — and nothing tried again, so a person
arriving seconds later passed in silence, and never got the face message of
12.7 either, which depends on the first message having gone out. On 30/09, 29
of the 85 events with a person also had an animal.

**The fix.** `EventRecorder.update()` calls `_notify_late()` on every frame of
an open event. While the event has not been announced, each label not yet
tried gets **one** attempt — so `config.json` is not read every frame:

```python
new = {s.label for s in subjects} - self.notify_tried
```

The photo is of that moment, not the event thumbnail (which shows the dog),
saved as `HH-MM-SS.alert.jpg`; if nothing was sent, it is deleted. The name
matters: see 19.2.

**Wording (R5).** The face message says `X recognized` only when the match is
at least `LEARN_THRESHOLD` (0.45) — the bar the gallery already trusts to learn
from (10.4). Between `MATCH_THRESHOLD` (0.363) and 0.45 it says `probably X`;
no name, `unknown face`. Messages are in English since 09/10/2026 (CLAUDE.md).

**`notify_prefix`** in `config.json`, empty by default, is put in front of every
message. The test copy uses `[TEST]` (18.7).

### 12.9 The picture, the face that passes fast, and a trace of every message (10/10/2026)

Developer session 1 answered what the first night of production showed
(CONTEXTO 13.6): the user went out and came back, was recorded, and still
believed they were not, because the event's picture was the dog and no face
message came.

**The event's picture is its best view of a person (R19).** While an event is
open, `EventRecorder._consider_view()` keeps a copy of the frame where a person
scores best, `confidence × box height` — height so that a person standing beats
a dog lying down even when the detector calls the dog a person. At the end it
is written as `HH-MM-SS.best.jpg`, and the event JSON gains the optional
`best_thumbnail`. The page shows it when present; older events, and events with
no person, keep showing the first frame, which is also kept on disk because it
shows what triggered the event. `frame.copy()` matters: a numpy array is a
reference to a buffer the capture keeps reusing.

**The phone ends with a picture of the person.** The first message still goes
at the start with the first frame — speed beats beauty there. After the clip
is scanned, a notified event gets either the face messages (12.7) or, when no
face was found, one more message with the best view — unless the best view is
the very frame already sent.

**Faces that are frontal for a fraction of a second (R20).** On the 22:29 clip
only 4 or 5 of ~840 frames held a face that was both frontal and at least
36 px wide, and one frame in fourteen missed them all. The recorder now notes
the wall-clock spans when a person was seen (a gap over
`PERSON_GAP_SECONDS` = 2 opens a new span); `_assemble` turns them into
seconds into the clip, counted from the first segment's name, which is the PC
clock at the moment ffmpeg opened it — the same clock the spans use. The scan
then reads every `DENSE_EVERY` = 2nd frame inside those spans widened by
`DENSE_MARGIN_SECONDS` = 1.5, plus the old sparse pass elsewhere, at most
`MAX_DENSE_SAMPLES` = 300 extra frames. All of it is one ffmpeg `select`
expression — `n` is the frame number, `t` its time, `+` is a logical or:

```
not(mod(n\,14))+(between(t\,34.50\,45.50))*not(mod(n\,2))
```

Measured on the M900 on that clip: sparse, 60 frames, 12 s, no face; dense,
300 frames, **45 s**, the user found as "probably" (41 px, 0.421). YuNet costs
~143 ms per 1080p frame there. `tools/refazer_rostos.py` does not know the
spans, so a rescan stays sparse. **Open:** what 45 s of multi-threaded DNN
does to live analysis on 4 cores (R21).

**Every message leaves a line in the log (R16).** `Notification <camera>
<labels>: sent` and `skipped: cooldown` at INFO, `failed: <detail>` at
WARNING, so a check for warnings finds a failed send. `_allowed()` became
`_wanted()` and `_cooled_down()` to tell the two skips apart; a label nobody
asked for stays silent. **The token never reaches text:** a `requests`
exception quotes the URL, and the URL holds the token (`/bot<token>/…`).
`_redact()` removes it inside `_call()` and `discover_chat()`, the only places
the token can enter a string, so no caller has to remember.

### 12.10 Watching the watcher (10/10/2026)

Developer session 2 added the instruments that 12.9 lacked.

**Frames analysed per minute (R21).** The `Core` counts analysed frames per
camera; every 60 s `_tally()` turns them into `analysed_per_minute`, served by
`/api/status`, and logs the numbers when a face scan ran in that minute
(`faces.scanning()` asks `_SCAN_LOCK.locked()` — whether a lock is held,
without taking it). Measured on the M900: a quiet scene barely notices a dense
scan (584 → 575–583 frames a minute), but **YOLO runs 1.6× slower during one**
(280 → 454 ms), because every `cv2.dnn` network in the process shares one pool
of worker threads. Giving the scan fewer threads does not help:
`cv2.setNumThreads` is process-wide and slowed YOLO itself (472 ms at 2
threads, 772 ms at 1). The decision is in CONTEXTO 13.8 (R23).

**Where each scan looked (R22).** One INFO line per scan:
`face scan 22-29-22.mp4: dense 7.3-15.7 s, 36.3-42.1 s, 162 frames, 23.1 s, 3 face view(s)`.

**`tools/replay.py` (R17).** Plays any video through the real
`MotionDetector` and `SubjectDetector` and prints why each candidate was kept
or dropped. Both classes gained an optional `trace` list, `None` by default —
when nobody set it, nothing is recorded and nothing changes (the Python version
of an optional listener in Java); the old and new code gave identical results
on all 561 frames of the 22:29 clip. `SubjectDetector.detect()` gained an
optional `now`, so `MIN_INTERVAL` and the static spots follow the video's
clock instead of the wall clock. The reasons are the clearest list of what each
layer filters: too small, few changed pixels, lighting change, not confirmed
(n/3), whole frame changed, warming up; animal below confidence, person too
short, no motion overlap, duplicate, static spot. `--prime` teaches MOG2 the
background from the first 6 s first, because a fresh MOG2 is blind for 6 s —
exactly where an event's pre-roll ends. The primed background already holds
whatever was in the scene, which production's long-learned one would not:
good enough to reproduce an event, not identical to production.

**The running version (backlog 18).** `web._read_version()` runs
`git describe --tags --always --dirty` once at startup: production shows its
tag (`v2026.10.10`), the test copy something like `v2026.10.10-12-g1b8822d`,
"12 commits after that tag" — which also tells the two pages apart. Served as
`version` in `/api/status` and shown muted at the right of the header;
`unknown` if git cannot answer, never an error.
**The scan steps aside during events (R23, 10/10/2026).** Before each frame,
`_scan_clip()` calls `_wait_while(busy, budget)`: while `busy()` is true it
sleeps in 0.2 s steps, at most `MAX_PAUSE_SECONDS` = 600 per scan, and the
ffmpeg feeding the pipe simply blocks. `busy` is a function passed in —
Java's `BooleanSupplier`, C#'s `Func<bool>` — so `faces` knows nothing of
cameras: `clips.recording_now()` asks every `EventRecorder`, kept in a
`weakref.WeakSet` (a set that does not keep its members alive, like the keys of
Java's `WeakHashMap`). Measured: YOLO 328 ms alone, ~590 ms during a dense
scan, **342 ms while the scan is paused**. A paused scan still holds
`_SCAN_LOCK`, so on a long busy evening the face messages arrive late; the
first message of each event never waits.

**The dog on the mat (R18).** `SubjectDetector.detect()` drops a `person`
whose box is more than `WIDE_PERSON_RATIO` = 2.0× wider than tall **and**
whose bottom lies within `BOTTOM_EDGE_FRACTION` = 3 % of the frame's bottom
(`people.wide_at_bottom()`, trace reason "wide at the bottom edge"). Both
conditions: a wide box mid-frame could be a person lying down, and a standing
person whose feet touch the edge is always tall. The architect had specified
2.5; the replay of all 25 person events showed the dog **sitting up** on the
mat at 2.42–2.48, so 2.0 — real persons measure 0.4–0.6, still a fourfold
margin. Every box the rule drops in those events is the mat.

**A found face is always announced (R25, 10/10/2026).** The face message used to go out only after the event's own first message, so a face found in an event that fell in the 120 s cooldown was never sent — and faces are rare (2 of 21 scans that afternoon). Now `faces_seen` runs whenever the scan found a face; `_cooled_down(key, settings)` takes any key, the camera for events and `("face", person_id)` for faces, in the same table, so the same person is not announced twice within `notify_cooldown`. The best-view follow-up keeps its rule: only after a sent event.

---

## 13. Restrição importante das câmeras Tapo

**A câmera suporta apenas duas destas três funções ao mesmo tempo:**

1. Tapo Care (nuvem)
2. Gravação em cartão SD
3. NVR / NAS / ONVIF / **RTSP**

Com Tapo Care + SD ativos, o RTSP é desativado silenciosamente. O sintoma é
peculiar: `DESCRIBE` responde `200 OK` normalmente (é só metadado), mas o
`SETUP` fecha a conexão sem sequer pedir autenticação.

**Desativar a gravação no app não basta — o cartão precisa ser removido
fisicamente.** Alternativa: desligar o Tapo Care.

`probe_rtsp.py` diagnostica isso mostrando cada etapa do handshake:

```
uv run tools/probe_rtsp.py <ip> <usuario> <senha> stream1
```

---

## 14. Ícone e atalho

**Um `.bat` não tem ícone próprio.** O Windows desenha o ícone de um arquivo
pelo tipo dele, e todo `.bat` usa o mesmo. Quem pode ter ícone é um **atalho**
(`.lnk`), que aponta para o `.bat` e guarda o caminho de um `.ico`.
`tools/criar_atalho.ps1` cria esse atalho na Área de Trabalho pelo objeto COM
`WScript.Shell` — o mesmo que o Windows usa em "Criar atalho". O
`instalar.bat` roda o script no passo 5.

**O ícone é código.** `tools/gerar_icone.py` desenha um olho robótico com
NumPy, sem nenhum programa de desenho:

| Camada | Como |
|---|---|
| Carcaça de aço | Círculo com brilho variando pelo ângulo (`cos`), simulando luz vinda do alto à esquerda |
| Anel segmentado e parafusos | 12 setores alternados pelo ângulo; 12 círculos pequenos |
| Íris | Gradiente radial do ciano quase branco no centro ao azul na borda, com 36 raios e dois anéis finos |
| Pupila | Obturador de 6 lâminas: o raio cresce dentro de cada setor, o que dá o contorno em hélice |
| Reflexo | Um círculo branco fora do centro |

Cada camada é uma **máscara** de 0 a 1 por pixel, calculada de uma vez sobre a
imagem inteira a partir de dois mapas: a distância de cada pixel ao centro e o
ângulo dele. `edge()` transforma "dentro do círculo de raio R" nessa máscara,
com 2 px de transição para a borda não serrilhar. Em Java seria um laço duplo
sobre x e y; aqui cada linha opera sobre o milhão de pixels de uma vez.

O desenho é feito a 1024 px e reduzido com `INTER_AREA` para os 7 tamanhos que
o Windows usa (16 a 256). O `.ico` é escrito à mão: um cabeçalho de 6 bytes,
uma entrada de 16 bytes por tamanho, e cada imagem como PNG — o formato que o
Windows aceita desde o Vista. O OpenCV lê e grava PNG mas não `.ico`, e o
`struct.pack` resolve em ~20 linhas.

Aqui o Pillow faria em duas linhas. Mantido à mão porque é ferramenta de uso
único, roda fora do caminho crítico e já está testada — não porque economiza
dependência. Se o Pillow entrar por outro motivo, troque.

Para mudar o desenho, edite as cores e raios em `gerar_icone.py`, rode
`uv run tools/gerar_icone.py` e depois o `criar_atalho.ps1` de novo (o Windows
guarda ícones em cache; se o antigo continuar aparecendo, reinicie o Explorer).

---

## 15. Núcleo e interface — vigilância sem janela

### 15.1 O problema: a gravação era passageira da janela

Até 09/10/2026 o `main()` era um laço só, e quem ditava o ritmo dele era a
janela:

```python
key = cv2.waitKey(15) & 0xFF
...
if cv2.getWindowProperty(WINDOW, cv2.WND_PROP_VISIBLE) < 1:
    break
```

O `cv2.waitKey` não é só "ler tecla" — é a função que bombeia a fila de eventos
do HighGUI, e era ela que dava o compasso de todo o resto. Detecção, gravação,
rostos e notificação rodavam **dentro** desse laço. Fechar a janela encerrava a
vigilância.

Para um visor de câmeras isso estava certo. Para um sistema de segurança, não:
ninguém fica com a janela aberta 24 h por dia, e é justamente quando não há
ninguém olhando que gravar importa mais.

### 15.2 A separação

`cameras.py` passou a ter três peças, e a dependência só aponta para um lado:

| Peça | O que é | Sabe da janela? |
|---|---|---|
| `Core` | captura, movimento, sujeitos, gravação, arquivo | **não** |
| `run_window` | desenha, lê teclado e mouse | sim |
| `run_headless` | só chama `Core.step()` num laço | não |

O `Core.step()` é uma passada por todas as câmeras e devolve `True` se algum
frame era novo. Quem chama decide o que fazer com isso:

```python
def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    headless = HEADLESS_FLAG in argv
    core = Core(start_cameras(), draw=not headless)
    try:
        (run_headless if headless else run_window)(core)
    finally:
        core.close()
```

O `finally` é o que garante que clipe pendente seja montado e stream fechado,
seja qual for o motivo da saída — tecla `q`, janela fechada, `Ctrl+C` ou
exceção.

**Detalhe de Python:** `(run_headless if headless else run_window)(core)`
escolhe a função e chama. Funções são valores, como em C# com delegate, mas sem
precisar declarar o tipo. O parêntese em volta é obrigatório: sem ele o `if`
ternário engoliria a chamada.

### 15.3 O ritmo, sem waitKey

Sem janela não existe `waitKey`, então o laço precisa de ritmo próprio:

```python
while True:
    if not core.step():
        time.sleep(IDLE_SLEEP)
```

Dorme **só quando não veio frame novo**. Se veio, processa a próxima passada na
hora. Isso é melhor que o laço antigo, que pagava os 15 ms do `waitKey` em toda
iteração, tendo frame ou não. Medido: 2.995 passadas em 15 s, 300 com frame
novo — ou seja, 10 fps por câmera, e o resto do tempo dormindo em vez de girar
em falso.

### 15.4 O `draw` e o que ele economiza

O `Core` só monta painel se `draw=True`:

```python
self.panels = {cam.label: make_panel(None, cam.label, PANEL_HEIGHT)
               for cam in streams} if draw else {}
```

Medido nesta máquina: `make_panel` custa **0,43 ms por câmera** e o mosaico
(`np.hstack`) **0,41 ms**, somando **1,27 ms** com duas câmeras, de uns 20 ms
por frame. São ~6%. Vale economizar, mas **não é o motivo da mudança** — o
motivo é a seção 15.1.

### 15.5 Como rodar

| Quero | Comando |
|---|---|
| Usar o J.A.R.V.I.S. | `jarvis.bat` ou o atalho: serviço + navegador (17.7) |
| Só o serviço, sem abrir nada | `jarvis_vigilancia.bat` (`--headless`) |
| Parar de qualquer terminal | `uv run python -m jarvis --stop` |
| A janela antiga, provisória | `uv run python -m jarvis --window` |
| Ver pelo navegador ou celular | `http://127.0.0.1:8765`, ou o endereço de rede que ele imprime |

Sem janela, o encerramento é `Ctrl+C` ou `--stop`. No Windows, `Ctrl+C` no
terminal vira `KeyboardInterrupt` no Python, que o `run_headless` captura; o
`--stop` pede pela web e o laço sai pelo mesmo caminho. Nos dois casos o
`finally` do `main()` fecha tudo em ordem. Production, since 09/10/2026, runs
as a scheduled task with no console: 18.7.

**Ainda não é serviço de verdade.** Rodar no boot sem ninguém logado é outro
assunto (Agendador de Tarefas ou NSSM), e depende da interface web do item 3 do
backlog, porque hoje não há como olhar um núcleo sem janela.

---

## 16. Estado atual

**Funcionando no M900 desde 29/09/2026:**

| Camada | Seção |
|---|---|
| Captura pelo ffmpeg, gravação sem recodificar, timeout de conexão | 5 |
| Movimento com filtro de luz, máscara do relógio e confirmação temporal | 6 |
| Pessoas e animais pelo YOLO, cenário estático, altura mínima | 7 |
| Eventos com pré-gravação, miniatura e metadados | 8 |
| Interface Live, Records e People, com calendário e rolagem | 9 |
| Rostos: só de frente e sobre uma pessoa, nome que vira referência | 10 |
| Armazenamento em camadas, HD externo após 30 dias | 11 |
| Aviso no celular pelo Telegram, inclusive pessoa que chega depois de um animal | 12 |
| Ícone e atalho na Área de Trabalho | 14 |
| Vigilância sem janela (`--headless`), parada limpa (`--stop`) | 15 |
| Interface web: ao vivo e lista de eventos, no navegador e na rede local | 17.6–17.8 |
| Production in `C:\JARVIS` as a startup task, reviewed releases, update with rollback | 18.7 |
| Every file ever written stays readable; `check_data.py` proves it | 19 |

Limitações aceitas, próximos passos em ordem de prioridade e o histórico de
bugs ficam num lugar só: [CONTEXTO.md](CONTEXTO.md), seções 4, 7 e 8.

## 17. Interface web — plano de execução

Decidido em 09/10/2026. Item 3 do backlog. Esta seção é o plano, para que a
obra possa ser retomada por outra sessão ou pela outra máquina sem perder as
decisões. **Estágios 1 e 3 feitos em 09/10/2026** (17.6, 17.7); 4 e 2 ainda não.

**Mudança de rumo do usuário, no mesmo dia:** *"não quero ter duas formas de
acesso; se possível tudo web, com um serviço rodando."* O plano original
mantinha a janela do OpenCV ao lado da web para comparar; agora a web é o único
acesso, e a janela sai assim que a web cobrir o que só ela faz. A ordem passou
a ser 1 → 3 → 4 → remover a janela e subir com o Windows → 2.

### 17.1 Por que, em uma frase

A vigilância já roda sem janela (seção 15), mas não há como **olhar** um núcleo
sem janela. A web fecha esse ciclo e, de passagem, entrega acento, reprodução de
vídeo, rolagem, colar texto e acesso pelo celular — tudo que o HighGUI não tem.

### 17.2 A stack, e por que não a biblioteca padrão

**FastAPI + uvicorn.** Dois requisitos decidem, e nenhum é estético:

| Requisito | Por que o `http.server` não serve |
|---|---|
| Vídeo ao vivo (MJPEG) | É uma resposta que nunca termina. O `http.server` é de uma thread; um espectador travaria todo o resto |
| Arrastar a barra do vídeo | O `<video>` exige HTTP Range. O `FileResponse` já faz; à mão é fácil de errar |

A primeira ideia desta sessão foi `http.server` "sem dependência nova" — era o
viés da seção 11 voltando pela porta dos fundos, e foi descartada.

**Risco verificado:** o FastAPI traz `pydantic`, cujo núcleo é Rust compilado —
a mesma categoria de binário que o Smart App Control bloqueou no PyTorch (7.11).
Testado em 09/10/2026 na máquina de desenvolvimento: `import pydantic_core`
carrega sem erro. **Confirmado no M900 também, em 09/10/2026** (`pydantic_core`
2.50.0) — que é onde o Smart App Control mais incomodou. Antes disso foi
preciso trocar o próprio Python por um assinado (INSTALACAO 1.2). O teste:

```bat
uv run python -c "import pydantic_core, fastapi, uvicorn; print('ok')"
```

Se falhar lá, o plano muda: Flask com servidor WSGI com threads, que é Python
puro, em vez de abandonar a web.

### 17.3 Os quatro estágios

Cada um termina em commit que funciona sozinho. **A janela do OpenCV continua
intacta do começo ao fim** — a comparação é o critério de aceite, e só se
descarta o HighGUI depois de a web provar que é melhor.

**Estágio 1 — servidor e lista de eventos.** `web.py` novo, subindo o uvicorn
numa thread ao lado do `Core`. Serve uma página que lista os eventos lendo os
JSON que já existem em `clips/`. Não toca em nada que funciona hoje. Aceite:
abrir no navegador e ver os eventos de hoje, com acento.

**Estágio 2 — reprodução.** `FileResponse` nos `.mp4`, `<video>` na página.
Fecha o item 5 do backlog (hoje clicar abre o Explorer) e o 6 fica barato,
porque filtrar é JavaScript sobre a lista. Aceite: assistir um evento e arrastar
a barra, sem abrir player externo.

**Estágio 3 — ao vivo.** `StreamingResponse` com MJPEG a partir dos frames que o
`Core` já tem em memória. Aceite: duas câmeras ao vivo no navegador, e no
celular pela rede local.

**Estágio 4 — People e Ajustes.** As telas que mais sofrem com o HighGUI: é
onde não se consegue colar o token de 46 caracteres nem escrever um nome com
acento. Aceite: cadastrar nome e colar o token pelo navegador.

### 17.4 Decisões já tomadas, para não reabrir

- **Só rede local.** Sem porta aberta para a internet, sem login. A notificação
  do Telegram é que atravessa a rede, e já funciona. Autenticação só entra se o
  acesso de fora algum dia entrar, e aí é decisão nova.
- **A web lê o que já existe.** Os JSON em `clips/` continuam sendo a fonte. O
  banco de eventos (item 13) é independente e vem depois, se vier.
- **O `Core` não sabe da web.** Do mesmo jeito que não sabe que existe janela:
  quem serve é que lê o `Core`. O estágio 3 acrescentou a ele dois acessos só
  de leitura, `labels` e `live_view()` (17.7) — o `Core` não importa `web` nem
  muda de comportamento por existir alguém olhando.
- **Sem framework de frontend.** HTML e JavaScript simples servem para listar,
  filtrar e tocar vídeo. React aqui seria o oposto do reaproveitamento útil:
  peso sem problema que justifique.

### 17.5 O que isso fecha no backlog

Itens 5 (reprodução), 6 (busca e filtro), 11 (linha do tempo) e o acesso remoto
saem quase de graça, porque o navegador já faz o trabalho pesado de cada um.

### 17.6 Estágio 1, como ficou

**Aceite cumprido no M900:** `http://127.0.0.1:8765` mostrou os 139 eventos de
30/09 (Front 44, Back 95), com miniatura, hora, câmera, duração e rótulo em
português com acento.

**Onde roda.** `main()` em `cameras.py` chama `web.start()` logo depois de criar
o `Core`, com janela ou sem. O servidor sobe numa thread *daemon*:

```python
server = uvicorn.Server(uvicorn.Config(app, host=host, port=port,
                                      log_level="warning", access_log=False))
threading.Thread(target=server.run, name="web", daemon=True).start()
```

O uvicorn só instala os tratadores de `Ctrl+C` quando roda na thread principal,
então numa thread de fundo ele não rouba o `Ctrl+C` do `run_headless`. Ao sair,
o `finally` do `main()` chama `web.stop()`, que só liga `should_exit` — o
uvicorn termina sozinho na volta seguinte do laço dele. Por ser *daemon*, a
thread também não segura o processo se algo der errado.

**O que serve.**

| Rota | Devolve |
|---|---|
| `/` | `static/index.html` |
| `/static/...` | CSS e JavaScript da página (`StaticFiles`) |
| `/icone.png` | o `assets/jarvis.png`, sem duplicar o arquivo |
| `/api/dias` | dias com gravação, do mais novo ao mais velho |
| `/api/eventos?dia=AAAA-MM-DD` | os eventos do dia, lidos de `clips.list_clips()`; sem `dia`, hoje |
| `/miniatura/<câmera>/<dia>/<HH-MM-SS>.jpg` | a miniatura do evento |

A API devolve **URLs, não caminhos de disco**: `_event()` troca o
`thumbnail_path` por `/miniatura/...`. A página nunca sabe onde os arquivos
estão.

**Ninguém sai de `clips/`.** A rota de miniatura recebe três pedaços do
endereço. Cada um tem que casar com uma expressão regular estrita (letras e
`-`/`_`; `AAAA-MM-DD`; `HH-MM-SS.jpg`), e o caminho final, depois de
`resolve()`, tem que estar dentro de `CLIP_DIR` (`is_relative_to`). Testado: as
cinco tentativas de sair com `..` e `%2F` voltaram 404, e um `dia` inválido
volta 400.

**Porta ocupada não derruba nada.** `_port_free()` tenta abrir a porta antes do
uvicorn. Se outra instância já estiver servindo, aparece "Interface web
desligada: a porta 8765 ja esta em uso" e a vigilância segue normalmente —
porque a interface é opcional e gravar não é.

**Só esta máquina, no estágio 1.** `HOST = "127.0.0.1"` escutava só conexões
locais. O estágio 3 abriu para a rede (17.7).

**A página.** HTML, CSS e JavaScript simples em `src/jarvis/static/`, sem
framework (17.4). O JavaScript busca `/api/eventos` e monta os cartões a partir
de um `<template>`. As setas ◀ ▶ pulam para o dia anterior ou próximo **com
gravação**, usando `/api/dias`. Vendo o dia de hoje, a lista se atualiza a cada
15 s, e para quando a aba não está visível (`document.hidden`).

Os rótulos chegam em inglês (`person`, `dog`), porque é o que o YOLO e os JSON
usam, e a página traduz na exibição: o dado continua o mesmo, só a apresentação
é em português. O mesmo vale para a data: o `<input type="date">` mostra no
formato do navegador, enquanto a API fala `AAAA-MM-DD`.

**O que ainda não faz:** clicar no cartão não abre o vídeo (estágio 2), e só
lista o que está em `clips/` — eventos já movidos para o HD externo (seção 11)
não aparecem, igual à janela.

### 17.7 Estágio 3, como ficou: ao vivo e um ponto de entrada só

**Aceite cumprido no M900:** as duas câmeras ao vivo na aba **Ao vivo**, com
nome, caixas de detecção e o `REC` de quando está gravando, a ~8 quadros por
segundo. O celular pela rede local depende do firewall (abaixo); a regra para o
`python.exe` existe, mas o teste no celular ainda não foi feito.

**MJPEG.** Cada câmera é uma resposta HTTP que nunca termina:
`multipart/x-mixed-replace`, uma sequência de JPEGs separados por uma linha de
fronteira (`--frame`). O navegador troca a imagem a cada parte que chega, e
mostra isso num `<img>` comum — sem player, sem JavaScript de vídeo. É o motivo
por que o `http.server` foi descartado (17.2): um espectador seguraria a única
thread dele para sempre.

```python
yield (f"--{BOUNDARY}\r\nContent-Type: image/jpeg\r\n"
       f"Content-Length: {len(data)}\r\n\r\n").encode() + data + b"\r\n"
```

`_mjpeg()` é um *generator* comum; o `StreamingResponse` o consome numa thread
do pool do servidor, uma por espectador. Ele dorme `1 / LIVE_FPS` entre quadros
e para quando `web.stop()` liga o `_stopping` — sem isso, um navegador aberto
seguraria o encerramento do programa.

**De onde vem a imagem.** `Core.live_view(label)` monta o painel **na hora do
pedido**, a partir do que o `Core` já tem: o último frame de análise
(`stream.latest`), as últimas detecções (`subjects.subjects`) e se está
gravando. Reaproveita o `make_panel` da janela, então o desenho é idêntico. Só
lê: o `make_panel` redimensiona para um array novo antes de desenhar, e o frame
original nunca é tocado — importante, porque ele é lido pela thread da web
enquanto o laço do `Core` segue na principal.

Ninguém olhando, ninguém paga: o `Core` continua com `draw=False` no modo
serviço, e o painel só existe quando um navegador pede. A página fecha os
streams quando sai da aba Ao vivo ou quando o navegador é minimizado
(`document.hidden`), tirando o `src` das imagens.

O rótulo da câmera desceu para `LABEL_Y = 62`: em `y = 34` ele ficava em cima do
relógio que a própria Tapo escreve no canto.

**Rede local.** `HOST = "0.0.0.0"` escuta em todas as interfaces, e o programa
imprime o endereço para o celular (`lan_address()`: conectar um socket UDP não
envia nada, só faz o Windows escolher a interface de saída, cujo endereço é o
nosso). Na primeira vez o Windows pergunta no firewall se o `python.exe` pode
receber conexões; sem permitir, só esta máquina abre a página. A rede do M900
está classificada como **Pública**, e a regra criada vale para esse perfil.
Continua sem login e sem porta aberta para a internet (17.4).

**Um ponto de entrada.** `main()` em `cameras.py` passou a ter três modos:

| Comando | Faz |
|---|---|
| `python -m jarvis` (o `jarvis.bat` e o atalho) | serviço + abre o navegador na página |
| `python -m jarvis --sem-janela` (`jarvis_vigilancia.bat`) | só o serviço; para subir com o Windows |
| `python -m jarvis --janela` | a janela antiga do OpenCV, **provisória** até o estágio 4 |

Antes de abrir câmera, `web.already_running()` pergunta a `/api/cameras` se já
há um J.A.R.V.I.S. servindo. Se houver, o segundo não sobe: só abre o navegador
(ou avisa) e sai. Testado: com o serviço no ar, um segundo lançamento saiu em
3 s e as câmeras continuaram com os dois ffmpeg da primeira instância. Sem
isso, clicar duas vezes no atalho faria o segundo brigar pela única conexão RTSP
de cada câmera.

**Encerrar** continua sendo `Ctrl+C` no console. Fechar o console no X não passa
pelo `finally` do `main()` — o Windows mata o processo, e um clipe em montagem
se perderia. Rodar como serviço de verdade, sem console, é o passo depois do
estágio 4.

### 17.8 Current state of the web, after the pre-production delivery (09/10/2026)

17.6 and 17.7 record how stages 1 and 3 were built; some names there have
changed since. This is the current state.

**Routes** (renamed to English while nothing outside the page depended on them):

| Route | Returns |
|---|---|
| `/` | the page |
| `/static/...`, `/icon.png` | CSS, JavaScript, icon |
| `/api/cameras` | camera names; empty while they are still starting |
| `/api/status` | `cameras`, `started` (when this server started), `frame_age` (seconds since each camera's last frame, `null` if none ever arrived) |
| `/api/days` | days with recordings, newest first |
| `/api/events?day=YYYY-MM-DD` | `{day, events}`; without `day`, today |
| `/thumbnail/<cam>/<day>/<HH-MM-SS>.jpg` | an event thumbnail, same checks as before (17.6) |
| `/live/<cam>` | MJPEG (17.7) |
| `POST /api/shutdown` | clean stop; **only from 127.0.0.1** — the port is open to the LAN, and anyone on the Wi-Fi could otherwise switch the surveillance off. 403 from anywhere else |

**Command line:**

| Command | Does |
|---|---|
| `python -m jarvis` | service plus browser (`jarvis.bat`, the shortcut) |
| `python -m jarvis --headless` | service only (`jarvis_vigilancia.bat`, the startup task) |
| `python -m jarvis --stop` | asks a running service to stop, waits until it is gone |
| `python -m jarvis --window` | the old OpenCV window, temporary |

`--sem-janela` and `--janela` still work as aliases.

**The port is the lock (R2).** The web binds its port before the cameras open,
atomically (18.8), so a second launch during the slow camera startup finds it
taken. `web.attach(core)` hands the `Core` over once the cameras are up; until
then `/api/cameras` answers with an empty list.

**No frozen pictures (R3).** `FFmpegCamera.frame_age` says how old the last
frame is. `Core.live_view()` draws "no signal" instead of a picture older than
`STALE_SECONDS` (5 s): a stopped camera must not look like a quiet scene. The
page asks `/api/status` every 5 s; if `started` changes — the service
restarted — it reopens the streams, because a broken MJPEG connection would
otherwise sit on its last frame forever.

**Failures are visible (R8).** If `/api/status` stops answering, a red "No
connection to J.A.R.V.I.S." appears at the top and the live pictures are
replaced by the same message; everything reconnects on its own.

**The page is in English**, and labels are shown as the system names them
(`person`, `dog`) — the Portuguese translation table is gone with the language
decision.

**HTTPS from another computer.** The server speaks plain HTTP. A browser that
tries `https://` first — typed without the scheme, or with "always use secure
connections" on — gets nothing, and the service logs `Invalid HTTP request
received` several times a second. Reproduced on 09/10/2026: an `https://`
request produces exactly that line, `http://` answers 200. The user confirmed
`http://192.168.0.18:8765` works from the other computer. HTTPS on a home
network would need a certificate the browser trusts; a self-signed one means a
warning on every visit, so it is not worth it now.

---

### 17.9 Stage 4: People and Settings on the web (10/10/2026)

The page gained the two tabs that only the OpenCV window had.

| Route | Does |
|---|---|
| `GET /api/face-days`, `GET /api/people?day=` | days with faces; that day's sightings with the gallery's current names |
| `GET /face/<day>/<HH-MM-SS_xxxxxx>.jpg` | one face crop; name checked by pattern, then must resolve inside `faces/` |
| `POST /api/people/<p_xxxxxxxx>/name` | `Gallery.rename`: the same name on another face merges them (10.4) |
| `GET` / `POST /api/settings` | read, or change some keys; each one type-checked, labels limited to YOLO's classes, unknown keys refused |
| `POST /api/notify/discover`, `POST /api/notify/test` | find the chat, send a test |

**The token is write-only.** The page can set it but never read it back —
only `notify_token_set` — because anyone on the Wi-Fi can open the page (R4).
**"Archive now" was left out on purpose:** it would move files from the web
thread while the `Housekeeper` may be moving the same files in the main loop.
Writes from the network are guarded by R24 (CONTEXTO 13.9).
### 17.10 The lock, People by person, who appears, and the window gone (10/10/2026)

**Every write is guarded (R24).** A FastAPI middleware — code that wraps every
request, like a servlet `Filter` or ASP.NET middleware — refuses any
`POST`/`PUT`/`PATCH`/`DELETE` unless (a) it carries `X-Jarvis-Request: 1`, even
from 127.0.0.1, and (b) from any other address, `X-Jarvis-Pin` equals
`write_pin`, compared with `hmac.compare_digest` (constant time, so the
comparison does not leak how many digits matched). The header defeats
cross-site forgery: a foreign page cannot add a custom header without the
browser first asking the server (a CORS preflight), and this server never says
yes. The PIN (4–12 digits) is set only from the M900's own page (Settings,
Other devices) and typed once on each other device, which keeps it in
`localStorage`. Threat model, honestly: good against a guest's phone and a
forged request; not against someone sniffing the Wi-Fi, since the PIN travels
in clear over HTTP, and it sits in plain text in `config.json`, like the token.
`--stop` sends the header, and `production.ps1` always stops a service with
that same version's `--stop`, so the guard cannot lock it out.

**People by person (backlog 19).** A grid of the named, the unnamed with a name
field and a "Belongs to…" picker, and a person page (`#people/<id>`) with
rename, the stored views and a month calendar of their recordings. The gallery
gained two optional keys per person: `views`, aligned by index with
`embeddings`, holding the path of each view's face crop in `faces/views/`
(`None` for views stored before, padded by `views_of()`), and `pending`, views
waiting once a person holds 40 (`MAX_PENDING` 100, oldest dropped with its
file). `Gallery._take()` is the one place that stores or queues a view —
`add`, `reinforce` and `_merge` all go through it, and merge no longer drops
the overflow. `remove_view()` frees a slot and pulls the oldest waiting view;
it refuses a person's last view when nothing waits. A rename to a name that
belongs to someone else answers **409 Conflict**, which the page turns into
"this will merge with X — continue?" and resends with `merge: true`. After a
rollback, an older version ignores both keys and only appends embeddings, so
the alignment holds (its new views just get `None`). **The favourite photo (backlog 21):** a star on each view with a photo sets the person's optional `cover` — the view's crop path, not its index, so it survives views being removed or reordered; `cover_of()` ignores it once it no longer matches a view, and removing the favourite falls back to the first view with a photo. A merge keeps the target's cover.

**Who appears (backlog 20).** `/api/events` reads the day's sightings once,
keyed by camera, day and clip time, and adds `people` (current names; unnamed
as "unknown") and `animals` to each event; the card shows them under the time.
Sightings stored Windows paths, so the clip path is split on either slash.

**The OpenCV window is gone.** `ui.py` and every drawing path in `cameras.py`
were deleted; `--window`/`--janela` now log where the web page is and start
as usual, for one release. A pitfall met on the way: content inside a
`<template>` lives in an inert document, where `a.href = "#x"` resolves against
`about:blank` — use `setAttribute`.
## 18. Production and test (designed and built 09/10/2026)

Written in English: the user decided on 09/10/2026 that documentation moves to
English (CONTEXTO R10). Older sections are still in Portuguese until then.

### 18.1 What the user asked for

> "My proposal is to have a service already installed on my machine, running
> constantly. [...] Have the production version always running, with an update
> process for it, and meanwhile we run in a test environment to evolve the
> version."

Today there is one copy of the program, and it is also the one being edited.
Every change goes live the moment it is saved, and testing a change means
stopping the surveillance.

### 18.2 The camera limit, measured

The obstacle the user anticipated is real, but narrower than assumed. Measured
on 09/10/2026 on the Front camera, a second client started 3 s after the first:

| First client | Second client | Result |
|---|---|---|
| `stream1` | `stream1` | second refused (`406`, "not one of 40{0,1,3,4}") |
| `stream1` | `stream2` | **both deliver** (151 and 76 frames) |
| `stream2` | `stream2` | **both deliver** |

| Stream | Codec | Resolution | Frame rate |
|---|---|---|---|
| `stream1` | H.264 | 1920x1080 | 15 fps |
| `stream2` | H.264 | 640x360 | 15 fps |

Same on the Back camera. So the Tapo C310 allows **one** client on the HD stream
and several on the SD stream at the same time. The September finding
("the camera accepts a single RTSP session", 5.2) was only ever tested on
`stream1`.

### 18.3 The design

**Two installations, each with its own data:**

| | Production | Test |
|---|---|---|
| Where | its own clone, `C:\JARVIS`, outside the project folder | the development checkout |
| Code | a **release tag**, never a working copy | whatever is being written |
| Camera stream | `stream1`, 1080p, records in HD | `stream2`, 640x360 |
| Web port | 8765, open to the home network (decided, R4) | 8766 |
| `clips/`, `faces/`, `config.json` | its own | its own; separate already, because every path hangs off `ROOT` (3.2) |
| Telegram | on | off by default, or prefixed `[TEST]` |
| Runs as | Task Scheduler task at boot, no console | by hand |

Both read the same cameras at once thanks to 18.2. The test copy can run on the
M900 or on the development machine; the cameras are on the network either way.

**What 640x360 costs the test copy:** motion, YOLO, recording, the web and the
notifications all work, but a face that is 45 px in 1080p is 15 px here — face
recognition cannot be tested live. For that, test against recorded HD clips
(see 18.6).

**Releases.** Production only ever runs a tagged commit, and a commit only gets
a tag after the architect review (CONTEXTO 13) has covered it. That ties the
two workflows together: nothing unreviewed reaches the machine that guards the
house.

**Updating production**, one command (`tools/update_production.ps1`, to be
written):

1. Fetch tags into `C:\JARVIS` and remember the tag currently running.
2. Stop the service **gracefully**, so a clip being assembled is not lost.
3. Check out the new tag and run `uv sync`.
4. Start the Task Scheduler task.
5. Health check: within 60 s, `/api/cameras` lists every camera and the live
   view delivers frames.
6. On failure, check out the previous tag, `uv sync`, start again, and say so
   on Telegram. On success, report the new version on Telegram.

### 18.4 What the code needs before this works

| Change | Why |
|---|---|
| Stream per installation in `.env` (`CAM_STREAM`, default `stream1`) | `STREAM` is a constant in `cameras.py` today |
| Web port per installation (`WEB_PORT`, default 8765) | `PORT` is a constant in `web.py` |
| A graceful stop that is not Ctrl+C | a scheduled task has no console; ending the task kills the process without running the `finally` in `main()` (17.7) |
| Logging to a file with rotation instead of `print` | with no console, `print` goes nowhere |
| Notification prefix per installation | so a test event is never mistaken for a real one |

The graceful stop has two reasonable forms: a `POST /api/shutdown` that only
accepts connections from `127.0.0.1`, or a stop file the main loop checks every
pass. The endpoint is simpler to call from the update script; the file works
even if the web thread is stuck.

### 18.5 Open decisions for the user

- Does the test copy run on the M900 next to production, or on the development
  machine? Recommendation: development machine — it is where the code is
  written and it has the CPU to spare; the M900 only runs production.
- Who runs the update? Recommendation: Claude, on request, after a review —
  never automatically, because an automatic update that fails at 3 a.m. is a
  night without surveillance.

**Where they stand (09/10/2026).** Who updates: **Claude, on request, after a
review** — that is how the user asked for the first release, and how
`update` is meant to be run. Where the test copy runs: not decided; the install
turns the development folder on the M900 into the test copy, which only runs
when started. Moving it to the other computer later means configuring that
checkout the same way (`CAM_STREAM=stream2`, `WEB_PORT=8766`, no token).

### 18.6 Later

A **file source**: point the test copy at a folder of recorded clips instead of
a camera, and replay them through the whole pipeline. It makes face
recognition testable at full resolution and makes any bug reproducible with
the exact footage that caused it.

### 18.7 As built (09/10/2026)

Everything in 18.4 is implemented. Production lives in `C:\JARVIS`, a clone of
the GitHub repository checked out at a release tag, and is driven by one
script, run from the development folder:

```bat
powershell -ExecutionPolicy Bypass -File tools\production.ps1 -Action <action>
```

| Action | Does | Needs admin |
|---|---|---|
| `install` | clone, copy data, `uv sync`, check data, start, health check, Telegram, turn the development folder into the test copy, desktop shortcut, register the startup task | only for the task, which it asks for on its own |
| `update` | update to the newest release tag (or `-Tag vX`), with checks and rollback | no |
| `status` | version, task, held or not, seconds since each camera's last frame | no |
| `stop` | stop cleanly **and hold**: the task will not start it again | no |
| `start` | release the hold, start, health check | no |
| `check` | run `tools/check_data.py` against production's data | no |
| `register` | register the startup task only | **yes** |

**The startup task** runs `C:\JARVIS\.venv\Scripts\pythonw.exe -m jarvis
--headless` directly: no console and no uv in the way. `pythonw.exe` there is
the venv launcher of the signed python.org build, so Smart App Control lets it
run (INSTALACAO 1.2); `Sync` refuses to finish if it is not.

| Setting | Value | Why |
|---|---|---|
| Logon type | S4U | runs whether or not anyone is logged on, with no password stored. Registering it is what needs admin |
| Triggers | at startup, **and every 5 min** | see below |
| Multiple instances | ignore new | the 5-minute trigger does nothing while it runs |
| Execution time limit | none | **the Task Scheduler default is 72 hours**: left alone it would kill the surveillance every three days |

**Why a 5-minute trigger.** The first version relied on "restart on failure".
The review found that this setting only acts when the task *fails to start*,
not when the program, once started, exits with an error — so a crash would
have ended the surveillance until the next reboot. A trigger every 5 minutes
with "ignore new" is the reliable form: running, nothing happens; crashed, it
is back within 5 minutes. A second copy cannot slip in either way, because
`main()` itself refuses to start next to a running one (17.7, 18.8).

**Why a `HOLD` file.** Starting and stopping a scheduled task needs admin
rights, and updates run without them. So the script never touches the task: it
stops the service through `--stop` and starts it directly with `pythonw.exe`.
That leaves one problem — the 5-minute trigger could start production in the
middle of an update, on half-switched code. `main()` therefore refuses to start
while `C:\JARVIS\HOLD` exists. `update` creates it before stopping and
`start` removes it; `stop` leaves it in place, which is what "stop" should mean.

**Two ways production starts, and they do not look the same** (seen on the
first night, 09/10/2026):

| Started by | Runs in | Visible? | At logoff |
|---|---|---|---|
| the task (boot, or the 5-minute trigger) | session 0, as S4U | nothing | keeps running |
| `production.ps1` (`install`, `update`, `start`) | the logged-on user's session | **every ffmpeg it starts gets a console window** | ends with the session; the 5-minute trigger starts it again in session 0 |

The windows come from how Windows treats console programs. `pythonw.exe` has
no console, and a console program started from a process without one gets a
**new** console window of its own. ffmpeg is a console program, so the user
saw two windows that stayed (one capture per camera, titled with the ffmpeg
path under `site-packages\imageio_ffmpeg`) and others that flashed (clip
assembly and the face scan). Closing one kills that ffmpeg. The fix is in the
code, not the script: every subprocess now starts with `CREATE_NO_WINDOW` (R15,
10/10/2026) — C#'s `ProcessStartInfo.CreateNoWindow`. Checking it taught two
things: a `conhost.exe` child is not a sign of a window (Windows creates one
with the flag too, and with Windows Terminal the window belongs to
`WindowsTerminal.exe`); what works is `AttachConsole(pid)` then
`GetConsoleWindow()`, NULL without a window. And a script under `pythonw.exe`
that captures a subprocess's output needs `stdin=subprocess.DEVNULL`, or it
dies silently on an invalid handle.

**An update**, in order, and where it stops:

1. Check the data with the **current** version. Unreadable already → refuse,
   nothing changed.
2. Hold, stop cleanly.
3. `git checkout --force <tag>`, `uv sync --frozen --no-dev` (since 10/10/2026: production carries no test tools, and the sync removes them if present), signature check.
4. Check the data with the **new** version.
5. Release, start, health check: within 90 s every camera's last frame must be
   under 5 s old (`/api/status`, `frame_age`).
6. Any failure in 3–5 → hold, stop, check out the previous version, sync,
   start, health check, and a Telegram message saying the update failed and
   what is running.

**Tested before the first release**, in a temporary folder with
`-SkipTask` (no task, no shortcut, no Telegram):

| Test | Result |
|---|---|
| install | clone, copy, sync and both cameras fresh in about 30 s |
| `stop` | clean stop, `HOLD` created |
| what the task would do while held | "Held: ... Not starting." |
| `status` | version, held, not answering |
| `start` | hold released, running |
| update to a version broken on purpose | failed the health check, rolled back by itself; `status` afterwards showed the previous version with both cameras fresh (0.0 s and 0.1 s) |

What only the real install can test: registering the task (admin), the shortcut,
turning the development folder into the test copy, and a reboot.

### 18.8 What the review changed (09/10/2026)

The developer's first version was reviewed before the first release (CONTEXTO
13.2, review 2). Besides the task design above:

- **The port as an atomic lock.** The first version checked whether the port
  was free and bound it a moment later, in uvicorn's thread; two launches a
  moment apart could both see it free. `web._bind()` now binds it in the main
  thread with `SO_EXCLUSIVEADDRUSE` (without it, Windows lets a second process
  bind the same port) and hands the bound socket to uvicorn
  (`Server.run(sockets=[...])`). If the port is taken, `main()` waits up to 5 s
  for a J.A.R.V.I.S. to answer there and leaves if one does; if nothing
  answers, another program has the port and the surveillance runs without the
  web rather than not at all. Tested: two launches at the same instant, one
  runs.
- **Only the service writes `logs/jarvis.log`.** `--stop` and a duplicate
  launch log to the console only: on Windows, rotating a log that another
  process holds open fails.
- **`.env` written without a BOM** by the install script; with one, the first
  key of the file would silently stop matching (19.3).
- **The test copy also loses `archive_path`**: two copies moving recordings
  into the same external drive would fight over it.

### 18.9 PowerShell traps met while building this

Worth knowing for anyone touching `tools/production.ps1`:

| Trap | What happened |
|---|---|
| Everything a function prints is part of its return value | `CheckData` returned the check's output lines plus `$true`/`$false`; a non-empty array is truthy, so **the data gate always passed**. Fixed with `\| Out-Host`, proven with a corrupted file |
| Names are case-insensitive | a helper named `Git` shadowed `git.exe` and would have called itself forever |
| Windows PowerShell 5.1 reads a `.ps1` without BOM as ANSI | an em dash in a message became a closing quote, and the script stopped parsing. The script is ASCII-only now |
| `$ErrorActionPreference = 'Stop'` turns a native program's stderr into an exception | `git describe` on an untagged commit aborted `status` |
| `Start-Process -Wait` waits for every process the child started too | a test harness hung on the service the install left running (the script itself only waits on the elevated registration, which starts nothing) |

---

## 19. Files on disk, and keeping them readable

### 19.1 The rule

Decided by the user on 09/10/2026: **a new version must never break files
written by an older one.** The recordings, the face gallery and the names given
to it are the system's memory; a version that cannot read them has thrown that
memory away.

So changes to anything below are **additive**: new optional fields, new files.
A field is never renamed, removed or given a new meaning. If a change cannot be
additive, the developer stops and tells the user before writing it, and ships a
migration with it (CLAUDE.md).

### 19.2 What is on disk

| File | Written by | Read by | Content |
|---|---|---|---|
| `clips/<cam>/<day>/HH-MM-SS.mp4` | `clips._concat` | the user, the face scan, `tools/verificar_clipes.py` | the camera's own H.264, never re-encoded (8.1) |
| `clips/<cam>/<day>/HH-MM-SS.jpg` | `EventRecorder._start` | Records, web, notification | first frame with the subject, boxes drawn (8.5) |
| `clips/<cam>/<day>/HH-MM-SS.json` | `EventRecorder._write_metadata` | Records, web, archive, `check_data` | `camera`, `started_at`, `time`, `seconds`, `labels`, `best_confidence`, `video`, `thumbnail`, `reason`; `best_thumbnail` **optional since 10/10/2026** |
| `clips/<cam>/<day>/HH-MM-SS.alert.jpg` | `EventRecorder._notify_late` | the Telegram message | **optional, since 09/10/2026**: only when the notification went out after the event began (12.8) |
| `clips/<cam>/<day>/HH-MM-SS.best.jpg` | `EventRecorder.stop` | web, the follow-up message | **optional, since 10/10/2026**: the best view of a person in the event (12.9) |
| `clips/<cam>/<day>/HH-MM-SS.side.jpg` | `scan_clip` | the follow-up message | **optional, since 11/10/2026**: the best face seen from the side when none was recognisable (section 21) |
| `clips/_buffer/<cam>/*.mp4` | ffmpeg | `covering()` | rolling segments, deleted on their own (5.5) |
| `faces/gallery.json` | `Gallery.save` | People, the face scan | `people`: `id`, `name`, `embeddings` (128 floats each), `thumbnail`, `first_seen`; `views`, `pending` and `cover` **optional since 10/10/2026** (17.10) |
| `dogs/` (`gallery.json`, `views/`, `<day>/*.json` + crops) | `dogs.py` | the Dogs tab, matching, `check_data` | **since 10/10/2026** (section 20); dog sightings: `dog_id`, `camera`, `at`, `time`, `infrared`, `clip`, `thumbnail`, `certainty`, `match`, `words` |
| `faces/views/<12hex>.jpg` | `Gallery._store_view` | the person page | **since 10/10/2026**: one face crop per stored or queued view |
| `faces/<day>/<HH-MM-SS>_<id>.json` + `.jpg` | `scan_clip` | People, `check_data` | `person_id`, `camera`, `at`, `time`, `score`, `frames`, `face_width`, `reliable`, `clip`, `thumbnail` |
| `config.json` | `settings.save` | everything that reads settings | `archive_*`, `notify_*`; `notify_prefix` **since 09/10/2026**; `write_pin` **since 10/10/2026** (17.10). Since 10/10/2026 `save()` keeps keys it does not know, so an older version never erases a newer one's settings (R11) |
| `.env` | the user | `cameras.main` | `CAM_<LABEL>_IP/_USER/_PASSWORD`; `CAM_STREAM`, `WEB_PORT` **optional since 09/10/2026** |
| `logs/jarvis.log` (+ `.1` to `.5`) | `log.to_file` | the user | 1 MB each, the oldest is dropped |
| `HOLD` | `tools/production.ps1` | `cameras.main` | present while production is held (18.7) |

Every event file shares the basename `HH-MM-SS`, and that is load-bearing: the
archive moves an event with `glob(f"{base.name}.*")` (11.2). That is why the
late alert photo is `HH-MM-SS.alert.jpg` and not `HH-MM-SS_alert.jpg` — the
second name would be left behind when the event moves to the external drive.

### 19.3 Two traps already met

**`settings.save()` drops keys it does not know.** It keeps only the keys in
`DEFAULTS`. An older version saving `config.json` erases settings a newer one
added. Harmless as long as production only moves forward, but it is the reason
`check_data` warns about unknown keys.

**A byte-order mark makes JSON unreadable.** PowerShell's
`Set-Content -Encoding UTF8` and some editors start a UTF-8 file with the three
bytes `EF BB BF`. `json.loads` on a string read as `utf-8` fails on them — and
`settings.load()` swallowed the error and returned the defaults, so a
`config.json` saved that way **silently lost the Telegram token**. Found on
09/10/2026 when a test restore added a BOM and `check_data` caught it. Every
JSON reader now opens files as `utf-8-sig`, which accepts both; writing is
unchanged (no BOM).

### 19.4 `tools/check_data.py`

Reads every event, face sighting, the gallery and `config.json` **with the
current code**, the way the program reads them (including `web._event`, what
the page shows), plus the archive folder if one is configured and reachable.
Exit code 1 if any file cannot be read.

```bat
uv run tools/check_data.py
```

On the M900 on 09/10/2026: 149 events, 7 people, 20 sightings, all readable.

It is part of every production update, before and after switching versions
(18.7): the update is refused if the data is already unreadable, and rolled
back if the new version cannot read it. Proven with a deliberately corrupted
event JSON (exit 1) and the restored file (exit 0).

Unknown keys in `config.json` are a **warning**, not a failure: the file is
still readable, and failing would block going back to an older version.

### 19.5 Automatic tests (10/10/2026)

`uv run pytest` runs 23 tests in `tests/` in about 3 s (R6): the gallery's view alignment (`test_gallery.py`: a photo per view, old views without one, the queue past 40 and its cap, removal pulling from the queue, merges), the write guard (`test_web_guard.py`: FastAPI's `TestClient` as 127.0.0.1 and as a LAN address), and the notification rules (`test_notify.py`: redaction, labels, both cooldowns). Every test works on temporary folders and replaces `notify.send`, so nothing touches real data or the network. `pytest` and `httpx2` are development dependencies only; `httpx2` is the successor of `httpx` that this Starlette's `TestClient` imports first (checked 10/10: same author, Pydantic's repository).

---

## 20. Dogs: each household teaches its own (10/10/2026)

**The rule (the user's):** nothing about any particular dog lives in the code.
The software is for any house; the user names their dogs on the **Dogs** tab,
and the system learns from those names.

**Seeing a dog's fur, not its box.** `dogs.fur_mask` cuts the dog out of its
YOLO box (+10 % margin) with OpenCV's **GrabCut** — a segmentation that starts
from a rectangle and iterates a graph cut over colour models of "inside" and
"outside". The first measurement without it failed: a box holds the mat, the
floor, sun and shade, and the fur tone of 168 detections was a continuous
smear. With it, 89 detections split into a dark and a light group, and at
night cleanly (CONTEXTO, backlog 15 and 22).

**The descriptor.** 41 numbers: an infrared flag, 16 tone bins of the fur,
and 16 hue + 8 saturation bins when the frame is in colour (zeros at night).
`is_infrared`: the mean channel difference is 3.98 on every night clip and
15–24 by day, so a threshold of 8 is safe.

**The gallery.** `DogGallery` subclasses `faces.Gallery` — the same views,
queue and favourite photo, in `dogs/`, with ids `d_…` — by overriding two
class attributes (`id_prefix`, `sighting_key`): the same code with different
constants, the way a Java subclass overrides a constant. Naming never gathers
other crops on its own (`_absorb` is off): two dogs' histograms can look alike.
The page reuses one JavaScript factory, `galleryTab(...)`, for People and Dogs.

**Matching.** `dogs.distance` is the mean Bhattacharyya distance over the
histograms (a standard measure of how much two distributions overlap), and
`None` between day and infrared — they are never compared. `match` takes the
nearest named dog: **sure** within 0.35 and at most 0.6× the second nearest,
**probable** within 0.5 and 0.8×; otherwise nobody. The margin to the second
is what lets it honestly say "I don't know". Measured on 20 test crops: day
distances 0.16–0.81 (median 0.53), infrared 0.18–1.0 (median 0.82); the
thresholds sit below the medians and **are not yet validated** — they wait for
the user's names.

**The wording (the user's rule).** A dog alerts because a dog is there,
whenever `dog` is an alert label; certainty only changes the words: the name,
"probably <name>", or "unidentified dog" (plain "dog" while nothing is named).
The first message names the dogs of the triggering frame (~100 ms, once per
dog event); the Recordings card shows the event's best dog frame, so the two
can differ. A sure match reinforces that dog with one more view; anything less
becomes an unnamed crop (R27 caps them). `tools/dog_crops.py [--days N]` gives
crops to events recorded before the feature (~21 s per event on the M900).

**Keeping the Dogs tab small (R27, 11/10/2026).** `DogGallery.add` keeps only the newest `MAX_UNNAMED` = 60 unnamed dogs; named dogs are never touched, and a dropped entry's photos go with it. Sightings stay, so calendars keep their history (a dropped `dog_id` reads as "?"). Each unnamed crop has a **Dismiss**. `tools/dog_tuning.py [--gallery PATH]` measures the thresholds by **leave-one-out** — each named view matched against all the others, the honest test with few labels — and prints right-sure, right-probable, wrong and no-name per lighting, then a grid of thresholds; it only reads, so it can run on production's `dogs/gallery.json`.

---

## 21. Fixes from the general review (11/10/2026)

**The page is never stale (R28).** `/` is built from `index.html` with the running version in the asset URLs (`app.js?v=<git describe>`) and sent with `Cache-Control: no-cache`; a middleware, `never_stale`, adds the same header to `/static/*`. `no-cache` means *revalidate*, not *do not store*: the browser asks with the file's ETag every load and gets a cheap 304 when nothing changed — so an update can never leave an old script running on another computer. Every refused write now shows the server's reason, e.g. an unpaired device: "no PIN is set: on the M900 itself, open Settings and set one to pair other devices". The M900's own browser at 192.168.0.18 counts as another device, which is how this was tested.

**The face seen from the side (R30, part a).** When a person event's scan keeps no recognisable face, `faces_in(frame, sides)` also collects the good non-frontal faces (score ≥ `IDENTITY_SCORE`, width ≥ 36 px) and the scan saves the best — smallest nose offset, then largest — as `HH-MM-SS.side.jpg` beside the clip, **never into the gallery**. The follow-up message after a sent event is, in order of preference: the recognised face, else "face, side view", else the best view. On the three daytime clips of 10/10 that had no face, each now gives a side view (40–59 px); they had failed on the eye spread, not the nose. Part (b), loosening the limits for recognition, waits for named views.

**Pair a device once (R34).** Pairing with the PIN makes the server set a cookie — `HttpOnly` (no script can read it), `SameSite=Strict` (never sent by another site), 30 days — holding a random token; `devices.json` keeps only its SHA-256 hash, a label and the last use, and every write from that device renews the 30 days. A cookie set by the server survives where the page's `localStorage` did not. The M900's Settings lists the paired devices with "forget"; the R24 header still blocks forged requests.

**Play a recording (backlog 5).** `GET /video/<camera>/<day>/<HH-MM-SS>.mp4`, with the thumbnail's name checks and a resolve inside `clips/`; Starlette's `FileResponse` answers HTTP **Range** requests (206), so the browser seeks without downloading the clip. Clicking a card opens a player on the page; a day on a person's or dog's calendar leads there.

**Dogs gather their look-alikes (R29).** Naming or merging a dog re-examines every unnamed crop against the dog's updated views with the *sure* rule only, same lighting only, repeating until nothing joins; past recordings show the dog's current name from `dog_id` instead of the words frozen when they were recorded.

**Bad detections are reported, not deleted (backlog 23).** Every unnamed face or dog card, and every label of a recording in the player, has "Bad detection": the crop leaves the gallery (or the label the card) and is kept in `reports/<kind>/` — the crop and a JSON with `kind` (face, dog), `source` (gallery, event), `verdict` ("not a dog"), label, score, box, camera, time and clip; gallery entries also keep their embeddings and sightings. Nothing learns from it yet: it is the evidence every rule change is measured against. Not versioned (it holds the household's images).

**The 40 most different views (backlog 24).** "Analyse" on a person or dog with more than 40 views proposes the 40 that are most different — greedy farthest-point selection: start from one view, then always add the view farthest from everything already chosen — and on confirmation keeps them and queues the rest. 0.03 s for 100 face views, 0.28 s for 140 dog views; on test data the closest pair kept went from identical to clearly different.

**A cheaper face scan (R31).** YuNet now finds faces on a 960-px copy of the frame and each face is refined on the full 1080p frame, where the alignment needs the detail: 45 ms per frame instead of 137, with 6 % fewer frontal face frames on 455 test frames — a face is seen in many frames of an event, so the loss per event is smaller. **Log noise (R32):** a browser closing the live view no longer logs an asyncio traceback at ERROR.

**What did not change, on purpose.** R35: the five boxes a lower ratio (1.5) would drop were all people — crouching at the door, bending, sitting below the camera — so R18 stays at 2.0, and the rare curled-up dog is left to the bad-detection reports. R30 (b): side faces of the one named person match 55–100 % of the time, but with a single named person nothing shows a stranger's side face would not match too, so the frontal limits stay until a second person is named.
