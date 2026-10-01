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

O `instalar.bat` faz seis coisas:

1. Instala o `uv` se faltar (se instalar, **feche a janela e rode de novo** — o
   PATH só atualiza numa janela nova)
2. Garante o Visual C++ Redistributable (ver 1.1)
3. `uv sync` — instala Python e dependências a partir do `uv.lock`, nas versões
   exatas que foram testadas, e o próprio `jarvis` como pacote (ARQUITETURA 3.1)
4. Baixa os modelos de visão (~60 MB no total)
5. Cria o atalho **J.A.R.V.I.S.** na Área de Trabalho, com o ícone do olho
   (um `.bat` não pode ter ícone próprio; ver ARQUITETURA 13)
6. Cria o `.env` a partir do `.env.example` e abre no Bloco de Notas

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

O `.bat` só confere se o `.env` existe e chama `uv run jarvis`. Os dois são
equivalentes; o `.bat` existe para dar para abrir com dois cliques e para a
janela não fechar sozinha quando algo dá errado.

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

## 5. Iniciar junto com o Windows

Para um sistema de vigilância isso costuma ser o que se quer. Use o Agendador de
Tarefas, não a pasta Inicializar — o Agendador reinicia o programa se ele cair.

1. Abra o **Agendador de Tarefas** → Criar Tarefa
2. **Geral:** marque "Executar estando o usuário conectado ou não" só se não
   precisar ver a janela. Para ver a interface, deixe "Executar somente quando o
   usuário estiver conectado"
3. **Disparadores:** Ao fazer logon
4. **Ações:** Iniciar um programa → o caminho completo do `jarvis.bat` (não o
   atalho: o Agendador precisa do arquivo de verdade)
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
  OK atual (como o programa roda)        118.0 frames  1o em 2.5s  segmentos 3
  OK sem use_wallclock_as_timestamps     118.0 frames  1o em 2.8s  segmentos 3
  -- fps por filtro em vez de -r           0.0 frames  1o em nunca segmentos 3
```

Se alguma variante entregar frames e a atual não, é ela que deve ir para o
`capture.py`. Se nenhuma entregar, as linhas de erro do ffmpeg aparecem junto.

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

Move o `faces/` atual para `faces_antigo_<data-hora>/` e reconstrói tudo a
partir dos clipes gravados. Os nomes precisam ser dados de novo, mas basta um
cartão por pessoa: os outros dela recebem o nome junto (ARQUITETURA 10.4).

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
