"""Find a working ffmpeg capture command for this machine.

Usage: uv run tools/diagnostico.py [rotulo]
       uv run tools/diagnostico.py --local     testa o ffmpeg sem nenhuma camera

Tries the current command and several variants, reporting how many analysis
frames each one delivers. A camera that connects but sends no frames stops
being a mystery, and the output says which setting to change.
"""

import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

from jarvis import cameras, capture

SECONDS = 14
FRAME_BYTES = capture.ANALYSIS_WIDTH * capture.ANALYSIS_HEIGHT * 3


def base(url, buffer, segments=True, wallclock=True, rate="-r"):
    comando = [
        capture.ffmpeg_exe(), "-hide_banner", "-loglevel", "warning", "-nostdin",
        "-rtsp_transport", "tcp",
        "-timeout", str(capture.SOCKET_TIMEOUT_SECONDS * 1_000_000),
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


def teste_local():
    """Decode a video ffmpeg makes itself, with no camera involved.

    Separates 'ffmpeg cannot decode on this machine' from anything to do with
    the cameras or the network.
    """
    with tempfile.TemporaryDirectory(prefix="jarvis_local_") as pasta:
        _teste_local(Path(pasta) / "amostra.mp4")


def _teste_local(amostra):
    print("1) gerando um video de teste 1920x1080 h264...")
    criar = subprocess.run(
        [capture.ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y",
         "-f", "lavfi", "-i", "testsrc=size=1920x1080:rate=15", "-t", "2",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", str(amostra)],
        capture_output=True)
    if not amostra.exists():
        print("   FALHOU ao gerar. O ffmpeg nao consegue codificar aqui.")
        print("   " + criar.stderr.decode(errors="replace")[:300])
        return
    print(f"   ok, {amostra.stat().st_size/1024:.0f} KB")

    print("2) decodificando para rawvideo 960x540, como o programa faz...")
    esperado = 5 * FRAME_BYTES
    decodificar = subprocess.run(
        [capture.ffmpeg_exe(), "-hide_banner", "-loglevel", "error",
         "-i", str(amostra), "-frames:v", "5",
         "-s", f"{capture.ANALYSIS_WIDTH}x{capture.ANALYSIS_HEIGHT}",
         "-pix_fmt", "bgr24", "-f", "rawvideo", "pipe:1"],
        capture_output=True)
    recebido = len(decodificar.stdout)
    print(f"   recebido {recebido} bytes, esperado {esperado}")
    if decodificar.stderr:
        print("   " + decodificar.stderr.decode(errors="replace")[:300])

    print()
    if recebido == esperado:
        print("VEREDITO: o ffmpeg decodifica e escreve no pipe normalmente.")
        print("O problema esta na captura RTSP, nao no decode. Rode sem --local.")
    elif recebido == 0:
        print("VEREDITO: o ffmpeg NAO decodifica nesta maquina.")
        print("Nao tem relacao com as cameras. Suspeite do binario do")
        print("imageio-ffmpeg, de antivirus, ou de politica do Windows.")
    else:
        print("VEREDITO: decode parcial. Leia o stderr acima.")


def main():
    if "--local" in sys.argv:
        teste_local()
        return
    wanted = sys.argv[1].capitalize() if len(sys.argv) > 1 else None
    env = cameras.load_env()
    todas = cameras.build_camera_list(env)
    escolhidas = [c for c in todas if wanted is None or c[0] == wanted]
    if not escolhidas:
        raise SystemExit(f"camera {wanted!r} nao encontrada em {[c[0] for c in todas]}")

    label, url = escolhidas[0]
    with tempfile.TemporaryDirectory(prefix="jarvis_diag_") as pasta:
        testar_variantes(label, url, Path(pasta))


def testar_variantes(label, url, buffer):
    print(f"camera: {label}   |   {SECONDS}s por variante   |   "
          f"esperado ~{capture.ANALYSIS_FPS * SECONDS} frames\n")

    variantes = [
        ("atual (como o programa roda)", base(url, buffer)),
        ("sem use_wallclock_as_timestamps", base(url, buffer, wallclock=False)),
        ("fps por filtro em vez de -r", base(url, buffer, rate="filter")),
        ("sem limitar taxa (todos os frames)", base(url, buffer, rate="none")),
        ("so analise, sem gravar segmentos", base(url, buffer, segments=False)),
    ]

    resultados = [(nome, tentar(nome, comando, buffer)) for nome, comando in variantes]
    atual = resultados[0][1]
    melhor = max(resultados, key=lambda r: r[1])

    print(f"\n{'=' * 66}")
    if atual >= 5:
        print("O comando atual funciona nesta maquina.")
    elif melhor[1] >= 5:
        print(f"O atual falhou, mas '{melhor[0]}' entregou {melhor[1]:.0f} frames.")
        print("Essa variante deve ir para o capture.py.")
    else:
        print("NENHUMA variante entregou frames.")
        print("Confira primeiro se a camera responde no IP do .env:")
        print("  powershell Test-NetConnection <ip> -Port 554")


if __name__ == "__main__":
    main()
