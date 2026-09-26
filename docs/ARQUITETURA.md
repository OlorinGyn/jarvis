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
   ┌───────────┐
   │ cameras.py│  captura, mede FPS, desenha, orquestra
   └─────┬─────┘
         │ frame (numpy array 1080x1920x3)
         ├──────────────────────────────────────┐
         ▼                                      │
   ┌───────────┐                                │
   │ motion.py │  MOG2: algo mudou na cena?     │
   └─────┬─────┘                                │
         │ caixas de movimento                  │
         ▼                                      │
   ┌───────────┐                                │
   │ people.py │  YOLO11: pessoa ou animal?     │
   └─────┬─────┘                                │
         │ Detection(x,y,w,h,conf,label)        │
         ▼                                      ▼
   ┌───────────────────────────────────────────────┐
   │ clips.py   vídeo H.264 + miniatura + JSON     │
   └─────────────────────┬─────────────────────────┘
                         │ metadados
                         ▼
                   ┌───────────┐
                   │   ui.py   │  menu lateral, tela Records
                   └───────────┘
```

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
├── cameras.py        aplicação principal (loop, exibição, orquestração)
├── motion.py         camada 1: detecção de movimento
├── people.py         camada 2: detecção de pessoas e animais
├── clips.py          camada 3: gravação, miniatura, compressão, metadados
├── ui.py             menu lateral e tela de gravações
├── geometry.py       tipo Detection e utilitários de caixas (IoU)
├── probe_rtsp.py     diagnóstico de RTSP (DESCRIBE → SETUP → PLAY)
├── .env              credenciais das câmeras (NÃO versionado)
├── yolo11s.pt        pesos do modelo (baixado automaticamente, não versionado)
├── clips/            vídeos gravados (não versionado)
└── docs/
    ├── ARQUITETURA.md
    └── PYTHON.md
```

### 3.1 O projeto não é um pacote

`pyproject.toml` declara:

```toml
[tool.uv]
package = false
```

O `uv init` originalmente configurou o projeto como pacote instalável
(`[build-system]` + `[project.scripts]`). Consequência: **todo `uv run`
reconstruía e reinstalava o `jarvis`**, imprimindo `Built jarvis`,
`Uninstalled 1 package`, `Installing wheels` e um aviso de hardlink — o cache
do `uv` fica no C: e o projeto no D:, e hardlink não atravessa volumes.

Nada disso era necessário: os scripts rodam direto (`uv run cameras.py`), sem
precisar do projeto instalado. Com `package = false` o `uv` apenas garante as
dependências, e a saída fica limpa.

A pasta `src/jarvis/` é resto do andaime do `uv init` e não é usada.

## 4. Configuração — `.env`

Uma câmera = três linhas. O nome do rótulo vira o nome exibido e a pasta dos
clipes.

```
CAM_FRONT_IP=192.168.0.10
CAM_FRONT_USER=<usuario-da-conta-da-camera>
CAM_FRONT_PASSWORD=<senha-da-conta-da-camera>
```

`build_camera_list()` varre as chaves procurando o padrão `CAM_<X>_IP` e monta
a URL RTSP. Adicionar uma terceira câmera não exige mudança de código.

A senha passa por `urllib.parse.quote()` porque caracteres como `@ : / #` são
estruturais numa URL e quebrariam o parsing.

---

## 5. Camada de captura — `cameras.py`

### 5.1 A linha mais frágil do projeto

```python
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

import cv2
```

**Essa atribuição precisa vir ANTES do `import cv2`.** O FFmpeg lê essa
variável de ambiente no carregamento do módulo. Se alguém "organizar" os
imports e mover o `import cv2` para cima, a configuração é silenciosamente
perdida — sem erro, sem aviso.

O efeito é o RTSP cair para UDP, e câmeras Tapo perdem frames e derrubam a
conexão em UDP. O sintoma aparece minutos depois, não na hora.

### 5.2 Timeouts

O padrão do FFmpeg é travar 30 segundos antes de desistir. Com duas câmeras,
um erro de credencial custava um minuto de espera. Reduzido para 5 s:

```python
cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000
cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000
```

### 5.3 `CAP_PROP_BUFFERSIZE = 1`

Sem isso, o OpenCV enfileira frames. Se o processamento fica mais lento que o
stream, a fila cresce e a imagem exibida atrasa progressivamente. Com buffer 1,
frames antigos são descartados e vemos sempre o mais recente.

### 5.4 Estimativa de FPS (e um bug real)

Os clipes precisam saber a taxa real de frames, senão tocam na velocidade
errada.

A primeira versão media o intervalo entre leituras consecutivas. **Resultado em
produção: 63 fps para uma câmera de 15 fps** — o clipe tocaria 4× acelerado.

Causa: RTSP entrega em rajadas. Quando já existe frame no buffer, `read()`
retorna instantaneamente, e esses intervalos quase-zero implicam FPS altíssimo.

Correção — média sobre a execução inteira em vez de intervalos individuais:

```python
self.fps = min(max(self._reads / elapsed, 1.0), 60.0)
```

Medição após a correção: **16,6 fps**. Correto.

O cálculo só começa após 2 segundos e 30 frames, para não usar a rajada
inicial de frames em buffer como amostra.

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
5. **Descarta o frame se mais de 50% "mudou".** Isso não é um objeto se
   movendo: é nuvem, sol ou a câmera entrando em modo noturno.
6. **Abertura e dilatação.** A abertura apaga pontos isolados; a dilatação
   cresce o que sobrou, unindo os fragmentos de uma mesma pessoa num só blob.
   É também por isso que a caixa fica um pouco maior que o objeto.
7. **Contornos + `boundingRect`.** Blobs com área menor que `MIN_AREA` são
   ignorados. As coordenadas voltam para a escala do frame original.
8. **Confirmação temporal.** Ver 6.3 — nada é reportado antes de persistir.

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

### 7.9 Um modelo, várias câmeras

`@lru_cache(maxsize=1)` em `load_model()` garante uma única instância do YOLO
na memória. É o oposto do `MotionDetector`:

| Componente | Estado | Instâncias |
|---|---|---|
| `MotionDetector` | modelo de fundo daquela câmera | **uma por câmera** |
| `PersonDetector` | só throttle e último resultado | uma por câmera |
| Modelo YOLO | nenhum | **uma compartilhada** |

---

## 8. Camada de gravação — `clips.py`

### 8.1 Pré-gravação (o conceito central)

Quando o YOLO confirma uma pessoa, a parte interessante — ela se aproximando —
já passou. Um clipe que começa nesse instante perde o evento.

Por isso `clips.py` mantém os **últimos 30 frames em memória o tempo todo**.
Ao detectar alguém, esses frames são escritos no arquivo **primeiro**, e o
clipe começa ~2 segundos antes da detecção.

```python
self.buffer = deque(maxlen=PRE_FRAMES)
```

`deque` com `maxlen` é um *ring buffer*: ao encher, o append descarta o mais
antigo. A memória nunca cresce.

**Custo de memória:** cada frame 1080p ocupa ~5,9 MB (1920 × 1080 × 3 bytes).
30 frames ≈ **180 MB por câmera**. É a constante a reduzir se a RAM apertar no
M900.

**Validação:** no teste, cada frame recebeu um brilho igual ao seu número, a
pessoa apareceu no frame 50, e o arquivo lido de volta começava no frame 20 —
30 frames de pré-gravação reais.

### 8.2 Quando o clipe termina

Não no instante em que a pessoa some. A detecção oscila (alguém vira de lado,
a confiança cai por um frame) e parar na hora fragmentaria um evento em dezenas
de arquivos.

- `POST_SECONDS = 5.0` — continua gravando por 5 s sem ninguém à vista.
- `MAX_SECONDS = 60.0` — teto rígido, para um clipe nunca crescer sem controle.

### 8.3 Três arquivos por evento

Cada gravação produz três arquivos com o mesmo nome base:

```
19-17-30.mp4     vídeo já em H.264
19-17-30.jpg     o primeiro frame em que o sujeito apareceu
19-17-30.json    metadados
```

O `.jpg` é gravado no instante do `_start()`, ou seja, **é exatamente o frame
que disparou a gravação** — com as caixas desenhadas e reduzido para
`THUMB_WIDTH = 480` px (~20 KB). É o que a tela Records usa.

O `.json` existe para que a tela Records **nunca precise abrir um vídeo**:

```json
{
  "camera": "Front",
  "started_at": "2026-09-26T19:52:06",
  "time": "19:52:06",
  "seconds": 6.9,
  "frames": 134,
  "fps": 15.0,
  "labels": ["dog", "person"],
  "best_confidence": 0.88,
  "video": "19-52-06.mp4",
  "thumbnail": "19-52-06.jpg",
  "reason": "subject left"
}
```

`labels` acumula tudo que apareceu durante o clipe, não só no primeiro frame.

Um JSON por clipe é deliberadamente simples e inspecionável — o passo natural
depois é SQLite, quando houver busca por pessoa e por período.

### 8.4 Compressão

O `VideoWriter` do OpenCV grava em `mp4v` (MPEG-4 Parte 2), que é ineficiente.
`avc1` (H.264) **não funciona** aqui: falta a DLL do OpenH264.

A solução foi o pacote `imageio-ffmpeg`, que empacota um binário estático do
FFmpeg 7.1 com `libx264`. O fluxo:

1. Grava em `<nome>.raw.mp4` com `mp4v` (rápido, sem travar o loop).
2. Ao fechar o clipe, uma **thread** recodifica para H.264 e apaga o raw.

```
ffmpeg -i raw.mp4 -c:v libx264 -preset veryfast -crf 26 -movflags +faststart
```

**Medido: 1017 KB → 336 KB, 3,0× menor**, com o vídeo final reproduzindo os
mesmos 64 frames.

A recodificação roda em thread porque levaria 1–3 s e congelaria a imagem ao
vivo. Aqui o GIL não estorva: o trabalho está num **subprocesso**, então a
thread só espera. As threads não são daemon, e `wait_for_compression()` é
chamado na saída para nenhum arquivo ficar pela metade.

`CRF = 26` controla a qualidade (menor = melhor e maior); `PRESET = "veryfast"`
troca compressão por CPU. No M900 vale medir e possivelmente subir o preset.

### 8.5 `release()` é obrigatório

Um MP4 precisa do índice escrito no final. Encerrar o processo sem chamar
`writer.release()` deixa o arquivo **inutilizável**. Por isso a saída do
programa fecha qualquer clipe aberto antes de terminar.

### 8.6 O vídeo recebe o frame limpo

O **vídeo** é gravado antes de qualquer caixa ser desenhada, porque a camada de
rosto vai reanalisar esse material e retângulos queimados o corromperiam.

A **miniatura** é a exceção: nela as caixas são desenhadas de propósito, já que
sua função é ser folheada por um humano na tela Records.

### 8.7 Armazenamento

Com `mp4v` eram ~1 MB/s. Com H.264 a 3× menos, cerca de **0,33 MB/s**:

| Atividade diária | Por dia | Por ano |
|---|---|---|
| 5 min | ~95 MB | ~35 GB |

Os 512 GB do M900 comportam anos disso, mas retenção automática segue sendo um
próximo passo.

---

## 9. Interface — `ui.py`

A janela inteira é uma única imagem numpy, montada assim:

```
┌──────────┬────────────────────────────────────┐
│ J.A.R.V. │                                    │
│          │   conteúdo: Live  ou  Records      │
│ ▸ Live   │                                    │
│   Records│                                    │
└──────────┴────────────────────────────────────┘
  190 px            largura dos painéis
```

O HighGUI do OpenCV **não tem widgets**: não existe botão, lista ou scroll.
Tudo é retângulo e texto desenhados à mão, e o clique chega por
`cv2.setMouseCallback`. A classe `Sidebar` guarda qual tela está ativa e
converte a coordenada do clique em índice de item:

```python
index = (y - ITEM_TOP) // ITEM_HEIGHT
```

### 9.1 Tela Live

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

### 9.2 Tela Records

Mostra as gravações **de hoje**, lendo apenas os `.json` e os `.jpg`. Nenhum
vídeo é aberto ou decodificado, o que era o requisito.

Dois cuidados de desempenho, porque isso redesenha a 15 fps:

- **Cache de miniaturas.** Decodificar JPEG a cada frame seria absurdo; as
  imagens já redimensionadas ficam num dicionário indexado por caminho e
  tamanho.
- **Rescan periódico.** A pasta só é relida a cada `RESCAN_SECONDS = 2.0`, não
  a cada frame.

O grid é adaptativo: `CARD_COLUMNS = 5` e o número de linhas sai da altura
disponível. Se houver mais gravações do que cabem, aparece `+N mais` no canto —
paginação é um próximo passo.

**As câmeras continuam sendo processadas enquanto a tela Records está aberta.**
Detecção e gravação não param por causa da navegação; só a imagem exibida muda.

### 9.3 Limitação: `cv2.putText` é só ASCII

As fontes Hershey do OpenCV não têm acentuação. Escrever `"gravação"` renderiza
caracteres quebrados, e por isso todo texto da interface está **sem acento** de
propósito ("gravacao", "Nenhuma gravacao hoje").

Acentos exigiriam desenhar texto com PIL (Pillow, já presente como dependência
do ultralytics) e converter para numpy — possível, mas é uma camada extra.

### 9.4 Fechar a janela no X

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

## 10. Restrição importante das câmeras Tapo

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
uv run probe_rtsp.py <ip> <usuario> <senha> stream1
```

---

## 11. Estado atual e próximos passos

**Funcionando:** captura RTSP, movimento com confirmação temporal, detecção de
pessoas e animais, supressão de cenário estático, gravação com pré-roll em
H.264, miniatura e metadados por evento, menu lateral com Live e Records.

**Próximos passos naturais:**

1. **Tracking** — manter a identidade de uma pessoa entre frames. Resolve o
   caso de quem para de se mover e faz um clipe corresponder a uma pessoa.
2. **Banco de eventos** (SQLite) — substituir os JSON quando houver busca por
   pessoa e período.
3. **Retenção** — apagar clipes antigos automaticamente.
4. **Reprodução no Records** — clicar num cartão e assistir ao clipe.
5. **Persistir os spots estáticos** — hoje a lista nasce vazia a cada execução,
   então o primeiro clipe falso da noite ainda é gravado.
6. **Reconhecimento facial** — SCRFD + ArcFace sobre as caixas de pessoa.
   Não serve para animais (ver 7.3); identidade de pets seria outra camada.
7. **Deploy no M900** — exportar o modelo para OpenVINO INT8.
