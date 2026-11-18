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
the M900; `python -m` goes through the signed Python instead (INSTALL 1.2).

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
the files instead of copying them. See ARCHITECTURE 3.1.

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
would suggest — switched TCP off silently (ARCHITECTURE 5.8). The lesson: in
Python the **order** of imports can carry meaning, and nothing in the file
warns you when it does.

### 2.3 `if __name__ == "__main__"`

```python
if __name__ == "__main__":
    main()
```

`__name__` is `"__main__"` when the file is run directly, and the module's
name when it is imported. Without that guard, `tools/diagnose.py`
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
disk; `tools/rebuild_faces.py` passes one gallery for every clip.

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
> (ARCHITECTURE 5.5). The `deque(maxlen=12)` that keeps ffmpeg's last error
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
queue up (ARCHITECTURE 10.9):

```python
_SCAN_LOCK = threading.Lock()

def scan_clip(clip, camera, started_at, gallery=None, moments=(), busy=None):
    with _SCAN_LOCK:
        ...
```

`with lock:` is C#'s `lock (obj) { }` and Java's `synchronized`: it acquires
on entry and releases on exit, even on an exception. The rule of thumb is the
same in both languages — a native object shared between threads needs an
owner or a lock. The GIL is not that lock. Since backlog 46 the scans
take turns instead of one lock, so a quick pass can go first (56.1).

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
(ARCHITECTURE 15).

---

## 17. A neural network without PyTorch: `cv2.dnn`

YOLO runs through OpenCV's `dnn` module, on the `.onnx` file — the standard
format for taking a trained network from one library to another. PyTorch left
the project because of Smart App Control (ARCHITECTURE 7.11), and with it the
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
keep = cv2.dnn.NMSBoxes(boxes, scores, floor, NMS_THRESHOLD)
return [(boxes[i], scores[i], classes[i]) for i in np.array(keep).ravel()]
```

The suppression is *greedy*: boxes are taken from the most confident down,
and a box is discarded only when a box already kept overlaps it. So adding
weaker boxes — a lower `floor` — never removes a stronger one; that is why
the detector can run YOLO once at the lowest of the three minimums and judge
each label afterwards (backlog 31, ARCHITECTURE 7.14).

`np.array(keep).ravel()` is there because, depending on the OpenCV version,
`keep` comes as a flat list or as a column `[[0], [3]]`; `ravel()` flattens
both forms into `[0, 3]`.

### 17.5 `zip`

`zip` walks two sequences in parallel — in `tools/make_icon.py`, each image
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

And `tools/diagnose.py` uses `with tempfile.TemporaryDirectory() as
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

A bad-detection report (ARCHITECTURE 21, R36) does three things to a gallery
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

The Telegram bot (`bot.py`, ARCHITECTURE 22.5) has to learn about a `/home`
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

**`_replace` (R44).** `Detection` is a `NamedTuple` (7.2 of ARCHITECTURE): like
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
ARCHITECTURE 11.6.

## 32. Record now, write once: a unit of work (R45)

Merging a photo into a dog rewrites the sighting files that pointed at it.
Before R45, `_merge` did that I/O itself, so a batch of 60 photos scanned
every sighting file 60 times. Now `_merge` only **records the intent**:

```python
self.repoints = {old: target["id"] if new == source["id"] else new
                 for old, new in self.repoints.items()}
self.repoints[source["id"]] = target["id"]
```

and `save()` applies the whole map in one pass before writing
`gallery.json`. It is the **Unit of Work** pattern — Entity Framework's
`DbContext` collects changes and `SaveChanges()` writes them at once; JPA's
persistence context does the same at `flush()`.

The first line is a **dict comprehension**, `{key: value for ... in ...}` —
like a LINQ `ToDictionary` or Java's `Collectors.toMap`, written inline. Its
job here is to collapse chains: if `a` was merged into `b` (`{a: b}`) and now
`b` is merged into `c`, every value equal to `b` becomes `c`, then `b: c` is
added — `{a: c, b: c}`. A sighting of `a` goes straight to `c`, never to the
`b` that no longer exists. `x if cond else y` is Python's ternary, C#'s
`cond ? x : y` written in reading order.

`load()` starts every operation with `self.repoints = {}`, so a merge from an
operation that failed before saving is never applied — as a `DbContext` that
is thrown away without `SaveChanges()`.

## 33. Counting calls in a test: `monkeypatch` as a spy (R45)

R45's acceptance was "each sighting file is read once". The test proves it by
replacing a method of a real class for the duration of one test:

```python
original = faces.Path.read_text

def counting(path, *args, **kwargs):
    reads[path.name] = reads.get(path.name, 0) + 1
    return original(path, *args, **kwargs)

monkeypatch.setattr(faces.Path, "read_text", counting)
```

`monkeypatch` is a pytest fixture: ask for it as a test parameter and pytest
hands it in, as an injected dependency. `setattr` swaps `Path.read_text` for
`counting`, which counts and then calls the original — Mockito's `spy`, but
on the class itself, and possible only because Python classes can be changed
at run time (Java and C# would need an interface or a mocking library that
rewrites bytecode). At the end of the test pytest **undoes it on its own**;
`monkeypatch.undo()` undoes it early, so the test's last check reads files
normally. `*args, **kwargs` take any positional and keyword arguments and pass
them on unchanged — C#'s `params object[]`, plus named arguments.

## 34. A rename git can follow, and a `.bat` that works from any folder (R10)

**Git does not store renames.** It stores snapshots; when it shows history it
*guesses* that a deleted file and an added one with at least 50 % of the same
content are one file moved. That is why R10 renamed the files in one commit
with almost no other change (`git mv`), and translated their text in the
next: `diagnose.py` translated would no longer look 50 % like
`diagnostico.py`. `git log --follow docs/ARCHITECTURE.md` walks back across
the rename to the file's first `ARQUITETURA.md` commit. An IDE's "Rename
file" refactoring does the same in one step; in git, the rename is inferred
afterwards.

**`%~dp0` in a batch file** is "the drive and folder of this script", so
`cd /d "%~dp0"` makes a `.bat` work wherever it is started from — Java's
"relative to the class, not the working directory". `call other.bat %*` runs
another batch file and comes back, passing every argument along (`%*`).
Without `call`, cmd would jump to the other file and never return: that is
how the old `jarvis_vigilancia.bat` handed over to `jarvis_headless.bat` in a
single line, for the one release it was kept (removed in `v2026.10.12.4`).

## 35. Is this file really Python? Authenticode, and exit codes across languages (R7)

**Authenticode** is Windows' code signing: the publisher signs a hash of the
`.exe` with a certificate, and Windows can verify both that the file was not
changed and who signed it — the same idea as a signed JAR (`jarsigner
-verify`) or an Authenticode-signed .NET assembly. Smart App Control trusts a
valid signature without asking Microsoft's cloud about the file's reputation,
which is why the project insists on the python.org build (INSTALL 1.2).
PowerShell reads a signature with one cmdlet:

```powershell
$signature = Get-AuthenticodeSignature -LiteralPath $Path
if ($signature.Status -eq 'Valid' -and $signature.SignerCertificate.Subject -match 'Python Software Foundation') {
```

`Status` is an enum — `Valid`, `NotSigned`, `HashMismatch` (the file changed
after signing), `UnknownError`… — and `SignerCertificate` is a .NET
`X509Certificate2`, the very class C# uses; `Subject` is its
`CN=Python Software Foundation, O=…` string, and `-match` is a regular
expression test. `-and` short-circuits like `&&`, so an unsigned file, whose
`SignerCertificate` is `$null`, never reaches `.Subject`. `-LiteralPath`
instead of `-Path` takes the text as it is: `-Path` would treat `[` and `]`
in a folder name as a wildcard. `uv`'s own launchers (`jarvis.exe`,
`pytest.exe`) come back `NotSigned` — which is how the check was proved to
fail when it should.

**The exit code is the contract between the two languages.** The check is
one script, `tools/check_python.ps1`, that ends in `exit 0` or `exit 1`, and
two callers read that number in their own way:

```bat
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\check_python.ps1" -Path "%~dp0.venv\Scripts\python.exe"
if errorlevel 1 (
```

From `cmd`, `powershell -File` makes the script's `exit 1` the process's exit
code, which cmd calls `errorlevel`. `if errorlevel 1` means "1 **or more**",
not "exactly 1" — an old quirk that happens to be what you want here.
`-ExecutionPolicy Bypass` lets an unsigned `.ps1` run for this one call
without changing the machine's policy.

```powershell
& (Join-Path $PSScriptRoot 'check_python.ps1') -Path (Join-Path $ProdDir '.venv\Scripts\pythonw.exe') | Out-Host
if ($LASTEXITCODE) { throw '...' }
```

Inside PowerShell, `&` runs the script in the same process, and its `exit 1`
ends only that script and sets `$LASTEXITCODE` — like reading
`Process.ExitCode` in C# and throwing when it is not zero. `$PSScriptRoot` is
the folder of the script that is running, Java's "relative to the class"; so
`production.ps1` always finds the `check_python.ps1` that sits beside it.
`| Out-Host` sends what the script prints to the screen instead of returning
it as the expression's value. Writing the rule once and calling it from both
places is the same reason a C# solution moves shared code into a library
instead of copying it into two projects.

## 36. A module as a singleton, and a clock only one module sees (backlog 29)

`analysis.py` holds the On/Off switch with no class at all:

```python
_lock = threading.Lock()
_on = True
_changed = time.monotonic()


def set_on(wanted):
    global _on, _changed
    with _lock:
        if _on == bool(wanted):
            return False
        _on = bool(wanted)
        _changed = time.monotonic()
    return True
```

**A module is imported once per process.** The first `import` runs the file
and keeps the module object in `sys.modules`; every later `import analysis`,
from any file, gets that same object. So its globals are one per process —
what a C# `static class` or a Java class with `static` fields is, without
writing the class. `cameras.py`, `bot.py` and `web.py` all read the same
`_on`.

**`global` is needed to assign, not to read.** Inside a function, assigning
`_on = …` would create a new local variable, as a C# local would hide a
field; `global _on, _changed` says "the module's". `is_on()` only reads, so it
needs nothing.

**The lock guards check-then-set**, not the read. Two threads calling
`set_on(False)` at once could both see `_on` true and both answer "changed";
under the lock only one does. Reading `_on` alone needs no lock: rebinding a
name is atomic under the GIL, so a reader sees the old value or the new one,
never half of it.

**A restart, inside a test.** `importlib.reload(analysis)` runs the file again
inside the same module object: `_on = True` executes again, exactly what a
new process does. That is how `test_a_restart_starts_on` proves Off is never
kept.

**A fake clock for one module.** The reminder fires after 3 hours; no test
waits that long. The test replaces the name `time` *inside* `analysis` (and
`clips`) with an object that only has `monotonic()`:

```python
class Clock:
    def __init__(self, now=1000.0):
        self.now = now

    def monotonic(self):
        return self.now

found = Clock()
monkeypatch.setattr(analysis, "time", found)
found.now += 3 * 3600
```

`analysis.time.monotonic()` now reads `found.now`, which the test moves by
hand. Only those two modules see it: pytest, `threading` and everything else
keep the real `time`, which `monkeypatch.setattr(time, "monotonic", …)` would
have replaced for all of them. In C# the code would have to be written for it
— an `ISystemClock` or .NET 8's `TimeProvider` injected in the constructor;
Python lets the test swap the module's reference afterwards, and duck typing
means `Clock` needs no interface, only the one method that is called.
`monkeypatch` puts the real `time` back when the test ends.

**Helpers from another test file.** `test_on_off.py` reuses the fake Telegram
of `test_bot.py` with `from test_bot import Telegram`. That works because
pytest, in its default "prepend" import mode, puts each test file's folder at
the front of `sys.path` — so `tests/` is importable as if it were a package.

## 37. Greedy one-to-one matching (R46)

Each vanished person may turn **one** dog box into a person. With two dog
boxes and one vanished person, the more confident box wins:

```python
replaced = {}
dogs = sorted((d for d in raw if d[2] == DOG_CLASS), key=lambda d: d[1], reverse=True)
for box, _, _ in dogs:
    best = max(vanished, key=lambda person: iou(box, person), default=None)
    if best is not None and iou(box, best) >= REPLACED_PERSON_IOU:
        replaced[tuple(box)] = best
        vanished.remove(best)
```

- `sorted(…, key=…, reverse=True)` is LINQ's `OrderByDescending`; `d[1]` is
  the confidence in a `(box, confidence, class_id)` tuple.
- `max(…, key=…, default=None)` is `MaxBy` that answers `None` for an empty
  list instead of raising — once every vanished person is claimed, the
  remaining dog boxes simply find nothing.
- `vanished.remove(best)` removes the first element **equal** to `best`,
  like `List<T>.Remove`: a claimed person is not offered to the next box.
- `tuple(box)` as the key: a list can change, so Python refuses it as a
  dictionary key (it is not hashable); a tuple cannot change and can be one —
  the same reason a C# dictionary key should be an immutable record. The loop
  later asks `tuple(box) in replaced`.

**Greedy, not optimal.** Taking the best box first and never revisiting is
the cheap cousin of the **Hungarian algorithm**, which finds the pairing with
the best total over every box and person at once — what ByteTrack and
similar trackers use, through `scipy.optimize.linear_sum_assignment`. With
the one or two boxes a camera sees here, both give the same answer, and the
greedy one needs nothing installed.

## 38. Vectorising a pairwise loop, `inf` as "cannot compare", and identity (backlog 28)

**The loop that became a matrix product.** `DogGallery.distances` used to
call `distance(a, b)` for every pair — 820 Python calls for 41 views, 36 ms.
The Bhattacharyya coefficient of two histograms is `Σ √(aᵢ·bᵢ)`, which is a
dot product of their square roots. Put every histogram in a row of a matrix
`A`, and **all** the coefficients come out of one product:

```python
roots = np.sqrt(np.clip(histograms, 0.0, None))
matrix = np.sqrt(np.clip(1.0 - roots @ roots.T, 0.0, None))
```

`@` is matrix multiplication; `roots @ roots.T` is a 41×41 table whose cell
`[i, j]` is the dot product of rows `i` and `j`. NumPy hands it to a compiled
BLAS routine — the C# analogue is replacing two nested `for` loops with a call
into a native maths library. 0.5 ms instead of 36.

The `if`s of the scalar version become **boolean masks** and **broadcasting**:

```python
empty = histograms.sum(axis=1) <= 0
matrix[empty, :] = 1.0
infrared = x[:, 0] != 0
matrix = np.where(infrared[:, None], tone, colour)
matrix[infrared[:, None] != infrared[None, :]] = np.inf
```

- `matrix[empty, :] = 1.0` writes every row whose mask is `True` — no loop.
- `infrared[:, None]` turns a vector of 41 into a 41×1 column and
  `infrared[None, :]` into a 1×41 row; comparing them **broadcasts** to a
  41×41 table, true wherever the two views differ in lighting.
- `np.where(cond, a, b)` picks per cell, like `cond ? a : b` over a whole
  array.

**`np.inf` as "cannot be compared".** A day view and a night view have no
distance. Storing `inf` instead of `None` keeps the arithmetic working: `min`
skips it naturally, `x > inf` is always false, and `np.isfinite(...)` picks the
comparable ones. `faces.replaced_view` needs no `None` checks at all.

**Identity, not equality.** `settle_waiting` counts which chosen views
survived by `id(embedding)` — the object's identity, like `==` on references in
Java — because two views can hold equal lists of numbers and still be different
views. `id` is only safe while every object compared is alive, which holds
here: the gallery and the queue keep them all until the count is done.

**Delete after commit.** `save()` writes `gallery.json` first and only then
deletes the photos of the views that left (`self.dropped`) — the order of a
database commit followed by file cleanup. A crash in between leaves an unused
photo, never a view whose photo is gone.

**Importing a script in a test.** `tools/` is not a package, so the test puts
it on `sys.path` and loads the script by name:

```python
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
settle_waiting = importlib.import_module("settle_waiting")
```

after which `settle_waiting.main(["--dry-run"])` runs the tool in the test's
process, and `monkeypatch` can replace its `web.already_running`.

## 39. A function as a default argument, asking again after a while, and spreading a dict (backlog 31)

**A function is a value.** `SubjectDetector(load_settings=settings.load)`:
the default is the function itself — no parentheses — not its result.
Production writes `SubjectDetector()` and gets the real reader; a test passes
`lambda: dict(settings.DEFAULTS)` and never touches the machine's
`config.json`. In Java the constructor would take a `Supplier<Settings>`, in
C# a `Func<Settings>`, with an overload that supplies the real one; Python
needs no overload. One catch: a default is evaluated once, when `def` runs,
so a test that later replaces `settings.load` does not reach a detector
built with the default. It must pass its own function, or change
`settings.FILE`, which `load` reads at each call — what the tests do.

**Asking again after a while.** Nobody tells the detector that a setting
changed; it asks again when its copy is older than
`SETTINGS_REFRESH_SECONDS`:

```python
def _minimums(self):
    clock = time.monotonic()
    if self.minimum_read is None or clock - self.minimum_read >= SETTINGS_REFRESH_SECONDS:
        self.minimum = minimum_confidences(self.load_settings())
        self.minimum_read = clock
    return self.minimum
```

A cache with a time-to-live. Being told — an observer the web would call on
save — is instant, but ties `web` to every camera thread and misses a hand
edit of the file; asking costs a change up to 2 s late and a 0.23 ms read
per camera every 2 s. `time.monotonic()`, not `time.time()`: it never jumps
back when Windows corrects the clock.

**Spreading one dict into another.** `**` inside a dict literal copies a
dict's pairs into the new one, like `{...a}` in JavaScript:

```python
EDITABLE = {
    "archive_min_free_gb": float,
    **{key: float for key in settings.CONFIDENCE_KEYS},
}
```

The inner part is a dict comprehension, `{key: value for ...}`, building
`{"confidence_person": float, ...}` from the one tuple in `settings.py`: a
label added there is editable here with no second list.

**`True` is an `int`.** `confidence_valid` asks
`isinstance(value, (int, float)) and not isinstance(value, bool)`, because
`bool` is a subclass of `int` in Python — `isinstance(True, int)` is true and
`True + True` is 2. Java and C# keep `boolean` and `int` apart, so the second
test has no equivalent there.

## 40. A face pipeline in four steps, and how to compare two models fairly (R49)

`tools/face_bench.py` (ARCHITECTURE 10.14) runs other people's networks by
hand, so it shows what OpenCV's `FaceDetectorYN` and `FaceRecognizerSF` had
been doing out of sight.

**Detector, landmarks, alignment, embedding.** A detector (YuNet, SCRFD)
gives a box and five points: the eyes, the nose tip and the mouth corners. A
recogniser (SFace, ArcFace) does not take the box. It takes a 112×112 crop in
which those five points land on fixed spots, a template, so that every face
it sees is posed the same way. The step between is a **similarity
transform**, a rotation plus one scale plus a shift, fitted from the five
detected points to the five template points. The bench does it this way:

```python
matrix, _ = cv2.estimateAffinePartial2D(points, ARCFACE_POINTS * (size / 112), method=cv2.LMEDS)
return cv2.warpAffine(image, matrix, (size, size), borderValue=0.0)
```

LMEDS is a robust fit that may throw away a point it judges an outlier, and
on 19 of 146 views it did. With five points and no real outliers, plain least
squares is the right fit, and OpenCV already has one: SFace's
`FaceRecognizerSF.alignCrop` aligns onto ArcFace's own template, so it serves
any recogniser trained on that template. Given SCRFD's points in YuNet's row
layout — the box, ten coordinates and the score, 15 numbers — it gave
exactly the crop insightface makes, pixel for pixel. The switch uses it.
Better points mean a
better-aligned crop, which is why changing only the detector moved ArcFace
from 36 right answers to 125. The final step, the **embedding**, is the
recogniser's output: 128 numbers for SFace, 512 for ArcFace, compared by
cosine.

**Decoding a detector's raw output** (`Scrfd.detect`). OpenCV wraps YuNet's
decoding; SCRFD comes as a bare ONNX graph, so the tool does it. The network
looks at the image through three grids, one cell every 8, 16 and 32 pixels,
with two anchors per cell. For each anchor it outputs a score, four distances
from the cell centre to the box edges, and ten offsets to the landmarks:

```python
grid = np.stack(np.mgrid[:side, :side][::-1], axis=-1).reshape(-1, 2)
centres = np.repeat(grid * stride, 2, axis=0)
box = [cx - d0, cy - d1, cx + d2, cy + d3]
```

`np.mgrid` builds two arrays of row and column indices, the same as two
nested `for` loops written as data. `[::-1]` swaps them to (x, y), and
`np.repeat(..., 2, axis=0)` writes each centre twice, once per anchor. The
anchors whose score clears the threshold become boxes. Non-maximum
suppression (`cv2.dnn.NMSBoxes`) then keeps, among boxes that overlap, only
the most confident. In Java terms it is a stream over every grid cell,
filtered by score and then deduplicated.

**ONNX export.** AdaFace and MagFace ship as PyTorch weights.
`torch.onnx.export` runs the network once on a sample input, records every
operation it performs, and writes that graph to a file. `cv2.dnn` then runs
the file with no PyTorch at all. It is like compiling a C# project to a DLL
that another program loads without the compiler. The export ran once, in a
throwaway environment, and only the `.onnx` file stayed.

**Comparing models with different scales.** Each model's cosines live on
their own scale: SFace calls 0.45 "sure", while ArcFace puts two different
people at 0.31 at most. A single shared threshold would favour whichever
model happens to score high. So the bench uses **leave-one-out**: each view
is matched against all the others, with itself and its exact copies left
out, as if it were a new photo. It then **sweeps** the threshold and reports
the first threshold at which nothing is wrong, together with how many are
right there. "0.275 → 125" against "0.375 → 110" compares the two models at
equal safety, each on its own scale. It is a cross-validation, the same idea
as holding out test data in any classifier.

**An embedding's length as quality.** Cosine ignores a vector's length, so
a recogniser's raw output is free to carry it. AdaFace and MagFace are
trained so that the length grows with how recognisable the face is. A
head-top should come out short. It did not: lengths of 14–21 on head-tops
against 14–21 on faces (AdaFace), 20–31 against 20–28 (MagFace), and 10–21
against 9.5–21 for ArcFace, which makes no such promise. The idea is sound, but this house's
head-tops look enough like faces to the networks.

**Data that a subclass overrides.** `ArcFace(AdaFace)` and `MagFace(AdaFace)`
change only class attributes: `model = BENCH_DIR / ...` and
`pixels = (scale, mean, rgb)`. `self.model` inside `AdaFace.__init__` reads the
subclass's value, because Python looks an attribute up on the object's own
class first. Java's static fields are not looked up that way: a static read
through `this` resolves at compile time. The nearest Java equivalent is an
overridden getter. `PIPELINES` maps each name to a **factory**, either the
class itself or a `lambda` that calls it with arguments, so a model is loaded
only when its pipeline is picked — a `Map<String, Supplier<Pipeline>>`.


## 41. A migration that survives a rollback: zip members, atomic writes, a hash, and lock order (R49)

R49 step 2 changed every face embedding from SFace's 128 numbers to ArcFace's
512. Vectors from two networks live in **different spaces**: even at the same
length, a cosine between them would mean nothing. So every stored view is
embedded again from its photo, and `cosine` returns 0.0 for two lengths
instead of letting `np.dot` raise. The interesting part is how the new file is
built so that the old version still works after a rollback (ARCHITECTURE
10.14). Five small tools do it.

**One member of a zip, without extracting the rest.** InsightFace ships
`buffalo_l.zip` (289 MB, five models); the program needs two:

```python
with zipfile.ZipFile(archive) as bundle:
    for name in missing:
        partial = folder / f"{name}.part"
        partial.write_bytes(bundle.read(name))
        partial.replace(folder / name)
```

`ZipFile.read(name)` decompresses only that member — Java's
`ZipFile.getInputStream(entry)`. The `with` closes the archive even on an
exception, so the `finally: archive.unlink(...)` around it can delete it.

**Write beside, then rename.** `partial.replace(target)` is `os.replace`: on
the same volume it is an atomic rename, so a reader sees the old file or the
new one, never half of one — .NET's `File.Replace`, Java's
`Files.move(..., ATOMIC_MOVE)`. A crash mid-write leaves a stray `.part`, not
a truncated gallery.

**`collections.Counter`**, a `dict` whose missing keys read as 0, is the
migration's tally:

```python
tally = Counter()
tally["no face"] += 1
```

No `tally.get("no face", 0) + 1`, and no `defaultdict(int)` to declare.

**A hash as a change detector between two programs.** The new file records
`hashlib.sha1(gallery_json_bytes).hexdigest()` of the file it was built from.
The new version never writes `gallery.json`, so a different hash at start can
only mean an older version ran meanwhile — a rollback — and the migration runs
again. Comparing timestamps would be fragile (a copy changes them); comparing
content by hash is not. SHA-1 is fine here: nobody attacks this file; it only
has to notice a change.

**Lock order.** A scan takes `_SCAN_LOCK` (the networks; since backlog 46 a turn, 56.1) and, inside, the
gallery's `_GALLERY_LOCK`. Undoing an old report must embed photos (needs
`_SCAN_LOCK`) and then write the gallery (needs `_GALLERY_LOCK`). If it took
the gallery lock first and then waited for the scan lock, while a scan held
the scan lock and waited for the gallery lock, both would wait forever — the
classic deadlock, same as two Java `synchronized` blocks in opposite orders.
So `put_back` calls `refit` **before** it takes `_GALLERY_LOCK`: every thread
takes the two locks in the same order, or not at the same time.

**PowerShell: reading a file from another version, and a 5.1 trap.**
`git show v2026.10.14:src/jarvis/downloads.py` prints a file as it is in that
tag, without checking anything out; `production.ps1` runs it before stopping
production. A native program's exit code is in `$LASTEXITCODE`, not in
`$?`'s exceptions. The trap, found in review 23: with
`$ErrorActionPreference = 'Stop'` at the top of the script, Windows
PowerShell 5.1 wraps each line a native command writes to a **redirected**
stderr (`2>$null`, `2>&1`) in an error record — and `Stop` makes that record
throw. So `git show` of a missing path threw before the
`if ($LASTEXITCODE)` line could run:

```powershell
$previous = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
$source = git -C $ProdDir show "${Version}:src/jarvis/downloads.py" 2>$null
$found = ($LASTEXITCODE -eq 0)
$ErrorActionPreference = $previous
```

`CurrentVersion`, in the same script, already did this; the M900 runs 5.1,
the PowerShell Windows ships.

## 42. A lock between processes, a tuple as a ranking, a slider with a bent scale, and a page that adapts (developer 22)

Six small things from one delivery: backlog 34–36, R51, R52 and R30 (b)
(ARCHITECTURE 7.14, 10.3, 10.12, 10.14, 22.4, 22.7).

**A lock that other processes see — `filelock` (R52).** `threading.Lock`
(PYTHON 14) works between the threads of **one** process, like C#'s `lock` /
`Monitor` or Java's `synchronized`. Two copies of J.A.R.V.I.S. are two
processes, each with its own memory, so each would have its own
`threading.Lock` and neither would see the other's. What both see is the
file system, and the operating system can lock a file:

```python
from filelock import FileLock

with FileLock(target.with_name(f"{target.name}.lock")):
    return _migrate(target, source, backup_dir)
```

On Windows `filelock` opens the `.lock` file and locks a byte of it with
`msvcrt.locking`; a second process asking for the same lock waits until the
first releases it. It is .NET's **named `Mutex`** (`new Mutex(false,
"Global\jarvis-gallery")`) or Java's `FileChannel.lock()`. Two properties
matter here: if the holder crashes, Windows closes its handles and the lock
is gone — no stale lock to clean by hand; and the file is deleted on
release. The `with` block is a `try/finally` (C#'s `using`, Java's
try-with-resources): the lock is released even when `_migrate` raises, and
`return` inside the `with` still runs the release first. The package is pure
Python — a few `.py` files calling the standard library — so Smart App
Control has nothing to block (PROCESS 5.3).

**A tuple as a ranking (R51).** `_best_view` must prefer, in order: a view
that matched someone, then one that matched a **named** person, then the
higher score. Python compares tuples element by element, left to right — the
first difference decides, exactly like comparing words letter by letter:

```python
key = (person_id is not None, bool(person and person["name"]), score)
if best is None or key > best[0]:
    best = (key, person_id, score, index)
```

`(True, False, 0.61) < (True, True, 0.31)`: the second element already
differs, so the score is never looked at. `False < True` because `bool` is a
subclass of `int` (0 and 1). In Java this is
`Comparator.comparing(found).thenComparing(named).thenComparing(score)`; in
C#, `OrderBy(...).ThenBy(...)`, or a `ValueTuple`, which compares the same
way. `max(views, key=...)` would do it in one line; the loop is there because
it also keeps the index of the winning view, whose crop is the one learned.

**A slider whose middle is not the middle of its range (backlog 35).** The
user wanted the default in the middle of the slider, but 0.35 is not the
middle of 0.20–0.90. The answer is two straight lines that meet at the
default — a **piecewise linear** map:

```python
def slider_position(value, default):
    low, high = CONFIDENCE_RANGE
    middle = SLIDER_STEPS / 2
    if value <= default:
        share = (value - low) / (default - low) if default > low else 1.0
        return round(share * middle)
    share = (value - default) / (high - default) if high > default else 0.0
    return round(middle + share * middle)
```

`share` is "how far along this half", from 0 to 1. The `if default > low else
1.0` is Python's conditional expression — C#'s and Java's `cond ? a : b`
written in the order of the sentence — and it avoids dividing by zero if a
default ever sat at an end. `slider_value` is the same line read backwards,
rounded to two decimals. **Why 1000 steps:** the page sends every slider on
Save, so a slider nobody touched must give back exactly the number it showed.
With 100 steps, one step of the person slider's right half is 0.011, so 0.40
lands between two steps and comes back as 0.41; with 1000 it is 0.0011, finer
than the two decimals stored, and every two-decimal value survives the round
trip. A test checks it for several defaults rather than trusting the
argument.

**The page: a range input, a grid that folds, and blocking dialogs.**

```html
<input type="range" id="slider-confidence_person" name="confidence_person">
```

`type="range"` is the browser's own slider: `min`, `max`, `step` and `value`
are set from `/api/settings`, and it works with a finger, a mouse or the
arrow keys. Its `<label for="...">` names it for screen readers. The
Notifications part puts two panels side by side with a **CSS grid**:

```css
.settings[data-part="notifications"] {
  grid-template-columns: minmax(0, 3fr) minmax(300px, 2fr);
}
@media (max-width: 860px) {
  .settings[data-part="notifications"] { grid-template-columns: minmax(0, 1fr); }
}
```

`fr` is a share of the free space — 3 parts for the table, 2 for Telegram,
like star sizing (`3*`, `2*`) in a WPF `Grid`. `minmax(300px, 2fr)` stops the
Telegram column from getting narrower than 300 px; `minmax(0, 3fr)` lets the
table shrink instead of pushing the page sideways. The `@media` block is a
rule that applies only while the window is at most 860 px wide: there the grid
becomes one column and the panels stack. That is how one page serves a phone
and a desktop without two versions.

On the header switch, `confirm()` and `alert()` are the browser's own modal
dialogs: `confirm` **stops the script** until the user answers and returns
`true` or `false`, so Off asks before any request leaves:

```javascript
if (!wanted && !confirm("Switch analysis Off? ...")) return;
analysisLabel.disabled = true;
try {
  showAnalysis((await send("/api/analysis", { on: wanted })).analysis);
} catch (problem) {
  alert(`Not done: ${problem.message}`);
} finally {
  analysisLabel.disabled = false;
}
```

`disabled` during the request stops a second click from sending a second
change; `finally` turns it back on whatever happened — the same
`try/catch/finally` as in Java and C#, around an `await` — JavaScript's `async`/`await` reads like C#'s.

**Leave-one-out, and why it matters (R51).** To ask "does the best view
recognise better than the heaviest?", the developer scored production's clips
against production's gallery. But the gallery **learned from those same
clips**: some of their views are stored in it. Scoring a clip against a
gallery that holds the clip's own views measures memory, not recognition —
it gave 0.959. Hiding, for each clip, the views written while it was scanned
gave the honest 0.551. It is the rule behind every fair test of a model: never
test on what it was trained on — in machine learning, the split between a
training set and a test set; "leave-one-out" when each item in turn is the
test and all the others the reference (PYTHON 40 used it for the face bench).

## 43. Functions passed as values, a thread's keyword arguments, every cosine at once, embeddings against histograms, and a list drawn in pages (developer 23)

From one delivery: R42 (b), backlog 32 for faces, R53 step 1, backlog 37
and 38 (ARCHITECTURE 7.14, 10.15, 17.17, 20, 22.3).

**A function as an argument, and `*extra` (R42 (b)).** Three messages — the
side view, the best view, the hidden person — answer to the same rules: the
`faceless_person` switch, then the camera's cooldown. Instead of copying the
rules three times, `_faceless` takes the function that sends the message:

```python
def _faceless(camera, started_at, image, held, notified, settings, message, *extra):
    if not modes.allowed("faceless_person", settings):
        return 0
    ...
    return int(bool(message(camera, started_at, image, *extra, settings=settings)))

_faceless(camera, started_at, side, held, notified, settings, side_face)
_faceless(camera, started_at, best, held, notified, settings, hidden_person, people, len(found))
```

`side_face` without parentheses is the function itself, not a call: in
Python a function is an ordinary value, like a C# `Func<...>` or delegate,
or a Java `BiFunction` / method reference (`Notify::sideFace`). `*extra`
collects any further positional arguments into a tuple — C#'s `params
object[]`, Java's `Object... extra` — and `*extra` in the call spreads them
back out, so `hidden_person` gets its two numbers and `side_face` gets none.
`int(bool(x))` turns "sent or not" into 1 or 0 for the count.

**A thread's keyword arguments.** `threading.Thread(target=_assemble,
args=(...), kwargs={"people": self.most_people})` runs
`_assemble(*args, **kwargs)` in the new thread. `**` spreads a dict into
named arguments, as `*` spreads a tuple into positional ones. Passing the new
value by name, not as the eleventh position, means no existing caller or
test has to count positions — like a C# lambda `() => Assemble(..., people:
n)` with a named argument. `self.most_people` is read **now**, when the
thread is created, so a new event starting meanwhile cannot change it.

**Every cosine at once, and leaving yourself out (backlog 32).** The
accuracy table matches each of 80 views against the other 79. Two loops in
Python would be 6,400 slow calls. numpy does it as one matrix product:

```python
matrix = rows / np.linalg.norm(rows, axis=1, keepdims=True)
similar = matrix @ matrix.T
scores = np.where(similar[probe] >= COPY_SIMILARITY, -1.0, similar[probe])
top = int(np.argmax(scores))
```

Dividing each row by its length makes it a unit vector, and the dot product
of two unit vectors **is** their cosine; `@` is matrix multiplication, so
`similar[i, j]` is the cosine of views i and j — the whole 80 × 80 table in
one call into compiled code. `keepdims=True` keeps the lengths as an 80 × 1
column so the division applies row by row (broadcasting, PYTHON 38).
`np.where(condition, a, b)` is an element-wise `condition ? a : b`: the
probe's own entry (cosine 1.0 with itself) and its exact copies become −1,
so `argmax` can never pick them. That is leave-one-out without building 80
smaller galleries.

**Learned embeddings against histograms (R53).** A colour histogram counts
how many pixels fall in each band of tone and hue: it knows *how much black*,
nothing about *what shape*. Dark shoes and a black dog have similar counts.
A network trained on millions of images turns a picture into a vector — 384
numbers for DINOv2-small — where pictures that look alike, in shape and
texture as well as colour, land close together; the distance is
`1 − cosine`, as for faces. How the network was trained decides what "alike"
means. MobileNet was trained to *classify* ImageNet's 1,000 classes, 120 of
them dog breeds, so its features are taught to put every dog of one breed
together. DINOv2 was trained without labels, to recognise two crops of the
same image as the same and others as different — closer to "which dog is
this", which is why review 25 chose it for two dogs of one breed.

**Exporting to ONNX once, and OpenCV's two engines.** PyTorch is not
installed in the program's environment (CONTEXT 3), so a model is converted
once, in a throwaway environment, with `torch.onnx.export`: it runs the
model on an example input, records every operation, and writes the graph and
the weights into one `.onnx` file — a portable format, like compiling to
bytecode that another runtime executes. `cv2.dnn.readNetFromONNX` then runs
it. OpenCV 5 has a new graph engine and keeps the old one;
`readNetFromONNX(path, engine=cv2.dnn.ENGINE_CLASSIC)` picks the old one,
which was the only one that ran CLIP. The check that an export is faithful:
the same fixed random input through PyTorch and through `cv2.dnn`, and a
cosine of 1.0 between the two outputs.

**A tick on a slider — `<datalist>` (backlog 38).**

```html
<datalist id="slider-default"><option></option></datalist>
<input type="range" name="confidence_person" list="slider-default">
```

A `<datalist>` is a list of suggested values; an input names it with `list`.
On a text input it becomes an autocomplete menu; on a range input the
browser draws a tick at each value. One list serves the three sliders, and
`showDetection` sets its option to the middle step.

**A list drawn in pages, with a closure (backlog 37).**

```javascript
function paged(container, items, render, shown, key) {
  let count = Math.min(items.length, Math.max(PAGE_STEP, shown.get(key) || 0));
  container.replaceChildren(...items.slice(0, count).map((item, index) => render(item, index)));
  ...
  more.addEventListener("click", () => {
    const next = Math.min(items.length, count + PAGE_STEP);
    more.before(...items.slice(count, next).map((item, index) => render(item, count + index)));
    count = next;
    shown.set(key, count);
  });
}
```

The click handler is a **closure**: it keeps `count`, `items` and `more`
alive after `paged` has returned, and each call of `paged` has its own — as a
C# lambda captures a local variable, or a Java lambda an effectively-final
one (Java would need a one-element array or an `AtomicInteger` to change
`count`; JavaScript and C# let the closure assign it). `more.before(...nodes)`
inserts the new cards just before the button, so the 24 already drawn stay
as they are — no flicker, no lost scroll position. `shown` is a `Map` that
outlives each redraw, so a list the user opened stays open when naming a
photo reloads it; `shown.get(key) || 0` reads 0 for a key never set, as
`dict.get(key, 0)` would in Python.

## 44. A vision transformer's summary token, a pinned download, a stand-in network in every test, and a rule that must come first (developer 24)

From one delivery: R53 step 2, backlog 39, R56 and R57 (ARCHITECTURE 10.2,
10.14, 17.17, 18.7, 20, 22.3).

**The CLS token (R53 step 2).** A convolutional network such as MobileNet
slides small filters over the image. A vision transformer — DINOv2 is one —
first cuts the image into patches: at 224 px, a 16×16 grid of 14 px
squares, 256 patches, each flattened into a vector. It adds one extra vector
that belongs to no patch, the **CLS** ("class") token, and then every layer
lets each of the 257 vectors look at all the others (attention) and update
itself. After the last layer the CLS token has gathered something from every
patch: it is the image's summary, and DINOv2's authors use it as the
image's embedding. That is why the file's output is `(1, 257, 384)` — one
batch, 257 tokens, 384 numbers each — and the program keeps only row 0:

```python
output = self.net.forward()
vector = np.asarray(output, np.float32).reshape(-1, EMBEDDING_SIZE)[0]
```

`reshape(-1, 384)` turns the output into 257 rows of 384, whatever the
leading dimensions (`-1` means "as many as it takes", like letting the
compiler infer an array length), and `[0]` is the CLS row. Hugging Face's
Python model also returns a `pooler_output`, which is this same row after
the final layer norm; the ONNX file does not list it because an ONNX graph
exposes only its declared outputs, and `net.getUnconnectedOutLayersNames()`
shows which those are. Developer 24 checked the CLS row against their own
export: cosine 0.99999988 or more on all 167 bench crops.

**Pinning a download, and reading a file in blocks.** A URL on Hugging Face
`.../resolve/main/...` follows whatever the repository holds today; with a
commit hash in place of `main` it is fixed forever, like depending on a
library at an exact version instead of "latest". The SHA-256 then proves the
bytes are the ones measured:

```python
def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()
```

`iter(callable, sentinel)` — the two-argument form — calls the function
again and again and stops when it returns the sentinel: here, read 1 MB
(`1 << 20`, a bit shift, 2²⁰ bytes) until `read` returns `b""` at the end of
the file. It is Python's way of writing `while ((n = stream.Read(buffer))
> 0)` from C# or Java, without holding 88 MB in memory at once. The hash is
checked on `<name>.part`, which is renamed into place only on a match, so a
half-downloaded or tampered file never sits under the real name.

**One stand-in for every test: `conftest.py`, `autouse` and a class
method replaced.** Every test that records a dog would load an 88 MB network
— or download it. pytest reads `tests/conftest.py` before the tests, and a
fixture declared there with `autouse=True` runs for **every** test without
being named:

```python
@pytest.fixture(autouse=True)
def fake_dog_network(request, monkeypatch):
    if request.node.get_closest_marker("real_dog_model") is None:
        monkeypatch.setattr(dogs.Network, "embed", fake_embed)
```

`monkeypatch.setattr` on the **class** replaces the method for every
instance, `LIVE` and `STORED` included, and puts it back when the test ends
— like a mocking framework replacing a virtual method for one test, but
with no interface needed. `fake_embed(self, image)` takes `self` because it
becomes a method. A test marked `@pytest.mark.real_dog_model` is left alone
(`get_closest_marker` looks at the test's own marks), and it skips itself
when `models/` lacks the file. `pytest_configure` registers the marker so
pytest does not warn about an unknown name.

**A cosine you choose (`tests/dog_vectors.py`).** To test thresholds the
tests need descriptors at exact distances. A unit vector turned by an angle
θ from an axis has cosine `cos θ` with it, so `descriptor(direction, angle)`
puts `cos θ` and `sin θ` on two neighbouring axes, and `at_distance(d)` asks
for `θ = acos(1 − d)`: a distance of exactly `d`. The fake network writes on
axes the test descriptors never use, so a real crop and a hand-made
descriptor are always far apart.

**CSS: at equal specificity, the later rule wins (backlog 39).**

```css
.phone-only { display: none; }
@media (max-width: 480px) {
  .phone-only { display: inline; }
}
```

Both selectors weigh the same, and a media query adds no weight: it only
switches its rules on or off. So when both apply — on a phone — the one
written **later** in the file wins. Written the other way round, the base
rule would hide the phone text on the phone too; developer 24 hit exactly
that and moved it up.

**PowerShell: `$null` on the left, and returning a reason (R57).**
`FrameProblem` returns `$null` when all is well, or a sentence saying what
is wrong, so one value both decides and explains — the caller writes
`if ($problem) { throw "... $problem" }`. Comparisons put `$null` first,
`$null -eq $age`, because PowerShell compares a collection on the left
element by element: `@(1, $null) -eq $null` returns the matching elements,
not `$true` or `$false`. With `$null` on the left the answer is always one
boolean.

## 45. Testing on what was learned, a group-by minimum in one call, a picture compared by eye, a file's time as evidence, and a closure as an object (developer 25)

From one delivery: R55 and backlog 32 for dogs (ARCHITECTURE 10.15, 10.16,
20).

**Leave-one-out and its leak (R55).** To measure a recogniser without a
separate test set, each named view is taken out in turn and matched against
the others: leave-one-out, the honest test when labels are few. It has one
trap. The views of one visit are consecutive frames — twins. Take one out
and its twin is still there, so the match is nearly certain; the table
measures how well the gallery recognises a frame it has already seen. In
Java terms, that is testing on the training set. The fix is to leave out the
whole group the probe belongs to — here its event — so every probe faces the
gallery as a new visit would. In code it is one more mask:

```python
out = scores >= COPY_SIMILARITY
out = out | (events == event) if event else out
scores = np.where(out, -1.0, scores)
```

`events` is a NumPy array of strings (`dtype=object`), so `events == event`
compares every element at once and returns an array of booleans, as
`scores >= COPY_SIMILARITY` does; `|` joins two such masks element by
element. On production the faces' coverage fell from 66 to 39 of 80 at 0.40,
with no new error; the dogs did not change at all — one crop per dog per
event leaves no twin to leak.

**`np.minimum.at`: a group-by minimum without a loop (backlog 32 for dogs).**
Each probe gets a distance to every named view; what `match` needs is each
dog's nearest view. In Java that is
`Collectors.groupingBy(owner, Collectors.minBy(...))`:

```python
per_dog = np.full(dogs, np.inf)
np.minimum.at(per_dog, owners, distances)
```

`owners[i]` is the dog of view `i`. `np.minimum.at` walks the pairs and does
`per_dog[owners[i]] = min(per_dog[owners[i]], distances[i])` for each — in
C. It must be the `.at` form: `per_dog[owners] = np.minimum(per_dog[owners],
distances)` looks the same but is *buffered* — when one dog owns several
views, every assignment to the same slot reads the same old value and the
last write wins, not the smallest. `.at` is unbuffered: each write sees the
one before. Then `np.argsort(per_dog)` gives the nearest dog and the second.

**Comparing pictures by eye, not by bytes (R55).** A dog's view and its
sighting are the same crop saved twice, at JPEG quality 92 and 90. Their
bytes differ, so a SHA-1 would call them different. A perceptual comparison
looks at what a person would see:

```python
image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
tiny = cv2.resize(image, (16, 16), interpolation=cv2.INTER_AREA).astype(np.float32)
same = np.abs(tiny - other).mean() < 1.0
```

`INTER_AREA` averages every source pixel that falls into each of the 256
cells, so JPEG's small noise cancels out and two savings of one picture
differ by a fraction of a grey level, while two different frames differ by
many. `astype(np.float32)` matters: on `uint8` arrays `a - b` wraps around
(3 − 5 is 254), as a Java `byte` would.

**A file's time as evidence (R55).** `Path(photo).stat().st_mtime` is the
last time the file was written, in seconds since 1970 as a float — the
`File.lastModified()` of Java, in seconds. A face view and its sighting are
written in the same moment, so a view whose photo was written within 2 s of
exactly one event's sightings came from that event. The weakness is that
the time is the file system's, not the photo's: a plain copy, a restore or a
rewrite sets a new one (`cp -p`, `shutil.copy2` and `robocopy` keep it;
`shutil.copy` does not). That is why the recovery runs once, on
production's own files.

**A closure as a small object (`surePanel` in `app.js`).** The face and dog
panels differ in a few cells and words, so one function builds both:

```js
function surePanel({ form, key, endpoint, ... }) {
  let fallback = null;
  async function load() { ... fallback = table.default; ... }
  async function save(chosen) { ... }
  panel.querySelector(".sure-default").addEventListener("click", () => save(fallback));
  return { load };
}
const dogSure = surePanel({ form: "dog-sure-form", key: "dog_sure_distance", ... });
```

`fallback`, `load` and `save` live in the function's scope, and the inner
functions keep that scope alive after `surePanel` returns: a **closure**.
Each call makes a fresh scope, so the two panels have two `fallback`s that
never meet. What is returned, `{ load }`, is the public part; the rest is
private. In Java it is an anonymous class instance with private fields, or a
C# lambda capturing locals. The configuration object passes functions as
values (`value: (row) => row.distance`) — the strategy pattern without an
interface. And `#accuracy-table` became the class `.accuracy-table`: an id
must be unique in a page, so two tables need a class, and each panel finds
its own parts with `panel.querySelector(...)` inside its form.

## 46. Intersection over the smaller box, a network wrapped by duck typing, and three phases of one rhythm (developer 26)

From one measurement: R59 and R58 (`tools/person_signals.py`,
ARCHITECTURE 7.15 and 22.3). Nothing was built; what the tool does is worth
knowing.

**IoU against intersection over the smaller box (R58).** IoU — the shared
area over the union of the two boxes — says whether two boxes are *the same
box*. NMS and `drop_duplicates` use it, so they merge twins. It cannot say
whether one box sits *inside* another: a small box wholly within one four
times its size shares all of itself and still scores IoU = small / big =
0.25. Dividing by the smaller box instead gives 1.0 for any box wholly
inside:

```python
def inside_smaller(a, b):
    width = min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0])
    height = min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1])
    smaller = min(a[2] * a[3], b[2] * b[3])
    return max(width, 0) * max(height, 0) / smaller if smaller else 0.0
```

The overlap's width is how far the right edge that comes first lies past
the left edge that comes last; negative means the boxes do not touch,
which `max(width, 0)` turns into no area. One body with two boxes — the
person, and the person with the car door — scored IoU 0.33–0.43, under
both filters, and 0.96–1.00 here.

**A wrapper that the detector never notices (duck typing).** The tool
needed YOLO's raw output after each run, which `SubjectDetector` keeps to
itself. In Java one would extract an interface for the network and inject
a decorator. Python has no interface to extract: an object is acceptable
wherever its methods are, so a class with the same two methods is enough.

```python
class Recording:
    def __init__(self, net):
        self.net = net
        self.output = None

    def setInput(self, blob):
        self.net.setInput(blob)

    def forward(self):
        self.output = self.net.forward()
        return self.output
```

`detector.model = Recording(detector.model)` swaps it in; the detector
calls `setInput` and `forward` as before and the tool reads `.output`
afterwards. "If it walks like a duck": nothing checks the type, only the
methods called. It is the same move as the tests' stand-in network
(section 44), used here to watch instead of to replace.

**Three phases of one rhythm.** Live, YOLO runs at most every 0.3 s, so at
10 analysis frames a second it sees one frame in three, and which third
depends on when the event began. A replay that runs YOLO on every third
frame shows one of three possible lives of the clip. The tool keeps three
detectors and gives frame `i` to detector `i % 3`: each detector sees its
own third, with its own memories (R44, R46), as a live camera on that
phase would — every box any live run could have drawn, and each one's
origin.

## 47. A one-shot timer, a call put off with `lambda`, and an optional form field (developer 27)

Backlog 40 (ARCHITECTURE 12.11, 12.12) needed three things the project had
not used yet, and two it had.

**`threading.Timer`: run something once, later, in its own thread.** The
floor rings at most once in 30 s; a message that should ring inside it goes
out silent at once, and something has to wake at the 30 s mark to send the
one loud text that names it:

```python
timer = threading.Timer(last + LOUD_FLOOR_SECONDS - now, _end_of_floor, args=(settings,))
timer.daemon = True
_floor["timer"] = timer
timer.start()
```

`Timer` is a `Thread` subclass: `start()` launches a thread that waits for
the interval and then calls the function with `args`, unless `cancel()` was
called first. It is Java's `ScheduledExecutorService.schedule(task, delay)`
and C#'s `System.Threading.Timer` with no period — but each `Timer` is a
whole thread, fine for one pending at a time, as here (`_floor["timer"]` is
`None` again once it fires). `daemon = True` means it does not keep the
process alive at exit. `_end_of_floor` takes the module's lock, copies and
empties the list and only then sends, outside the lock — section 26's
rule. Two things it does not have: a monotonic interval you can control in
a test, and a way to fire it early. The tests swap `threading.Timer` for a
small class with the same `start` and `cancel` that records itself and
fires on demand — the duck typing of section 46.

**A sleep a stop can end, again.** The camera watch's loop is
`while not stop.wait(CHECK_SECONDS)` — section 27's `Event.wait(timeout)`,
which returns `False` after the timeout and `True` the moment the service
sets `stop`. A `time.sleep(5)` would hold a stopping service up to 5 s.

**A clock passed in.** `CameraWatch(ages, clock=time.monotonic,
wall=datetime.now)` takes its clocks as arguments with the real ones as
defaults (section 39), and `notify` keeps `_clock = time.monotonic` as a
module name (section 36). A test passes `lambda: now[0]` and moves time by
hand — what Java does with an injected `java.time.Clock` and .NET with
`TimeProvider`. Nothing waits for real in those tests.

**A call put off: `lambda` with no arguments.** `_faceless` decides whether
a faceless message goes out at all; each of its three callers sends a
different message with different arguments. Instead of passing the
function and its arguments separately (`message, *extra`), each caller
hands over the finished call, unrun:

```python
return _faceless(camera, held, notified, settings,
                 lambda: best_view(camera, started_at, best, settings, seen))
```

and `_faceless` ends with `message()`. A `lambda` with no parameters is
Java's `Supplier<T>` or C#'s `Func<T>`: the body runs only when called,
and it reads `camera`, `best` and the others from the enclosing call
(a closure, section 45). One more thing comes from running late: the name
`best_view` is looked up in the module **when the lambda runs**, not when
it is written. That is why the tests' `monkeypatch.setattr(notify,
"best_view", fake)` still reaches it — the lambda finds the fake.

**An optional field in a form.** Telegram's `disable_notification` should
be in the request only when the message is silent:

```python
quiet = {"disable_notification": "true"} if silent else {}
{"chat_id": chat, "text": text[:4096], **quiet}
```

`**quiet` spreads the dict into the literal (section 39); an empty dict
spreads into nothing, so a loud message's form is exactly what it was
before. The value is the string `"true"` because `requests.post(data=fields)`
sends form fields — URL-encoded for a text, `multipart/form-data` beside a
photo — and a form field is always text; Telegram reads `"true"` as the
boolean.

## 48. A tracker that never looks at the image, a library's units read in its source, columns instead of objects, and a script's function tested alone (developer 28)

Item 7's first part (ARCHITECTURE 7.16, 18.7) brought the project's first
multi-object tracker and a deploy step written in PowerShell.

**Multi-object tracking: predict, then match.** YOLO answers "where are
the people in this frame?", never "is this the same person as before?".
ByteTrack answers the second without looking at a pixel. It keeps, per
object, a **Kalman filter** — a small state (the box's centre, size, and
their velocities) and how uncertain each value is. Every update has two
steps, like a physics step in a game loop followed by a correction:

1. **Predict**: move every box by its velocity — "if it kept walking, it
   should be here now".
2. **Match**: compare each prediction with each new YOLO box by overlap
   (IoU, section 46), and pick the pairing with the most total overlap.
   That pairing is the **assignment problem**, solved by the Hungarian
   algorithm — `scipy.optimize.linear_sum_assignment(cost)`, one call on a
   matrix of predictions × detections, O(n³) and exact.

A matched box corrects its filter (the measurement pulls the prediction
back, weighted by how sure each is); an unmatched prediction is kept, still
predicted, for `lost_track_buffer`; an unmatched detection starts a new
track. ByteTrack's own idea is a **second round**: detections too weak to
start anything are still offered to the tracks left unmatched, so a person
YOLO hesitated on for one frame keeps their track. Here the detector already
drops what is under its minimums, so that round is empty.

The constant velocity is also its limit, measured on real walks: a person
who leaves the view for 7 s is predicted 7 s further along the line they
were walking, far from where they come back, so no buffer joins the two
halves. Prediction is not memory.

**A parameter's unit is in the source, not in its name.**
`lost_track_buffer=30` reads like "30 frames", and with `frame_rate=10/3`
one would compute 9 s. `trackers/core/base.py` says otherwise: the buffer
is counted in frames **of 30 FPS** whatever `frame_rate` is, and when
`update(detections, timestamp=t)` is given times, the budget becomes
`lost_track_buffer / 30` seconds. So 3 s is `90`. The same reading found
why a track's first box always comes back with `tracker_id` −1:
`_spawn_new_tracks` appends −1 for every new track, and the id is allocated
at its next match. Opening `.venv\Lib\site-packages\<package>` is the
Python version of "Go to Definition" into a decompiled DLL — except that
here the source is the real one.

**`supervision.Detections`: columns, not a list of objects.** In Java one
would write `List<Detection>`, each object holding its box, score and class.
`Detections` is the other way round — one numpy array per field:

```python
sv.Detections(xyxy=np.array([[x0, y0, x1, y1], ...]),
              confidence=np.array([0.62, ...]),
              class_id=np.array([0, ...]),
              data={"label": np.array(["person", ...])})
```

Row *i* of every array is detection *i*: a struct of arrays, like a
DataFrame without pandas, or a table in a column store. Vector maths runs
on a whole column at once (section 43), and `detections[idx]` with an
array of indices reorders **every** column together. The tracker returns
its detections in its own order — matched first, then new — so the tool
keeps the label inside `data`, where it travels with its row, instead of
trusting the order it passed in.

**Importing by name.** The warm-up imports every package installed, without
knowing their names in advance:

```python
for name in sorted(importlib.metadata.packages_distributions()):
    if not name.startswith("_"):
        importlib.import_module(name)
```

`packages_distributions()` maps each top-level import name (`cv2`, `PIL`,
`yaml`) to the distribution that installs it (`opencv-python`, `pillow`,
`pyyaml`) — the names differ, which is why it exists. `import_module(name)`
is `import name` with the name in a variable: Java's `Class.forName`, C#'s
`Assembly.Load`. Importing a package runs its `__init__.py`, which loads
its compiled `.pyd` files — the DLLs Smart App Control wants to see.

**PowerShell and a native program's bytes.** `git archive --format=zip
<tag> files > out.zip` would break the zip in Windows PowerShell 5.1: its
pipeline carries text, so the bytes are decoded and re-encoded on the way.
`git archive -o out.zip` lets git write the file itself. The function also
sets `$ErrorActionPreference = 'Continue'` as its first line: in PowerShell
a variable assigned inside a function is local to that call (dynamic scope),
so the script's `'Stop'` is back when it returns — section 41's trap, where
a stderr line became a terminating error, without touching the rest of the
script.

**Testing one function of a script that acts when it loads.**
`production.ps1` runs its `-Action` at the bottom, so dot-sourcing it in a
test would run an update. The developer parsed it instead and defined only
its functions, in this shape:

```powershell
$ast = [System.Management.Automation.Language.Parser]::ParseFile($path, [ref]$null, [ref]$null)
$ast.FindAll({ $args[0] -is [System.Management.Automation.Language.FunctionDefinitionAst] }, $true) |
    ForEach-Object { Invoke-Expression $_.Extent.Text }
```

`ParseFile` returns the syntax tree without running anything — Roslyn's
`SyntaxTree` in C# — and each function's `Extent.Text` is its source,
evaluated on its own. The `$WarmUpScript` here-string is a variable, not a
function, so it has to be defined the same way by hand.


## 49. An object as its own key, an immutable tuple copied with one field changed, a library read before working around it, and a guard on what nothing depends on (developer 29)

Item 7's part 1 finished (ARCHITECTURE 7.16): tracks are recorded live, in
each event's JSON, and act on nothing yet.

**An object as a `dict` key, by identity.** `Tracks` needs to follow a
ByteTrack tracklet from the update that spawns it, before the library gives
it any id. It does so with a `dict` whose keys are the tracklet objects
themselves:

```python
self.ids = {}
...
if tracklet not in self.ids:
    self.ids[tracklet] = self.next_id
    self.next_id += 1
```

A `dict` key must be **hashable**. A class that defines neither `__eq__`
nor `__hash__` inherits both from `object`, where equality *is* identity
and the hash comes from it — exactly Java's `Object.equals` and
`hashCode()` without an override, or a C# class used as a `Dictionary` key
without overriding `Equals`/`GetHashCode`. So the same tracklet is the
same key for its whole life, whatever its box does, and two tracklets with
the same box stay two keys. The review checked the library first: neither
`BaseTracklet` nor `ByteTrackTracklet` overrides them, and neither is a
`@dataclass`, which with its default `eq=True` would set `__hash__` to
`None` and make the object unhashable. Two traps of the alternatives:
a key `id(tracklet)` — the object's address in CPython — can be reused by
a new object once the old one dies, so a dead tracklet's number could pass
to a stranger; and a class whose `__eq__` compares fields would make two
tracklets at the same spot one key. `Tracks` also removes the keys of
tracklets the library pruned, so the `dict` does not keep dead objects
alive — a strong reference in a `dict` stops the garbage collector, as in
Java.

**`namedtuple._replace`: a copy with one field changed.** `Detection` is a
`namedtuple`, immutable like a C# `record`. The test moves a box with

```python
PERSON._replace(x=PERSON.x + 5 * step)
```

which returns a **new** tuple with `x` changed and every other field
copied — C#'s `person with { X = person.X + 5 }`. The leading underscore
is not "private" here: `namedtuple` names its own methods `_replace`,
`_asdict`, `_fields` so they never clash with a field the user might call
`replace`.

**Read the library before working around it.** The plan suggested holding
a track's first box until the library named it. Reading
`trackers/core/bytetrack/tracker.py` changed the method: the spawned
tracklet object is already in `tracker.tracks` after the update, so the
box can be credited at once. It also showed why the "obvious" fix —
giving the library's id at spawn — was wrong: `_get_alive_tracklets` keeps
any tracklet with `tracker_id != -1` alive through misses, so that change
would have changed which tracks survive, not only how they are counted.
Section 48 read the same source for a unit; this time it decided a design.

**A guard on what nothing depends on.** `Camera.detect` wraps the
tracker's update:

```python
try:
    return subjects, (self.subjects.last_run, self.tracks.update(subjects, self.subjects.last_run))
except Exception:
    logger.exception("Tracking failed on %s; this run goes untracked", self.label)
    return subjects, None
```

`except Exception` catches every ordinary error (not `KeyboardInterrupt`
or `SystemExit`, which derive from `BaseException`), and
`logger.exception` logs at ERROR with the traceback — Java's
`log.error(msg, e)`. A catch this broad is usually a smell, because it
hides bugs. It is acceptable here because the tracks are only recorded:
losing one run's tracks costs a line of a JSON, while an exception reaching
the camera loop would stop recording. Around the detector the same guard
would be wrong — a detector that fails silently is a camera that records
nothing. The review found its one cost: a tracker that failed on *every*
run would write a traceback three times a second per camera into a log
that keeps 6 MB (R62).

## 50. Retry with backoff, the slow path in a thread, decide under a lock and act outside it, patching a module's globals, and a replay that runs the shipped code (developer 30)

Developer 30 made a failed message try again (R63, ARCHITECTURE 12.13),
built the visit (backlog 41, 12.14) and replayed a month of production
through it.

**Retry with a growing pause.** Every reliable network client does the
same thing: try, and on a failure that may pass, wait and try again, a
little longer each time, a bounded number of times.

```python
RETRY_PAUSES = (5, 15, 30, 60)

def _retry(subject, text, image, settings, silent, pause):
    attempt = 1
    while pause is not None:
        _sleep(pause)
        attempt += 1
        ok, detail, wait = _post(text, image, settings, silent)
        if ok:
            return True
        pause = _failed(subject, attempt, detail, wait)
    return False
```

The growing pause gives a server that is struggling room to recover; a
fixed one hammers it at the same rate. Which failures to retry is the real
design: a time-out or a 500 may pass; a 400 "chat not found" never will,
and retrying it only fills the log; a 429 says how long to wait in its own
body. `_call` encodes that in its third value, `wait` — `None` for "do not
try again", a number for "try again after this". Returning a tuple of three
and unpacking it, `ok, detail, wait = …`, is Python's way to return several
values; Java would need a small record class, C# a tuple `(bool, string,
double?)` — and `None` here plays the role of C#'s `null` in a `double?`.

**Idempotency, and why a duplicate is accepted.** A request is idempotent
when doing it twice is the same as doing it once — `PUT` a value, `DELETE`
an id. `sendPhoto` is not: when the read times out, Telegram may already
have the photo, and the retry posts it again. The choice is between a rare
duplicate and a lost message; the user's rule (a risk is never lost)
decides it.

**The first attempt inline, the slow path in a thread.** `_send_logged`
tries once on the caller's own thread, so the caller gets its answer as
before; only a failure starts a thread:

```python
ok, detail, wait = _post(text, image, settings, silent)
if ok:
    return True
pause = _failed(subject, 1, detail, wait)
if pause is not None:
    threading.Thread(target=_retry, args=(subject, text, image, settings, silent, pause),
                     daemon=True).start()
return False
```

It is the shape of C#'s `if (!TrySend()) _ = Task.Run(() => RetryLoop())`:
the common case costs nothing extra, and the two minutes of pauses never
block a camera's assembly thread. `daemon=True` means the thread does not
keep the process alive at shutdown — a retry left over is abandoned, like
a background `Thread` in .NET with `IsBackground = true`.

**A module-level dict under a lock.** The visit state is a plain `dict`
at module level, `_visits`, shared by every assembly thread, with its own
`threading.Lock`:

```python
with _visit_lock:
    visit = _visit(camera, started_at, ended_at or started_at)
    quiet = rules and visit["sent"] and seen <= visit["people"]
    ...
    _remember(visit, found, seen, started_at, settings)
    ...
    visit["sent"] |= bool(planned)
```

`with lock:` is Java's `synchronized (lock) { … }` and C#'s `lock (obj)
{ … }`: acquired on entry, released on exit even if an exception leaves
the block. The GIL does not make this unnecessary. It makes each bytecode
step atomic, not a sequence: two threads can both read `visit["sent"]` as
`False`, both decide to send, and both set it — two "first" messages. The
read, the decision and the write must be one step, so they share one
lock.

**Decide under the lock, act outside it.** The sending happens after the
`with` block ends. Holding a lock across a network call would make every
other thread wait for Telegram's 15 s time-out, and a lock held while
calling code that takes *another* lock is how deadlocks are made. The
same pattern has a sharper edge here: `threading.Lock` is **not
re-entrant** — the same thread taking it twice waits for itself forever
(PYTHON 31). `_deliver` calls `_loud`, which takes `_lock`; had the visit
used `_lock` too, deciding a visit while delivering would hang. That is
why there are two locks, and why the test fixture that first fired the
floor's timer inline did deadlock until it stopped doing so. Java's
`synchronized` and C#'s `lock` are re-entrant, so this trap does not exist
there; Python's `threading.RLock` is the re-entrant one.

**Patching a module's globals in a test.** The tests replace module-level
names with pytest's `monkeypatch`, which puts every one back after the
test:

```python
monkeypatch.setattr(notify, "_post", fake_post)
monkeypatch.setattr(notify, "_sleep", pauses.append)
monkeypatch.setattr(notify.threading, "Thread", Inline)
```

A function looks up a global name **when it runs**, not when it was
defined, so `_send_logged` calls whatever `notify._post` is at that
moment. `_sleep = time.sleep` exists only so a test can swap it for
`pauses.append` and see the pauses without waiting two minutes. The third
line has a catch: `notify.threading` is not a copy, it **is** the
`threading` module, the same object every module imported. Patching
`notify.threading.Thread` patches `threading.Thread` for every module in
the process during that test — which is why the thread test of the visit
puts the real class back (`REAL_THREAD`) before using a pool. In Java
terms it is replacing a static field of a shared class, not of one
instance.

**A replay that runs the shipped function.** `tools/replay_visits.py`
does not re-implement the visit rules to estimate their effect; it calls
`notify.after_scan` itself on each of the month's events, with the
sending replaced by a list:

```python
notify._send_logged = lambda subject, text, image, values, silent=False: \
    sent[current["key"]].append(subject) or True
```

(`list.append` returns `None`, so `… or True` makes the lambda return
`True`, as a successful send does.) First it runs with the visit off and
checks that it reproduces the log event by event — 0 events differ —
which proves the replay's inputs are right; only then does it switch the
visit on and count. A rule measured through a copy of itself measures the
copy.

## 51. Assigning inside an expression, a whole-string match, groups joined by shared sets, and the most common item (developer 31)

### 51.1 `:=`, the walrus operator

```python
held = [int(found.group(1)) for p in self.people
        if (found := VISITOR_PATTERN.fullmatch(p.get("temporary_name") or ""))]
```

The comprehension needs the match twice: to filter (is this a "Visitor N"?)
and to read its number. `found := ...` stores the match in `found` **and**
yields it, so the `if` tests it and the expression before `for` uses it.
C# does the same with `out var`: `if (dict.TryGetValue(key, out var v))
Use(v);`. Without it, the code would call `fullmatch` twice or need a loop
with a temporary. Inside an `if` of a comprehension the parentheses are
required. It is called the walrus for its look, `:=` on its side.

### 51.2 `re.fullmatch` against `re.match`

`re.match` anchors only at the start: `re.match(r"Visitor (\d+)",
"Visitor 12b")` matches "Visitor 12". `re.fullmatch` wants the whole string,
like `^...$`, so "Visitor 12 (aunt)" typed by someone is never read as a
number. In C#: `Regex.IsMatch(s, @"^Visitor (\d+)$")`. The pattern is
compiled once, at import (`re.compile`), as a `static readonly Regex`.

### 51.3 Groups joined by shared sets

`one_body_groups` joins entries transitively: A and B share one event, B
and C another, so A, B and C are one person. It keeps `group_of`, a dict
from each id to **the same `set` object** shared by its whole group:

```python
joined = set(ids).union(*(group_of.get(i, set()) for i in ids))
for i in joined:
    group_of[i] = joined
```

Joining builds a new set with every member of every group touched and
points each member at it, so the old sets are left with no one pointing at
them. It is the simplest form of union-find (disjoint sets); the textbook
one keeps a parent per element and is faster for millions of elements,
which fifty entries do not need. At the end each group sits in `group_of`
once per member: `{id(g): g for g in group_of.values()}` keeps each set
once, keyed by `id()` — the object's identity, like C#'s
`ReferenceEquals` — because a `set` is mutable and so cannot itself be a
dict key or the member of another set.

### 51.4 `Counter.most_common`

`received[source][target] += 1` counts, per emptied entry, the residents
that took its views; `targets.most_common(1)[0][0]` is the one that took
most. `most_common(n)` returns the n `(key, count)` pairs with the highest
counts, ties in insertion order — LINQ's
`GroupBy(...).OrderByDescending(g => g.Count()).First().Key`, without the
grouping, because a `Counter` is already a dict from key to count.

### 51.5 A commit message from a file

Windows PowerShell 5.1 passes arguments to a native program by rebuilding
its command line, and double quotes inside an argument are lost:
`git commit -m "the "Visitor N" name"` reaches git as several arguments,
which git reads as paths. `git commit -F message.txt` reads the message
from a file and needs no quoting at all.

## 52. Sharpness as the variance of the Laplacian, a photo's real resolution, a threshold fitted to its labels, and a sleep a stop interrupts (developer 32)

### 52.1 The variance of the Laplacian

```python
def sharpness(grey):
    return float(cv2.Laplacian(grey, cv2.CV_64F).var())
```

The Laplacian is a second derivative: at each pixel it says how much the
brightness bends compared with its neighbours. On a flat area it is near
zero; on an edge it swings hard positive and negative. Its **variance** over
a region is therefore large when the region holds many sharp edges and
small when it is smooth — and a blurred photo is a photo whose edges were
smoothed. `cv2.CV_64F` asks for 64-bit floats, because the result is
negative as often as positive and would be clipped in 8-bit pixels.

Why it fails at night (ARCHITECTURE 10.18): it measures edges, not focus.
An infrared picture is grey on grey, with little contrast, so a sharp dog at
night scores 3–4 while a blurred dog by day scores more. A measure is only
good for what it measures; "sharp" and "has strong edges" coincide only
when the lighting is the same.

### 52.2 A photo's real resolution, by shrinking and enlarging

The gallery stores every face at 300 px, but a 40 px face enlarged to 300
holds no more detail than 40 px. `effective_side` finds the side it came
from: shrink the photo to each candidate side (`INTER_AREA`, the averaging
resize) and enlarge it back (`INTER_CUBIC`), then measure how far the
round trip moved the pixels. A side at or above the original resolution
loses almost nothing; below it, detail is lost. The smallest side whose
error is still close to the floor is the estimate. It is how one checks a
JPEG for upscaling. Measured against the 140 views whose real width is
known, the correlation is 0.86 — good enough to rank, not to measure.

### 52.3 A threshold fitted to its own labels

The pair "SCRFD ≥ 0.70 and sharpness ≥ 75" was chosen because, of all the
pairs tried, it dodges every one of the 102 photos marked poor. Tried on
those same 102, it cannot fail — it was picked for that. The real test is
photos it has never seen, next month's. In Java or C# terms it is a unit
test written after reading the bug's input: green on that input proves
little about the next one. The more combinations are tried, the more
likely one fits the labels by chance. R55 fixed the same mistake for the
face table (leave each view's whole visit out); here the honest version is
to fit the cut on some views and count the errors on the others.

### 52.4 The daily loop, once more

`keep_gallery` ends each pass with `if stop.wait(KEEP_SECONDS): return` —
section 27's `Event.wait(timeout)`, the camera watch's pattern of section
47: a 24-hour sleep that returns `True` the moment the service sets
`stop`, where `time.sleep(86400)` would hold the thread for a day. The
test replaces `stop.wait` on the instance with a lambda that records the
timeout, so a "day" passes in no time.

## 53. A network that grades a photo, the length of an embedding, and holding data out by day (developer 33)

### 53.1 Face image quality assessment

A recogniser such as ArcFace turns a face into a vector; a **face image
quality** model (FIQA) answers a different question: *how much should a
recogniser trust this photo?* It is not "is it pretty" — a sharp photo of
the top of a head is useless to a recogniser, a soft frontal one is fine.
eDifFIQA learns that answer without anyone labelling quality: during
training each face is noised and denoised by a diffusion model many
times, and the photos whose ArcFace-style embedding barely moves are the
good ones. A small network (eDifFIQA(T), the "tiny" one) is then taught to
predict that stability from the photo alone, so at run time it is one
forward pass, about 10 ms on the M900. That is why it scores the
cameras' downward views low: a face seen from above *is* unstable for a
recogniser. In `tools/view_quality.py`:

```python
@lru_cache(maxsize=1)
def quality_net():
    return cv2.dnn.readNetFromONNX(str(QUALITY_MODEL))
```

`@lru_cache(maxsize=1)` on a function with no arguments is section 12.2's
cache used as a lazy singleton: the file is read on the first call and the
same `Net` returned after — C#'s `Lazy<T>`, Java's holder idiom.

### 53.2 The length of an embedding as a quality signal

ArcFace's raw output is a 512-number vector; the gallery stores it as it
comes, and `cosine` divides by both lengths (norms) before comparing, so
only the direction names a person. **MagFace** trained a recogniser whose
loss ties the length to quality — a clear face gets a long vector — and
the idea is that any recogniser might do it a little. Measured here, it
barely does: ArcFace's plain loss never asked the length to mean anything.
`np.linalg.norm(v)` is the length, `sqrt(sum(v*v))`.

### 53.3 Holding data out by day, not by row

To check a threshold honestly (section 52.3) you choose it on some views
and count its mistakes on others. Picking the others at random by row
would be too kind: two views of one visit, a second apart, are near
copies, and one would land in each half — the test would see the answer.
`halves` gives each *day* to one half, alternating, so every visit stays
whole on one side, as leave-one-event-out does (R55):

```python
order = {day: index % 2 for index, day in enumerate(sorted({day_of(r) for r in rows}))}
```

A set comprehension collects the days, `sorted` orders them,
`enumerate` numbers them and `index % 2` alternates 0 and 1 — a dictionary
comprehension building `{day: half}` in one line. In Java it is a `Stream`
of distinct sorted days collected with an index into a `Map`.

## 54. Late binding, a hook a subclass overrides, and identity (developer 34)

### 54.1 Patching a module's function in a test

`tests/conftest.py` makes every face photo pass the quality cut with
`monkeypatch.setattr(faces, "face_quality", lambda image, face=None: 1.0)`.
It works because `Gallery.admits` looks the name `face_quality` up in the
module's globals **each time it runs**: Python binds names late, so
replacing the module attribute replaces what every caller gets. A Java
static import is resolved when the class is compiled and cannot be swapped
this way; the nearest C# habit is an interface injected for the test. The
tool calls `faces.face_quality(...)` through the module for the same
reason: a `from faces import face_quality` would copy the original into
the tool's own globals, and a patch would not reach it.

### 54.2 A hook the subclass overrides

`Gallery.add` and `Gallery.reinforce` call `self.admits(crop)`;
`DogGallery` inherits both and overrides only `admits`, to take every
crop (a dog's gate is its box, decided in `dogs.record`). That is the
template-method pattern — a C# `protected virtual bool Admits(...)` the
base class calls. Without the override the dog gallery would have been
gated by a face model, since in Python every method is virtual.

### 54.3 The same object, not an equal one

In `notify`, a sighting already seen in the visit is found with `s is r`
and `id(s)`, not `==`: two sightings of two different strangers can be
equal dictionaries, and only identity says they are two faces. `is` is
C#'s `ReferenceEquals`; `==` on dicts compares contents, like a value
`Equals`. And `gallery.add(...) or ""` gives `""` when `add` returns
`None`, because `None` is falsy — C#'s `??` for this case, though `or`
also replaces `0`, `""` and empty lists, which `??` would not.


## 55. A generator the caller answers, a generator closed early, a frame's own clock, two threads on one condition, a queue simulated, and a Win32 call (developer 35)

### 55.1 A generator whose caller answers before the next item

`faces.matches(gallery, observations)` is a generator: it `yield`s one
dict per face group and stops there until the caller asks for the next.
The caller may change the dict in between, and the generator reads the
change when it resumes:

```python
for match in matches(gallery, observations):
    recorded.append(_record(gallery, match, ...))   # sets match["person_id"]
```

```python
yield match
if person_id is None:
    new_here.extend(match["references"])
if match["person_id"]:
    seen_here.add(match["person_id"])
```

`_record` writes the entry a new face made into `match["person_id"]`; the
generator, resumed, adds it to `seen_here`, so a later group of the same
person is skipped. The scan writes; the replay tool sets `""` and writes
nothing — the same skips serve both. In C# this is an `IEnumerable` built
with `yield return` whose loop body changes the item just returned; in
Java an `Iterator` whose `next()` reads the element it handed out last.
It works because the dict is one object shared by both sides (54.3), and
because a generator runs only when asked: nothing past the `yield` runs
before the caller's body has.

### 55.2 `contextlib.closing`: a generator stopped halfway still cleans up

The frame reader (`faces.frames_selected`) is a generator with a
`finally` that kills its ffmpeg (21). A `for` loop that `break`s leaves
the generator suspended, and its `finally` runs only when the garbage
collector closes it — some time later. `closing(gen)` calls
`gen.close()` at the end of the `with`, which raises `GeneratorExit` at
the paused `yield` and runs the `finally` at once:

```python
with closing(faces.frames_selected(clip, expression, n, w, h)) as frames:
    observations, count, _, _ = faces.observe(frames, stop=...)
```

`observe` stops at the first sure face; the `with` makes sure the ffmpeg
behind it dies then, not whenever memory is collected. It is `using` in
C# or try-with-resources in Java, for any object with a `close()`.

### 55.3 A frame's own clock: pts, `showinfo` and `select=eq(pts\,P)`

Every frame of a video carries a **pts**, a presentation timestamp in the
stream's time base: when the frame is meant to be shown. "Frame *n* is at
*n* / fps" holds only when the camera keeps a perfect rhythm, and these
do not: a frame the arithmetic placed at 10.79 s fell outside its window.
ffmpeg's `showinfo` filter prints each frame that passes it, with its
`pts` and `pts_time`, on stderr; `select=eq(pts\,1234)+eq(pts\,5678)`
then keeps exactly those frames on a second run (`+` is "or" in ffmpeg's
expressions, and the backslash escapes the comma, 10.11). The tool reads
the stamps once and decodes the very same frames later — checked
byte-identical.

### 55.4 Two threads on one `threading.Condition`

The pixels come on ffmpeg's stdout and the stamps on its stderr, and a
pipe read by nobody fills up and blocks the process. So one thread reads
stderr and appends stamps; the main thread reads a frame from stdout and
waits for its stamp:

```python
with ready:
    stamps.append(stamp)
    ready.notify_all()
...
with ready:
    ready.wait_for(lambda: len(stamps) > index)
```

A `Condition` is a lock plus a waiting room: `wait_for` releases the
lock, sleeps until another thread's `notify_all`, takes the lock again
and re-checks the predicate. Java's `synchronized` + `wait()` /
`notifyAll()` in a `while` loop, or C#'s `Monitor.Wait` / `PulseAll`. The
reader appends `None` at the end, so the waiter never sleeps forever on a
stamp that will not come.

### 55.5 A queue simulated one event at a time

`simulate(jobs, quick_first)` replays `_SCAN_LOCK` as one worker that is
never interrupted: take every job ready by now, pick one (oldest first,
or quick jobs first), advance the clock by its service time, repeat; when
nothing is waiting, jump the clock to the next arrival. That is a
**discrete-event simulation**: time moves from event to event, never in
ticks. The model is trusted only because its FIFO replay of the month
reproduces the log — 1 s median error, 4 s at p90 — before it is asked
about an order nobody ran. A service time may be a function of its start
(`finish_with_pause`): a scan that pauses while a camera records ends
later when it starts in a busy minute.

### 55.6 A Win32 call through `ctypes`

```python
kernel = ctypes.windll.kernel32
kernel.SetPriorityClass(kernel.GetCurrentProcess(), 0x4000)
```

`ctypes` calls a function of a native DLL with no wrapper written: C#'s
`[DllImport("kernel32.dll")]`, Java's JNA. `0x4000` is
`BELOW_NORMAL_PRIORITY_CLASS`; the ffmpeg processes the tool starts
inherit it, so a measurement running beside production on the M900
yields the CPU to it (R12).

## 56. Turns on a condition, `@contextmanager`, a join with a deadline, an object that is a path, a function with a field, bytes as an upload (developer 36)

### 56.1 Turns: a `Condition`, a flag and a queue of tickets

`faces.Turns` (ARCHITECTURE 10.20) decides who runs the face networks.
A plain `Lock` could not: Python's `Lock` promises no order among the
threads waiting for it, and it cannot say "a quick pass goes before a
full scan's next frame". So the state is written out — `_busy`, and a
`deque` of the quick passes waiting — and a `threading.Condition`
(55.4) guards it:

```python
def quick(self):
    ticket = object()
    with self._ready:
        self._quick.append(ticket)
        self._ready.wait_for(lambda: not self._busy and self._quick[0] is ticket)
        self._quick.popleft()
        self._busy = True
    ...

def turn(self):
    with self._ready:
        self._ready.wait_for(lambda: not self._busy and not self._quick)
        self._busy = True
```

Each waiting thread re-checks its own predicate whenever `_release` calls
`notify_all`: a quick pass whose ticket is at the head gets through, a
full scan's frame sees the queue not empty and sleeps again. `object()`
is the cheapest unique thing Python has: no two are `is` each other, so
it works as a ticket with no counter. Java would write the same with
`ReentrantLock` + `Condition.await()`/`signalAll()`; C# with
`Monitor.Wait`/`PulseAll`. The lock is held only to change or read the
state, never while the networks run — that is what `_busy` is for.

Two rules come with it. **No turn inside a turn**: a thread holding the
networks that asks for them again waits for itself forever. And **one
order for two locks**: the networks first, then `_GALLERY_LOCK` (41).

### 56.2 `@contextmanager`: a `with` block from a generator

```python
@contextmanager
def turn(self):
    ...take the networks...
    try:
        yield
    finally:
        self._release()
```

`with _TURNS.turn():` runs the function up to `yield`, runs the block,
then the rest — the `finally` even when the block raised. It is C#'s
`using` and Java's try-with-resources without writing a class with
`__enter__` and `__exit__` (or `IDisposable`, `AutoCloseable`).
`nullcontext` is the `with` that does nothing: `observe` takes a `turn`,
and without one uses `nullcontext`, so the loop has one shape.

### 56.3 `Thread.join(timeout)` as a deadline, with one thread deciding

```python
worker.start()
worker.join(QUICK_DEADLINE_SECONDS)
if "found" in scan:
    ...the full scan decided...
```

`join(45)` returns after at most 45 s whether or not the thread ended;
nothing in its return value says which. The worker fills a dict as its
last step, and only the waiting thread reads it and decides. So there is
no race between "the scan ended" and "the deadline passed": a scan that
ends a millisecond after the check is simply late, and its faces go as
the follow-up. Java's `Thread.join(millis)` and C#'s `Thread.Join(ms)`
behave the same; C# returns a `bool` that tells.

### 56.4 An object that is a path: `__fspath__`

The replay's `SideView` gives `after_scan` an event's side-view path that
"exists" only once a pass of the replay kept a side view:

```python
def __fspath__(self):
    return str(self.stand_in) if self.key in self.kept else "-missing-"
```

`Path(obj)`, `open(obj)` and `os.path` accept any object with
`__fspath__` (the `os.PathLike` protocol), as a Java method accepts any
class implementing an interface. Here the path it gives changes with the
state.

### 56.5 A function with a field

```python
def sure_stop(gallery, sure):
    def stop(kept):
        stop.found = stop.found or any(...)
        return stop.found
    stop.found = False
    return stop
```

A Python function is an object and can carry attributes, so the stop the
quick pass calls also tells the log line afterwards whether it fired. The
same as a lambda capturing a mutable holder (a one-element array in Java).

### 56.6 Bytes as a file in a multipart upload

```python
files = {"photo": ("face.jpg", picture_bytes)}
requests.post(url, data=fields, files=files)
```

`requests` builds the `multipart/form-data` body from a name and the
bytes: no file on disk is needed. The quick pass's face crop goes
straight from `cv2.imencode` to Telegram (ARCHITECTURE 12.15).
`cv2.imencode(".jpg", image)` is `imwrite` into memory: it returns
`(ok, buffer)`, a numpy array of bytes, and `.tobytes()` makes it a
`bytes`.

## 57. A binary search, set algebra in operators, the smallest tuple, and a function that remembers (developer 37)

`tools/follow_body.py` measures what a name following the body would add
over the visit (ARCHITECTURE 7.16). Four small tools of the language carry
it.

### 57.1 `bisect`: which run a moment belongs to

```python
restarts = [datetime(2026, 11, 14, 8), datetime(2026, 11, 15, 20, 30)]
run = bisect.bisect_right(restarts, moment)
```

A track id is unique only within one run of production: ids start at 1
again on every restart. `bisect_right` is a binary search on a sorted list
that returns the **insertion point** — how many elements are `<=` the
value — so "how many restarts happened before this moment" *is* the run's
number, with no loop and no `if`. Java's `Collections.binarySearch` and
C#'s `List.BinarySearch` answer "where is it", and give the insertion
point only encoded as a negative number; Python hands it over directly.
`bisect_left` counts only the elements strictly smaller, which matters
when the value can equal one of them.

### 57.2 Sets with operators

```python
if ids & earlier_ids: ...                     # intersection: a shared track
every = persons <= (with_face | carried)       # subset of a union
```

`&`, `|` and `-` are intersection, union and difference; `<=` is "is a
subset of", `<` a proper subset. Each returns a new set (or a `bool`) and
leaves the operands alone — unlike Java's `retainAll`, `addAll` and
`removeAll`, which change the collection in place, so Java code usually
copies first. C#'s `HashSet` has `IsSubsetOf` and `IntersectWith`, also in
place. An empty set is false in an `if`, so `if ids & earlier_ids:` reads
"if they share an id".

### 57.3 The smallest tuple wins

```python
around = [(d.w * d.h, tid) for tid, d in observed if contains(d, centre)]
track = min(around)[1] if around else None
```

Tuples compare element by element, the first that differs deciding — the
way strings compare letter by letter. Putting the area first makes `min`
return the **smallest box** holding the face's centre (the body nearest
the face when one box sits inside another), and the track id second
breaks a tie. In Java this is a `Comparator.comparing(...).thenComparing(...)`;
here the order of the tuple is the comparator.

### 57.4 A function that remembers its arguments

```python
def identity_of(gallery, sure):
    def label_of(embedding):
        person_id, score = gallery.match(embedding)
        ...
        return "sure resident" if score >= sure else "probable resident"
    return label_of
```

`identity_of` returns a function that keeps `gallery` and `sure` from the
call that made it — a **closure**, as in JavaScript (section 45). The
caller (`bind`) only ever calls `label_of(embedding)`, so the tests give it
`lambda e: "sure resident"` instead of a real gallery. It plays the role of
a strategy object — an anonymous class implementing a one-method
interface in Java, or a lambda capturing locals in C#. Python's one
difference: the inner function may read `gallery` freely, but assigning to
it would make a new local name, unless declared `nonlocal`.

## 58. An endless counter read lazily, an ordered de-duplicate, a filter before every request, a blocking question, and a size that writes CSS (developer 38, review 40)

### 58.1 The smallest free number

```python
held = {int(found.group(1)) for p in self.people
        if (found := VISITOR_PATTERN.fullmatch(p.get("temporary_name") or ""))}
return VISITOR_NAME.format(next(n for n in itertools.count(1) if n not in held))
```

`itertools.count(1)` is an endless counter — `for (int n = 1; ; n++)` in
Java or C#. It never builds a list: it hands out one number when asked.
The parenthesised `n for n in … if …` is a **generator expression**
(section 55), just as lazy, and `next()` asks it for its first value, so
the loop stops at the first free number. `held` is a **set**, written
with braces, so `n not in held` is one hash lookup, like a
`HashSet<int>.contains`; with a list it would walk every element. `:=`
names the regex match inside the comprehension so the filter and the
value share it.

### 58.2 An ordered de-duplicate

```python
for entry_id in dict.fromkeys(_ids(gallery, payload)):
```

`dict.fromkeys(ids)` makes a dictionary whose keys are the ids, each
once, **in the order first seen** — dictionaries keep insertion order
since Python 3.7. Iterating it gives the ids without repeats, the job of
a `LinkedHashSet` in Java. A `set` would drop repeats too, but in no
promised order, and the answer lists them back to the page.

### 58.3 A filter before every request

The four new `delete` routes have no guard code, yet an unpaired device
gets 403. The guard is one function registered with
`@app.middleware("http")`: FastAPI runs it before every request and
passes it the next step, which it calls only when the request may go on.
It is a servlet filter in Java, or an ASP.NET Core middleware in C#.
Every POST goes through it, so a new route is guarded by being a POST.

### 58.4 A blocking question in the browser

```js
if (!confirm(`Delete ${count}? ${deleteWarning(count > 1)}`)) return;
```

`confirm()` shows the browser's own yes/no dialog and **stops the
script** until it is answered — true for OK, false for Cancel. It is the
one blocking call a page still uses, fine for a question asked once per
destructive click. A test can replace `window.confirm` with a function
that records its text and answers true, which is how the page tests read
the wording.

### 58.5 A size that writes CSS

```js
new ResizeObserver(() => {
  list.style.setProperty("--select-bar-height", `${selectBar.offsetHeight}px`);
}).observe(selectBar);
```

```css
.list.selecting {
  padding-bottom: calc(var(--select-bar-height, 124px) + 16px);
}
```

The selection bar is fixed to the bottom of the screen, so it takes no
room in the page and would cover the last photos; the list leaves room
under itself. A fixed number guessed the bar's height and was 3 px from
wrong on a phone. A `ResizeObserver` calls its function whenever the
observed element changes size — a wrap to more rows, a larger system
font, a rotation — just before the browser paints. It writes the height
to a **CSS custom property** (a variable whose name starts with `--`),
and `var(--select-bar-height, 124px)` reads it, with 124 px until it is
first written. `calc()` adds the margin. The JavaScript knows the size;
the CSS keeps deciding the layout.
