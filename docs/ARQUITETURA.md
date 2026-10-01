# J.A.R.V.I.S. — Arquitetura

Documentação de como o sistema funciona e, principalmente, **por que** cada
decisão foi tomada. O código não tem comentários; todo o raciocínio está aqui.

Para aspectos de linguagem e bibliotecas, veja [PYTHON.md](PYTHON.md).

---

## 1. O que o sistema faz

Monitora câmeras Tapo pela rede local, identifica quando há **movimento**,
decide se esse movimento é uma **pessoa**, e grava um **vídeo** do evento.

O objetivo final é reconhecimento facial, mas a camada de pessoa é
deliberadamente independente disso: alguém de máscara, capacete ou de costas
continua sendo detectado como humano.

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
| MOG2 | ~3 ms | todo frame |
| YOLO11 | ~24 ms | só com movimento, no máximo 4×/s |
| Gravação | ~2 ms | só com pessoa |

## 3. Estrutura de arquivos

```
jarvis/
├── src/jarvis/           o programa, como pacote Python
│   ├── __init__.py       ROOT: a raiz do projeto, base de todo caminho
│   ├── __main__.py       permite `python -m jarvis`
│   ├── cameras.py        aplicação principal (loop, exibição, orquestração)
│   ├── capture.py        ffmpeg por câmera: segmentos originais + frames
│   ├── motion.py         camada 1: detecção de movimento
│   ├── people.py         camada 2: detecção de pessoas e animais
│   ├── clips.py          camada 3: eventos, montagem sem perda, metadados
│   ├── faces.py          camada 4: detecção de rosto, embedding, galeria
│   ├── ui.py             menu lateral, telas Live, Records e People
│   └── geometry.py       tipo Detection e utilitários de caixas (IoU)
├── tools/                ferramentas, fora do programa
│   ├── diagnostico.py    variantes do comando de captura; --local sem câmera
│   ├── probe_rtsp.py     RTSP puro (DESCRIBE → SETUP → PLAY)
│   ├── refazer_rostos.py reconstrói faces/ a partir dos clipes
│   ├── verificar_clipes.py dano de imagem vindo das câmeras
│   ├── gerar_icone.py    desenha o ícone (seção 13)
│   └── criar_atalho.ps1  atalho na Área de Trabalho com o ícone
├── assets/               jarvis.ico e uma prévia em PNG
├── docs/
│   ├── ARQUITETURA.md    como funciona e por quê
│   ├── INSTALACAO.md     como instalar e operar numa máquina nova
│   ├── PYTHON.md         Python e bibliotecas, para quem vem de Java/C#
│   └── CONTEXTO.md       histórico, decisões, caminhos descartados
├── instalar.bat          instalação em máquina nova (roda uma vez)
├── jarvis.bat            atalho para iniciar o programa
├── .env.example          modelo de configuração, versionado
├── .env                  credenciais das câmeras (NÃO versionado)
├── models/               ONNX do YOLO, YuNet e SFace (baixados, não versionado)
├── clips/                gravações (não versionado)
│   ├── _buffer/          segmentos rotativos por câmera, apagados sozinhos
│   └── Front/2026-09-26/19-17-30.{mp4,jpg,json}
└── faces/                rostos e galeria (não versionado)
    ├── gallery.json      pessoas conhecidas e desconhecidas
    └── 2026-09-28/21-42-00_a1b2c3.{jpg,json}
```

Na raiz ficam só o que o usuário abre ou edita (os `.bat`, o `.env`) e o que
as ferramentas exigem ali (`pyproject.toml`, `uv.lock`, `.python-version`).

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

**Sobre compactar tipo zip:** medido no arquivo real, ZIP ganha 5,2% e LZMA
11,1%. Vídeo já é comprimido — a entropia foi removida pelo codec, então o
compactador acha pouca redundância. Guardar o stream original economiza 20% e
dá qualidade perfeita, sem etapa de descompactar.

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
para o ArcFace. Quando essa camada chegar, o recorte em alta resolução deve
sair **do segmento gravado**, usando o horário exato do evento. Os segmentos
são a fonte de alta qualidade.

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
`protect_from` impede que os segmentos dele sejam apagados. Medido: ~1 MB por
câmera para 20 s de buffer.

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
`.env.example`, de onde o `instalar.bat` cria o `.env`. O painel dizia só "nenhum frame recebido", e a investigação foi atrás
de decode, pipe e antivírus antes de alguém rodar `Test-NetConnection`. A única
linha do log, mesmo em `-loglevel verbose`, era `Starting connection attempt`.

Com `-timeout` (em microssegundos, `SOCKET_TIMEOUT_SECONDS` no `capture.py`) o
ffmpeg desiste em ~6 s. No Windows o erro sai como `Error number -138`, que é o
`ETIMEDOUT` da biblioteca C, sem as palavras "timed out" — por isso a linha
própria na tabela. O mesmo prazo vale para leituras: câmera que para de mandar
dados por 5 s derruba o processo, e o reinício automático (5.8) reconecta.

O painel "sem sinal" mostra esse texto quebrado em linhas, então o motivo fica
visível sem abrir o terminal.

### 5.8 Reinício automático

Se o ffmpeg morrer (queda de rede, câmera reiniciando), `read()` devolve `None`
e o processo é recriado após `RESTART_SECONDS`. O painel mostra `no signal`
nesse intervalo, e a aplicação não cai.

Como o OpenCV não faz mais captura, a variável de ambiente
`OPENCV_FFMPEG_CAPTURE_OPTIONS` desapareceu — junto com a fragilidade de ter
uma atribuição obrigatória antes do `import cv2`. O transporte TCP agora é um
argumento explícito do ffmpeg (`-rtsp_transport tcp`).

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

Custo: uma pessoa é reportada 3 frames (~0,2 s) depois de aparecer. Como o
gravador tem pré-gravação de 30 frames, nada de útil se perde no vídeo.

**Limitação conhecida:** um inseto que fique pairando exatamente no mesmo ponto
por vários frames acaba confirmado. O YOLO rejeita esse caso.

Este também é o embrião do *tracking* que virá depois.

### 6.4 Aquecimento

`WARMUP_FRAMES = 60` (~4 s). Antes disso tudo é "novidade" e o detector
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
ANIMAL_CLASSES = (14, 15, 16, 17, 18, 19)
```

Ou seja: `person`, `bird`, `cat`, `dog`, `horse`, `sheep`, `cow`. Bear, elephant
e zebra existem no COCO e foram deixados de fora por serem implausíveis aqui —
incluí-los só criaria falsos positivos exóticos.

Animais usam um limiar de confiança mais alto (`ANIMAL_CONFIDENCE = 0.45` contra
`CONFIDENCE = 0.35`), porque objetos de cena são confundidos com animais com
mais facilidade que com pessoas.

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

### 7.3 Rosto de cachorro não funciona

Registro explícito, porque é uma pergunta natural: **a camada de rosto planejada
(SCRFD + ArcFace) não detecta rosto de animal.** Os dois modelos são treinados
exclusivamente em faces humanas; o SCRFD procura a geometria de olhos/nariz/boca
humanos, e o embedding do ArcFace não tem significado para outra espécie.

Portanto:

| Objetivo | Situação |
|---|---|
| Detectar que existe um cachorro | Funciona hoje (COCO classe 16) |
| Saber *qual* cachorro | Problema separado (pet re-ID), sem modelo pronto bom |
| Rosto humano | SCRFD + ArcFace, camada futura |

Identificar cães individualmente exigiria um classificador treinado com fotos
dos seus próprios animais — viável, mas é outra camada.

### 7.4 Decisão de projeto: frame inteiro, não recorte

A primeira versão recortava o frame na região do movimento e rodava o YOLO só
nesse recorte. Teste revelou a falha:

- Recorte de 192×192, pessoa ocupando quase a imagem toda.
- O YOLO acertou "pessoa", mas **a caixa retornada ficou limitada ao recorte**:
  153×115 em vez do corpo inteiro.

Isso é um teto estrutural, não questão de ajuste. Pior: se o movimento pegar só
as pernas, a caixa recortada **nunca** conterá a cabeça — justamente o que a
futura camada de rosto precisa.

**Solução:** YOLO roda no frame inteiro. O movimento serve como (a) gatilho e
(b) filtro de relevância. Reteste com o mesmo blob minúsculo: caixa completa
`120,202 → 1109,712`, confiança 0.92, batendo com o *ground truth*.

### 7.5 Throttle

YOLO custa ~24 ms nesta CPU. Rodar em todo frame comeria o orçamento e
travaria o vídeo. `MIN_INTERVAL = 0.25` limita a 4 execuções por segundo por
câmera, **reaproveitando a resposta anterior** no intervalo.

Evidência de que funciona: a taxa de frames ficou em 12,7 fps antes e depois de
adicionar o YOLO.

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
na memória. É o oposto do `MotionDetector`:

| Componente | Estado | Instâncias |
|---|---|---|
| `MotionDetector` | modelo de fundo daquela câmera | **uma por câmera** |
| `SubjectDetector` | throttle, último resultado e cenário estático | uma por câmera |
| Rede YOLO | nenhum | **uma compartilhada** |

---

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

Foi exatamente o trabalho que, lá no começo do projeto, eu apontei como o custo
de usar C++ em vez de Python. Ele apareceu de qualquer forma — só que por um
motivo que ninguém previu.

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

Medido no clipe real montado: **859 KB para 18 s** = ~48 KB/s.

| | Antes | Agora |
|---|---|---|
| Taxa | 72 KB/s | **48 KB/s** |
| 5 min/dia | ~285 MB | **~14 MB** |
| Por ano | ~100 GB | **~5 GB** |

O buffer rotativo custa à parte: ~1 MB por câmera para 20 s, ou ~12 MB por
câmera com `BUFFER_SECONDS = 240`.

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

1. Não gravar o que não é evento — feito (movimento, confirmação temporal,
   supressão de cenário estático).
2. Não recodificar — feito (seção 5.1). Levou de ~100 GB/ano para ~5 GB/ano.
3. **Retenção automática** — não feito, e é o único lever grande que resta.
4. Compactar — 0,2%, descartado.

---

## 9. Interface — `ui.py`

A janela inteira é uma única imagem numpy, montada assim:

```
┌──────────┬──────────────────────────┬──────────┐
│ J.A.R.V. │                          │ 09/2026  │
│          │   Live (letterbox)       │ D S T Q  │
│ ▸ Live   │        ou                │  1 2 3 4 │
│   Records│   grade de gravações     │  5 6 7 8 │
└──────────┴──────────────────────────┴──────────┘
  190 px                                 250 px
                                      (só em Records)
```

O HighGUI do OpenCV **não tem widgets**: não existe botão, lista, scroll nem
gerenciador de layout. Tudo é retângulo e texto desenhados à mão.

### 9.0 Proporção ao redimensionar a janela

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

### 9.0 Só redesenha quando vale a pena

As câmeras entregam ~10 frames por segundo, mas o laço gira a cada ~20 ms. A
maioria das voltas não tem frame novo, e redesenhar a tela inteira nelas seria
desperdício puro — num M900 de quatro núcleos, desperdício caro.

O redesenho acontece quando **alguma câmera trouxe frame novo**, ou quando
passaram `REDRAW_SECONDS = 0.15` sem nada. O segundo caso existe para a
interface continuar viva: o cursor do campo de nome pisca, e a tela Records
precisa reler a pasta de tempos em tempos.

O `cv2.waitKey(15)` continua sendo chamado em **toda** volta, com frame novo ou
sem. É ele que mantém a janela respondendo (ver 9.5), e os 15 ms também evitam
que o laço gire a mil por segundo sem fazer nada.

Os painéis ficam guardados por câmera num dicionário. Câmera sem frame novo
reaproveita o painel anterior, em vez de virar "no signal" a cada volta.

### 9.1 Modo imediato: nada persiste

Vindo de Swing, WinForms ou WPF, o instinto é criar controles uma vez e deixar
o framework mantê-los. Aqui é o oposto — é o modelo que jogos usam:

**A cada volta do laço a janela é redesenhada do zero.** Não existe objeto
"botão" guardado em lugar algum; existe apenas um array numpy que nasce, recebe
pixels e é jogado na tela. No frame seguinte, outro array.

A composição é literalmente concatenação de imagens:

```python
bar = sidebar.draw(content.shape[0])
return np.hstack([bar, content])
```

A barra nasce como um bloco de cor sólida, e o conteúdo é a tela Live ou a
Records. As primitivas são todas chamadas do `cv2` sobre o array:
`rectangle` (com espessura `-1` para preenchido), `putText`, `line`, `circle`.

Consequência prática: **não há estado de interface para dessincronizar**. O que
aparece é função direta dos dados daquele instante. Em troca, tudo é
recalculado 15 vezes por segundo — daí os cuidados de cache da seção 9.3.

### 9.2 Cliques: coordenadas cruas e uma pegadinha

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
| `view` | Troca entre Live e Records |
| `day` | Seleciona o dia exibido |
| `month` | Avança ou volta um mês no calendário |
| `open` | Abre o arquivo no Explorer |

A vantagem é que layout e interação nunca saem de sincronia: quem move um
cartão move automaticamente sua área clicável, porque é a mesma linha de código
que faz as duas coisas.

### 9.3 Tela Live

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

### 9.4 Tela Records

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
sem reformatação, que é o que resolve. Ver PYTHON.md seção 17.5.

Se o `.mp4` final ainda não existir (a compressão roda em thread), `reveal()`
tenta o `.raw.mp4` e, em último caso, a pasta do dia.

### 9.4.1 Calendário

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

**O grid sai de aritmética simples.** A largura do cartão é o espaço livre
dividido pelas colunas, descontando os vãos — para 5 colunas há 6 vãos (um em
cada borda mais os internos):

```python
card_w = (width - CARD_GAP * (CARD_COLUMNS + 1)) // CARD_COLUMNS
thumb_h = int(card_w * 9 / 16)
```

Medido: conteúdo de 1706 px gera cartões de 326 px com miniatura de 183 px.

A posição de cada cartão vem de `divmod`, que devolve quociente e resto numa
só chamada — o 8º cartão (índice 7) com 5 colunas cai em linha 1, coluna 2:

```python
row, column = divmod(index, CARD_COLUMNS)
x = CARD_GAP + column * (card_w + CARD_GAP)
y = top_offset + row * (card_h + CARD_GAP)
```

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
como `//` arredonda para baixo (PYTHON.md 19.1), negar duas vezes inverte o
sentido do arredondamento.

Os cartões também encolheram (`MIN_CARD_WIDTH` de 210 para 168), então mais
gravações cabem antes de precisar rolar.

A barra à direita **não é clicável**: indica apenas posição e proporção, e seu
tamanho reflete quanto do total está visível.

**A ordem de desenho importa:** os cartões são desenhados **antes** do
cabeçalho, porque é `_draw_cards` que calcula `max_scroll`, e o cabeçalho
precisa desse valor para decidir se mostra a dica "roda do mouse para rolar".

**Dois cuidados de desempenho**, porque isso é redesenhado a 15 fps:

- **Cache de miniaturas.** Decodificar JPEG a cada frame seria absurdo; as
  imagens já redimensionadas ficam num dicionário indexado por caminho **e
  tamanho** — o tamanho entra na chave porque redimensionar a janela muda
  `card_w` e invalidaria as imagens antigas.
- **Rescan periódico.** A pasta só é relida a cada `RESCAN_SECONDS = 2.0`, não
  a cada frame.

**As câmeras continuam sendo processadas enquanto a tela Records está aberta.**
Detecção e gravação não param por causa da navegação; só a imagem exibida muda.

### 9.5 Limitação: `cv2.putText` é só ASCII

As fontes Hershey do OpenCV não têm acentuação. Escrever `"gravação"` renderiza
caracteres quebrados, e por isso todo texto da interface está **sem acento** de
propósito ("gravacao", "Nenhuma gravacao hoje").

Acentos exigiriam desenhar texto com PIL (Pillow, já presente como dependência
do ultralytics) e converter para numpy — possível, mas é uma camada extra.

### 9.6 Fechar a janela no X

O HighGUI do OpenCV não tem evento de fechamento. Ao clicar no X a janela é
destruída, mas o `imshow` seguinte **cria outra**. Por isso perguntamos a cada
frame se ela ainda existe:

```python
if cv2.getWindowProperty(WINDOW, cv2.WND_PROP_VISIBLE) < 1:
    break
```

A verificação precisa vir **depois** de `cv2.waitKey(1)`, porque é o `waitKey`
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

### 10.2 YuNet e SFace, sem dependência nova

O OpenCV traz os dois modelos embutidos:

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
GOOD_FACE_WIDTH = 80    # abaixo disso entra, mas nao reforca a galeria
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
key = cv2.waitKey(1) & 0xFF
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

A tela People é exatamente a ferramenta que coletaria esses recortes, então a
infraestrutura já está pronta quando essa camada for feita.

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

## 11. Restrição importante das câmeras Tapo

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

## 12. Estado atual e próximos passos

**Funcionando:** captura via ffmpeg sem recodificar, movimento com confirmação
temporal, detecção de pessoas e animais, supressão de cenário estático, altura
mínima para pessoa, gravação com pré-roll montada dos segmentos originais,
miniatura e metadados por evento, reconhecimento facial com galeria e cadastro
de nome, e a interface com Live, Records (calendário e rolagem) e People.
Rodando no M900 desde 29/09/2026, depois da correção do IP (5.7).

**Próximos passos naturais:**

1. **Tracking** — manter a identidade de uma pessoa entre frames. Resolve o
   caso de quem para de se mover e faz um clipe corresponder a uma pessoa.
2. **Banco de eventos** (SQLite) — substituir os JSON quando houver busca por
   pessoa e período.
3. **Retenção** — apagar clipes antigos automaticamente.
4. **Reprodução no Records** — clicar num cartão e assistir ao clipe.
5. **Persistir os spots estáticos** — hoje a lista nasce vazia a cada execução,
   então o primeiro clipe falso da noite ainda é gravado.
6. **Iluminação na área da Front** — o maior ganho possível de precisão facial.
   Uma luz acionada por movimento tira a câmera do modo infravermelho e leva o
   rosto de ~44 px cinzentos para algo utilizável (ver 10.5).
7. **Re-ID de animais** — classificador sobre o corpo inteiro do cachorro,
   usando recortes coletados pela própria tela People (ver 10.8).
8. **OpenVINO no M900** — exportar os modelos para OpenVINO INT8 e recuperar a
   velocidade perdida ao sair do PyTorch.

---

## 13. Ícone e atalho

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
Windows aceita desde o Vista. O OpenCV lê e grava PNG mas não `.ico`, e montar
os bytes com `struct.pack` evita uma dependência nova só para isso.

Para mudar o desenho, edite as cores e raios em `gerar_icone.py`, rode
`uv run tools/gerar_icone.py` e depois o `criar_atalho.ps1` de novo (o Windows
guarda ícones em cache; se o antigo continuar aparecendo, reinicie o Explorer).
