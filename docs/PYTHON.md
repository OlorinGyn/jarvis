# Python and the libraries — a guide for someone coming from Java / C#

This document covers **only what is specific to Python** and to the libraries
the project uses. It assumes you already program: it does not explain what a
class, a loop or polymorphism is — it explains where Python departs from what
you would expect coming from a statically typed language.

Every example is real code from this project.

---

## 1. Environment and dependencies

| Java / C# | Python (here) |
|---|---|
| Maven / Gradle / NuGet | `uv` |
| `pom.xml` / `.csproj` | `pyproject.toml` |
| `~/.m2`, `packages/` | `.venv/` |
| A JAR on the classpath | a package installed in the venv |

Python has no classpath. It resolves imports by searching `sys.path`, and a
**virtualenv** (`.venv/`) is simply a folder with its own interpreter and its
own libraries. Without a venv everything is installed globally and projects
conflict.

```bash
uv run python -m jarvis
```

`uv run` runs with the project's venv without "activating" anything. That is
why `import cv2` works in this command and would fail with the system's
`python`. `-m jarvis` runs the package's `__main__.py` (2.1) — the equivalent
of an executable JAR's `Main-Class`. `pyproject.toml` also declares a `jarvis`
command in `[project.scripts]`, and `uv run jarvis` would work, but `uv`
generates it as an unsigned `jarvis.exe`, which Smart App Control blocks on
the M900; `python -m` goes through the signed Python instead (INSTALACAO 1.2).

**There is no compilation.** No `javac`, no build. A typo on a line shows up
only when that line runs — which makes tests far more important than in Java.

---

## 2. Modules: the file is the unit, not the class

In Java the unit is the class and the file must carry its name. In Python:

- **One `.py` file = one module.**
- Functions and variables can live loose in the module. No class is needed to
  group anything.
- `motion.py` defines `MotionDetector`; `from jarvis import motion` brings in
  the module, `from jarvis.motion import MotionDetector` brings in the name
  directly.

```python
from jarvis.clips import BUFFER_DIR, EventRecorder
```

That imports a constant **and** a class from the same module — something that
in Java would take a `static import` of a constant inside some class.

### 2.1 Package: a folder of modules

A folder with `__init__.py` is a **package**, the equivalent of a Java
`package` or a C# `namespace`. The project's code lives in `src/jarvis/`, so
each module's full name is `jarvis.<file>`.

| File | Role | Parallel |
|---|---|---|
| `__init__.py` | runs on the first `import jarvis`; here it defines `ROOT` | the namespace's static constructor |
| `__main__.py` | runs with `python -m jarvis` | the class with `main` |
| `cameras.py` | the module `jarvis.cameras` | a class inside the package |

Why `src/` in the middle? Without it, running `python` from the project root
would import the `jarvis/` folder straight from disk, and an installation
error would go unnoticed. With `src/`, `jarvis` is found only if it is
**installed** in the venv — `uv sync` does that in editable mode, pointing at
the files instead of copying them. See ARQUITETURA 3.1.

The tools in `tools/` live outside the package but use it like any library:
`from jarvis import cameras, capture`.

### 2.2 Imports run code

An `import` runs the whole file the first time, and that allows couplings that
would not exist in Java. The project has one case, in `jarvis/__init__.py`:

```python
import os
from pathlib import Path

os.environ.setdefault("OPENCV_LOG_LEVEL", "ERROR")
```

OpenCV reads that variable **when the `cv2` module is loaded**. It only works
because the package's `__init__.py` runs before any other `jarvis` module —
and all of them `import cv2` afterwards. If someone imported `cv2` before
importing `jarvis`, the variable would arrive too late and the warning it
silences would come back, with no error at all. In Java, imports are
declarations resolved at compile time and could never have that side effect.

Here the damage would only be one more warning in the terminal. In an old
version of the project the same trap broke RTSP: `OPENCV_FFMPEG_CAPTURE_OPTIONS`
had to be set before `import cv2`, and moving the import up — as any linter
would suggest — switched TCP off silently (ARQUITETURA 5.8). The lesson: in
Python the **order** of imports can carry meaning, and nothing in the file
warns you when it does.

### 2.3 `if __name__ == "__main__"`

```python
if __name__ == "__main__":
    main()
```

`__name__` is `"__main__"` when the file is run directly, and the module's
name when it is imported. Without that guard, `tools/diagnostico.py`
importing `cameras` to reuse something from it would open the cameras as a
side effect.

It is the equivalent of `public static void main`, but by convention, not by a
rule of the language.

---

## 3. Typing: dynamic and by behaviour

There is no mandatory type declaration. A function accepts whatever answers
the operations it uses — *duck typing*.

```python
def make_panel(frame, label, height, motion_boxes=(), subjects=(), recording=False,
               reason=""):
```

Nothing here guarantees `frame` is an image. If it is not, the error shows at
run time, inside `cv2.resize`.

**There are no interfaces.** You do not declare `implements`. If an object has
the right method, it will do. There is no idiomatic `instanceof` for
contracts.

**There is no method overloading.** You cannot have two `scan_clip()` with
different signatures. Arguments with default values are used instead:

```python
def scan_clip(clip, camera, started_at, gallery=None, moments=(), busy=None):
```

The program calls it without `gallery` and each scan loads the gallery from
disk; `tools/refazer_rostos.py` passes one gallery for every clip.

Type hints (`def f(x: int) -> str`) exist, but they are **annotations ignored
at run time** — documentation checked by external tools (mypy), never by the
interpreter.

---

## 4. No access modifiers

There is no `private`, `protected` or `public`. **Everything is accessible.**

The convention is the underscore:

```python
self._errors = deque(maxlen=12)
self.frames_read = 0
```

(From `FFmpegCamera`, in `capture.py`: the first is "internal, do not touch",
the second part of the public API.) It is only a convention — `cam._errors`
works perfectly. Python's culture trusts the programmer instead of imposing
barriers through the compiler.

The same goes for module functions: `_similarity()` in `faces.py` signals
internal use, while `cosine()`, in the same file, is for anyone who wants it.

---

## 5. Data structures

### 5.1 Tuple vs list

| | Tuple `(1, 2)` | List `[1, 2]` |
|---|---|---|
| Mutable | no | yes |
| Typical use | a record of fixed fields | a homogeneous collection |

The project uses tuples as light records — the role of a Java `record` or a
C# `struct`:

```python
(x, y, w, h)
```

(a motion box). YOLO's detections started as `(x, y, w, h, confidence)` and
became a `NamedTuple` when they needed a label (5.4).

### 5.2 Unpacking

Multiple assignment is idiomatic and everywhere:

```python
h, w = frame.shape[:2]
x, y, bw, bh = cv2.boundingRect(contour)
width, height, total = _describe(clip)
```

The last one is Python's pattern for "returning several values" — there is no
`out` parameter as in C#. `_describe()` does `return width, height, total`,
which builds a tuple, and the caller unpacks it (more in section 27).

The same mechanism swaps values without a temporary variable. In
`capture.py`:

```python
frame, self._pending = self._pending, None
```

The right-hand side becomes a tuple **before** any assignment; only then do
the two names on the left receive the values. It takes the pending frame and
clears the field in one line.

### 5.3 `dict`

It is the `HashMap`/`Dictionary`. In `clips.py` a dict is used as an anonymous
return object, and the same dict becomes the event's `.json`:

```python
meta = {
    "camera": self.label,
    "started_at": self.started_at.isoformat(timespec="seconds"),
    "seconds": round(seconds, 1),
    "labels": sorted(self.labels),
    ...
}
```

Coming from C#, it is tempting to create a class for that. In Python a dict is
acceptable and common for data in transit.

### 5.4 `NamedTuple` — Python's `record`

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

It is the closest equivalent of a Java `record` or a C# `readonly struct`:
immutable, compared by value, with named fields. And it can have methods and
properties, like any class.

The detail that matters here: **it is still a real tuple**. Indexing (`d[4]`),
unpacking (`x, y, w, h, c, l = d`) and slicing (`d[:4]`) all work. That is what
allowed adding the label without rewriting the code that already treated
detections as `(x, y, w, h, conf)`.

The `x: int` are *type hints* — ignored at run time, as section 3 says.
Nothing stops a string from being stored there.

The alternative is `@dataclass`, which is mutable and does not behave like a
tuple. Use `NamedTuple` when the value is an immutable record; `dataclass` when
it is an object whose state changes.

### 5.5 `set` — with first-class syntax

Sets have their own literal and operators, not only methods. In
`clips.EventRecorder`:

```python
seen = {s.label for s in subjects}
new = {s.label for s in subjects} - self.notify_tried
```

`{expression for x in y}` is a **set comprehension** — sister of the list
comprehension, but dropping duplicates. The first line answers "which
distinct labels are in the frame" with no loop and no explicit `HashSet`. The
second uses `-`, **set difference**: the labels in this frame that have not
been tried yet — Java's `removeAll` on a copy, as one operator. `|` is union
and `&` intersection; `self.notify_tried |= new` adds in place.

Membership (`label in self.notify_tried`) is O(1) — the same reason as a
`HashSet` in Java, without the ceremony.

> A historical note: there used to be a section here on `deque(maxlen=...)`
> as a ring buffer, used by the in-memory pre-recording. That structure went
> away when the pre-recording started coming from the segments on disk
> (ARQUITETURA 5.5). The `deque(maxlen=12)` that keeps ffmpeg's last error
> messages, in `capture.py`, is the same feature: past 12, the oldest drops
> out on its own.

---

## 6. Slicing

Perhaps the strangest syntax for someone coming from Java.
`sequence[start:end]` — start included, end **excluded**.

```python
frame.shape[:2]
sys.argv[1:5]
self.segments()[:-1]
key[len("CAM_"):-len("_IP")]
```

In order: the first two elements; indices 1 to 4; everything but the last (the
segment ffmpeg is still writing); the key without its prefix and suffix.
Negative indices count from the end: `[-1]` is the last element. This replaces
much of `substring` and `Arrays.copyOfRange`.

---

## 7. Truthiness — a dangerous difference

In Java, `if` demands a `boolean`. In Python **every object has a truth
value**:

| False | True |
|---|---|
| `0`, `0.0`, `""`, `[]`, `()`, `{}`, `None`, `False` | everything else |

That is why the code writes:

```python
if not motion_boxes:
if subjects:
if not observations:
```

(an empty list; a non-empty list; no face in the whole clip).

**Trap:** `if not x` is true both for an empty list and for `None`. When the
difference matters, test explicitly:

```python
if frame is None:
if not frame:
```

The first is right; the second is **wrong** — a numpy array raises an
exception there. This case appears for real in the project. A numpy array has
no defined truth value and raises `ValueError` — which is why
`FFmpegCamera.read()` returns `None` when there is no new frame, and the loop
in `cameras.py` tests `if frame is None`.

---

## 8. `None` and identity

`None` is `null`, but it is a **singleton object**. It is compared with `is`,
not `==`:

```python
if self.process is None:
```

`is` compares identity (the same object in memory), `==` compares value. For
`None`, always `is`.

---

## 9. f-strings

Interpolation with an `f` prefix:

```python
print(f"  {cam.label}: {cam.stream.wait_ready()}")
f"{subject.label} {subject.confidence:.2f}"
f"{saved['seconds']}s, {saved['reason']}"
```

A call inside the string; two decimal places; single quotes inside double
ones. What follows `:` is the same mini-format as `String.format`. It is the
modern, preferred form — it replaces `%` and `.format()`.

---

## 10. Comprehensions

They replace collection-building loops, and the role of Java's Streams:

```python
streams = [Camera(label, url) for label, url in cameras]
return [box for box, _, class_id in _raw_detections(load_background_model(), frame)
        if class_id == PERSON_CLASS]
```

The second, from `people.person_boxes()`, unpacks each `(box, confidence,
class)` tuple right in the `for`, discards the confidence with `_` and
filters by class — what in Java would be `stream().filter().map().collect()`.

Without brackets it becomes a **generator** — evaluated on demand, without
building the list:

```python
if REQUIRE_MOTION_OVERLAP and not any(
        overlap_area(box, m) for m in motion_boxes):
```

`any()` stops at the first true value. It is `stream().anyMatch()`, but the
syntax belongs to the language, not to an API.

---

## 11. `for ... else`

A construct with no equivalent in Java or C#, used on purpose in
`drop_duplicates`:

```python
for other in kept:
    if subject.label == other.label and iou(subject, other) > SAME_SUBJECT_IOU:
        break
else:
    kept.append(subject)
```

**The `else` block runs only if the loop ended without `break`.** It reads
literally as "if nothing matched, add it". The Java alternative would be a
boolean flag variable.

---

## 12. Decorators

The `@something` syntax above a function. It is sugar for
`f = something(f)` — the function is passed to another function that returns
a modified version. The nearest concept in C# is attributes, but decorators
**really change behaviour**, not just metadata.

### 12.1 `@property`

```python
@property
def alive(self):
    return self.process is not None and self.process.poll() is None
```

It turns a method into a read-only attribute: `capture.py` writes
`if not self.alive:`, without parentheses. It is exactly C#'s *property*, and
the reason Python needs no trivial getters — a public field can become a
property later without breaking its users.

### 12.2 `@lru_cache`

```python
@lru_cache(maxsize=1)
def load_model():
    ensure_model()
    return cv2.dnn.readNetFromONNX(str(MODEL_FILE))
```

It memoises the return value by arguments. With `maxsize=1` and no arguments
it is a **lazy singleton**: the first call loads the model, the following ones
return the same object. It replaces all of Java's singleton boilerplate.

And precisely because it is a singleton, it does not serve two threads:
`people.py` has a second one, `load_background_model()`, identical, so the
face-scanning thread has its own network (14.2).

---

## 13. Classes

```python
class EventRecorder:
    def __init__(self, camera, directory=CLIP_DIR):
        self.camera = camera
        self.label = camera.label
```

- `__init__` is the initialiser (the object already exists when it runs).
- **`self` is explicit** and is always the first parameter of instance
  methods. There is no implicit `this`.
- Attributes are created by assignment in `__init__`. Fields are not declared
  as in Java.
- There are no overloaded constructors — use default values.

### 13.1 `__slots__`

```python
class _Candidate:
    __slots__ = ("box", "hits", "misses")
```

By default every Python object carries a `__dict__` — a dictionary of
attributes — which allows creating new fields at run time. That costs memory
and a hash lookup on every access.

`__slots__` declares the fields up front: the object uses fixed positions,
like a class field in Java. It is smaller and faster, and assigning an
undeclared attribute becomes an `AttributeError` instead of silently working.

Worth it when there are many small, short-lived instances — exactly the case
of the blob candidates, created and discarded every frame.

### 13.2 Trap: a default argument evaluated only once

The default value is evaluated **when the function is defined**, not on each
call. The famous form of this trap involves lists, but it bites more subtly
too. This bug happened for real in `faces.py`:

```python
GALLERY_FILE = Path("faces/gallery.json")

class Gallery:
    def __init__(self, path=GALLERY_FILE):
        ...
```

That is **wrong**: the default **freezes** the value `GALLERY_FILE` had when
the class was defined. Changing `faces.GALLERY_FILE` later — in a test, say —
has no effect at all, and the object keeps reading the old file, silently.

The fix is to read the global at run time:

```python
    def __init__(self, path=None):
        self.path = Path(path or GALLERY_FILE)
```

In Java the equivalent would be a default captured in a static constant
initialised once — except that in Python any expression can sit there, which
makes the effect far less obvious.

### 13.3 Trap: a mutable default argument

The default value is evaluated **only once**, at definition. This is a classic
bug:

```python
def f(boxes=[]):
```

The same list is shared by every call. That is why the project uses an empty
tuple, which is immutable:

```python
def make_panel(frame, label, height, motion_boxes=(), subjects=(), recording=False,
               reason=""):
```

---

## 14. The GIL — why threads do not run in parallel

CPython has the *Global Interpreter Lock*: **only one thread runs Python
bytecode at a time**. Threads do not use several cores for pure Python code.

That sounds fatal for a video project, but it is not, because the libraries
release the GIL while running native code:

- Reading ffmpeg's pipe (`process.stdout.read()`) releases it while waiting.
- OpenCV and numpy operations release it while processing.
- YOLO's inference (`net.forward()`, in C++) releases it.

So the heavy work **is** parallel; Python only orchestrates. When real
parallelism of Python code is needed, `multiprocessing` is used (separate
processes, each with its own interpreter) — not threads.

### 14.1 Threads pay off for subprocesses

The GIL prevents parallel *Python bytecode*, but does not get in the way of
waiting for an external process. Assembling a clip uses that (shortened):

```python
job = threading.Thread(target=_assemble,
                       args=(self.camera, self.started_at, ended_at,
                             destination, set(self.labels)))
job.start()
```

`_assemble` sleeps until the last segment closes and then calls
`subprocess.run(ffmpeg...)`. The real work happens in another process, on its
own cores; the thread only blocks waiting. It is the case where threading in
Python works exactly as you would expect from Java or C#.

**Non-daemon threads.** By default the interpreter **waits** for threads to
finish before exiting. That is wanted here (no half-made clip). Java is the
same: a `Thread` created from `main` is non-daemon and the JVM waits for it.
In C# a `Thread` also holds the process, but a `Task` does not — it runs on
the pool, whose threads are background ones. Even so, `wait_for_jobs()` is
called explicitly on exit, so the user can be told.

### 14.2 Releasing the GIL makes nothing thread-safe

The other side of the list above: if OpenCV releases the GIL inside
`forward()`, two threads calling `forward()` **on the same network** really do
run at the same time. And a `cv2.dnn.Net` keeps internal buffers between
calls — it was not made for that.

It happened in the project: the face scan, in a background thread, started
using YOLO through the same `load_model()` as the live loop. The program
crashed with `buf.shape() == m.shape()` right after an event. The fix was a
second network for the background thread and a `threading.Lock` so the scans
queue up (ARQUITETURA 10.9):

```python
_SCAN_LOCK = threading.Lock()

def scan_clip(clip, camera, started_at, gallery=None, moments=(), busy=None):
    with _SCAN_LOCK:
        ...
```

`with lock:` is C#'s `lock (obj) { }` and Java's `synchronized`: it acquires
on entry and releases on exit, even on an exception. The rule of thumb is the
same in both languages — a native object shared between threads needs an
owner or a lock. The GIL is not that lock.

## 15. numpy — the most important type in the project

An image **is** a `numpy.ndarray`. There is no `Image` class.

```python
h, w = frame.shape[:2]
```

### 15.1 `shape` is (rows, columns, channels)

**Height comes before width.** A 1080p frame has shape `(1080, 1920, 3)`. That
inversion of the usual `(width, height)` is a constant source of bugs.

And the `dtype` is `uint8`: values 0–255 that **wrap around instead of
saturating**. In an operation between arrays, `250 + 10` gives `4`, silently —
no exception, no clamp. (On lone scalars numpy 2.x issues a `RuntimeWarning`,
but on arrays, the real case, the overflow is silent.)

The practical consequence: to brighten an image, adding directly corrupts the
brightest pixels. Use `cv2.add`, which saturates at 255.

### 15.2 Indexing is [row, column]

```python
crop = frame[y:y+h, x:x+w]
```

The vertical axis first, then the horizontal — the opposite of Cartesian
coordinates.

### 15.3 Slices are *views*, not copies

This is the most important conceptual difference from Java arrays:

```python
crop = frame[100:200, 100:200]
crop[:] = 0
```

The second line **changes `frame` too**: the slice shares the same memory.
Great for performance (cropping copies nothing) and dangerous if you expected
a value. To really copy: `frame[100:200, 100:200].copy()`.

### 15.4 Vectorised operations

A `for` loop over pixels in Python is orders of magnitude slower. Everything
is written as an operation on the whole array, run in C:

```python
np.zeros((height, width, 3), dtype=np.uint8)
np.hstack(panels)
```

---

## 16. OpenCV (`cv2`)

It is a C++ library with a generated binding. The practical consequences:

**The API is not Pythonic.** Names in `CAPS`, constants loose in the module
(`cv2.MORPH_OPEN`), functions that return tuples:

```python
_, mask = cv2.threshold(mask, 200, 255, cv2.THRESH_BINARY)
contours, _ = cv2.findContours(...)
```

`_` is the convention for "value discarded".

**Colours are BGR, not RGB.**

```python
GREEN = (0, 255, 0)
RED = (0, 0, 255)
```

(`RED` looks blue if read as RGB.)

**The documentation is C++'s.** When looking up `cv::VideoCapture`, translate
it in your head to `cv2.VideoCapture`; the parameters are the same.

**Errors are usually silent.** No exceptions: `cv2.imread` on a missing file
returns `None`, and `cv2.imwrite` returns `False` instead of complaining. In
Java you would get an `IOException`. Here the return value must be checked —
the old window's `ui.py` did that when loading thumbnails, falling back to a
grey card when the image would not open.

**`waitKey` did two things** in that old window: it waited for a key **and**
processed the window's event queue. Without it the window never redrew. It was
the piece that replaces the event loop that WinForms or Swing make implicit —
and the reason the surveillance loop rode on the window until it was separated
(ARQUITETURA 15).

---

## 17. A neural network without PyTorch: `cv2.dnn`

YOLO runs through OpenCV's `dnn` module, on the `.onnx` file — the standard
format for taking a trained network from one library to another. PyTorch left
the project because of Smart App Control (ARQUITETURA 7.11), and with it the
`ultralytics` library, which hid all the pre- and post-processing. Now it is
explicit in `people._raw_detections()`, and each step teaches something about
numpy.

### 17.1 Input: a "blob"

```python
canvas, scale = _letterbox(frame)
blob = cv2.dnn.blobFromImage(canvas, 1 / 255.0, (IMG_SIZE, IMG_SIZE),
                             swapRB=True, crop=False)
net.setInput(blob)
```

The network expects a `(1, 3, 640, 640)` array of floats between 0 and 1, in
RGB: 1 image, 3 channels, height, width. OpenCV's frame is `(540, 960, 3)` of
integers 0–255 in BGR. `blobFromImage` does the whole conversion: scales
(`1 / 255.0`), swaps BGR→RGB (`swapRB=True`) and reorders the axes to
"channels first". `_letterbox`, before it, fits the frame into a square
without distorting it, and returns the scale to undo it afterwards.

### 17.2 Output: transpose to iterate

```python
predictions = net.forward()[0].T
```

`forward()` returns `(1, 84, 8400)`: 8400 candidate boxes, each described by
84 numbers (4 of geometry + 80 scores, one per COCO class). But a box's 84
numbers sit in a **column**. `[0]` removes the batch dimension and `.T` (the
transpose) turns the matrix into `(8400, 84)`: now each **row** is a box, and
`for row in predictions` walks the boxes.

In Java that would be a `float[84][8400]` and a loop with the indices swapped.
Here `.T` copies nothing: it is a *view* (15.3) that reads the same memory in
another order.

### 17.3 The winning class and the box format

```python
class_scores = row[4:]
class_id = int(np.argmax(class_scores))
cx, cy, width, height = row[:4]
boxes.append([int((cx - width / 2) / scale), int((cy - height / 2) / scale),
              int(width / scale), int(height / scale)])
```

`np.argmax` returns the **index** of the largest value — the most likely
class. The geometry comes as **centre + size** (`cx, cy, w, h`), while the
whole project uses **corner + size** (`x, y, w, h`); the conversion takes half
the width and height off. Dividing by `scale` undoes the letterbox fit and
gives the box in the original frame's pixels. Always check which convention
an API uses: all three (corners, centre, corner + size) are common.

### 17.4 One person, several boxes: NMS

The network tends to propose several nearly identical boxes for the same
object. `cv2.dnn.NMSBoxes` (*non-maximum suppression*) keeps the most
confident and discards those that overlap it beyond `NMS_THRESHOLD`. It
returns only the indices that survived:

```python
keep = cv2.dnn.NMSBoxes(boxes, scores, CONFIDENCE, NMS_THRESHOLD)
return [(boxes[i], scores[i], classes[i]) for i in np.array(keep).ravel()]
```

`np.array(keep).ravel()` is there because, depending on the OpenCV version,
`keep` comes as a flat list or as a column `[[0], [3]]`; `ravel()` flattens
both forms into `[0, 3]`.

### 17.5 `zip`

`zip` walks two sequences in parallel — in `tools/gerar_icone.py`, each image
with its PNG:

```python
for image, blob in zip(images, blobs):
```

What in Java would take an index loop over two lists of the same size.

---

## 18. `pathlib` instead of joining strings

```python
folder = self.directory / self.label / stamp.strftime("%Y-%m-%d")
folder.mkdir(parents=True, exist_ok=True)
self.base = folder / stamp.strftime("%H-%M-%S")
self.base.with_suffix(".jpg")
```

The `/` operator is overloaded to join paths, and `with_suffix()` swaps the
extension — that is how an event's files share one base name. `Path` is the
equivalent of `java.nio.file.Path` and fully replaces string handling with
`os.path.join`.

One detail: a `Path` is not a string. When passing it to a C++ API such as
`cv2.imwrite`, or to `subprocess`, `str(path)` is needed.

## 19. `subprocess`: a list or a string, and why it matters on Windows

The general rule is to pass a **list** of arguments, never a string: it avoids
quoting and injection problems, since no shell is involved. Assembling clips
in `clips.py`:

```python
subprocess.run(
    [ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error",
     "-f", "concat", "-safe", "0", "-i", str(listing),
     "-c", "copy", "-movflags", "+faststart", str(destination)],
    check=True, capture_output=True)
```

`check=True` turns a non-zero exit code into an exception
(`CalledProcessError`); without it, an ffmpeg failure would pass silently.
`capture_output=True` keeps stdout and stderr instead of sending them to the
terminal.

On Windows, though, the operating system does not take a list:
`CreateProcess` receives **a single command line**. `subprocess` converts your
list with `list2cmdline()`, which wraps in quotes every argument containing a
space.

That breaks programs whose syntax does not follow the standard convention —
`explorer.exe` is the classic case, met by the old window's "show in
Explorer":

```python
subprocess.list2cmdline(["explorer", "/select,D:\\Personal Projects\\a.mp4"])
```

That gives `explorer "/select,D:\Personal Projects\a.mp4"` — the option inside
the quotes. Explorer needs `/select,"path"`, with quotes only around the path.
To control the exact format, pass **the ready-made string**, which on Windows
goes straight to `CreateProcess`:

```python
subprocess.Popen(f'explorer /select,"{target}"')
```

Coming from Java, the analogue is the difference between
`ProcessBuilder(List<String>)` and `Runtime.exec(String)` — with the same
quoting trap on Windows.

The practical rule: **a list by default; a string only when the target program
has its own syntax** that automatic quoting would spoil.

## 20. Reading binary from a pipe and turning it into an array without copying

Capture reads raw frames from ffmpeg's output, and the face scan does the same
with the clip. The pattern is worth knowing:

```python
data = self.process.stdout.read(self.frame_bytes)
frame = np.frombuffer(data, np.uint8).reshape(HEIGHT, WIDTH, 3).copy()
```

Three points:

**`read(n)` on a binary pipe returns exactly `n` bytes**, or fewer only at the
end of the stream. Since every frame has a fixed size (`960*540*3`), asking
for that number keeps reader and producer in step without a header or a
delimiter.

**`np.frombuffer` copies nothing.** It creates an array that *points* at the
bytes already in memory — unlike `np.array(data)`, which would copy. For 1.5 MB
per frame at 10 fps, the difference matters.

**Precisely because it does not copy, the array is read-only**, since `bytes`
is immutable in Python. Any attempt to draw on it raises an exception, which
is why there is an explicit `.copy()` at the end. It is the reverse of the
Java intuition: here the cheap "cast" comes with immutability, and you pay for
the copy only when you need to write.

## 21. Memory and external resources

Python uses reference counting **plus** a collector for cycles. Objects die
deterministically and immediately when the last reference goes — more
predictable than the JVM's GC.

But external resources are not released by themselves. Each camera's ffmpeg
process has to be ended by hand:

```python
self.process.terminate()
self.process.wait(timeout=5)
```

Without that, ffmpeg would outlive Python and keep holding the camera's only
RTSP session — and the next run could not connect. The `except` falls back to
`kill()` if the process ignores `terminate()`.

`with` (a context manager) is the equivalent of `try-with-resources` and would
be the idiomatic way. `subprocess.Popen` even implements it, but here the
process must live for the whole run of the program, not for one block — so
the release is explicit at shutdown.

When the resource lives only for one function, the project uses
`try`/`finally`. In the face scan's frame reader, which is a *generator*
(`yield`), the `finally` runs even if the consumer stops halfway:

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

And `tools/diagnostico.py` uses `with tempfile.TemporaryDirectory() as
pasta:`: the temporary folder is deleted on leaving the block, error or not —
`try-with-resources` for a directory.

---

## 22. Final differences and traps

### 22.1 `//` rounds down, it does not truncate

The quietest difference on this list. Python has two division operators: `/`
always returns a `float`, and `//` returns an integer **rounded towards minus
infinity**. Java and C# truncate towards zero.

```python
-12 // 54
```

That is `-1` in Python; `(-12) / 54` is `0` in Java.

The old window's `ui.py` used it to know how many rows of cards there were —
division **rounding up**, with integers only:

```python
total_rows = -(-len(self.entries) // columns)
```

With 11 cards in 5 columns: `-11 // 5` gives `-3` (down, towards minus
infinity), and negating it back gives `3` rows. In Java `-11 / 5` gives `-2`
and the trick does not work; there you use `Math.ceilDiv` or
`(a + b - 1) / b`.

To truncate as in Java, use `int(a / b)`. For the remainder, `%` follows the
divisor's sign in Python (`-1 % 5 == 4`), unlike Java (`-1 % 5 == -1`).

### 22.2 The traps, in short

| Trap | Detail |
|---|---|
| `//` | Rounds down; Java truncates towards zero. |
| `if not array` | Raises an exception on numpy. Use `is None`. |
| `shape` | It is `(height, width)`, not `(width, height)`. |
| A numpy slice | It is a *view*; writing to it changes the original. |
| A mutable default | `def f(x=[])` shares the list between calls. |
| A frozen default | `def f(path=CONSTANT)` reads the constant only once (13.2). |
| Colours | BGR, not RGB. |
| `==` vs `is` | `is` only for `None` and singletons. |
| Import order | Can have side effects (`OPENCV_LOG_LEVEL`, 2.2). |
| An OpenCV failure | Silent: `imread` returns `None`, `imwrite` returns `False`. |
| Threads | Do not parallelise pure Python code (GIL), but shared native objects are at real risk (14.2). |
| No compilation | A typo shows only when that line runs. |

---

## 23. `logging` instead of `print`

Written in English: the user moved the documentation to English on 09/10/2026.

`print` writes to the console, and a scheduled task has none. The standard
library's `logging` separates **what** is said from **where** it goes:

```python
logger = logging.getLogger(__name__)
logger.info("  event %s %s [%s] %ss, %s", cam.label, saved["path"].name,
            names, saved["seconds"], saved["reason"])
```

- **One logger per module**, named after it (`jarvis.cameras`, `jarvis.web`).
  They form a tree under the root logger, the way `ILogger<T>` does in .NET.
- **Handlers** decide where messages go. `log.setup()` adds one to the console;
  `log.to_file()` adds a `RotatingFileHandler` — at 1 MB the file becomes
  `jarvis.log.1`, the oldest of five is dropped, and the log never fills the
  disk. In .NET terms: sinks.
- **`%s` placeholders, not f-strings.** The arguments are only formatted if the
  message is actually written. Minor here; it is the habit the library expects.
- **Crashes go to the log too.** `sys.excepthook` is called for an exception
  nobody caught in the main thread, `threading.excepthook` for one in any other
  thread. Without the second, a thread that dies — the web server, a clip
  assembly — disappears with a traceback on a console nobody sees.

Only the running service writes the file. A second process writing it — the
`--stop` command, say — would break rotation on Windows, which cannot rename a
file another process holds open.

## 24. `threading.Event`: a stop signal between threads

`--stop` arrives as an HTTP request, handled in a web server thread. The loop
that has to stop runs in the main thread. They meet through a
`threading.Event`, created in `main()` and handed to both sides:

```python
stop = threading.Event()
server = web.start(port=port, on_stop=stop.set)
...
while not stop.is_set():
    if not core.step():
        time.sleep(IDLE_SLEEP)
```

`stop.set` is passed **without parentheses**: the function itself, to be
called later — a delegate in C#, a `Runnable` method reference in Java. The web
thread calls it; the main loop sees the flag on its next pass and leaves
through the same path as Ctrl+C, so the `finally` that assembles pending clips
still runs.

Why not a global boolean? An `Event` is safe to set from one thread and read
from another, and it can also be *waited on* (`stop.wait(timeout)`), which a
plain variable cannot.

## 25. Text encodings: the byte-order mark

UTF-8 files sometimes start with three invisible bytes, `EF BB BF`, the
**byte-order mark**. Windows tools like to add it: PowerShell's
`Set-Content -Encoding UTF8` does, and so do some editors. Python reading the
file as `utf-8` keeps it as a character, `﻿`, and `json.loads` fails on
it.

That cost something real here: `settings.load()` caught the error and quietly
returned the defaults, so a `config.json` saved with a BOM **lost the Telegram
token without any message**. The fix is one word:

```python
json.loads(FILE.read_text(encoding="utf-8-sig"))
```

`utf-8-sig` skips the mark if it is there and reads normally if it is not.
Writing stays plain `utf-8`, without a mark. Java's `InputStreamReader` with
UTF-8 has the same trap; .NET's `StreamReader` detects the mark by default.

## 26. Take it out under the lock, then work on it

A bad-detection report (ARQUITETURA 21, R36) does three things to a gallery
entry: copy it into a report, copy its photos, delete it. The first version
did it in the order that reads naturally:

```python
entry = gallery.get(entry_id)       # a snapshot
path = write_report(entry)          # slow: files copied
gallery.take_out(entry_id)          # remove whatever is there *now*
```

Between the first line and the last, a face scan on another thread could add
a view to the same entry. The report held the snapshot, the removal took the
newer entry, and the new view vanished from both. The fix moves the removal
first, inside the lock, and makes it **return what it removed**:

```python
def take_out(self, person_id, forget=True):
    with _GALLERY_LOCK:
        self.load()
        person = self.get(person_id)
        if person is None or person["name"]:
            return None
        self.people.remove(person)
        self.save()
    ...
    return person
```

Whatever the report is then written from is exactly what left — nothing can
change it, because it is no longer in the gallery. Java's
`map.remove(key)` returns the removed value for the same reason, and
`ConcurrentHashMap` offers no "get, then remove" pair that is safe together.
`with _GALLERY_LOCK:` is Python's `synchronized (lock) { ... }` block: the
lock is taken on entry and released on exit, even by an exception.

If writing the report fails, the entry must not be lost:

```python
try:
    path, sightings = _report_taken(gallery, entry)
except Exception:
    gallery.put_back(entry)
    raise
```

A bare `raise` inside `except` re-throws **the same exception with its
original stack** — C#'s `throw;` (not `throw e;`, which resets the stack) and
Java's `throw e;` inside the `catch`. The caller still sees the failure; the
gallery is as it was.

Two `shutil` functions do the file work: `shutil.copyfile(source, target)`
is `Files.copy` / `File.Copy`, and `shutil.rmtree(folder, ignore_errors=True)`
deletes a folder and everything in it without raising when it is already
gone — `Directory.Delete(path, true)` wrapped in a `try` that ignores
`DirectoryNotFoundException`.

On the page, the Settings list fills each report's "Actually…" choice with
`new Option(text, value)`, the DOM's shortcut for creating an `<option>`
element: `select.append(new Option("dog", "dog"))` is the one-line form of
`createElement("option")` and setting its text and value.

## 27. Long polling, one reader, and a sleep that can be interrupted

The Telegram bot (`bot.py`, ARQUITETURA 22.5) has to learn about a `/home`
typed on the phone within a second or so, without opening a port on the
M900. A **webhook** would need Telegram to connect *to* us; **long polling**
turns it around — we connect to Telegram and ask, and Telegram holds the
request open until there is something to say:

```python
fields = {"timeout": LONG_POLL_SECONDS,
          "allowed_updates": json.dumps(["message", "callback_query"])}
if self.offset is not None:
    fields["offset"] = self.offset
payload, problem = self.call(token, "getUpdates", fields, LONG_POLL_SECONDS + 10)
```

`timeout=50` goes to Telegram: "wait up to 50 s for a message before
answering empty". The last argument is *our* timeout for the HTTP request, ten
seconds longer, so a slow answer is not mistaken for a dead connection. The
loop around it is the Java `BlockingQueue.take()` idea, stretched over HTTP:
the thread sits blocked inside `requests.post` and wakes when a message
arrives.

`offset` is how Telegram knows what we have already read. Each update has an
`update_id`; asking with `offset = last id + 1` confirms everything before it,
and Telegram forgets those. That is also why **only one program may read a
bot**: whoever asks first takes the update, and the other never sees it —
Telegram answers the second reader **409 Conflict**. So Find chat, on the web
page, no longer asks Telegram itself; it asks the running poller what chat it
saw last.

When something goes wrong the poller waits, longer each time — 5 s, 10, 20…
up to 5 minutes (**exponential backoff**). The wait is not `time.sleep`:

```python
def _wait_after(self, problem, seconds=None):
    if problem != self.trouble:
        logger.warning("Telegram commands: %s", problem)
        self.trouble = problem
    wait = seconds or self.backoff
    self.backoff = min(self.backoff * 2, MAX_BACKOFF)
    self.stopping.wait(wait)
```

`self.stopping` is a `threading.Event` (section 24). `wait(seconds)` sleeps
until the time passes **or** someone calls `stopping.set()`, whichever comes
first — Java's `CountDownLatch.await(timeout)`, C#'s
`ManualResetEventSlim.Wait(timeout)`. So `stop()` wakes the thread at once
instead of leaving it asleep for five minutes. The `if problem != self.trouble`
line is the "log once" rule: a network outage that lasts an hour writes one
warning, not seventy.

`seconds or self.backoff` uses `or` to pick a value, not a boolean: it
returns the left side if it is truthy, else the right — C#'s `seconds ??
backoff`, except that `0` and `""` count as missing too.

A function that returns two things returns a **tuple**:

```python
def _api(token, method, fields, timeout):
    ...
    return response.json(), ""
    ...
    return None, _redact(str(problem), token)

payload, problem = _api(...)
```

`return a, b` builds a tuple and `x, y = ...` unpacks it — C#'s
`(var payload, var problem) = Api(...)`. `notify.event` does the same and
returns `(sent, held)`.

## 28. Optimistic concurrency: send what you saw (R41)

A person's page shows the views as a grid, and × deletes "view number 7". But
between loading the page and the click, a face scan can drop the oldest
waiting view, and number 7 is now the photo that was number 8. Locking the
gallery while the user looks at a page is not an option. The fix is the one
databases use:

```python
def _check_view(views, index, expected):
    if expected is not None and 0 <= index < len(views):
        if (Path(views[index]).name if views[index] else "") != expected:
            raise ViewsChanged()
```

The page sends the index **and** the name of the photo it showed there; the
server checks, under the gallery lock, that it is still that photo, and
refuses with 409 if not. The page then reloads and the user clicks again. It
is the same idea as an HTTP `If-Match` with an ETag, or a `[Timestamp]` row
version in Entity Framework: nobody waits for anybody, and a change made on
stale information is refused instead of applied to the wrong thing. It is
called *optimistic* because it assumes conflicts are rare and only pays when
one happens.

The check runs **inside** `with _GALLERY_LOCK:`, in the same block as the
change. Checking first and changing in a second step would leave a gap for
the scan to slip into — the same lesson as section 26.

`ViewsChanged` is an exception class with no body but its docstring:

```python
class ViewsChanged(Exception):
    """The view at a position is no longer the one the page showed there (R41)."""
```

The docstring is enough to make a valid class body, so no `pass` is needed.
The web route turns it into the 409 with `except faces.ViewsChanged: raise
HTTPException(409, ...)` — a typed exception crossing layers, as in Java.

## 29. A checkbox drawn as a switch

Settings → Notifications has 21 on/off switches. They are plain checkboxes:

```html
<input type="checkbox" role="switch">
```

`role="switch"` tells screen readers to announce "switch, on" instead of
"checkbox, checked"; the keyboard (Tab, Space) works because it *is* a form
control. The look is CSS only: `appearance: none` removes the browser's own
drawing of the box, the input itself becomes the rounded track, and a
`::before` pseudo-element — a box CSS adds inside the element, with no HTML
for it — is the round knob. `:checked::before` moves the knob right with a
`transform: translateX(...)`, and a `transition` animates it. No library: the
browser already has the control; only its picture changes.

## 30. Changing one field of an immutable tuple, and a set that keeps order

**`_replace` (R44).** `Detection` is a `NamedTuple` (7.2 of ARQUITETURA): like
a Java `record`, its fields cannot be assigned. When a `dog` box turns out to
be the person who stood there a moment ago, the code needs the same box with
another label:

```python
detection = detection._replace(label=CLASS_NAMES[class_id])
```

`_replace` returns a **copy** with the named fields changed — what a `with`
expression does to a C# record (`d with { Label = "person" }`). The leading
underscore is not "private" here: `namedtuple` prefixes its own methods with
`_` so they cannot clash with a field someone calls `replace`.

**`dict.fromkeys` (backlog 26).** The page may send the same id twice. To drop
duplicates and keep the order the user picked them in:

```python
for entry_id in dict.fromkeys(ids):
```

A `dict` keeps insertion order (guaranteed since Python 3.7), and
`fromkeys` makes each id a key with the value `None`, so a repeated id is
just written again in the same place. It is Java's `LinkedHashSet`. A plain
`set(ids)` would also drop the duplicates, but in no particular order.

## 31. Two writers, one file: the lock, and write-then-rename (R43)

`config.json` is changed by a read-modify-write: read the whole file, change
one key, write the whole file. Since the Telegram bot also writes it, two
classic bugs became possible:

- **Lost update.** The page and the bot both read the file, each changes its
  own key, both write: the second write carries the first one's *old* value,
  and the first change vanishes.
- **Torn read.** `write_text` truncates the file and then writes it. A reader
  that opens it in between sees an empty or half file.

The lost update is fixed with a lock around the whole cycle:

```python
_LOCK = threading.RLock()

def update(**changes):
    with _LOCK:
        values = load()
        values.update(changes)
        return save(values)
```

`with _LOCK:` is C#'s `lock (...) { }` or Java's `synchronized`. It is an
`RLock` — a *re-entrant* lock, Java's `ReentrantLock` — because `update` holds
it and then calls `save`, which takes it again; a plain `Lock` would wait for
itself forever. (C#'s `lock` and Java's `synchronized` are re-entrant by
default; Python's `Lock` is not.)

The torn read is fixed by never writing the real file at all:

```python
temporary.write_text(text, encoding="utf-8")
os.replace(temporary, FILE)
```

Write everything to a temporary file next to it, then rename it over the old
one. The rename is atomic, so a reader opens either the old file or the new
one, never half of either. It is how editors and databases save files, and
what .NET's `File.Replace` does. The temporary file must be on the same disk —
hence next to `config.json`, not in the system's temp folder: `os.replace`
cannot move a file across disks, and a move that copies is not atomic.

Windows adds one wrinkle that Linux does not have: a file that another thread
has open cannot be replaced, and cannot be opened while it is being replaced.
Both sides answer `PermissionError`, so both retry for a moment (50 × 10 ms)
instead of failing. The measurement that justified each piece is in
ARQUITETURA 11.6.
