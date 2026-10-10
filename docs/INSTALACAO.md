# J.A.R.V.I.S. — instalação e operação

Como colocar o sistema para rodar numa máquina nova. Para entender **como** ele
funciona, veja [ARQUITETURA.md](ARQUITETURA.md).

---

## 1. O que precisa estar instalado

Quatro coisas:

| Programa | Para quê |
|---|---|
| **git** | Baixar e atualizar o código |
| **uv** | Instalar as dependências e rodar o programa |
| **Python 3.14 oficial** (python.org) | O interpretador. Tem que ser o **assinado**, ver 1.2 |
| **Visual C++ Redistributable** | O OpenCV depende dele |

**Não é preciso instalar ffmpeg, CUDA, PyTorch nem codecs.** O ffmpeg vem
empacotado na dependência `imageio-ffmpeg`; as demais estão no `pyproject.toml`
e o `uv` as instala.

O `instalar.bat` cuida do `uv`, do Python e do Redistributable sozinho.

### 1.1 Por que o Visual C++ Redistributable

Bibliotecas nativas trazem DLLs próprias mas **não empacotam o runtime C++ da
Microsoft** de que elas dependem. Numa instalação limpa do Windows esse runtime
não existe, e o erro é parecido com este — que apareceu no M900 quando o
projeto ainda usava PyTorch; hoje a DLL citada seria a do OpenCV:

```
OSError: [WinError 1114] A dynamic link library (DLL) initialization
routine failed. Error loading "...\torch\lib\c10.dll"
```

A mensagem não diz o que falta. A correção:

```bat
winget install --id Microsoft.VCRedist.2015+.x64 -e
```

Ou baixe <https://aka.ms/vs/17/release/vc_redist.x64.exe>. Reinicie depois de
instalar.

Na máquina de desenvolvimento isso já estava presente por causa de outros
programas, e por isso o problema só apareceu na máquina de destino.

### 1.2 Por que o Python oficial, e não o que o uv baixa

O `uv` sabe baixar Python sozinho, e o projeto usava isso. Esses binários
(do projeto *python-build-standalone*) **não são assinados**. O Smart App
Control do Windows 11 deixa passar binário sem assinatura só se a nuvem da
Microsoft disser que ele tem boa reputação — e esse veredito muda com o tempo.

Aconteceu no M900 em 09/10/2026, e o detalhe é o que torna o problema
traiçoeiro: o Python bloqueado era o **mesmo arquivo** que rodou normalmente em
29 e 30/09 — o `cpython-3.14.7` que o `uv` baixou em 29/09. Nada mudou no
disco; mudou o veredito do Windows sobre ele. O próprio interpretador passou a
ser recusado (`WinError 4551`), nem `python -c "print(1)"` rodava, e o
programa não tinha como voltar a subir. O registro `CodeIntegrity` do Windows
não mostra quando o veredito virou: o M900 não tinha rodado o J.A.R.V.I.S. entre
30/09 e 09/10, e o primeiro bloqueio registrado do `python.exe` é o da tentativa
de 09/10. (Os bloqueios de 29/09 no mesmo registro são outra coisa: DLLs do
PyTorch carregadas pelo Python, o caso da ARQUITETURA 7.11.)

O Python do python.org é **assinado pela Python Software Foundation**, e
assinatura válida passa sem depender de reputação. O `pyproject.toml` declara
`python-preference = "system"`: o `uv` usa o Python instalado no Windows quando
existe, e só cai para o dele se não houver nenhum. Para instalar à mão:

```bat
winget install --id Python.Python.3.14 -e --scope user
```

Para conferir que o ambiente está no Python assinado:

```powershell
Get-AuthenticodeSignature .venv\Scripts\python.exe
```

Tem que dizer `Valid` e `CN=Python Software Foundation`.

## 2. Passo a passo

```bat
git clone https://github.com/OlorinGyn/jarvis.git
cd jarvis
instalar.bat
```

O `instalar.bat` faz sete coisas:

1. Instala o `uv` se faltar (se instalar, **feche a janela e rode de novo** — o
   PATH só atualiza numa janela nova)
2. Garante o Visual C++ Redistributable (ver 1.1)
3. Instala o Python 3.14 oficial, só para o usuário atual (ver 1.2)
4. `uv sync` — instala as dependências a partir do `uv.lock`, nas versões
   exatas que foram testadas, e o próprio `jarvis` como pacote (ARQUITETURA 3.1)
5. Baixa os modelos de visão (~73 MB no total, ver seção 3)
6. Cria o atalho **J.A.R.V.I.S.** na Área de Trabalho, com o ícone do olho
   (um `.bat` não pode ter ícone próprio; ver ARQUITETURA 14)
7. Cria o `.env` a partir do `.env.example` e abre no Bloco de Notas

Cada passo tem sua própria mensagem de erro. A primeira versão juntava o
download dos modelos com a carga do PyTorch e, quando o PyTorch falhava,
culpava a conexão de internet — que estava perfeita.

Preencha o `.env` e inicie pelo atalho da Área de Trabalho, ou:

```bat
jarvis.bat
```

Para recriar só o atalho:

```bat
powershell -ExecutionPolicy Bypass -File tools\criar_atalho.ps1
```

Isso liga o serviço — câmeras, detecção, gravação, rostos, notificação — e abre
o navegador em `http://127.0.0.1:8765`, com as abas **Ao vivo** e
**Gravações**. Clicar no atalho com o serviço já rodando só abre o navegador;
não sobe um segundo, que brigaria pela câmera. O console que fica aberto é o
serviço: encerre com `Ctrl+C` nele, não no X (ARQUITETURA 17.7).

O `.bat` só confere se o `.env` existe e chama `uv run python -m jarvis`, que
vai direto ao Python assinado em vez do `jarvis.exe` sem assinatura que o `uv`
gera (seção 1.2).

Para ligar **só o serviço**, sem abrir o navegador — é o que se usa para subir
com o Windows (seção 5):

```bat
jarvis_vigilancia.bat
```

**Pelo celular**, na mesma rede Wi-Fi: o console mostra o endereço, algo como
`http://192.168.0.18:8765`. Na primeira vez o Windows pergunta se o Python pode
receber conexões da rede; é preciso permitir. Sem isso, só o próprio computador
abre a página.

Para parar de qualquer terminal, sem procurar o console do serviço:

```bat
uv run python -m jarvis --stop
```

O que aconteceu fica em `logs\jarvis.log`.

A janela antiga do OpenCV ainda existe, **provisoriamente**, para nomear rostos
e mexer nos ajustes até a web fazer isso (backlog, item 3):

```bat
uv run python -m jarvis --window
```

**Since 09/10/2026 the copy that stays on is production, in `C:\JARVIS`**, and
this folder becomes the test copy. Running the commands above here starts the
test copy. See section 9.

## 3. O que é baixado automaticamente

Nada disso está no repositório, porque são arquivos grandes que não devem ser
versionados:

| Arquivo | Tamanho | Origem |
|---|---|---|
| `models/yolo11s.onnx` | 36 MB | ultralytics/assets (release oficial) |
| `models/face_detection_yunet_2023mar.onnx` | 227 KB | opencv/opencv_zoo |
| `models/face_recognition_sface_2021dec.onnx` | 37 MB | opencv/opencv_zoo |

Os modelos são baixados por `people.ensure_model()` e `faces.ensure_models()`
na primeira vez que cada camada roda. O `instalar.bat` antecipa isso para o primeiro
evento não esperar o download.

## 4. Configurar as câmeras

O `.env` guarda uma câmera por trio de linhas. O rótulo vira o nome na tela e o
nome da pasta das gravações.

```
CAM_FRONT_IP=192.168.0.116
CAM_FRONT_USER=usuario
CAM_FRONT_PASSWORD=senha
```

Três armadilhas, todas já custaram tempo neste projeto:

**As credenciais não são as da conta TP-Link.** Crie uma "Conta da Câmera" no
app Tapo: câmera → engrenagem → Configurações Avançadas → Conta da Câmera.

**A câmera só faz duas de três funções ao mesmo tempo:** Tapo Care, gravação em
cartão SD e RTSP. Com as duas primeiras ativas, o RTSP é desligado em silêncio —
o sintoma é `DESCRIBE` responder `200 OK` e o `SETUP` fechar a conexão.
**Desativar a gravação no app não basta: o cartão precisa ser removido
fisicamente.** Ou desligue o Tapo Care. Detalhes em ARQUITETURA seção 11.

**Reserve o IP por MAC no roteador.** Sem isso o endereço muda numa renovação de
DHCP e o sistema para de conectar.

## 5. Starting with Windows

Do not create the task by hand. `tools\production.ps1 -Action install`
(section 9) registers it with the settings that matter, and two of them are easy
to get wrong by hand:

- **No execution time limit.** The Task Scheduler default is 72 hours: it
  would kill the surveillance every three days.
- **A trigger every 5 minutes**, not "restart on failure", which only acts
  when the task fails to *start*, not when the program crashes later
  (ARQUITETURA 18.7).

The task runs production from `C:\JARVIS` without a console, whether or not
anyone is logged on.

## 6. Ajustes para o M900

O M900 tem 4 núcleos Skylake, bem menos que a máquina de desenvolvimento. As
constantes que mais importam, em ordem de impacto:

| Constante | Arquivo | Efeito |
|---|---|---|
| `HWACCEL` | `capture.py` | Decode por hardware. Vazio por padrão. No M900 teste `"dxva2"` ou `"qsv"` — o Quick Sync do Skylake decodifica H.264 em silício e libera CPU |
| `ANALYSIS_FPS` | `capture.py` | 10 hoje. Baixar para 6 corta quase 40% do trabalho de análise |
| `MIN_INTERVAL` | `people.py` | 0.25 s entre execuções do YOLO. Subir para 0.5 reduz pela metade |
| `MODEL_FILE` e `MODEL_URL` | `people.py` | `yolo11s.onnx`. Trocar os dois para `yolo11n.onnx` é bem mais rápido e um pouco menos preciso |

**Meça antes de mexer.** A gravação em si não custa quase nada, porque os
pacotes da câmera são copiados sem recodificar (ARQUITETURA 5.1). O custo está
no decode para análise e no YOLO.

O `HWACCEL` só afeta a saída de análise; a gravação nunca decodifica.

## 7. Atualizar

```bat
git pull
uv sync
```

O `uv sync` é necessário só quando as dependências mudam, mas rodar sempre não
faz mal. O `uv run` também sincroniza sozinho antes de executar.

**Ao atualizar uma cópia anterior a 29/09/2026:** o código saiu da raiz para
`src/jarvis/` e `tools/`. O `git pull` move os arquivos; se sobrar uma pasta
`__pycache__/` na raiz, pode apagar. O `.env`, `models/`, `clips/` e `faces/`
continuam onde estão.

## 8. Quando algo não funciona

**`406 Not Acceptable` ou `DESCRIBE failed`**

A câmera aceita **uma única sessão RTSP**. Verifique se não há outra instância
do J.A.R.V.I.S. aberta, ou um ffmpeg órfão:

```bat
tasklist | findstr ffmpeg
```

Se o programa foi encerrado à força, o ffmpeg pode ter sobrevivido e estar
segurando a câmera.

**"Tempo esgotado. Confira a rede e o IP da camera"**

Nada responde no IP do `.env`. Ou o IP nunca foi preenchido, ou o roteador deu
outro endereço à câmera. Confirme:

```powershell
Test-NetConnection 192.168.0.116 -Port 554
```

Se falhar, descubra o IP atual no app Tapo (câmera → engrenagem → Informações
do dispositivo) ou na lista de clientes do roteador, atualize o `.env` e
reserve o IP (seção 4). As Tapo têm MAC começando com `14-EB-B6`. As
credenciais identificam qual é qual: cada câmera só aceita a própria Conta da
Câmera e responde `401` às outras.

**Conecta mas nunca aparece imagem ("nenhum frame recebido")**

Antes de tudo, faça o teste de IP acima: versões antigas do `capture.py`, sem
`-timeout`, mostravam esta mensagem também para IP errado (ARQUITETURA 5.7).

O RTSP está bom mas o ffmpeg não entrega frames para análise. Rode:

```bat
uv run tools/diagnostico.py Front
```

Ele testa cinco variantes do comando de captura, 14 segundos cada, e informa
quantos frames cada uma entregou nesta máquina:

```
  OK atual (como o programa roda)        126.0 frames  1o em    2.6s  segmentos 3
  OK sem use_wallclock_as_timestamps     125.0 frames  1o em    3.0s  segmentos 3
  ...
O comando atual funciona nesta maquina.
```

Se a atual falhar e outra variante entregar frames, ele diz qual — é ela que
deve ir para o `capture.py`. Se nenhuma entregar, as linhas de erro do ffmpeg
aparecem junto, e ele lembra de testar o IP primeiro. Os segmentos de teste vão
para uma pasta temporária do sistema, apagada no fim.

A coluna `segmentos` separa os dois casos: segmentos sendo gravados com zero
frames significa que a câmera e a rede estão bem, e o problema está só na saída
de análise.

**Diagnóstico completo de uma câmera**

```bat
uv run tools/probe_rtsp.py 192.168.0.116 usuario senha stream1
```

Mostra cada etapa do handshake. O esperado é `200 OK` nas três:

```
DESCRIBE  -> RTSP/1.0 200 OK
SETUP     -> RTSP/1.0 200 OK
PLAY      -> RTSP/1.0 200 OK
```

Se `DESCRIBE` passa e `SETUP` fecha a conexão, é a regra das duas funções da
seção 4.

**A janela abre cinza e diz "Não Responde"**

Isto **não deve mais acontecer**. Era causado pela leitura do pipe bloquear o
laço da interface enquanto o ffmpeg negociava o RTSP, o que leva ~2,5 s. Hoje a
leitura roda em thread separada (ARQUITETURA 5.4).

Se voltar a acontecer, é sinal de que algo novo passou a bloquear o laço
principal — desconfie de operação de disco ou rede feita dentro dele.

**Linhas `[h264 @ ...] error while decoding MB ...` no terminal**

Não é erro do programa. Quer dizer que a **câmera** mandou um pedaço de imagem
danificado: um bloco de 16x16 px (o "MB", macrobloco) borrado por uma fração de
segundo, até o próximo quadro completo. A gravação copia os bytes da câmera sem
recodificar, então o dano já veio assim. Como a conexão é TCP, a rede não perde
dados no caminho; quem descarta é a própria câmera, quando o Wi-Fi dela engasga.

Desde 30/09/2026 essas linhas não aparecem mais no terminal (ARQUITETURA 10.11).
Para ver se uma câmera está com o sinal ruim:

```bat
uv run tools/verificar_clipes.py 2026-09-30
```

```
  Back   13-47-27  5 bloco(s) danificado(s)
  ...
2026-09-30:
  Back   8 de 68 clipes com dano
  Front  0 de 34 clipes com dano
```

Se uma câmera tem dano frequente e a outra não, confira o sinal dela no app
Tapo (câmera → engrenagem → Informações do dispositivo). O que costuma resolver:
aproximar o roteador ou pôr um repetidor, e preferir a rede de 2,4 GHz, que
alcança mais longe que a de 5 GHz.

**Rostos errados ou repetidos na tela People**

Com o programa **fechado**:

```bat
uv run tools/refazer_rostos.py
```

Move o `faces/` atual para `backups/faces_<data-hora>/` e reconstrói tudo a
partir dos clipes gravados. Os nomes precisam ser dados de novo, mas basta um
cartão por pessoa: os outros dela recebem o nome junto (ARQUITETURA 10.4).
Depois de conferir que está tudo certo, a cópia em `backups/` pode ser apagada.

**Painel mostra `sem sinal`**

O motivo aparece **em amarelo no próprio painel**. Os mais comuns:

| Texto | O que fazer |
|---|---|
| Camera ocupada | Outra coisa está usando a câmera. Ver abaixo. |
| Credenciais incorretas | Confira a Conta da Câmera no app Tapo |
| Confira o IP / Tempo esgotado | A câmera mudou de endereço ou está desligada. Ver "Tempo esgotado" acima |

**"Camera ocupada" é o caso mais frequente numa instalação nova.** A Tapo aceita
**uma conexão RTSP por vez**. Se o J.A.R.V.I.S. estiver rodando noutra máquina —
a de desenvolvimento, por exemplo — a segunda não conecta. Feche a outra
instância, o app Tapo, ou um ffmpeg órfão:

```bat
tasklist | findstr ffmpeg
```

**Nenhum rosto aparece na aba People**

É o comportamento esperado em muitos eventos. Um rosto só entra se cumprir
tudo isto:

- o evento teve `person` entre os rótulos;
- o rosto está **de frente** — perfil, nuca e cabeça baixa são ignorados;
- está em cima de uma pessoa que o YOLO vê no mesmo frame;
- se for alguém novo, apareceu em pelo menos 2 frames do clipe.

E aparece alguns segundos depois do evento: a varredura roda depois que o
clipe é montado, uma de cada vez. Detalhes em ARQUITETURA 10.9. À noite, no
infravermelho, o rosto costuma ter ~44 px contra os ~112 px ideais, e o
reconhecimento é instável (ARQUITETURA 10.5).

**`WinError 1114` ou `Error loading ... .dll`**

Falta o Visual C++ Redistributable. Ver seção 1.1.

**`WinError 4551: An Application Control policy has blocked this file`**

O Smart App Control do Windows 11 bloqueou um binário sem assinatura
reconhecida. Já aconteceu duas vezes:

| Quando | O que foi bloqueado | Saída |
|---|---|---|
| 29/09/2026 | DLLs do PyTorch | PyTorch removido, YOLO pelo `cv2.dnn` (ARQUITETURA 7.11) |
| 09/10/2026 | o **próprio Python** que o `uv` baixa | Python oficial assinado (seção 1.2) |

Se a mensagem cita `python.exe` ou o `uv` diz `Failed to spawn: python`, é o
segundo caso: confira a assinatura com `Get-AuthenticodeSignature
.venv\Scripts\python.exe`, e se não for da Python Software Foundation, instale
o Python oficial e recrie o ambiente (`Remove-Item .venv -Recurse` e `uv sync`).

Se aparecer em outra biblioteca, **não desligue o Smart App Control** sem
pensar — ele é irreversível, só volta reinstalando o Windows. Procure primeiro
uma alternativa assinada. Para ver o que foi bloqueado, o Windows registra cada
bloqueio no log `Microsoft-Windows-CodeIntegrity/Operational`.

Para conferir o estado dele:

```bat
reg query "HKLM\SYSTEM\CurrentControlSet\Control\CI\Policy" /v VerifiedAndReputablePolicyState
```

`0x1` significa ligado e bloqueando.

**O disco está enchendo**

Não há retenção automática ainda, e o ritmo real é de **~300 MB por dia**
(medido em 30/09/2026, ARQUITETURA 8.6). As gravações ficam em
`clips/<camera>/<data>/`, uma pasta por dia, e podem ser apagadas à vontade —
o mais simples é apagar as pastas de dias antigos. O buffer em `clips/_buffer/`
se limpa sozinho, e `backups/` só tem o que as ferramentas guardaram.

## 9. Production and test (since 09/10/2026)

Written in English (CLAUDE.md, language). How it works and why: ARQUITETURA
18.

### 9.1 The two copies

| | Production | Test copy |
|---|---|---|
| Folder | `C:\JARVIS` | this project folder |
| Runs | always, started by Windows | only when you start it |
| Version | the latest **release tag**, reviewed | whatever is being written |
| Cameras | `stream1`, 1080p, records in HD | `stream2`, 640x360 |
| Page | `http://127.0.0.1:8765` (from another computer: `http://192.168.0.18:8765`) | `http://127.0.0.1:8766` |
| Telegram | on | off, prefix `[TEST]` |
| Desktop | **J.A.R.V.I.S.** opens it | **J.A.R.V.I.S. (test)** starts it |

Both can run at once: the camera serves `stream1` to one client and `stream2` to
several (ARQUITETURA 18.2). Each copy has its own recordings, faces and
settings — a name given in the test copy does not reach production.

### 9.2 Day to day

| Want | Do |
|---|---|
| Look at the cameras | the **J.A.R.V.I.S.** desktop shortcut |
| Is production all right? | `powershell -ExecutionPolicy Bypass -File tools\production.ps1 -Action status` |
| Stop it on purpose | `... -Action stop` — stays stopped, even after a reboot, until `start` |
| Start it again | `... -Action start` |
| Are the recordings still readable? | `... -Action check` |
| What happened? | `C:\JARVIS\logs\jarvis.log` |

Stopping production any other way (Task Manager, ending the task) skips the
clean shutdown, and a clip being assembled at that moment is lost. Within
5 minutes Windows starts it again anyway, unless it was stopped with `stop`.

### 9.3 Updating

Updates are run by Claude, on request, after an architect review has tagged a
release (CONTEXTO 13). Never automatic: a failed update at night is a night
without surveillance.

```bat
powershell -ExecutionPolicy Bypass -File tools\production.ps1 -Action update
```

It checks that every recording and face is readable before and after, and if
the new version fails anything, it puts the previous one back and says so on
Telegram.

### 9.4 Installing on a new machine

From the project folder, after `instalar.bat` and with the program closed:

```bat
powershell -ExecutionPolicy Bypass -File tools\production.ps1 -Action install
```

Windows asks once for administrator permission, to register the startup task.
Refusing it leaves production running now, but it will not come back after a
reboot; register it later from an administrator PowerShell with
`-Action register`. If an install fails half-way, delete `C:\JARVIS` and run it
again.

### 9.5 When something is wrong

| Symptom | Look at |
|---|---|
| The page does not open | `-Action status`; if it says HELD, `-Action start`; otherwise `C:\JARVIS\logs\jarvis.log` |
| Another computer gets nothing, and the log says `Invalid HTTP request received` | the browser is trying `https://`; type `http://192.168.0.18:8765` (ARQUITETURA 17.8) |
| A camera shows "no signal" | its last frame is over 5 s old; the reason is written under it, and the camera reconnects on its own |
| Telegram message "update ... FAILED" | the previous version is back; the message says whether it is running |
| Black console windows titled `...site-packages\imageio_ffmpeg\...`, two that stay and others that flash | production's ffmpeg, visible when production was started by `production.ps1` instead of by Windows (ARQUITETURA 18.7). **Do not close them**: closing one of the two that stay cuts that camera until it reconnects, and closing a flashing one loses the clip being assembled. **Gone since `v2026.10.10`** (R15): seen on an older version, they disappear after a reboot |
