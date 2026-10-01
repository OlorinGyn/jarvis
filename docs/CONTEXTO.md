# J.A.R.V.I.S. — contexto completo do projeto

Este arquivo existe para uma sessão nova do Claude Code continuar o trabalho sem
perder o que já foi decidido, testado e descartado. **Leia isto antes de mexer
em qualquer coisa.**

Complementa, não substitui:

| Documento | Para quê |
|---|---|
| `ARQUITETURA.md` | Como o sistema funciona e por quê, camada por camada |
| `INSTALACAO.md` | Instalar e operar numa máquina nova, solução de problemas |
| `PYTHON.md` | Python e bibliotecas para quem vem de Java/C# |
| **este arquivo** | Histórico, preferências do usuário, caminhos já descartados |

---

## 1. O projeto

Vigilância doméstica com duas câmeras TP-Link **Tapo C310** externas, via RTSP.
O sistema detecta movimento, decide se é pessoa ou animal, grava o evento,
reconhece rostos e permite cadastrar nomes.

Interface OpenCV com três abas: **Live**, **Records** (gravações, com calendário
e rolagem) e **People** (rostos, com cadastro de nome).

**Duas máquinas:**

| | Desenvolvimento | Destino |
|---|---|---|
| Máquina | Ryzen 9 7950X, 64 GB, RTX 4080 | Lenovo M900, i5 Skylake 4 núcleos, 16 GB |
| Caminho | `D:\Personal Projects\J.A.R.V.I.S\jarvis` | `C:\Personal Projects\jarvis` |
| Estado | Tudo funciona | Tudo funciona desde 29/09/2026 (seção 6) |

**A RTX 4080 é deliberadamente ignorada.** Nada aqui é treinado, e desenvolver
no mesmo caminho de CPU que o M900 usará evita divergência entre as máquinas.

## 2. Como o usuário trabalha — siga isto

Quatro regras que ele estabeleceu explicitamente:

**Código sem comentários.** Nenhum. Toda explicação vive em `docs/`. Docstrings
de uma linha são aceitas. Confira antes de commitar:

```bat
uv run python -c "import tokenize,pathlib; print(sum(sum(1 for t in tokenize.generate_tokens(tokenize.open(f).readline) if t.type==tokenize.COMMENT) for d in ('src','tools') for f in pathlib.Path(d).rglob('*.py')))"
```

Olha só `src/` e `tools/`; o `.venv` tem milhares de comentários de terceiros.

**Toda mudança termina em commit + documentação atualizada.** Sem exceção, e sem
precisar pedir. A mensagem de commit explica o **porquê**, não só o quê.

**Antes de commitar, confira que o `.env` não entrou.** Ele tem as senhas reais
das câmeras. Eu já vazei essas senhas uma vez, em exemplos dentro da
documentação, e precisei corrigir. Cheque também `*.onnx`, `*.pt` e `clips/`.

**Explique o código, não só o resultado.** O usuário está aprendendo Python e
OpenCV, vindo de Java e C#. Ele pediu respostas concisas em opções e tangentes,
mas **nunca** economize na explicação de código ou comando — já reclamou quando
eu cortei demais.

Documentação em português; código e identificadores em inglês.

## 3. Decisões tomadas — não desfaça sem motivo novo

### Python em vez de C++
Os bindings Python do OpenCV chamam o mesmo C++ compilado, com microssegundos de
sobrecarga por chamada. O tempo real está em decode e inferência, ambos em
código nativo. O ecossistema de visão é Python-first.

### ffmpeg em vez de `cv2.VideoCapture`
O `VideoCapture` entrega frames decodificados, o que obriga a **recodificar**
para salvar. Medido: o pipeline antigo produzia arquivos **25% maiores que o
original da câmera e com três gerações de perda**. Hoje um processo ffmpeg por
câmera serve duas saídas — segmentos `-c copy` (cópia byte a byte) e frames
960x540 para análise. Ver ARQUITETURA 5.1 e 5.2.

### Sem PyTorch
O **Smart App Control** do Windows 11 bloqueia binários sem assinatura
reconhecida, e as DLLs do PyTorch não são assinadas (`WinError 4551`).
Desligá-lo é **irreversível** — só volta reinstalando o Windows. Em vez disso,
o YOLO roda por `cv2.dnn` sobre o `yolo11s.onnx` oficial. Tirou ~2,5 GB de
dependências; o projeto tem hoje só `opencv-python` e `imageio-ffmpeg`.
Custo: inferência de 24 ms para 50–62 ms. Ver ARQUITETURA 7.11.

### Sem compactar os vídeos
Implementado e removido. Medido em arquivo real: zip economiza **0,2%**, bzip2 e
lzma deixam o arquivo **maior**. H.264 já é codificado por entropia. Ver
ARQUITETURA 8.7. **Uma medição antiga dizia 5–11% e valia para o formato
recodificado antigo — não se aplica mais.**

### Uma conexão RTSP por câmera
A Tapo aceita só uma sessão. Testado: com uma conexão aberta, a segunda recebe
`406 Not Acceptable`. Por isso um único ffmpeg faz as duas saídas.

### Rosto no clipe, não ao vivo
Um rosto de 60 px em 1080p vira 30 px nos frames de análise de 960x540, e o
reconhecedor quer ~112 px. O `scan_clip()` roda sobre o clipe montado, em
resolução original, fora do caminho crítico.

### YuNet e SFace em vez de InsightFace
Ambos embutidos no OpenCV, sem dependência nova. Medido: similaridade **1.000**
para o mesmo rosto e **0.045** para rostos diferentes, com limiar de 0.363.

## 4. Bugs encontrados e corrigidos — não reintroduza

| Bug | Causa | Correção |
|---|---|---|
| Janela não fechava no X | HighGUI não tem evento de fechamento; o `imshow` seguinte recria a janela | Consultar `getWindowProperty` **depois** do `waitKey` |
| Vídeo esticava ao redimensionar | `WINDOW_KEEPRATIO` vale 0 no backend Win32 | Gerar imagem do tamanho exato da janela via `getWindowImageRect` e fazer letterbox |
| Clique no cartão abria Documentos | `subprocess` com lista põe aspas em todo argumento com espaço, e o `/select,` do Explorer ia para dentro delas | Passar a string pronta no Windows |
| Detecção de rosto dava zero | A amostragem lia os primeiros frames do clipe, e a pré-gravação faz o começo ser **antes** da pessoa chegar | Calcular o passo pelo total de frames |
| Rosto de 44 px descartado | `MIN_FACE_WIDTH` alto demais | Baixar o piso e **marcar** rostos pequenos em vez de descartar |
| Galeria ignorava caminho de teste | `def __init__(self, path=GALLERY_FILE)` congela o valor na definição | `path=None` e resolver dentro |
| Janela cinza "Não Responde" | O laço bloqueava lendo o pipe; o primeiro frame leva **2,45 s** | Thread leitora por câmera; o laço nunca bloqueia |
| "sem sinal" sem motivo | `stderr` do ffmpeg ia para `DEVNULL`, e o `ok` do arranque checava `poll()` antes de o processo ter tempo de falhar | Capturar stderr, esperar o primeiro frame de verdade, traduzir erros conhecidos |
| Falsos positivos de pessoa | Objetos de parede sob infravermelho | Altura mínima (medido: falsos 36–86 px, pessoas reais 294–306 px, **18/18 corretos**) |
| Mosquitos disparando gravação | Insetos perto da lente ficam grandes no IR | Confirmação temporal: só reporta o que persiste 3 frames no mesmo lugar (**83% menos disparos**) |
| "nenhum frame recebido" no M900, sem erro | `.env` com os IPs de exemplo do `.env.example`; sem timeout o ffmpeg espera o TCP para sempre em silêncio | `-timeout` no RTSP e tradução do `Error number -138` (seção 6) |
| Falso movimento de dia na Front | Manchas de sol e sombra de folhas; o relógio da câmera no canto | Filtro de luz por correlação com o fundo e máscara do relógio: **99 → 15 frames**, pessoa coberta 262 → 258 de 273 (ARQUITETURA 6.7) |
| 14 "pessoas" para 3 reais; nome não reconhecia depois | Todo rosto não casado virava pessoa (inclusive perfil, nuca, braço); mesmo nome criava gêmeos; só aprendia com ≥ 80 px | Filtro de rosto de frente + YOLO, junção por nome, absorção ao nomear, aprendizado por semelhança (ARQUITETURA 10.4, 10.9) |
| Programa caía logo após um evento (`buf.shape() == m.shape()`) | A varredura de rostos usava a mesma rede YOLO do laço ao vivo, em outra thread | Rede própria para threads de fundo e varreduras em fila (ARQUITETURA 10.9) |
| Terminal cheio de `[h264] error while decoding MB` | Câmera Back mandando blocos danificados (Wi-Fi), impressos pelo decodificador interno do OpenCV na varredura de rostos | Varredura lê pelo nosso ffmpeg em `-loglevel quiet`, 2× mais rápida; `tools/verificar_clipes.py` mede o dano (ARQUITETURA 10.11) |
| Foto do rosto ruim | Era o recorte de 112 px do reconhecedor, ampliado duas vezes | Recorte do frame original com cabelo e ombros, 300 px (ARQUITETURA 10.10) |
| Scripts dependiam da pasta atual | Caminhos relativos (`Path("clips")`) | `ROOT` no pacote; todo caminho parte da raiz (ARQUITETURA 3.2) |

## 5. Medições de referência

Guardadas porque conclusões mudam quando o formato muda.

| O que | Valor |
|---|---|
| Stream original da câmera | 579 KB / 10 s (463 kbps) |
| Pipeline antigo recodificado | 725 KB / 10 s, **pior qualidade** |
| Armazenamento hoje | ~48 KB/s, ~5 GB/ano com 5 min/dia de atividade |
| Inferência YOLO (dev) | 50–62 ms |
| Movimento após confirmação temporal | Front 8,7% → 1,5% dos frames |
| Rosto à noite | 44 px (desejável ~112 px) |
| Primeiro frame do ffmpeg | ~2,5 s |
| Laço da interface | mediana 19,9 ms, pior 88,8 ms |
| Varredura de rostos por clipe (M900) | 9 a 17 s, fora do caminho crítico |
| Rostos de dia no M900 | 36 a 80 px, a maioria abaixo de 60 |

## 6. Resolvido: M900 sem frames (29/09/2026)

**Sintoma:** no M900, `FALHOU - nenhum frame recebido`, painel "sem sinal",
nenhuma mensagem de erro do ffmpeg. O mesmo commit funcionava no dev.

**Causa:** as câmeras estão em `192.168.0.116` (Front) e `192.168.0.42`
(Back), e o `.env` do M900 apontava para `.10` e `.11`, onde nada responde. As
duas máquinas estão na **mesma rede**; `.10` e `.11` eram os valores de
exemplo do `.env.example`, que o `instalar.bat` copia para criar o `.env`. O
`.env` do dev, não versionado, tem os IPs certos. Sem timeout, o ffmpeg espera a conexão TCP
para sempre e **não escreve nada**. A única linha, mesmo em `-loglevel
verbose`, era `Starting connection attempt to 192.168.0.10 port 554`.

**Como foi achado, em ordem:**

1. `tools/diagnostico.py --local` deu 7776000 de 7776000 bytes: decode, pipe,
   binário e antivírus descartados de uma vez
2. Comando de captura à mão com log detalhado: zero frames **e zero
   segmentos**, então nem conectava. O log parava na tentativa de conexão
3. `Test-NetConnection` na porta 554 também falhava, e o ARP mostrava os dois
   IPs como `Unreachable`: não era o ffmpeg, não havia ninguém lá
4. Varredura da sub-rede pela porta 554 achou três hosts; dois com MAC
   `14-EB-B6` (TP-Link). As credenciais identificaram cada câmera: cada uma só
   aceita a própria Conta da Câmera e responde `401` às outras

**Lição:** o `probe_rtsp.py` que "passou" recebe o IP digitado à mão, então
não testava o `.env`. Numa máquina nova, **teste o IP do `.env` primeiro**.
Para não repetir, o `.env.example` agora traz o texto `ip-da-camera` no lugar
do IP, e o programa se recusa a iniciar enquanto ele estiver lá.

**Correção:** `-timeout` no RTSP (ARQUITETURA 5.7). Hoje um IP errado aparece
em ~6 s como "Tempo esgotado. Confira a rede e o IP da camera".

**Pendente do usuário:** reservar `.116` e `.42` por MAC no roteador do M900.

## 7. Limitações conhecidas e aceitas

- **Reconhecimento facial à noite é instável.** O infravermelho dá rostos de
  ~44 px. Detectar que há um rosto funciona; dizer de quem é, não. **O maior
  ganho possível não é de software: é uma luz acionada por movimento**, que tira
  a câmera do modo infravermelho.
- **Não identifica *qual* animal.** SFace é treinado só em faces humanas. Exigiria
  uma camada de re-ID sobre o corpo inteiro. A tela People já é a ferramenta que
  coletaria os recortes de treino.
- **Pessoa parada por ~12 s é suprimida** pela supressão de cenário estático, até
  se mexer de novo.
- **Sem retenção automática.** Gravações acumulam em `clips/`; o buffer em
  `clips/_buffer/` se limpa sozinho.
- **Texto da interface sem acentos.** `cv2.putText` usa fontes Hershey, que não
  têm glifos acentuados.
- **A interface precisa de sessão gráfica.** Não roda como serviço invisível.

## 8. Próximos passos planejados

1. **Medir o M900 rodando** — CPU com as duas câmeras, e se `HWACCEL` ajuda
   (INSTALACAO seção 6)
2. **Retenção automática** — o único lever grande que resta para disco
3. **Tracking** — manter identidade entre frames; resolve a pessoa parada e faz
   um clipe corresponder a uma pessoa
4. **Banco de eventos** (SQLite) no lugar dos JSON, quando houver busca
5. **Reprodução no Records** — clicar num cartão e assistir
6. **Persistir os spots estáticos** — hoje a lista nasce vazia a cada execução
7. **Desfazer junção na tela People** — hoje um nome dado ao cartão errado só
   se corrige com `tools/refazer_rostos.py`
8. **OpenVINO no M900** — o `cv2.dnn` aceita esse backend, e era o plano para
   recuperar a velocidade perdida ao sair do PyTorch

## 9. Mapa do repositório

```
src/jarvis/
  __init__.py     ROOT, a raiz do projeto
  cameras.py      aplicação principal: laço, exibição, orquestração
  capture.py      ffmpeg por câmera: segmentos originais + frames de análise
  motion.py       camada 1: MOG2 + confirmação temporal
  people.py       camada 2: YOLO via cv2.dnn, pessoas e animais
  clips.py        camada 3: eventos, montagem sem perda, metadados
  faces.py        camada 4: YuNet + SFace, galeria, cadastro de nome
  ui.py           menu lateral e as três telas
  geometry.py     tipo Detection e utilitários de caixas
tools/
  diagnostico.py  diagnóstico de captura (variantes, e --local sem câmera)
  probe_rtsp.py   diagnóstico de RTSP puro (DESCRIBE → SETUP → PLAY)
  refazer_rostos.py  reconstrói faces/ a partir dos clipes gravados
  verificar_clipes.py  conta blocos danificados por câmera num dia
  gerar_icone.py  desenha o ícone do olho robótico em assets/jarvis.ico
  criar_atalho.ps1   atalho com ícone na Área de Trabalho
assets/           jarvis.ico e prévia PNG (gerados, mas versionados)
docs/             ARQUITETURA, INSTALACAO, PYTHON e este arquivo
instalar.bat      instalação numa máquina nova
jarvis.bat        atalho para iniciar (uv run jarvis)
```

Estrutura explicada em ARQUITETURA seção 3.

Não versionados: `.env` (credenciais), `models/` (~95 MB, baixados sob demanda),
`clips/`, `faces/`.

## 10. Comandos úteis

```bat
jarvis.bat                                              iniciar
uv run jarvis                                           iniciar, sem o .bat
uv run tools/diagnostico.py Front                       testar variantes de captura
uv run tools/diagnostico.py --local                     testar ffmpeg sem câmera
uv run tools/probe_rtsp.py <ip> <user> <senha> stream1  testar RTSP puro
powershell Test-NetConnection <ip> -Port 554            a câmera responde nesse IP?
uv run tools/refazer_rostos.py                          refazer faces/ (feche o programa antes)
uv run tools/verificar_clipes.py [AAAA-MM-DD]           dano de imagem vindo das câmeras
tasklist | findstr ffmpeg                               procurar ffmpeg órfão
```

Constantes de ajuste: `capture.py` (`ANALYSIS_FPS`, `HWACCEL`,
`SEGMENT_SECONDS`), `people.py` (`MIN_INTERVAL`, `MIN_PERSON_HEIGHT_FRACTION`),
`motion.py` (`MIN_AREA`, `CONFIRM_FRAMES`, `LIGHTING_CORRELATION`), `faces.py`
(`MATCH_THRESHOLD`, `LEARN_THRESHOLD`, `IDENTITY_SCORE`, `MIN_VIEWS_FOR_NEW`).
