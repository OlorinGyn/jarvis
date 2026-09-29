# J.A.R.V.I.S. — instalação e operação

Como colocar o sistema para rodar numa máquina nova. Para entender **como** ele
funciona, veja [ARQUITETURA.md](ARQUITETURA.md).

---

## 1. O que precisa estar instalado

Três coisas:

| Programa | Para quê |
|---|---|
| **git** | Baixar e atualizar o código |
| **uv** | Instalar o Python e as dependências |
| **Visual C++ Redistributable** | O OpenCV depende dele |

**Não é preciso instalar Python, ffmpeg, CUDA, PyTorch nem codecs.** O `uv` traz
o Python; o ffmpeg vem empacotado na dependência `imageio-ffmpeg`. O projeto tem
apenas **duas** dependências Python: `opencv-python` e `imageio-ffmpeg`, cerca de
90 MB no total.

O `instalar.bat` cuida do `uv` e do Redistributable sozinho.

### 1.1 Por que o Visual C++ Redistributable

Bibliotecas nativas trazem DLLs próprias mas **não empacotam o runtime C++ da
Microsoft** de que elas dependem. Numa instalação limpa do Windows esse runtime
não existe, e o erro é:

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

## 2. Passo a passo

```bat
git clone https://github.com/OlorinGyn/jarvis.git
cd jarvis
instalar.bat
```

O `instalar.bat` faz cinco coisas:

1. Instala o `uv` se faltar (se instalar, **feche a janela e rode de novo** — o
   PATH só atualiza numa janela nova)
2. Garante o Visual C++ Redistributable (ver 1.1)
3. `uv sync` — instala Python e dependências a partir do `uv.lock`, nas versões
   exatas que foram testadas
4. Baixa os modelos de visão (~60 MB no total)
5. Cria o `.env` a partir do `.env.example` e abre no Bloco de Notas

Cada passo tem sua própria mensagem de erro. A primeira versão juntava o
download dos modelos com a carga do PyTorch e, quando o PyTorch falhava,
culpava a conexão de internet — que estava perfeita.

Preencha o `.env` e inicie:

```bat
jarvis.bat
```

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
CAM_FRONT_IP=192.168.0.10
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

## 5. Iniciar junto com o Windows

Para um sistema de vigilância isso costuma ser o que se quer. Use o Agendador de
Tarefas, não a pasta Inicializar — o Agendador reinicia o programa se ele cair.

1. Abra o **Agendador de Tarefas** → Criar Tarefa
2. **Geral:** marque "Executar estando o usuário conectado ou não" só se não
   precisar ver a janela. Para ver a interface, deixe "Executar somente quando o
   usuário estiver conectado"
3. **Disparadores:** Ao fazer logon
4. **Ações:** Iniciar um programa → o caminho completo do `jarvis.bat`
5. **Configurações:** marque "Se a tarefa falhar, reiniciar a cada 1 minuto"

A interface precisa de uma sessão gráfica ativa; ela não roda como serviço do
Windows sem janela.

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
faz mal.

## 8. Quando algo não funciona

**`406 Not Acceptable` ou `DESCRIBE failed`**

A câmera aceita **uma única sessão RTSP**. Verifique se não há outra instância
do J.A.R.V.I.S. aberta, ou um ffmpeg órfão:

```bat
tasklist | findstr ffmpeg
```

Se o programa foi encerrado à força, o ffmpeg pode ter sobrevivido e estar
segurando a câmera.

**Diagnóstico completo de uma câmera**

```bat
uv run probe_rtsp.py 192.168.0.10 usuario senha stream1
```

Mostra cada etapa do handshake. O esperado é `200 OK` nas três:

```
DESCRIBE  -> RTSP/1.0 200 OK
SETUP     -> RTSP/1.0 200 OK
PLAY      -> RTSP/1.0 200 OK
```

Se `DESCRIBE` passa e `SETUP` fecha a conexão, é a regra das duas funções da
seção 4.

**Painel mostra `no signal`**

O ffmpeg daquela câmera caiu e será reiniciado sozinho em 5 segundos. Se
persistir, teste a rede e rode o `probe_rtsp.py`.

**Nenhum rosto aparece na aba People**

Rostos só são procurados em eventos que tiveram `person`. À noite, no
infravermelho, um rosto costuma ter ~44 px contra os ~112 px ideais — aparece
marcado em vermelho e não reforça a galeria. Detalhes em ARQUITETURA 10.5.

**`WinError 1114` ou `Error loading ... .dll`**

Falta o Visual C++ Redistributable. Ver seção 1.1.

**`WinError 4551: An Application Control policy has blocked this file`**

O Smart App Control do Windows 11 bloqueou uma DLL sem assinatura reconhecida.

Isto **não deve mais acontecer**: o PyTorch, que era o único componente afetado,
foi removido do projeto justamente por causa disso (ARQUITETURA 7.11). Se
aparecer em outra biblioteca, **não desligue o Smart App Control** sem pensar —
ele é irreversível, só volta reinstalando o Windows. Procure primeiro uma
alternativa assinada.

Para conferir o estado dele:

```bat
reg query "HKLM\SYSTEM\CurrentControlSet\Control\CI\Policy" /v VerifiedAndReputablePolicyState
```

`0x1` significa ligado e bloqueando.

**O disco está enchendo**

Não há retenção automática ainda. As gravações ficam em `clips/<camera>/<data>/`
e podem ser apagadas à vontade; o buffer em `clips/_buffer/` se limpa sozinho.
