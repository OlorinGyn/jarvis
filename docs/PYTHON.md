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
uv run cameras.py
```

`uv run` executa usando o venv do projeto sem precisar "ativar" nada. É por
isso que `import cv2` funciona nesse comando e falharia com um `python` do
sistema.

**Não existe compilação.** Não há `javac` nem build. O erro de digitação numa
linha só aparece quando aquela linha executa — o que torna testes bem mais
importantes do que em Java.

---

## 2. Módulos: arquivo é unidade, não classe

Em Java, a unidade é a classe e o arquivo precisa ter o nome dela. Em Python:

- **Um arquivo `.py` = um módulo.**
- Funções e variáveis podem viver soltas no módulo. Não precisa de classe para
  agrupar nada.
- `motion.py` define `MotionDetector`; `import motion` traz o módulo,
  `from motion import MotionDetector` traz o nome direto.

```python
from clips import ClipRecorder, DEFAULT_FPS
```

Isso importa uma classe **e** uma constante do mesmo módulo — algo que em Java
exigiria `static import` de uma constante dentro de alguma classe.

### 2.1 Imports executam código

Um `import` roda o arquivo inteiro na primeira vez. É por isso que esta ordem
importa e é frágil:

```python
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

import cv2
```

O FFmpeg lê essa variável **durante o carregamento do módulo**. Mover o import
para cima quebra silenciosamente. Em Java, imports são declarações resolvidas
em compilação e nunca teriam esse efeito colateral.

### 2.2 `if __name__ == "__main__"`

```python
if __name__ == "__main__":
    main()
```

`__name__` vale `"__main__"` quando o arquivo é executado diretamente, e o nome
do módulo quando ele é importado. Sem essa guarda, importar `cameras` para
reaproveitar `load_env()` abriria as câmeras e a janela como efeito colateral.

É o equivalente do `public static void main`, mas por convenção, não por regra
da linguagem.

---

## 3. Tipagem: dinâmica e por comportamento

Não há declaração de tipo obrigatória. A função aceita o que quer que responda
às operações usadas — *duck typing*.

```python
def make_panel(frame, label, height, motion_boxes=(), people=(), recording=False):
```

Nada aqui garante que `frame` seja uma imagem. Se não for, o erro aparece em
runtime, dentro de `cv2.resize`.

**Não existem interfaces.** Você não declara `implements`. Se um objeto tem o
método certo, serve. Não há `instanceof` idiomático para contratos.

**Não há sobrecarga de métodos.** Não dá para ter dois `detect()` com
assinaturas diferentes. Usa-se argumentos com valor padrão:

```python
def update(self, frame, people, fps=DEFAULT_FPS):
```

Type hints (`def f(x: int) -> str`) existem, mas são **anotações ignoradas em
runtime** — documentação verificada por ferramentas externas (mypy), nunca pelo
interpretador.

---

## 4. Sem modificadores de acesso

Não existe `private`, `protected` ou `public`. **Tudo é acessível.**

A convenção é o underscore:

```python
self._reads = 0          # "interno, não mexa"
self.fps = DEFAULT_FPS   # parte da API pública
```

É só convenção — `cam._reads` funciona perfeitamente. A cultura de Python
confia no programador em vez de impor barreiras pelo compilador.

O mesmo vale para funções de módulo: `_overlap_area()` em `people.py` sinaliza
uso interno.

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
(x, y, w, h, confidence)  # caixa de pessoa
```

### 5.2 Desempacotamento

Atribuição múltipla é idiomática e onipresente:

```python
h, w = frame.shape[:2]
x, y, bw, bh = cv2.boundingRect(contour)
ok, frame = self.cap.read()
```

Esse último é o padrão de Python para "retornar dois valores" — não existe
`out` parameter como em C#. A função devolve uma tupla e você a desempacota.

### 5.3 `dict`

É o `HashMap`/`Dictionary`. Em `clips.py` um dict é usado como objeto de
retorno anônimo:

```python
return {"camera": self.label, "path": self.path, "frames": self.frames_written}
```

Vindo de C#, é tentador criar uma classe para isso. Em Python, dict é aceitável
e comum para dados de passagem.

### 5.4 `deque` — o ring buffer

```python
from collections import deque
self.buffer = deque(maxlen=PRE_FRAMES)
```

Com `maxlen`, o append num deque cheio **descarta o mais antigo silenciosamente**.
É um buffer circular pronto, sem lógica de índice. Não há equivalente direto
tão conciso na biblioteca padrão do Java.

---

## 6. Slicing

Talvez a sintaxe mais estranha para quem vem de Java. `sequencia[inicio:fim]` —
início incluído, fim **excluído**.

```python
frame.shape[:2]          # os dois primeiros elementos
sys.argv[1:5]            # do índice 1 ao 4
list(self.buffer)[:-1]   # tudo menos o último
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
if people:                # lista não vazia
if not shared:            # área de sobreposição igual a zero
```

**Armadilha:** `if not x` é verdadeiro tanto para lista vazia quanto para
`None`. Quando a distinção importa, teste explicitamente:

```python
if frame is None:         # correto
if not frame:             # ERRADO: um numpy array levanta exceção aqui
```

Esse caso aparece de verdade no projeto. Um array numpy não tem valor de
verdade definido e lança `ValueError` — por isso `Camera.read()` devolve `None`
e o chamador usa `is None`.

---

## 8. `None` e identidade

`None` é o `null`, mas é um **objeto singleton**. Compara-se com `is`, não `==`:

```python
if self._first_read is None:
```

`is` compara identidade (mesmo objeto na memória), `==` compara valor. Para
`None` sempre se usa `is`.

---

## 9. f-strings

Interpolação com prefixo `f`:

```python
print(f"  {cam.label}: {state}")
f"{confidence:.2f}"                  # duas casas decimais
f"{saved['seconds']:.1f}s"           # aspas simples dentro de aspas duplas
```

O que vem depois de `:` é o mesmo mini-formato do `String.format`. É a forma
moderna e preferida — substitui `%` e `.format()`.

---

## 10. Comprehensions

Substituem laços de construção de coleção e o papel de Streams do Java:

```python
streams = [Camera(label, url) for label, url in cameras]
crops = [frame[y:y+h, x:x+w] for x, y, w, h in regions if w > 0]
```

Sem colchetes vira um **generator** — avaliado sob demanda, sem materializar a
lista:

```python
if not any(_overlap_area(box, m) for m in motion_boxes):
```

`any()` para no primeiro verdadeiro. Equivale a `stream().anyMatch()`, porém a
sintaxe é da própria linguagem, não de uma API.

---

## 11. `for ... else`

Construção sem equivalente em Java ou C#, e usada de propósito em
`drop_duplicates`:

```python
for other in kept:
    if muito_parecido:
        break
else:
    kept.append(person)
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
def recording(self):
    return self.writer is not None
```

Transforma um método em atributo de leitura: escreve-se `cam.recorder.recording`,
sem parênteses. É exatamente a *property* do C#, e a razão pela qual Python não
precisa de getters triviais — um campo público pode virar property depois sem
quebrar quem o usa.

### 12.2 `@lru_cache`

```python
@lru_cache(maxsize=1)
def load_model():
    return YOLO(MODEL)
```

Memoriza o retorno por argumentos. Com `maxsize=1` e nenhum argumento, é um
**singleton preguiçoso**: a primeira chamada carrega o modelo, as seguintes
devolvem o mesmo objeto. Substitui todo o boilerplate de singleton do Java.

---

## 13. Classes

```python
class ClipRecorder:
    def __init__(self, label, directory=CLIP_DIR):
        self.label = label
```

- `__init__` é o inicializador (o objeto já existe quando ele roda).
- **`self` é explícito** e é sempre o primeiro parâmetro de métodos de
  instância. Não existe `this` implícito.
- Atributos são criados por atribuição em `__init__`. Não há declaração de
  campos como em Java.
- Não há construtores sobrecarregados — use valores padrão.

### 13.1 Armadilha: argumento padrão mutável

O valor padrão é avaliado **uma única vez**, na definição da função. Isto é um
bug clássico:

```python
def f(boxes=[]):     # PERIGO: a mesma lista em todas as chamadas
```

Por isso o projeto usa tupla vazia, que é imutável:

```python
def make_panel(frame, label, height, motion_boxes=(), people=()):
```

---

## 14. GIL — por que threads não paralelizam

O CPython tem o *Global Interpreter Lock*: **apenas uma thread executa bytecode
Python por vez**. Threads não usam múltiplos núcleos para código Python puro.

Isso soa fatal para um projeto de vídeo, mas não é, porque as bibliotecas
liberam o GIL enquanto executam código nativo:

- `cap.read()` libera durante o decode H.264.
- Operações do OpenCV e do numpy liberam durante o processamento.
- A inferência do PyTorch libera.

Ou seja, o trabalho pesado **é** paralelo; o Python só orquestra. Quando é
preciso paralelismo real de código Python, usa-se `multiprocessing` (processos
separados, cada um com seu interpretador) — não threads.

---

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

**Erros costumam ser silenciosos.** `VideoCapture` que falha não lança exceção —
retorna um objeto com `isOpened() == False`. Sempre verifique.

**`waitKey` faz duas coisas:** espera tecla **e** processa a fila de eventos da
janela. Sem ele a janela nunca redesenha. É a peça que substitui o event loop
que em WinForms/Swing seria implícito.

---

## 17. Ultralytics e PyTorch

```python
result = self.model.predict(frame, classes=[0], conf=0.35, verbose=False)[0]
```

`predict` aceita uma imagem ou uma lista e **sempre devolve uma lista** de
resultados — daí o `[0]`.

### 17.1 Tensores

`result.boxes.xyxy` é um `torch.Tensor`, não uma lista. É um array
multidimensional que pode viver em GPU. Para voltar a tipos Python:

```python
result.boxes.xyxy.tolist()
result.boxes.conf.tolist()
```

Sem `.tolist()`, você carrega tensores por todo o código e paga conversões
implícitas.

### 17.2 `zip`

```python
for (x1, y1, x2, y2), confidence in zip(boxes.xyxy.tolist(), boxes.conf.tolist()):
```

`zip` percorre duas sequências em paralelo, e o desempacotamento aninhado abre
a caixa em quatro variáveis na própria assinatura do `for`.

### 17.3 Formato das caixas

O YOLO devolve `xyxy` (dois cantos). O resto do projeto usa `(x, y, w, h)`.
A conversão é explícita em `people.py` — vale conferir sempre qual convenção
uma API usa, porque as duas são comuns.

---

## 18. Memória

Python usa contagem de referências **mais** um coletor para ciclos. Objetos
morrem determinística e imediatamente quando a última referência some — mais
previsível que o GC da JVM.

Mas recursos nativos não são liberados sozinhos de forma confiável. Por isso
`release()` é explícito:

```python
self.writer.release()
cam.cap.release()
```

O `with` (context manager) é o equivalente de `try-with-resources` e seria o
idiomático — mas `VideoCapture` e `VideoWriter` do OpenCV não o implementam,
então a liberação fica manual.

---

## 19. Armadilhas resumidas

| Armadilha | Detalhe |
|---|---|
| `if not array` | Levanta exceção em numpy. Use `is None`. |
| `shape` | É `(altura, largura)`, não `(largura, altura)`. |
| Slice numpy | É *view*; escrever nele altera o original. |
| Padrão mutável | `def f(x=[])` compartilha a lista entre chamadas. |
| Cores | BGR, não RGB. |
| `==` vs `is` | `is` só para `None` e singletons. |
| Ordem de import | Pode ter efeito colateral (caso do FFmpeg). |
| Falha do OpenCV | Silenciosa; cheque `isOpened()`. |
| Threads | Não paralelizam código Python puro (GIL). |
| Sem compilação | Erro de digitação só aparece ao executar aquela linha. |
