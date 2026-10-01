# Python e bibliotecas — guia para quem vem de Java / C#

Este documento cobre **apenas o que é específico de Python** e das bibliotecas
usadas no projeto. Pressupõe que você já programa: não explica o que é uma
classe, um laço ou polimorfismo — explica onde Python diverge do que você
espera vindo de uma linguagem estática.

Todos os exemplos são código real deste projeto.

---

## 1. Ambiente e dependências

| Java / C# | Python (aqui) |
|---|---|
| Maven / Gradle / NuGet | `uv` |
| `pom.xml` / `.csproj` | `pyproject.toml` |
| `~/.m2`, `packages/` | `.venv/` |
| JAR no classpath | pacote instalado no venv |

Python não tem classpath. Ele resolve imports procurando em `sys.path`, e um
**virtualenv** (`.venv/`) é simplesmente um diretório com seu próprio
interpretador e suas próprias bibliotecas. Sem venv, tudo é instalado
globalmente e projetos conflitam.

```bash
uv run jarvis
```

`uv run` executa usando o venv do projeto sem precisar "ativar" nada. É por
isso que `import cv2` funciona nesse comando e falharia com um `python` do
sistema. O `jarvis` depois dele é o comando declarado em `[project.scripts]`
no `pyproject.toml` — o equivalente ao `Main-Class` de um JAR executável.

**Não existe compilação.** Não há `javac` nem build. O erro de digitação numa
linha só aparece quando aquela linha executa — o que torna testes bem mais
importantes do que em Java.

---

## 2. Módulos: arquivo é unidade, não classe

Em Java, a unidade é a classe e o arquivo precisa ter o nome dela. Em Python:

- **Um arquivo `.py` = um módulo.**
- Funções e variáveis podem viver soltas no módulo. Não precisa de classe para
  agrupar nada.
- `motion.py` define `MotionDetector`; `from jarvis import motion` traz o
  módulo, `from jarvis.motion import MotionDetector` traz o nome direto.

```python
from jarvis.clips import BUFFER_DIR, EventRecorder
```

Isso importa uma constante **e** uma classe do mesmo módulo — algo que em Java
exigiria `static import` de uma constante dentro de alguma classe.

### 2.1 Pacote: uma pasta de módulos

Uma pasta com `__init__.py` é um **pacote**, o equivalente a um `package` Java
ou a um `namespace` C#. O código do projeto vive em `src/jarvis/`, então cada
módulo tem nome completo `jarvis.<arquivo>`.

| Arquivo | Papel | Paralelo |
|---|---|---|
| `__init__.py` | roda no primeiro `import jarvis`; aqui define `ROOT` | construtor estático do namespace |
| `__main__.py` | roda com `python -m jarvis` | a classe com `main` |
| `cameras.py` | módulo `jarvis.cameras` | uma classe dentro do package |

Por que `src/` no meio? Sem ele, rodar `python` da raiz do projeto importaria
a pasta `jarvis/` direto do disco, e um erro de instalação passaria
despercebido. Com `src/`, o `jarvis` só é encontrado se estiver **instalado**
no venv — o `uv sync` faz isso em modo editável, apontando para os arquivos em
vez de copiá-los. Ver ARQUITETURA 3.1.

As ferramentas de `tools/` ficam fora do pacote, mas usam ele igual a qualquer
biblioteca: `from jarvis import cameras, capture`.

### 2.2 Imports executam código

Um `import` roda o arquivo inteiro na primeira vez, e isso permite acoplamentos
que em Java não existiriam. O projeto tem um caso, em `jarvis/__init__.py`:

```python
import os
from pathlib import Path

os.environ.setdefault("OPENCV_LOG_LEVEL", "ERROR")
```

O OpenCV lê essa variável **quando o módulo `cv2` é carregado**. Ela só
funciona porque o `__init__.py` do pacote roda antes de qualquer outro módulo
do `jarvis` — e todos eles fazem `import cv2` depois. Se alguém importasse
`cv2` antes de importar o `jarvis`, a variável chegaria tarde e o aviso que ela
silencia voltaria, sem erro nenhum. Em Java, imports são declarações resolvidas
em compilação e nunca teriam esse efeito colateral.

Aqui o prejuízo seria só um aviso a mais no terminal. Numa versão antiga do
projeto a mesma armadilha quebrava o RTSP: `OPENCV_FFMPEG_CAPTURE_OPTIONS` tinha
que ser atribuída antes do `import cv2`, e mover o import para cima — como
qualquer linter sugeriria — desligava o TCP em silêncio (ARQUITETURA 5.8). A
lição: em Python, a **ordem** dos imports pode ser semântica, e nada no arquivo
avisa quando é.

### 2.3 `if __name__ == "__main__"`

```python
if __name__ == "__main__":
    main()
```

`__name__` vale `"__main__"` quando o arquivo é executado diretamente, e o nome
do módulo quando ele é importado. Sem essa guarda, `tools/diagnostico.py`
importar `cameras` para reaproveitar `load_env()` abriria as câmeras e a janela
como efeito colateral.

É o equivalente do `public static void main`, mas por convenção, não por regra
da linguagem.

---

## 3. Tipagem: dinâmica e por comportamento

Não há declaração de tipo obrigatória. A função aceita o que quer que responda
às operações usadas — *duck typing*.

```python
def make_panel(frame, label, height, motion_boxes=(), subjects=(), recording=False,
               reason=""):
```

Nada aqui garante que `frame` seja uma imagem. Se não for, o erro aparece em
runtime, dentro de `cv2.resize`.

**Não existem interfaces.** Você não declara `implements`. Se um objeto tem o
método certo, serve. Não há `instanceof` idiomático para contratos.

**Não há sobrecarga de métodos.** Não dá para ter duas `scan_clip()` com
assinaturas diferentes. Usa-se argumentos com valor padrão:

```python
def scan_clip(clip, camera, started_at, gallery=None):
```

O programa chama sem `gallery` e cada varredura carrega a galeria do disco;
`tools/refazer_rostos.py` passa uma galeria só para todos os clipes.

Type hints (`def f(x: int) -> str`) existem, mas são **anotações ignoradas em
runtime** — documentação verificada por ferramentas externas (mypy), nunca pelo
interpretador.

---

## 4. Sem modificadores de acesso

Não existe `private`, `protected` ou `public`. **Tudo é acessível.**

A convenção é o underscore:

```python
self._errors = deque(maxlen=12)   # "interno, não mexa"
self.frames_read = 0              # parte da API pública
```

(Trecho do `FFmpegCamera`, em `capture.py`.) É só convenção — `cam._errors`
funciona perfeitamente. A cultura de Python confia no programador em vez de
impor barreiras pelo compilador.

O mesmo vale para funções de módulo: `_similarity()` em `faces.py` sinaliza
uso interno, enquanto `cosine()`, no mesmo arquivo, é para quem quiser usar.

---

## 5. Estruturas de dados

### 5.1 Tupla vs lista

| | Tupla `(1, 2)` | Lista `[1, 2]` |
|---|---|---|
| Mutável | não | sim |
| Uso típico | registro de campos fixos | coleção homogênea |

O projeto usa tuplas como registros leves — o papel de um `record` do Java ou
uma `struct` do C#:

```python
(x, y, w, h)              # caixa de movimento
```

As detecções do YOLO começaram como `(x, y, w, h, confidence)` e viraram um
`NamedTuple` quando precisaram de rótulo (5.4).

### 5.2 Desempacotamento

Atribuição múltipla é idiomática e onipresente:

```python
h, w = frame.shape[:2]
x, y, bw, bh = cv2.boundingRect(contour)
width, height, total = _describe(clip)
```

Esse último é o padrão de Python para "retornar vários valores" — não existe
`out` parameter como em C#. `_describe()` faz `return width, height, total`, o
que monta uma tupla, e quem chama a desempacota.

O mesmo mecanismo troca valores sem variável temporária. Em `capture.py`:

```python
frame, self._pending = self._pending, None
```

O lado direito vira uma tupla **antes** de qualquer atribuição; só depois os
dois nomes da esquerda recebem os valores. Pega o frame pendente e zera o campo
numa linha só.

### 5.3 `dict`

É o `HashMap`/`Dictionary`. Em `clips.py` um dict é usado como objeto de
retorno anônimo, e o mesmo dict vira o `.json` do evento:

```python
meta = {
    "camera": self.label,
    "started_at": self.started_at.isoformat(timespec="seconds"),
    "seconds": round(seconds, 1),
    "labels": sorted(self.labels),
    ...
}
```

Vindo de C#, é tentador criar uma classe para isso. Em Python, dict é aceitável
e comum para dados de passagem.

### 5.4 `NamedTuple` — o `record` do Python

```python
class Detection(NamedTuple):
    x: int
    y: int
    w: int
    h: int
    confidence: float
    label: str

    @property
    def is_person(self):
        return self.label == "person"
```

É o equivalente mais próximo de um `record` do Java ou de um `readonly struct`
do C#: imutável, comparável por valor, com campos nomeados. E pode ter métodos
e properties, como qualquer classe.

O detalhe que importa aqui: **continua sendo uma tupla de verdade**. Indexação
(`d[4]`), desempacotamento (`x, y, w, h, c, l = d`) e slicing (`d[:4]`) todos
funcionam. Foi isso que permitiu introduzir o rótulo sem reescrever o código
que já tratava detecções como `(x, y, w, h, conf)`.

Os `x: int` são *type hints* — ignorados em runtime, como descrito na seção 3.
Nada impede guardar uma string ali.

Alternativa: `@dataclass`, que é mutável e não se comporta como tupla. Use
`NamedTuple` quando o valor for um registro imutável; `dataclass` quando for um
objeto com estado que muda.

### 5.5 `set` — com sintaxe de primeira classe

Conjuntos têm literal próprio e operadores, não só métodos:

```python
self.labels = set()
self.labels.update(s.label for s in subjects)

names = ", ".join(sorted({s.label for s in subjects}))
```

`{expressão for x in y}` é uma **set comprehension** — irmã da list
comprehension, mas eliminando duplicatas. A linha acima resolve "quais espécies
distintas estão em cena" sem laço nem `HashSet` explícito.

`days_with_clips` também é um `set`, usado só por pertencimento
(`this_day in self.days_with_clips`), que é O(1) — mesma razão de um `HashSet`
em Java, só sem a cerimônia.

> Nota histórica: aqui havia uma seção sobre `deque(maxlen=...)` como ring
> buffer, usada pela pré-gravação em memória. Essa estrutura deixou de existir
> quando a pré-gravação passou a vir dos segmentos em disco (ARQUITETURA 5.5).
> O `deque(maxlen=12)` que guarda as últimas mensagens de erro do ffmpeg, em
> `capture.py`, é o mesmo recurso: ao passar de 12, a mais antiga sai sozinha.

---

## 6. Slicing

Talvez a sintaxe mais estranha para quem vem de Java. `sequencia[inicio:fim]` —
início incluído, fim **excluído**.

```python
frame.shape[:2]          # os dois primeiros elementos
sys.argv[1:5]            # do índice 1 ao 4
self.segments()[:-1]     # tudo menos o último (o que o ffmpeg ainda escreve)
key[len("CAM_"):-len("_IP")]   # tira prefixo e sufixo
```

Índices negativos contam do fim: `[-1]` é o último elemento. Isso substitui
boa parte das operações de `substring` e `Arrays.copyOfRange`.

---

## 7. Truthiness — diferença perigosa

Em Java, `if` exige `boolean`. Em Python, **qualquer objeto tem valor de
verdade**:

| Falso | Verdadeiro |
|---|---|
| `0`, `0.0`, `""`, `[]`, `()`, `{}`, `None`, `False` | todo o resto |

Por isso o código escreve:

```python
if not motion_boxes:      # lista vazia
if subjects:              # lista não vazia
if not observations:      # nenhum rosto no clipe inteiro
```

**Armadilha:** `if not x` é verdadeiro tanto para lista vazia quanto para
`None`. Quando a distinção importa, teste explicitamente:

```python
if frame is None:         # correto
if not frame:             # ERRADO: um numpy array levanta exceção aqui
```

Esse caso aparece de verdade no projeto. Um array numpy não tem valor de
verdade definido e lança `ValueError` — por isso `FFmpegCamera.read()` devolve
`None` quando não há frame novo, e o laço em `cameras.py` testa
`if frame is None`.

---

## 8. `None` e identidade

`None` é o `null`, mas é um **objeto singleton**. Compara-se com `is`, não `==`:

```python
if self.process is None:
```

`is` compara identidade (mesmo objeto na memória), `==` compara valor. Para
`None` sempre se usa `is`.

---

## 9. f-strings

Interpolação com prefixo `f`:

```python
print(f"  {cam.label}: {cam.stream.wait_ready()}")   # chamada dentro da string
f"{subject.label} {subject.confidence:.2f}"          # duas casas decimais
f"{saved['seconds']}s, {saved['reason']}"            # aspas simples dentro de duplas
```

O que vem depois de `:` é o mesmo mini-formato do `String.format`. É a forma
moderna e preferida — substitui `%` e `.format()`.

---

## 10. Comprehensions

Substituem laços de construção de coleção e o papel de Streams do Java:

```python
streams = [Camera(label, url) for label, url in cameras]
return [box for box, _, class_id in _raw_detections(load_background_model(), frame)
        if class_id == PERSON_CLASS]
```

O segundo, de `people.person_boxes()`, desempacota cada tupla `(caixa,
confiança, classe)` direto no `for`, descarta a confiança com `_` e filtra
pela classe — o que em Java seria um `stream().filter().map().collect()`.

Sem colchetes vira um **generator** — avaliado sob demanda, sem materializar a
lista:

```python
if REQUIRE_MOTION_OVERLAP and not any(
        overlap_area(box, m) for m in motion_boxes):
```

`any()` para no primeiro verdadeiro. Equivale a `stream().anyMatch()`, porém a
sintaxe é da própria linguagem, não de uma API.

---

## 11. `for ... else`

Construção sem equivalente em Java ou C#, e usada de propósito em
`drop_duplicates`:

```python
for other in kept:
    if subject.label == other.label and iou(subject, other) > SAME_SUBJECT_IOU:
        break
else:
    kept.append(subject)
```

**O bloco `else` roda somente se o laço terminou sem `break`.** Traduz
literalmente "se nada bateu, então adicione". A alternativa em Java seria uma
variável de flag booleana.

---

## 12. Decoradores

Sintaxe `@algo` acima de uma função. É açúcar para `f = algo(f)` — a função é
passada para outra função que devolve uma versão modificada. O conceito mais
próximo em C# são atributos, mas decoradores **realmente alteram
comportamento**, não só metadados.

### 12.1 `@property`

```python
@property
def alive(self):
    return self.process is not None and self.process.poll() is None
```

Transforma um método em atributo de leitura: em `capture.py` escreve-se
`if not self.alive:`, sem parênteses. É exatamente a *property* do C#, e a
razão pela qual Python não precisa de getters triviais — um campo público pode
virar property depois sem quebrar quem o usa.

### 12.2 `@lru_cache`

```python
@lru_cache(maxsize=1)
def load_model():
    ensure_model()
    return cv2.dnn.readNetFromONNX(str(MODEL_FILE))
```

Memoriza o retorno por argumentos. Com `maxsize=1` e nenhum argumento, é um
**singleton preguiçoso**: a primeira chamada carrega o modelo, as seguintes
devolvem o mesmo objeto. Substitui todo o boilerplate de singleton do Java.

E justamente por ser singleton, ele não serve para duas threads: `people.py`
tem um segundo, `load_background_model()`, idêntico, para a thread que varre
rostos ter a própria rede (14.2).

---

## 13. Classes

```python
class EventRecorder:
    def __init__(self, camera, directory=CLIP_DIR):
        self.camera = camera
        self.label = camera.label
```

- `__init__` é o inicializador (o objeto já existe quando ele roda).
- **`self` é explícito** e é sempre o primeiro parâmetro de métodos de
  instância. Não existe `this` implícito.
- Atributos são criados por atribuição em `__init__`. Não há declaração de
  campos como em Java.
- Não há construtores sobrecarregados — use valores padrão.

### 13.1 `__slots__`

```python
class _Candidate:
    __slots__ = ("box", "hits", "misses")
```

Por padrão, todo objeto Python carrega um `__dict__` — um dicionário de
atributos — o que permite criar campos novos em tempo de execução. Isso custa
memória e uma busca de hash a cada acesso.

`__slots__` declara os campos de antemão: o objeto passa a usar posições fixas,
como um campo de classe em Java. Fica menor e mais rápido, e atribuir um
atributo não declarado vira `AttributeError` em vez de funcionar silenciosamente.

Vale a pena quando há muitas instâncias pequenas e efêmeras — exatamente o caso
dos candidatos a blob, criados e descartados a cada frame.

### 13.2 Armadilha: argumento padrão avaliado uma vez só

O valor padrão é avaliado **na definição da função**, não a cada chamada. A
forma famosa dessa armadilha envolve listas, mas ela morde de um jeito mais
sutil também. Este bug apareceu de verdade em `faces.py`:

```python
GALLERY_FILE = Path("faces/gallery.json")

class Gallery:
    def __init__(self, path=GALLERY_FILE):   # ERRADO
        ...
```

O padrão **congela** o valor que `GALLERY_FILE` tinha quando a classe foi
definida. Trocar `faces.GALLERY_FILE` depois — num teste, por exemplo — não
tem efeito nenhum, e o objeto continua lendo o arquivo antigo, em silêncio.

A correção é ler o global em tempo de execução:

```python
    def __init__(self, path=None):
        self.path = Path(path or GALLERY_FILE)
```

Em Java o equivalente seria um valor default capturado numa constante estática
inicializada uma vez — só que em Python qualquer expressão pode estar ali, o que
torna o efeito bem menos óbvio.

### 13.3 Armadilha: argumento padrão mutável

O valor padrão é avaliado **uma única vez**, na definição da função. Isto é um
bug clássico:

```python
def f(boxes=[]):     # PERIGO: a mesma lista em todas as chamadas
```

Por isso o projeto usa tupla vazia, que é imutável:

```python
def make_panel(frame, label, height, motion_boxes=(), subjects=(), recording=False,
               reason=""):
```

---

## 14. GIL — por que threads não paralelizam

O CPython tem o *Global Interpreter Lock*: **apenas uma thread executa bytecode
Python por vez**. Threads não usam múltiplos núcleos para código Python puro.

Isso soa fatal para um projeto de vídeo, mas não é, porque as bibliotecas
liberam o GIL enquanto executam código nativo:

- Ler o pipe do ffmpeg (`process.stdout.read()`) libera enquanto espera.
- Operações do OpenCV e do numpy liberam durante o processamento.
- A inferência do YOLO (`net.forward()`, em C++) libera.

Ou seja, o trabalho pesado **é** paralelo; o Python só orquestra. Quando é
preciso paralelismo real de código Python, usa-se `multiprocessing` (processos
separados, cada um com seu interpretador) — não threads.

### 14.1 Threads valem a pena para subprocessos

O GIL impede paralelismo de *bytecode Python*, mas não atrapalha em nada
esperar por um processo externo. A montagem do clipe usa isso:

```python
job = threading.Thread(target=_assemble,
                       args=(self.camera, self.started_at, ended_at,
                             destination, set(self.labels)))
job.start()
```

`_assemble` dorme até o último segmento fechar e então chama
`subprocess.run(ffmpeg...)`. O trabalho real acontece noutro processo, com seus
próprios núcleos; a thread apenas bloqueia esperando. É o caso em que threading
em Python funciona exatamente como você esperaria de Java ou C#.

**Threads não-daemon.** Por padrão o interpretador **espera** as threads
terminarem antes de encerrar. É desejável aqui (não queremos um clipe pela
metade). Em Java é igual: uma `Thread` criada a partir do `main` é não-daemon,
e a JVM espera por ela. Em C# uma `Thread` também segura o processo, mas uma
`Task` não — ela roda no pool, cujas threads são de fundo. Ainda assim chamamos
`wait_for_jobs()` explicitamente na saída, para poder avisar o usuário.

### 14.2 Soltar o GIL não torna nada *thread-safe*

O outro lado da lista acima: se o OpenCV solta o GIL dentro do `forward()`, duas
threads chamando `forward()` **na mesma rede** rodam de verdade ao mesmo tempo.
E um `cv2.dnn.Net` guarda buffers internos entre chamadas — não foi feito para
isso.

Aconteceu no projeto: a varredura de rostos, numa thread de fundo, passou a
usar o YOLO pela mesma `load_model()` do laço ao vivo. O programa caiu com
`buf.shape() == m.shape()` logo depois de um evento. A correção foi uma segunda
rede para a thread de fundo e um `threading.Lock` para as varreduras ficarem em
fila (ARQUITETURA 10.9):

```python
_SCAN_LOCK = threading.Lock()

def scan_clip(clip, camera, started_at, gallery=None):
    with _SCAN_LOCK:
        return _scan_clip(clip, camera, started_at, gallery)
```

`with lock:` é o `lock (obj) { }` do C# e o `synchronized` do Java: adquire na
entrada e solta na saída, inclusive se houver exceção. A regra de bolso é a
mesma das duas linguagens — objeto nativo compartilhado entre threads precisa
de dono ou de trava. O GIL não é essa trava.

## 15. numpy — o tipo mais importante do projeto

Uma imagem **é** um `numpy.ndarray`. Não existe classe `Image`.

```python
h, w = frame.shape[:2]
```

### 15.1 `shape` é (linhas, colunas, canais)

**Altura vem antes de largura.** Um frame 1080p tem shape `(1080, 1920, 3)`.
Essa inversão em relação ao `(width, height)` costumeiro é fonte constante de
bugs.

E o `dtype` é `uint8`: valores 0–255 que **dão a volta em vez de saturar**.
Numa operação entre arrays, `250 + 10` resulta em `4`, silenciosamente — não há
exceção nem clamp. (Em escalares isolados o numpy 2.x emite um
`RuntimeWarning`, mas em arrays, que é o caso real, o estouro é mudo.)

Consequência prática: para clarear uma imagem, somar direto corrompe os pixels
mais claros. Use `cv2.add`, que satura em 255.

### 15.2 Indexação é [linha, coluna]

```python
crop = frame[y:y+h, x:x+w]
```

Primeiro o eixo vertical, depois o horizontal — o oposto de coordenadas
cartesianas.

### 15.3 Slices são *views*, não cópias

Esta é a diferença conceitual mais importante em relação a arrays de Java:

```python
crop = frame[100:200, 100:200]
crop[:] = 0                      # ALTERA frame também
```

O slice compartilha a mesma memória. É ótimo para performance (recortar não
copia nada) e perigoso se você esperava valor. Para copiar de verdade:
`frame[100:200, 100:200].copy()`.

### 15.4 Operações vetorizadas

Laço `for` sobre pixels em Python é ordens de magnitude mais lento. Tudo é
expresso como operação sobre o array inteiro, executada em C:

```python
np.zeros((height, width, 3), dtype=np.uint8)
np.hstack(panels)
```

---

## 16. OpenCV (`cv2`)

É uma biblioteca C++ com binding gerado. As consequências práticas:

**A API não é pythônica.** Nomes em `CAPS`, constantes soltas no módulo
(`cv2.MORPH_OPEN`), funções que devolvem tuplas:

```python
_, mask = cv2.threshold(mask, 200, 255, cv2.THRESH_BINARY)
contours, _ = cv2.findContours(...)
```

O `_` é convenção para "valor descartado".

**Cores são BGR, não RGB.**

```python
GREEN = (0, 255, 0)
RED = (0, 0, 255)      # parece azul em RGB
```

**A documentação é de C++.** Ao procurar `cv::VideoCapture`, traduza mentalmente
para `cv2.VideoCapture`; os parâmetros são os mesmos.

**Erros costumam ser silenciosos.** Nada de exceções: `cv2.imread` de um arquivo
inexistente devolve `None`, e `cv2.imwrite` devolve `False` em vez de reclamar.
Em Java você receberia uma `IOException`. Aqui é preciso conferir o retorno —
`ui.py` faz isso ao carregar miniaturas, caindo para um cartão cinza quando a
imagem não abre.

**`waitKey` faz duas coisas:** espera tecla **e** processa a fila de eventos da
janela. Sem ele a janela nunca redesenha. É a peça que substitui o event loop
que em WinForms/Swing seria implícito.

---

## 17. Rede neural sem PyTorch: `cv2.dnn`

O YOLO roda pelo módulo `dnn` do OpenCV, sobre o arquivo `.onnx` — o formato
padrão para levar uma rede treinada de uma biblioteca para outra. O PyTorch
saiu do projeto por causa do Smart App Control (ARQUITETURA 7.11), e com ele a
biblioteca `ultralytics`, que escondia todo o pré e pós-processamento. Agora
ele é explícito em `people._raw_detections()`, e cada passo ensina algo de
numpy.

### 17.1 Entrada: um "blob"

```python
canvas, scale = _letterbox(frame)
blob = cv2.dnn.blobFromImage(canvas, 1 / 255.0, (IMG_SIZE, IMG_SIZE),
                             swapRB=True, crop=False)
net.setInput(blob)
```

A rede espera um array `(1, 3, 640, 640)` de floats entre 0 e 1, em RGB:
1 imagem, 3 canais, altura, largura. O frame do OpenCV é `(540, 960, 3)` de
inteiros 0–255 em BGR. O `blobFromImage` faz a conversão inteira: escala
(`1 / 255.0`), troca BGR→RGB (`swapRB=True`) e reordena os eixos para "canais
primeiro". O `_letterbox` antes encaixa o frame num quadrado sem distorcer, e
devolve a escala para desfazer depois.

### 17.2 Saída: transpor para iterar

```python
predictions = net.forward()[0].T
```

O `forward()` devolve `(1, 84, 8400)`: 8400 caixas candidatas, cada uma
descrita por 84 números (4 de geometria + 80 pontuações, uma por classe do
COCO). Só que os 84 números de uma caixa estão numa **coluna**. O `[0]` tira a
dimensão de lote e o `.T` (transposta) vira a matriz para `(8400, 84)`: agora
cada **linha** é uma caixa, e um `for row in predictions` percorre caixas.

Em Java isso seria um `float[84][8400]` e um laço de índice trocado. Aqui o
`.T` não copia nada: é uma *view* (15.3) que lê a mesma memória em outra ordem.

### 17.3 Classe vencedora e formato da caixa

```python
class_scores = row[4:]
class_id = int(np.argmax(class_scores))
cx, cy, width, height = row[:4]
boxes.append([int((cx - width / 2) / scale), int((cy - height / 2) / scale),
              int(width / scale), int(height / scale)])
```

`np.argmax` devolve o **índice** do maior valor — a classe mais provável. A
geometria vem como **centro + tamanho** (`cx, cy, w, h`), enquanto o projeto
inteiro usa **canto + tamanho** (`x, y, w, h`); a conversão é tirar metade da
largura e da altura. Dividir por `scale` desfaz o encaixe do letterbox e devolve
a caixa em pixels do frame original. Vale conferir sempre qual convenção uma
API usa: as três (cantos, centro, canto + tamanho) são comuns.

### 17.4 Uma pessoa, várias caixas: NMS

A rede costuma propor várias caixas quase iguais para o mesmo objeto.
`cv2.dnn.NMSBoxes` (*non-maximum suppression*) fica com a de maior confiança e
descarta as que se sobrepõem a ela além de `NMS_THRESHOLD`. Devolve só os
índices que sobreviveram:

```python
keep = cv2.dnn.NMSBoxes(boxes, scores, CONFIDENCE, NMS_THRESHOLD)
return [(boxes[i], scores[i], classes[i]) for i in np.array(keep).ravel()]
```

O `np.array(keep).ravel()` está ali porque, conforme a versão do OpenCV, `keep`
vem como lista simples ou como coluna `[[0], [3]]`; o `ravel()` achata as duas
formas para `[0, 3]`.

### 17.5 `zip`

`zip` percorre duas sequências em paralelo — em `tools/gerar_icone.py`, cada
imagem com o PNG correspondente:

```python
for image, blob in zip(images, blobs):
```

É o que em Java exigiria um laço de índice sobre duas listas do mesmo tamanho.

---

## 18. `pathlib` em vez de concatenar strings

```python
folder = self.directory / self.label / stamp.strftime("%Y-%m-%d")
folder.mkdir(parents=True, exist_ok=True)
self.base = folder / stamp.strftime("%H-%M-%S")
self.base.with_suffix(".jpg")
```

O operador `/` é sobrecarregado para juntar caminhos, e `with_suffix()` troca a
extensão — é assim que os três arquivos de um evento compartilham o nome base.
`Path` é o equivalente de `java.nio.file.Path`, e substitui completamente a
manipulação de strings com `os.path.join`.

Um detalhe: `Path` não é string. Ao passar para uma API C++ como o
`cv2.imwrite`, ou para o `subprocess`, é preciso `str(path)`.

## 19. `subprocess`: lista ou string, e por que importa no Windows

A regra geral é passar uma **lista** de argumentos, nunca uma string: evita
problemas de quoting e de injeção, já que não há shell envolvido. A montagem
de clipes em `clips.py`:

```python
subprocess.run(
    [ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error",
     "-f", "concat", "-safe", "0", "-i", str(listing),
     "-c", "copy", "-movflags", "+faststart", str(destination)],
    check=True, capture_output=True)
```

`check=True` transforma código de saída diferente de zero em exceção
(`CalledProcessError`); sem ele, uma falha do ffmpeg passaria em silêncio.
`capture_output=True` guarda stdout e stderr em vez de jogá-los no terminal.

No Windows, porém, o sistema operacional não aceita uma lista: o `CreateProcess`
recebe **uma única linha de comando**. O `subprocess` então converte sua lista
com `list2cmdline()`, que envolve em aspas todo argumento contendo espaço.

Isso quebra programas cuja sintaxe não segue a convenção padrão — o
`explorer.exe` é o caso clássico:

```python
subprocess.list2cmdline(["explorer", "/select,D:\\Personal Projects\\a.mp4"])
# explorer "/select,D:\Personal Projects\a.mp4"     <- opcao dentro das aspas
```

O Explorer precisa de `/select,"caminho"`, com aspas apenas no caminho. Para
controlar o formato exato, passe **a string pronta**, que no Windows vai direta
ao `CreateProcess`:

```python
subprocess.Popen(f'explorer /select,"{target}"')
```

Vindo de Java, o análogo é a diferença entre `ProcessBuilder(List<String>)` e
`Runtime.exec(String)` — com a mesma armadilha de quoting no Windows.

Regra prática: **lista por padrão; string só quando o programa de destino tem
sintaxe própria** que o quoting automático estragaria.

## 20. Ler binário de um pipe e virar array sem copiar

A captura lê frames crus da saída do ffmpeg, e a varredura de rostos faz o
mesmo com o clipe (`faces._sampled_frames`). O padrão vale conhecer:

```python
data = self.process.stdout.read(self.frame_bytes)
frame = np.frombuffer(data, np.uint8).reshape(HEIGHT, WIDTH, 3).copy()
```

Três pontos:

**`read(n)` num pipe binário devolve exatamente `n` bytes** ou menos só no fim
do stream. Como cada frame tem tamanho fixo (`960*540*3`), pedir esse número
sincroniza o leitor com o produtor sem precisar de cabeçalho ou delimitador.

**`np.frombuffer` não copia nada.** Ele cria um array que *aponta* para os bytes
já em memória — diferente de `np.array(data)`, que copiaria. Para 1,5 MB por
frame a 10 fps, a diferença importa.

**Justamente por não copiar, o array é somente leitura**, porque `bytes` é
imutável em Python. Qualquer tentativa de desenhar nele levanta exceção, e é por
isso que há um `.copy()` explícito no fim. É o inverso da intuição de Java:
aqui o "cast" barato vem com imutabilidade, e você paga a cópia só quando
precisa escrever.

## 21. Memória e recursos externos

Python usa contagem de referências **mais** um coletor para ciclos. Objetos
morrem determinística e imediatamente quando a última referência some — mais
previsível que o GC da JVM.

Mas recursos externos não são liberados sozinhos. O processo ffmpeg de cada
câmera tem que ser encerrado à mão:

```python
self.process.terminate()
self.process.wait(timeout=5)
```

Sem isso, o ffmpeg sobreviveria ao Python e continuaria ocupando a única sessão
RTSP da câmera — o que impediria a próxima execução de conectar. O `except`
cai para `kill()` se o processo ignorar o `terminate()`.

O `with` (context manager) é o equivalente de `try-with-resources` e seria o
idiomático. `subprocess.Popen` até o implementa, mas aqui o processo tem que
viver por toda a execução do programa, não por um bloco — então a liberação
fica explícita no encerramento.

Quando o recurso vive só durante uma função, o projeto usa `try`/`finally`.
Em `faces._sampled_frames`, que é um *generator* (`yield`), o `finally` roda
mesmo se quem consome parar no meio:

```python
try:
    while True:
        ...
        yield frame
finally:
    process.stdout.close()
    process.kill()
    process.wait()
```

E `tools/diagnostico.py` usa `with tempfile.TemporaryDirectory() as pasta:`:
a pasta temporária é apagada ao sair do bloco, com ou sem erro — o
`try-with-resources` de um diretório.

---

## 22. Diferenças finais e armadilhas

### 22.1 `//` arredonda para baixo, não trunca

A diferença mais silenciosa desta lista. Python tem dois operadores de divisão:
`/` sempre devolve `float`, e `//` devolve inteiro **arredondado para menos
infinito**. Java e C# truncam em direção ao zero.

```python
-12 // 54    # Python: -1
(-12) / 54   # Java:    0
```

O projeto tira proveito disso em `ui.py`, para saber quantas linhas de cartões
existem — divisão **arredondando para cima**, só com inteiros:

```python
total_rows = -(-len(self.entries) // columns)
```

Com 11 cartões em 5 colunas: `-11 // 5` dá `-3` (para baixo, rumo a menos
infinito), e negar de volta dá `3` linhas. Em Java, `-11 / 5` dá `-2` e o
truque não funciona; lá se usa `Math.ceilDiv` ou `(a + b - 1) / b`.

Para truncar como em Java, use `int(a / b)`. Para o resto, `%` segue o sinal do
divisor em Python (`-1 % 5 == 4`), ao contrário de Java (`-1 % 5 == -1`).

### 22.2 Armadilhas resumidas

| Armadilha | Detalhe |
|---|---|
| `//` | Arredonda para baixo; Java trunca para zero. |
| `if not array` | Levanta exceção em numpy. Use `is None`. |
| `shape` | É `(altura, largura)`, não `(largura, altura)`. |
| Slice numpy | É *view*; escrever nele altera o original. |
| Padrão mutável | `def f(x=[])` compartilha a lista entre chamadas. |
| Padrão congelado | `def f(path=CONSTANTE)` lê a constante uma vez só (13.2). |
| Cores | BGR, não RGB. |
| `==` vs `is` | `is` só para `None` e singletons. |
| Ordem de import | Pode ter efeito colateral (`OPENCV_LOG_LEVEL`, 2.2). |
| Falha do OpenCV | Silenciosa: `imread` devolve `None`, `imwrite` devolve `False`. |
| Threads | Não paralelizam código Python puro (GIL), mas objetos nativos compartilhados correm risco de verdade (14.2). |
| Sem compilação | Erro de digitação só aparece ao executar aquela linha. |
