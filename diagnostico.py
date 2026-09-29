"""Find a working ffmpeg capture command for this machine.

Usage: uv run diagnostico.py [rotulo]

Tries the current command and several variants, reporting how many analysis
frames each one delivers. A camera that connects but sends no frames stops
being a mystery, and the output says which setting to change.
"""

import subprocess
import sys
import threading
import time
from pathlib import Path

import cameras
import capture

SECONDS = 14
FRAME_BYTES = capture.ANALYSIS_WIDTH * capture.ANALYSIS_HEIGHT * 3


def base(url, buffer, segments=True, wallclock=True, rate="-r"):
    comando = [
        capture.ffmpeg_exe(), "-hide_banner", "-loglevel", "warning", "-nostdin",
        "-rtsp_transport", "tcp",
    ]
    if wallclock:
        comando += ["-use_wallclock_as_timestamps", "1"]
    comando += ["-i", url]
    if segments:
        comando += [
            "-map", "0:v", "-an", "-c", "copy", "-f", "segment",
            "-segment_format", "mp4", "-segment_time", str(capture.SEGMENT_SECONDS),
            "-reset_timestamps", "1", "-strftime", "1",
            str(buffer / capture.SEGMENT_NAME),
        ]
    comando += ["-map", "0:v", "-an"]
    if rate == "-r":
        comando += ["-s", f"{capture.ANALYSIS_WIDTH}x{capture.ANALYSIS_HEIGHT}",
                    "-r", str(capture.ANALYSIS_FPS)]
    elif rate == "filter":
        comando += ["-vf", f"fps={capture.ANALYSIS_FPS},"
                           f"scale={capture.ANALYSIS_WIDTH}:{capture.ANALYSIS_HEIGHT}"]
    else:
        comando += ["-s", f"{capture.ANALYSIS_WIDTH}x{capture.ANALYSIS_HEIGHT}"]
    comando += ["-pix_fmt", "bgr24", "-f", "rawvideo", "pipe:1"]
    return comando


def tentar(nome, comando, buffer):
    for antigo in buffer.glob("*.mp4"):
        antigo.unlink(missing_ok=True)

    processo = subprocess.Popen(comando, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, bufsize=0)
    estado = {"bytes": 0, "primeiro": None, "erros": []}
    inicio = time.monotonic()

    def ler():
        while True:
            pedaco = processo.stdout.read(65536)
            if not pedaco:
                return
            if estado["primeiro"] is None:
                estado["primeiro"] = time.monotonic() - inicio
            estado["bytes"] += len(pedaco)

    def erros():
        for linha in processo.stderr:
            texto = linha.decode(errors="replace").strip()
            if texto and len(estado["erros"]) < 6:
                estado["erros"].append(texto)

    threading.Thread(target=ler, daemon=True).start()
    threading.Thread(target=erros, daemon=True).start()
    time.sleep(SECONDS)
    processo.terminate()
    try:
        processo.wait(timeout=5)
    except subprocess.TimeoutExpired:
        processo.kill()

    frames = estado["bytes"] / FRAME_BYTES
    segmentos = len(list(buffer.glob("*.mp4")))
    marca = "OK " if frames >= 5 else "-- "
    primeiro = f"{estado['primeiro']:.1f}s" if estado["primeiro"] else "nunca"
    print(f"  {marca}{nome:34} {frames:6.1f} frames  "
          f"1o em {primeiro:>7}  segmentos {segmentos}")
    for e in estado["erros"][:2]:
        print(f"       ffmpeg: {e[:88]}")
    return frames


def main():
    wanted = sys.argv[1].capitalize() if len(sys.argv) > 1 else None
    env = cameras.load_env()
    todas = cameras.build_camera_list(env)
    escolhidas = [c for c in todas if wanted is None or c[0] == wanted]
    if not escolhidas:
        raise SystemExit(f"camera {wanted!r} nao encontrada em {[c[0] for c in todas]}")

    label, url = escolhidas[0]
    buffer = Path("clips/_diag") / label
    buffer.mkdir(parents=True, exist_ok=True)

    print(f"camera: {label}   |   {SECONDS}s por variante   |   "
          f"esperado ~{capture.ANALYSIS_FPS * SECONDS} frames\n")

    variantes = [
        ("atual (como o programa roda)", base(url, buffer)),
        ("sem use_wallclock_as_timestamps", base(url, buffer, wallclock=False)),
        ("fps por filtro em vez de -r", base(url, buffer, rate="filter")),
        ("sem limitar taxa (todos os frames)", base(url, buffer, rate="none")),
        ("so analise, sem gravar segmentos", base(url, buffer, segments=False)),
    ]

    melhor = ("", 0.0)
    for nome, comando in variantes:
        frames = tentar(nome, comando, buffer)
        if frames > melhor[1]:
            melhor = (nome, frames)

    print(f"\n{'=' * 66}")
    if melhor[1] >= 5:
        print(f"MELHOR: {melhor[0]}  ({melhor[1]:.0f} frames)")
        if melhor[0].startswith("atual"):
            print("O comando atual funciona nesta maquina.")
        else:
            print("Mande este resultado que eu ajusto o capture.py.")
    else:
        print("NENHUMA variante entregou frames.")
        print("O ffmpeg conecta mas nao decodifica. Veja as linhas de erro acima.")

    for antigo in buffer.glob("*.mp4"):
        antigo.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
