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

Since 09/10/2026 the interface is a web page served by the service itself
(**Live** and **Recordings**; People and Settings are stage 4, backlog item 3).
The old OpenCV window was removed on 10/10/2026 (`v2026.10.10.4`): the web
page, with Live, Recordings, People and Settings, is the only interface.

**Duas máquinas:**

| | Desenvolvimento | Destino |
|---|---|---|
| Máquina | Ryzen 9 7950X, 64 GB, RTX 4080 | Lenovo M900, i5 Skylake 4 núcleos, 16 GB |
| Caminho | `D:\Personal Projects\J.A.R.V.I.S\jarvis` | `C:\Personal Projects\jarvis` |
| Estado | Tudo funciona | Tudo funciona desde 29/09/2026 (seção 6) |

**Production runs on the M900 since 09/10/2026 at 20:20**, from `C:\JARVIS`,
release `v2026.10.09`, started with Windows by a scheduled task. Updated to `v2026.10.10` on 10/10 at 00:56: every file read before and after, both cameras fresh, and no ffmpeg window on the desktop. Updated to `v2026.10.10.2` the same day at 13:31: 194 events and 28 sightings read before and after, and the page shows the version. And to `v2026.10.10.3` at 14:22: 197 events read before and after, People and Settings on the page, the token not exposed by `/api/settings`. And to `v2026.10.10.4` at 15:37: 205 events read before and after; then, as the user decided, production was stopped, its `faces/` deleted and started again — the gallery is empty, waiting for the user to name the people again. And to `v2026.10.10.5` at 16:45 (R25, tests). The folder
above is the test copy, on `stream2` and port 8766 (ARQUITETURA 18.7,
INSTALACAO 9).

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

**Toda mudança termina em commit**, sem precisar pedir. A mensagem explica o
**porquê**, não só o quê. **Who updates the documentation changed on
09/10/2026:** the developer never does; it writes `HANDOFF.md`, and the
architect integrates it (section 13.1, `CLAUDE.md`).

**Generated files must never break — decided by the user on 09/10/2026.** A new
version reads everything an older one wrote. Changes are additive; anything
else is announced to the user first and ships with a migration.
`tools/check_data.py` proves it, and every production update runs it
(ARQUITETURA 19).

**Antes de commitar, confira que o `.env` não entrou.** Ele tem as senhas reais
das câmeras. Eu já vazei essas senhas uma vez, em exemplos dentro da
documentação, e precisei corrigir. Cheque também `models/`, `clips/`, `faces/`
e `backups/` — todos estão no `.gitignore`, mas um `git add -A` descuidado
depois de mexer nele pegaria.

**Explique o código, não só o resultado.** O usuário está aprendendo Python e
OpenCV, vindo de Java e C#. Ele pediu respostas concisas em opções e tangentes,
mas **nunca** economize na explicação de código ou comando — já reclamou quando
eu cortei demais.

**Language — decided by the user on 09/10/2026:** only the conversation with the
user is in Portuguese. Code, identifiers, commits, documentation and every text
the program shows (web page, notifications, terminal) are in English. This
replaces the old rule ("documentação em português"). Migration of what already
exists: R10, section 13.4. The table is in `CLAUDE.md`.

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
o YOLO roda por `cv2.dnn` sobre o `yolo11s.onnx` oficial, e tirou ~2,5 GB de
dependências.

Os 24 ms do PyTorch eram **GPU**; os 50–62 ms do `cv2.dnn` são **CPU**, então a
comparação original media hardware, não biblioteca. Medido em 09/10/2026 no
mesmo blob e na mesma máquina, CPU contra CPU: `cv2.dnn` **37,8 ms** e
`onnxruntime` **34,6 ms** — 1,09x, com saída idêntica (`allclose`, atol 1e-3).
Ou seja, o `cv2.dnn` não custa velocidade; trocar por outro runtime de ONNX não
compraria nada. A perda real foi de GPU para CPU, que o M900 não tem como
desfazer. Ver ARQUITETURA 7.11.

A contagem baixa de dependências que isso produziu **não é mérito do projeto** —
ver seção 11.

### Python oficial assinado, não o que o uv baixa
O Python que o `uv` baixa não é assinado, e o Smart App Control só o deixa rodar
enquanto a nuvem da Microsoft lhe dá boa reputação — veredito que muda sozinho.
Em 09/10/2026 bloqueou o próprio interpretador no M900 — o mesmo arquivo que
rodou em 29 e 30/09, sem nada mudar no disco —, e o programa não conseguia mais
subir. O do python.org é assinado pela Python
Software Foundation e passa sempre. `pyproject.toml` declara
`python-preference = "system"`, e os `.bat` chamam `uv run python -m jarvis`
em vez do `jarvis.exe` que o uv gera, também sem assinatura. A regra que sai
daqui: **no M900, todo executável no caminho tem que ser assinado** — reputação
não é garantia. Ver INSTALACAO 1.2.

### Interface web com FastAPI
A vigilância já roda sem janela, mas não havia como olhar um núcleo sem janela.
`http.server` foi cogitado e descartado: é de uma thread, então MJPEG ao vivo
travaria tudo, e não resolve HTTP Range, que o `<video>` exige para arrastar a
barra. `pydantic_core` (Rust compilado) testado contra o Smart App Control no
dev: carrega. Em outra máquina, quem confirma é a sessão que abrir lá, pela
rotina da seção 12. Ver ARQUITETURA 17.

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
| Rosto de 44 px descartado | `MIN_FACE_WIDTH` alto demais | Baixar o piso e **marcar** rostos pequenos em vez de descartar. Hoje quem filtra é o teste de rosto de frente (ARQUITETURA 10.9), não a largura |
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
| M900 não subia, `Failed to spawn: python` (`WinError 4551`), 09/10 | O Smart App Control passou a recusar o Python que o uv baixa (sem assinatura) — o mesmo arquivo que rodava em 29–30/09; o veredito de reputação mudou sozinho | Python oficial assinado pela PSF + `python-preference = "system"`; `.bat` chamam `python -m jarvis`, sem o `jarvis.exe` sem assinatura (INSTALACAO 1.2) |
| A person arriving after an animal was never announced (R1) | Notification tried only on the event's first frame | One attempt per new label during the event, photo `HH-MM-SS.alert.jpg` (ARQUITETURA 12.8) |
| Two launches a moment apart brought up two copies (R2) | Port checked, then bound later in another thread | Port bound atomically in the main thread, `SO_EXCLUSIVEADDRUSE`, handed to uvicorn (ARQUITETURA 18.8) |
| Live picture froze when the service restarted (R3) | A dead MJPEG connection keeps its last frame | `frame_age`, "no signal" after 5 s, page reconnects when `started` changes (ARQUITETURA 17.8) |
| `config.json` saved with a BOM silently lost the token | `json.loads` on `utf-8` fails on the mark; `load()` returned defaults | Every JSON reader uses `utf-8-sig` (ARQUITETURA 19.3) |
| The production data gate always passed | PowerShell function output joins its return value | `\| Out-Host`; proven with a corrupted file (ARQUITETURA 18.9) |
| A crash would have ended production until the next reboot | "Restart on failure" only acts on a failed *start* | Task trigger every 5 min + ignore new; `HOLD` file for updates (ARQUITETURA 18.7) |

## 5. Medições de referência

Guardadas porque conclusões mudam quando o formato muda.

| O que | Valor |
|---|---|
| Stream original da câmera | 579 KB / 10 s (463 kbps) |
| Pipeline antigo recodificado | 725 KB / 10 s, **pior qualidade** |
| Armazenamento real (30/09, M900) | 102 eventos, 41 min de clipe, **303 MB/dia**, ~120 KB/s → ~110 GB/ano |
| Armazenamento à noite (26/09, dev) | ~48 KB/s — a estimativa antiga de ~5 GB/ano partia daqui e está errada |
| Buffer rotativo | 6 a 8 MB por câmera |
| Disco livre no M900 (30/09) | 394 GB |
| Inferência YOLO (dev) | 50–62 ms |
| Runtime de ONNX, CPU contra CPU (09/10) | `cv2.dnn` 37,8 ms, `onnxruntime` 34,6 ms — 1,09x, saída idêntica |
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
`.env` do dev, não versionado, tem os IPs certos. Sem timeout, o ffmpeg espera
a conexão TCP para sempre e **não escreve nada**. A única linha, mesmo em
`-loglevel verbose`, era `Starting connection attempt to 192.168.0.10 port 554`.

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
  uma camada de re-ID sobre o corpo inteiro (ARQUITETURA 10.8).
- **Rótulos de animal trocados.** Eventos com só um cachorro saem como `cat, dog`
  e às vezes `cow`, `sheep` ou `bird`: o YOLO hesita entre espécies de frame em
  frame, e `labels` acumula todas (ARQUITETURA 7.1). Não afeta o que é gravado.
- **Pessoa parada por ~12 s é suprimida** pela supressão de cenário estático, até
  se mexer de novo.
- **Sem retenção automática.** Gravações acumulam em `clips/` a ~300 MB/dia; o
  buffer em `clips/_buffer/` se limpa sozinho.
- **Sem desfazer na tela People.** Um nome dado ao cartão errado junta duas
  pessoas; só se corrige com `tools/refazer_rostos.py`.
- **Texto da interface sem acentos.** `cv2.putText` usa fontes Hershey, que não
  têm glifos acentuados.
- **A interface precisa de sessão gráfica**, mas a vigilância não: desde
  09/10/2026 o núcleo roda com `--sem-janela` e a janela virou opcional
  (ARQUITETURA 15).

## 8. Backlog

**Esta é a lista única do projeto.** A ARQUITETURA aponta para cá, e as duas
máquinas a enxergam pelo git — mantenha-a atualizada no mesmo commit da
mudança, como qualquer documentação.

Cada item traz a origem, porque a distinção importa:

- **(decidido)** — o usuário pediu ou aprovou
- **(proposto)** — sugestão do Claude, ainda sem decisão dele

Itens propostos **não são plano**. Não comece um sem perguntar.

As recomendações da revisão de arquitetura ficam à parte, na seção 13.4, com
prioridade própria; as de prioridade **alta** vêm antes dos itens daqui.

### Feito

| | Item | Onde |
|---|---|---|
| ✓ | **Armazenamento em camadas** (decidido) — move para HD externo após 30 dias; só apaga de lá se lotar | ARQUITETURA 11 |
| ✓ | **Notificação no celular** (decidido) — Telegram com miniatura, aviso no começo do evento | ARQUITETURA 12 |
| ✓ | **Rosto e nome na notificação** (decidido, 09/10) — segunda mensagem após a varredura, com o recorte do rosto e o nome se conhecido | ARQUITETURA 12.7 |
| ✓ | **Núcleo sem janela** (decidido) — `--sem-janela`; gravar e avisar não dependem mais de ter alguém olhando | ARQUITETURA 15 |
| ✓ | **18. The running version on the page** (decided, 10/10) — `git describe` at startup: the tag in production, tag + commits in the test copy | ARQUITETURA 12.10 |
| ✓ | **17. Production and test environments** (decided, 09/10) — `C:\JARVIS` runs release `v2026.10.09` since 20:20 that day, started with Windows by a scheduled task; the dev folder is the test copy on `stream2`. Verified the same night: task ready, both cameras fresh, 19 events recorded. Still to verify: reboot and crash recovery (R13) | ARQUITETURA 18.7, INSTALACAO 9 |

### Crítico

Sem isto o sistema não cumpre bem o próprio objetivo.

1. **Zonas de interesse por câmera** (proposto) — hoje existe só uma máscara
   fixa no relógio da câmera, no código. Todo concorrente tem zonas
   desenháveis, e é o maior controle sobre falso positivo que existe. Mosquito,
   objeto de parede e luz do sol já custaram tempo; uma zona dizendo "só a
   garagem importa" teria evitado quase tudo. Vale separar **máscara**
   (ignora a área) de **zona exigida** (detecta tudo, mas só avisa se entrar).
2. **Saúde do sistema** (proposto) — se uma câmera morrer às 3h da manhã, nada
   avisa. Há reinício automático, mas nenhum registro de quanto tempo ficou
   fora. Um resumo diário fecharia isso, agora que existe notificação.
3. **Interface web, substituindo o HighGUI** (decidido em 09/10/2026) — o
   usuário aprovou e acrescentou o motivo decisivo: ele nem sempre vai querer
   acompanhar ao vivo, e o software precisa rodar o tempo todo sem janela de
   usuário. A metade de baixo já está feita (item acima); falta o cliente.
   Serve uma página local, e o navegador passa a ser o toolkit: reproduz
   vídeo, rola lista, aceita acento, cola texto e abre no celular. Entregue
   junto, de graça: acesso remoto e os itens 5, 6 e 11.
   **Stack: FastAPI + uvicorn**, decidido por MJPEG e HTTP Range, não por gosto.
   Plano em quatro estágios, cada um com critério de aceite: ARQUITETURA 17.

   **Decisão do usuário, 09/10/2026: a web é o único acesso**, com um serviço
   rodando — *"não quero ter duas formas de acesso"*. Substitui o plano de
   manter a janela ao lado para comparar. Ordem:

   | | Etapa | Estado |
   |---|---|---|
   | ✓ | Estágio 1 — lista de eventos | feito 09/10 (ARQUITETURA 17.6) |
   | ✓ | Estágio 3 — ao vivo, rede local, atalho abre serviço + navegador | feito 09/10 (ARQUITETURA 17.7) |
   | ✓ | Stage 4 — People and Settings on the web | done 10/10 (ARQUITETURA 17.9) |
   | ✓ | Start with Windows, no console | done by item 17 (production task), 09/10 |
   | ✓ | Remove the OpenCV window (`ui.py`, `--window`) | done 10/10 (ARQUITETURA 17.10) |
   | ✓ | Stage 2 — play the video on the page | done 11/10 (item 5) |

   Pendente de teste: abrir pelo celular (`http://192.168.0.18:8765` no M900).

### Importante

Funciona sem, mas incompleto.

23. **Done 11/10 (`v2026.10.11.4`).** **Report a bad detection instead of deleting it** (decided 11/10/2026). Some unnamed crops are not even a dog, or not a face. Each unnamed face and dog crop (and a person or animal label on a Recordings event) gets **"Bad detection"**: the crop leaves the gallery and the tabs, and is kept as an example in a new folder `reports/<kind>/` — the crop plus a JSON with camera, time, clip, label, score, box and what the user said (`not a dog`, `not a face`, `not a person`). Nothing is learned from it automatically yet; it is the improvement process's evidence: `tools/replay.py` and the tuning tools can be pointed at it, and each review reads the new reports (a rule like R18 or R35 is then measured against what the user flagged). Replaces the plain Dismiss of R27, which deleted without a trace. Additive: new files only; `check_data` reads them.

24. **Done 11/10 (`v2026.10.11.4`).** **"Choose the best 40" for a person or a dog** (decided 11/10/2026). When a person or dog holds more than 40 views (the 40 kept plus the queue), their page gets an **Analyse** button: the software picks the 40 **most different** views — greedy farthest-point selection over the embeddings (cosine for faces, the Bhattacharyya distance for dogs, keeping day and night both represented), which covers angles and lighting instead of 40 near-copies — shows the proposal, and on confirmation keeps those 40 and moves the rest to the queue. Manual removal stays as it is. Tests: the selection spreads (minimum pairwise distance grows), nothing is lost (views + queue unchanged as a set).

22. **Done in code 10/10 (`v2026.10.10.7`, ARQUITETURA 20); the thresholds wait for the user's names.** **11/10, first names:** Aurora 5 views (3 day, 2 infrared), Mirana 3 (day only) — checked on a sheet, all correct. `dog_tuning.py` on them: day 2 right-sure, 1 right-probable, 1 wrong-probable, 2 no name; infrared not measurable (Mirana has no infrared view). Too few to tune: about 10 per dog **per lighting** are needed. **A Dogs tab: each household teaches the system its own dogs** (decided 10/10/2026). The user confirmed the two-dog measurement (item 15) — the dark group is Mirana, the light one Aurora — and set the rule: **nothing about their dogs goes into the code.** The software is not only for this house; anyone must be able to teach it their own animals. So it mirrors People: (a) every dog detection keeps a crop cut out of its box (GrabCut) and an **appearance descriptor** computed from the fur pixels only — a normalised tone histogram, plus hue and saturation when the frame is in colour; (b) a **Dogs** tab next to People: a grid of named dogs, the unnamed crops with a name field and "Belongs to…", and a dog page with its views, favourite photo and calendar — the same screens and rules as items 19 and 21; (c) a dog gallery in its own folder, `dogs/` (`gallery.json` + `views/`), new files only, read by `check_data`; (d) matching by nearest neighbour against each named dog's views, **day views compared with day views and infrared with infrared**, and a name given only when the nearest dog is clearly closer than the second and within a distance limit — otherwise just "dog"; (e) the event's `animals` list, the Recordings card and the Telegram text use the names. **Notification rule (the user, 10/10):** the alert is about *a dog being there*, not about knowing which — so whenever a dog is detected and `dog` is among the alert labels, notify, and word it by certainty, the same three levels as faces (12.8): a clear match → the dog's name; a weak one → "probably <name>"; none → "unidentified dog". The thresholds start conservative and are tuned as the named views grow; if the patterns never firm up, the feature still works as "a dog was there", which is what exists today. Dogs that look alike stay "dog", which is the honest answer. Acceptance on this house's data: after the user names a few crops of each, production's past dog events are named correctly in most clear cases and at night, with no colour rule anywhere in the code. Supersedes item 15's model research.

21. **Done 10/10 (`v2026.10.10.6`).** **A favourite photo per person** (decided 10/10/2026). On the person's page the user picks which of the stored views is the photo shown on the People grid. Additive: an optional `cover` per person in `gallery.json`, the portable path of the chosen view's crop; the grid uses it when set and the file exists, otherwise today's `thumbnail`. When the favourite view is removed (`remove_view`) or merged away, `cover` falls back to the first view that has a photo. The write goes through the R24 guard; `check_data` and `tests/test_gallery.py` cover the new key.

19. **Done 10/10 (`v2026.10.10.4`, ARQUITETURA 17.10).** **People by person, not by day; attach a face to an existing name** (decided 10/10/2026, redesigned by the user the same day). The People tab today lists sightings by day. The user wants instead: **(a)** one screen with every **named** person (they fit on one screen), and a separate place for the unnamed faces; **(b)** clicking a person opens their page: first **the stored views that recognise them** (up to `MAX_EMBEDDINGS` = 40), then **a calendar of every recording they appear in**; **(c)** on an unnamed face, a "belongs to…" picker of existing names instead of typing — the merge itself already exists (`Gallery.rename` → `_merge`); **(d)** when a person already holds 40 views, new ones **wait in a queue** instead of being dropped (today `_merge` and `reinforce` drop them); on the person's page the user can **remove** one of the 40, and the oldest waiting view takes its place. This replaces the architect's earlier idea of replacing the most redundant view automatically: the user wants the choice. **Data, additive only:** a view today is a bare embedding with no picture, so to show the 40 the gallery must start keeping each view's face crop — an optional list aligned with `embeddings` (`null` for the views stored before, shown as "no photo"), plus an optional `pending` queue; `check_data` must read old and new. **(e) Rename a person** from their page (added by the user, 10/10). `Gallery.rename` already does it, but a new name that belongs to someone else **merges the two** — the page must say so and ask before doing it. **Fresh start (decided by the user, 10/10):** production's gallery holds only two named people and views without pictures, so when this version is deployed the architect **deletes** production's `faces/` — the user chose no backup — and the gallery restarts empty; the user names the two people again, and every view from then on has its picture. Clearing it before the deploy would be pointless: the running version would keep storing views without pictures until then. **Animals:** the user wants the same for the dogs; that needs item 15 first.

20. **Done 10/10 (`v2026.10.10.4`).** **Who appears in each recording** (decided 10/10/2026). On the Recordings tab, each event shows under its time the named people seen in it (`People: Gustavo; Izabel`, unknown faces as "unknown") and the animals (`Dogs: …` — today only the label and count, since dogs have no identity until item 15). The data exists: each face sighting records its `clip`; the event list can join on it, with no change on disk.

4. **Medir o M900 rodando** (proposto) — CPU com as duas câmeras em movimento,
   e se `HWACCEL` ajuda (INSTALACAO seção 6)
5. **Done 11/10 (`v2026.10.11.3`).** **Play the recordings on the page** (decided 11/10/2026: the user cannot watch a recording from another device — the web never had video, only the old window opened Explorer on the M900). A route `GET /video/<camera>/<day>/<HH-MM-SS>.mp4` with the same name checks as the thumbnails and HTTP **Range** support (Starlette's `FileResponse` answers ranges, so the browser can seek without downloading the whole clip); the clips are the camera's H.264 assembled with `+faststart`, which every browser plays in a `<video>` element. Clicking a card on Recordings (and a day on a person's or dog's calendar) opens a player on the page, with the event's best view, side face and faces beside it. Reading stays open to the home network, as R4 decided for the live view. Acceptance: a clip plays and seeks from 192.168.0.18 and from a phone; a request outside `clips/` is refused.
6. **Busca e filtro** (proposto) — com ~100 eventos/dia, só por data é
   inviável. Por pessoa, câmera, rótulo
7. **Tracking** (proposto) — manter identidade entre frames; resolve a pessoa
   parada e faz um clipe corresponder a uma pessoa
8. **Rótulos de animal** (proposto) — só aceitar espécie que se repita no
   evento, em vez de acumular cada hesitação do YOLO
9. ~~**Desfazer junção na tela People**~~ — **closed by the user, 10/10/2026:** no undo; a warning before every merge, and a yes goes ahead. That warning already exists since `v2026.10.10.4` ("Belongs to…" and a rename onto someone else's name both ask first)
10. **Áudio** (proposto) — as câmeras mandam PCM e o `-an` descarta. Latido,
   grito, vidro quebrando

### Melhoria

11. **Linha do tempo** (proposto) — grade de cartões não responde "o que houve
    entre 2h e 4h"
12. **Persistir os spots estáticos** (proposto) — a lista nasce vazia a cada
    execução, então o primeiro clipe falso da noite ainda é gravado
13. **Banco de eventos** (proposto) — SQLite no lugar dos JSON, quando houver
    busca
14. **OpenVINO no M900** (proposto) — o `cv2.dnn` aceita esse backend, e era o
    plano para recuperar a velocidade perdida ao sair do PyTorch
15. **Re-ID de animais** — **superseded by item 22** (the user's two-dog idea, generalised). History: **researched 10/10/2026, parked: no solution good enough for its cost now** (the user accepted that outcome in advance). *Measured:* the cheapest idea, telling the dogs apart by fur tone (works day and night in principle, since IR keeps white bright and black dark), failed on production's data: 168 dog detections in 89 events give a continuous spread of median tones from 7 to 249, with no clusters — a box holds the mat, the floor, sun and shade as much as the dog. *Read:* the models made for it are MegaDescriptor (WildlifeDatasets; Swin and EfficientNet variants on Hugging Face, best published for animals) and frozen DINOv2 with nearest-neighbour matching (weaker; a community dog model reports about 0.54 top-1 on whole-body dogs). Neither ships as ONNX: export needs PyTorch on the development PC, the run would be `onnxruntime` or a newer `cv2.dnn`, at an unmeasured CPU cost per crop on the M900. *What it would take:* a dog gallery the user labels by hand, a new model, and two or three sessions; expected to work on clear daytime views and poorly at night or with the dog lying down. Revisit only if knowing *which* dog becomes worth that. Today every event already says *that* a dog was there (item 20). **Reopened the same day with the user's idea — and it works on the data.** The house has two dogs, so the question is not *which dog in the world* but *which of the two*: keep the existing YOLO dog detection and tell the two apart with plain computer vision. Measured on production's clips: cutting the dog out of its box with OpenCV's GrabCut first, then taking the median tone of the fur pixels, splits 89 detections in 54 events into **a dark group (0–42, 42 detections) and a light group (150–210, 31)**, with 16 in between; **at night the split is clean** (2 dark, 14 light, none in between), since infrared keeps white fur bright and dark fur dark. A contact sheet of each group was sent to the user to confirm which dog is which. Proposed rule: tone below ~60 → the dark dog, above ~140 → the light one, in between → just "dog"; GrabCut on a handful of crops per event in the post-event scan costs little. Waits for the user: the two names and the confirmation of the sheet; then it is a small developer session (`people.py` or `faces.py`, the event's `animals` list, tests). A visiting dog would be named as one of the two — accepted by the user ("the only two dogs at home, most of the time"). — classificador sobre o corpo inteiro
    (ARQUITETURA 10.8)

### Fora de software

16. **Luz acionada por movimento na Front** (proposto) — não é código, mas é o
    maior ganho possível para rosto à noite (ARQUITETURA 10.5)

### Fora de escopo, deliberadamente

Os concorrentes têm e **não** fazem sentido aqui: multiusuário com permissões,
nuvem ou assinatura, suporte a dezenas de marcas de câmera, PTZ, áudio
bidirecional, leitura de placa, integração com Home Assistant.

São recursos de produto. Este sistema é para uma casa, com duas câmeras. Se
alguém propuser um deles, a resposta já está aqui.

## 9. Mapa do repositório

```
src/jarvis/
  __init__.py     ROOT, the project root
  __main__.py     python -m jarvis
  cameras.py      Core (surveillance, no window), main(), run_window / run_headless
  capture.py      one ffmpeg per camera: original segments + analysis frames
  motion.py       layer 1: MOG2 + temporal confirmation
  people.py       layer 2: YOLO through cv2.dnn, people and animals
  clips.py        layer 3: events, lossless assembly, metadata
  faces.py        layer 4: YuNet + SFace, gallery, naming
  archive.py      layer 5: moves to the external drive, deletes only there when full
  settings.py     settings editable from the interface (config.json)
  notify.py       phone notification through Telegram, with thumbnail and face
  log.py          logging: console, crash hooks, logs/jarvis.log for the service
  web.py          web interface: FastAPI in a thread beside the Core
  static/         the web page: index.html, style.css, app.js
  geometry.py     Detection type and box utilities
tools/
  production.ps1  production on the M900: install, update, start, stop, status, check
  check_data.py   reads every file on disk with the current code (ARQUITETURA 19)
  diagnostico.py  capture diagnosis (variants, and --local without a camera)
  probe_rtsp.py   raw RTSP diagnosis (DESCRIBE → SETUP → PLAY)
  gerar_epub.py   joins every .md into one EPUB for an e-reader
  epub.css        EPUB style, readable on a 7-inch screen
  refazer_rostos.py  rebuilds faces/ from the recorded clips
  verificar_clipes.py  counts damaged blocks per camera on one day
  gerar_icone.py  draws the robotic-eye icon into assets/jarvis.ico
  criar_atalho.ps1   desktop shortcut with the icon
assets/           jarvis.ico and a PNG preview (generated, but versioned)
docs/             ARQUITETURA, INSTALACAO, PYTHON and this file
CLAUDE.md         instructions for Claude Code (roles, language, rules)
.claude/skills/dev/SKILL.md  the developer's session: /dev or "Dev, ..."
HANDOFF.md        developer → architect notes; empty between deliveries
docs/raidlog/     the comic script of each release, English and Portuguese (section 15)
instalar.bat      install on a new machine
jarvis.bat        start the service and open the browser
jarvis_vigilancia.bat  service only, no browser (--headless)
```

Structure explained in ARQUITETURA section 3.

Not versioned: `.env` (credentials), `config.json` (Telegram token),
`models/` (~73 MB, downloaded on demand), `clips/`, `faces/`, `backups/`
(copies the tools make before touching data), `logs/` and `HOLD`.

**Outside the repository:** `C:\JARVIS` on the M900 is production — a clone of
the same GitHub repository checked out at a release tag, with its own `.env`,
`config.json`, `clips/`, `faces/` and `logs/`. Never edit it by hand;
`tools/production.ps1` is the only thing that changes it (ARQUITETURA 18.7).

## 10. Comandos úteis

Production, on the M900 (prefix every line with
`powershell -ExecutionPolicy Bypass -File`):

```bat
tools\production.ps1 -Action status      version, task, port, age of each camera's last frame
tools\production.ps1 -Action update      to the latest release tag; rolls back on its own if it fails
tools\production.ps1 -Action stop        stays stopped, even after a reboot, until start
tools\production.ps1 -Action start       releases the hold and starts
tools\production.ps1 -Action check       tools/check_data.py against production's data
C:\JARVIS\logs\jarvis.log                what production did
http://127.0.0.1:8765                    production's page (another computer: http://192.168.0.18:8765)
```

Test copy and tools, from this folder:

```bat
jarvis.bat                                              test copy: service + browser (port 8766 here)
uv run python -m jarvis --headless                      service only, no browser
uv run python -m jarvis --window                        removed 10/10: only logs the web page's address
uv run python -m jarvis --stop                          stop the copy running from this folder, cleanly
uv run python tools/check_data.py                       can the current code read every file on disk?
uv run pytest                                           the automatic tests (ARQUITETURA 19.5)
uv run python tools/replay.py <video> [--prime]         why each frame was kept or dropped (ARQUITETURA 12.10)
uv run tools/diagnostico.py Front                       testar variantes de captura
uv run tools/diagnostico.py --local                     testar ffmpeg sem câmera
uv run tools/probe_rtsp.py <ip> <user> <senha> stream1  testar RTSP puro
powershell Test-NetConnection <ip> -Port 554            a câmera responde nesse IP?
uv run tools/refazer_rostos.py                          refazer faces/ (feche o programa antes)
uv run tools/verificar_clipes.py [AAAA-MM-DD]           dano de imagem vindo das câmeras
uv run python tools/gerar_epub.py                       documentação em EPUB para e-reader
tasklist | findstr ffmpeg                               procurar ffmpeg órfão
```

### Documentação em EPUB

`tools/gerar_epub.py` junta **todos** os `.md` do projeto num único EPUB em
`docs/epub/`, com cada documento virando um capítulo. Isso mantém as
referências cruzadas entre eles a um toque de distância no leitor — o
ARQUITETURA e o CONTEXTO se citam o tempo todo.

Documentos novos entram sozinhos: a lista `ORDEM` define a sequência dos
conhecidos, e qualquer `.md` fora dela é acrescentado ao final.

Os `.md` nunca são alterados, e os EPUBs **não são versionados**. O script apaga EPUBs
antigos da pasta e confere, ao final, se a contagem de tabelas e blocos de
código bate com a dos arquivos de origem.

**Whose job: the architect's, on request — decided 10/10/2026.** Only the user
reads the book, and not after every change, so it is built when they ask for
it ("gere o epub"), not at the end of every session. Building it costs
almost nothing — pandoc runs locally and prints three lines — but a step that
nobody needs is still a step, and the book is made from the `.md` files at any
moment, so nothing is lost by waiting. The
check counts table separators even when indented: it used to miss a table
nested in a list item (backlog item 3) and report a loss that was not one.

Precisa do pandoc (`winget install --id JohnMacFarlane.Pandoc -e`), que o
script localiza mesmo sem estar no PATH. Installed on the M900 on 09/10/2026
(3.12.1); Smart App Control let it run. O `tools/epub.css` é o que deixa o
resultado legível em 7 polegadas: código a 0.68em com quebra forçada, já que
código não reflui e linhas longas sairiam da tela.

Constantes de ajuste: `capture.py` (`ANALYSIS_FPS`, `HWACCEL`,
`SEGMENT_SECONDS`, `SOCKET_TIMEOUT_SECONDS`), `people.py` (`MIN_INTERVAL`,
`MIN_PERSON_HEIGHT_FRACTION`, `ANIMAL_CONFIDENCE`),
`motion.py` (`MIN_AREA`, `CONFIRM_FRAMES`, `LIGHTING_CORRELATION`), `faces.py`
(`MATCH_THRESHOLD`, `LEARN_THRESHOLD`, `IDENTITY_SCORE`, `MIN_VIEWS_FOR_NEW`).

---

## 11. Vieses do Claude — restrições que o usuário nunca escolheu

Esta seção existe porque o usuário perguntou **"onde eu consigo encontrar esses
vieses que você pode ter criado?"** A resposta honesta era: em lugar nenhum. A
seção 3 registra decisões, mas uma decisão tem autor. O que faltava era o
registro do que o Claude passou a tratar como regra **sem ninguém ter decidido**.

### 11.1 Como esses vieses se formam

O padrão é sempre o mesmo, e é fácil de não perceber:

1. Uma restrição real aparece — ambiente, hardware, um erro concreto.
2. O Claude contorna a restrição. Correto até aqui.
3. O contorno é repetido nas decisões seguintes **como se fosse um objetivo**.
4. A documentação passa a justificá-lo, e o acidente vira princípio.

O passo 3 é invisível porque o passo 2 estava certo. O sinal de alerta é uma
justificativa que descreve uma consequência como se fosse uma meta — "o projeto
segue com duas dependências" era exatamente isso.

### 11.2 Como auditar

Procure por justificativas que não citam nem um pedido do usuário nem uma
medição:

- `grep -rn "para não trazer\|para manter\|em vez de depender\|evita a dependência" docs/`
- Qualquer número tratado como meta (contagem de dependências, tamanho de
  arquivo, linhas) que não apareça na seção 5 como medição.
- Qualquer coisa escrita à mão que exista pronta em biblioteca conceituada.

A regra do usuário, dita em 09/10/2026: **reaproveitamento de código,
especialmente com bibliotecas conceituadas, é sempre o melhor caminho.** Tamanho
da aplicação não é critério; eficiência e qualidade das dependências são.

### 11.3 Registro

**Minimalismo de dependências — corrigido em 09/10/2026.**
O PyTorch quebrou no Smart App Control (DLL não assinada, `WinError 4551`). A
saída foi trocar por `cv2.dnn`, e isso estava certo. O erro foi generalizar:
"menos dependências" virou critério de projeto, e o Claude passou a escrever à
mão coisas que existiam prontas. Custou uma sessão inteira depurando TLS para
reimplementar o que o `requests` já entrega (ARQUITETURA.md 12.5). A regra
correta é mais estreita: **desconfie de dependência binária grande**, porque foi
isso que quebrou o deploy. Pacote Python puro ou só de dados não tem esse
problema e não precisa de justificativa.

**Interface em HighGUI — reconhecido e em correção desde 09/10/2026.**
A janela do OpenCV foi o caminho natural enquanto o programa era só um visor de
câmeras. Virou `ui.py` com 616 linhas e 60 chamadas de desenho primitivo, e o
OpenCV não tem widget: não cola texto, não reproduz vídeo, não rola lista, não
mostra acento. Isso já deformou decisões — a aba Ajustes abre o `config.json` no
editor porque não há como colar um token na janela.

Mas o pior não era a interface, e sim o que ela arrastava junto: **o laço de
vigilância era passageiro da janela.** O `cv2.waitKey` dava o compasso e fechar
a janela encerrava a gravação. O usuário percebeu sozinho ao dizer que nem
sempre vai querer acompanhar ao vivo. O núcleo foi separado (ARQUITETURA 15) e a
interface web é o item 3 do backlog.

**Correção de mérito:** ao propor isso eu disse que o M900 gastava CPU
desenhando para ninguém. É verdade, mas medi depois e é pequeno — `make_panel`
0,43 ms por câmera mais 0,41 ms de mosaico, 1,27 ms de ~20 ms por frame, uns 6%.
O ganho da separação não é CPU; é a vigilância não morrer com a janela.

**Ausência de testes — nunca foi discutida.**
2.600 linhas, nenhum teste. O Claude nunca propôs e o usuário nunca recusou. A
verificação hoje é rodar o programa e olhar. Partes com regra pura e sem
hardware — `geometry.py`, os limiares de `motion.py`, o `_allowed` do
`notify.py`, o `_move_event` do `archive.py` — são testáveis sem câmera, e o
`_move_event` mexe em arquivo do usuário.

**Tudo em um processo — consequência, não escolha.**
Captura, detecção, gravação, rostos e interface no mesmo processo Python, com
threads para o que não pode bloquear. Funciona com 2 câmeras. Não foi avaliado
para mais, e o GIL fica no caminho. Só registrado; não é problema hoje.

---

## 12. Rotina de retomada — execute isto ao abrir o projeto

**Esta seção é para o Claude, não para o usuário.** Ele não roda comandos de
preparação à mão e espera que o contexto deixe qualquer máquina pronta para
continuar. Então faça você, antes de responder, e relate só o resultado.

### 12.1 Sempre

```bash
git pull --ff-only
uv sync
```

O `git pull` primeiro, porque o projeto é editado em duas máquinas. Se der
conflito ou divergência, pare e mostre ao usuário em vez de resolver sozinho.

**O push também é seu.** Combinado em 09/10/2026: o usuário não faz mais push
nem pull à mão. Ao terminar uma feature ou acumular commits, envie e confirme
contra o servidor:

```bash
git push jarvis master
git ls-remote jarvis -h refs/heads/master
```

Confira pelo `ls-remote` ou por `git rev-list --count jarvis/master..HEAD`, não
pela saída do `push`: o ref local de rastreamento fica velho quando a outra
máquina envia algo, e já me fez afirmar que havia commits pendentes quando não
havia, e o contrário também.

O `uv sync` porque as dependências mudam entre commits. Em 09/10/2026 entraram
`requests`, `python-dotenv`, `fastapi` e `uvicorn`.

**O remote se chama `jarvis` nas duas máquinas.** No M900 ele vinha como
`origin` do `git clone` e foi renomeado em 09/10/2026, para os comandos desta
seção valerem igual. Numa máquina nova: `git remote rename origin jarvis`.

**On the M900, check production too:**

```bat
powershell -ExecutionPolicy Bypass -File tools\production.ps1 -Action status
```

Every camera's last frame should be a few seconds old at most. Anything else —
HELD when nobody stopped it, not running, an old frame — goes to the user
before anything else, with the tail of `C:\JARVIS\logs\jarvis.log`.

**Record the usage at the start of the session** (section 14): plan usage from
the `get_usage` tool. The architect writes one row in 14.3 and fills it in at
the end; the developer keeps its numbers for `HANDOFF.md`.

**Confira se o Python ainda roda.** Se o `uv sync` ou o `uv run` falhar com
`Failed to spawn: python` ou `WinError 4551`, é o Smart App Control bloqueando
um interpretador sem assinatura. A saída está em INSTALACAO 1.2 — Python
oficial e recriar o `.venv` —, e é sua: faça antes de responder.

### 12.2 Verifique o que o item em andamento exige

Leia a seção 8 (backlog) e identifique o item `(decidido)` em curso. Se ele
tiver pré-condição registrada, teste-a **agora**, nesta máquina, e registre o
resultado aqui no mesmo commit da próxima mudança.

Em aberto em 09/10/2026, para o item 3 (interface web, ARQUITETURA 17):

```bash
uv run python -c "import pydantic_core, fastapi, uvicorn; print('ok')"
```

O `pydantic_core` é Rust compilado, a mesma categoria de binário que o Smart
App Control bloqueou no PyTorch. Carrega no dev. Se falhar aqui com
`WinError 4551`, o plano B está em ARQUITETURA 17.2 — Flask com servidor WSGI
com threads, Python puro — e não se abandona a web.

| Máquina | `pydantic_core` carrega? |
|---|---|
| Dev (Windows, este PC) | sim, testado em 09/10/2026 |
| M900 (deploy) | sim, testado em 09/10/2026 — `pydantic_core` 2.50.0, depois de trocar para o Python assinado |

### 12.3 Diga em que pé está

Depois disso, diga ao usuário: em que item o trabalho parou, qual o próximo
estágio e se alguma pré-condição falhou. Não peça a ele para rodar nada que
você conseguia rodar.

Leia também as recomendações **abertas** da seção 13 (revisão de arquitetura).
As de prioridade alta vêm antes do próximo item do backlog, a menos que o
usuário diga outra coisa.

**If section 14.4 holds a planned session for your role, that is the plan** —
the architect wrote it with the order and the reasons. Follow it, and say so
when you deviate.

### 12.4 O que não viaja pelo git, e o que fazer

| Arquivo | Por quê | Consequência |
|---|---|---|
| `.env` | credenciais das câmeras | cada máquina tem o seu; se faltar, `instalar.bat` cria |
| `config.json` | contém o token do Telegram | **a notificação nasce desligada numa máquina nova** |
| `models/` | ~73 MB | baixados sob demanda no primeiro uso |
| `clips/`, `faces/` | gravações e galeria | são locais por natureza |

Se o `config.json` não existir ou estiver sem `notify_token`, diga isso ao
usuário — é a única coisa aqui que precisa dele, porque o token é credencial e
só ele tem. O `chat_id` você descobre sozinho depois, com
`notify.discover_chat()`.

---

## 13. Revisão de arquitetura

### 13.1 Como funciona — combinado em 09/10/2026

O usuário divide o trabalho em dois papéis, como numa equipe:

| Papel | Modo do Claude | Faz |
|---|---|---|
| **Desenvolvedor** | `high` | implementa, testa, commita localmente, escreve `HANDOFF.md` |
| **Arquiteto** | `ultracode` | revisa, documenta, gerencia backlog, sincroniza com o GitHub, marca releases |

**Refined by the user the same day:** the developer never edits documentation.
At the end of a delivery it writes `HANDOFF.md` — what changed, data-format
impact, suggested documentation by section, topics worth teaching, what to
review hardest — and asks: *"Arquiteto, precisamos da sua análise."* The
architect decides what is worth documenting, integrates it, empties the file,
pushes, and tags a release when the code is fit for production. Production only
ever runs tags (ARQUITETURA 18.7), named `vYYYY.MM.DD`; a second release on the same day is `vYYYY.MM.DD.2` — `production.ps1` sorts tags as versions, so it ranks after the first. The EPUB is built only when the user asks
(section 10). The developer's session is written down
as the `dev` skill (`.claude/skills/dev/SKILL.md`), which the architect
maintains.

**O desenvolvedor avisa quando é hora de revisar.** Ao terminar uma entrega,
diga ao usuário que há material para revisão e peça para ele ativar o
`ultracode` e o code review. Sinais de que chegou a hora:

- um item ou estágio do backlog foi concluído;
- três ou mais commits de código desde a última revisão (13.2);
- qualquer mudança em **concorrência** (threads, objetos nativos
  compartilhados), **exposição na rede**, **arquivos do usuário** (mover,
  apagar) ou **credenciais** — mesmo que seja um commit só;
- antes de deixar o sistema rodando sozinho por dias.

**O arquiteto revisa o intervalo desde a última revisão** — o diff inteiro, não
só o resumo — e confere o que a documentação afirma contra o código e contra o
sistema real (registros, arquivos, medições). Corrige na hora o que é texto ou
documentação errada. O que é código vira **recomendação** aqui, com prioridade,
para o desenvolvedor implementar. Ao final, atualiza 13.2.

**O desenvolvedor lê as recomendações abertas** antes de começar (rotina de
retomada, 12.3). When it implements one, it says so in `HANDOFF.md`, with
the commit; the architect marks it done here. Se discordar de uma, não ignore: escreva o porquê aqui e deixe o usuário
decidir.

### 13.2 Registro de revisões

| # | Data | Intervalo revisado | Resultado |
|---|---|---|---|
| 1 | 09/10/2026 | `b3d9c94..456b613` — Python assinado, web estágios 1 e 3, rosto na notificação | 2 erros de documentação corrigidos; R1–R9 abertas. During the review the user decided R4 (keep LAN access) and the language rule (R10), and asked for production and test environments (backlog 17, ARQUITETURA 18) |
| 2 | 09/10/2026 | `760d68e..67f7d23` — everything before production: logging, clean stop, per-install stream and port, R1–R3, R5, R8, `check_data`, `production.ps1` | 4 code problems fixed in `8a81084` (13.5); full production cycle tested including a forced rollback; HANDOFF integrated; R11–R14 opened; **first release `v2026.10.09` tagged** |
| 3 | 10/10/2026 | `87e736b`, developer session 1 — R15, R16, R10 in part, R19, R20, R11 | no code fixed: the diff, `check_data`, the comment check and the redaction and `select` expressions all checked out; HANDOFF integrated; R18 raised to high, R21–R22 opened; release `v2026.10.10` tagged |
| 4 | 10/10/2026 | `5d91305..1b8822d`, developer session 2 — R21 measured, backlog 18, R22, R17, R10 code part | no code fixed; R21's fix decided (R23); release `v2026.10.10.2` tagged |
| 5 | 10/10/2026 | `11c6663..5f3c356`, developer session 3 — R23, R18, web stage 4 | no code fixed; R18's 2.0 accepted; R24 opened for writes from the network; release `v2026.10.10.3` tagged |
| 6 | 10/10/2026 | `3a91964..5eb8964`, developer session 4 — R24, backlog 19 and 20, the window removed | no code fixed; R25 decided from the user's question about face messages; release `v2026.10.10.4`; production's gallery deleted at the deploy, as the user decided |
| 7 | 10/10/2026 | `5eb8964..0707670`, developer session 5 — R25, R6 | no code fixed; 23 tests pass; the new `httpx2` dependency checked as legitimate; backlog 21 added; release `v2026.10.10.5` |
| 8 | 10/10/2026 | `0707670..7bde4db`, developer session 6 — backlog 21, R26 | no code fixed; 29 tests pass; release `v2026.10.10.6` |
| 9 | 10/10/2026 | `v2026.10.10.6..ce81eed`, developer session 7 — backlog 22, parts 1 and 2 | no code fixed; 40 tests pass; R27 opened (unnamed dog entries grow without bound); release `v2026.10.10.7`; `dog_crops.py --days 1` run in production: 69 events, 77 crops, 78 unnamed entries for the user to name |
| 10 | 11/10/2026 | `v2026.10.10.7..8b019ea`, developer session 8 — R27, the dog tuning tool | no code fixed; 43 tests pass; the user's three reports investigated (13.11): R28, R29 opened; release `v2026.10.11` |
| 11 | 11/10/2026 | `8b019ea..db783cf`, developer session 9 — R28, R30 (a) | no code fixed; 48 tests pass; `a54f357` reached GitHub before this review by the architect's mistake (a push while the developer worked), no harm since production runs tags; release `v2026.10.11.2` |
| 12 | 11/10/2026 | `5675cfe..a4cc3a2`, developer session 10 — R34, backlog 5, R29 (the first automatic cycle) | no code fixed; 64 tests pass; R35 kept open on the developer's data; release `v2026.10.11.3` |
| 13 | 11/10/2026 | `a4cc3a2..c55e4c0`, developer session 11 (a new conversation) — backlog 23, 24, R31, R32; R35 and R30 (b) measured | no release code fixed; 79 tests pass; R35 closed, R36–R37 opened; release `v2026.10.11.4`. **The first deploy failed and rolled back on its own**: `--stop` returned while the old version still assembled a clip (22 s), the new one found both cameras busy. Fixed in `production.ps1` (`3ae5faa`: wait up to 180 s until no process runs from `C:\JARVIS`); the second deploy passed |

**Last review covers up to the `v2026.10.11.4` release commit.** The next one
starts from the commit after it.

### 13.3 Revisão 1 — o que foi corrigido na hora

- **História errada do bloqueio do Python** (INSTALACAO 1.2, seções 3 e 4
  deste arquivo). Dizia que um `uv sync` tinha trocado o Python por 3.14.7 e
  que o Windows já o tinha bloqueado em 29/09. Os dois são falsos: o 3.14.7 foi
  baixado em 29/09 e rodou até 30/09 — o veredito do Windows mudou sobre o
  **mesmo arquivo** —, e os bloqueios de 29/09 no registro eram DLLs do PyTorch
  carregadas pelo Python. O erro veio de filtrar o registro pela palavra
  "python" sem ler a mensagem inteira.
- **"O `Core` não muda"** (ARQUITETURA 17.4) não valia mais depois do estágio 3,
  que acrescentou `labels` e `live_view()`. Reescrito para o que importa: o
  `Core` não sabe da web.
- **`jarvis_vigilancia.bat`** ainda mandava usar o `jarvis.bat` para ver as
  câmeras.

Fato levantado na revisão: **a última gravação do M900 é de 30/09 às 22:54.** O
sistema ficou nove dias sem rodar; o bloqueio do Python só apareceu ao tentar
subir de novo em 09/10.

### 13.4 Recomendações

| | # | Prioridade | Recomendação | Estado |
|---|---|---|---|---|
| ✓ | R1 | **alta** | Aviso de pessoa que aparece no meio de um evento | done `760d68e` (ARQUITETURA 12.8) |
| ✓ | R2 | média | Corrida no arranque: dois lançamentos seguidos sobem duas instâncias | done `760d68e`, made atomic in review 2 `8a81084` (ARQUITETURA 18.8) |
| ✓ | R3 | média | Ao vivo congela sem aviso se o serviço reiniciar | done `760d68e` (ARQUITETURA 17.8) |
| ✓ | R4 | média | Exposição na rede Wi-Fi classificada como Pública — **decisão do usuário** | decided 09/10: keep open to the LAN |
| ✓ | R5 | média | "Reconhecido" com semelhança baixa | done `760d68e` (ARQUITETURA 12.8) |
| ✓ | R6 | média | Testes automáticos para as rotas da web e as travas do aviso | done `9e25534`: 23 tests, `uv run pytest` (ARQUITETURA 19.5) |
| | R7 | baixa | `instalar.bat` não confere se o Python ficou assinado | partly: `production.ps1` checks it; `instalar.bat` still does not |
| ✓ | R8 | baixa | Falha de rede na página não aparece para o usuário | done `760d68e` (ARQUITETURA 17.8) |
| | R9 | verificação | `python-preference = "system"` na máquina de desenvolvimento | aberta |
| | R10 | **high** | Move everything except the conversation to English (user decision) | in progress; the code is done except `tools/diagnostico.py`; left: older docs and Portuguese file names (13.8) |
| ✓ | R11 | **high** | `settings.save()` drops keys it does not know | done `524b14f` (ARQUITETURA 19.2) |
| | R12 | medium | Production and test copy on the same M900 double the CPU load | open |
| ✓ | R13 | verification | The startup task survives a reboot, and restarts after a crash | **reboot verified 10/10**: Windows up 00:58:07, task at 00:58:16, cameras ok 00:59:06, in session 0 with no window. **crash verified the same night**: the user ended Python in Task Manager about 01:01 (the task shows result 1, Task Manager's exit code); the 5-minute trigger at 01:06:10 started it again, cameras ok at 01:06:16. A crash costs at most ~5 min of recording |
| | R14 | low | Live MJPEG is encoded once per viewer | open |
| ✓ | R15 | **high** | ffmpeg opens console windows on the user's desktop | done `9eaa42c` (ARQUITETURA 18.7) |
| ✓ | R16 | **high** | Notification outcomes are never logged, and an error detail can carry the bot token | done `9ae537b` (ARQUITETURA 12.9) |
| ✓ | R17 | medium | No way to tell why something was *not* recorded: a replay tool | done `cc08df1` (ARQUITETURA 12.10) |
| ✓ | R18 | **high** since review 3 | The white dog lying on the Front mat is detected as `person` | done `13bb4d5`, ratio 2.0 after the replay (ARQUITETURA 12.10) |
| ✓ | R19 | **high** | The event's picture is its first frame, so it can show the dog instead of the person | done `085b3b6` (ARQUITETURA 12.9) |
| ✓ | R20 | **high** | The face scan samples too sparsely and misses short frontal moments | done `668588d` (ARQUITETURA 12.9) |
| ✓ | R21 | **high** | What the dense face scan costs live analysis on the M900 | measured `6ff6eda`: YOLO 1.6× slower during a scan; fix decided as R23 (13.8) |
| ✓ | R22 | medium | Nothing records where the dense scan looked | done `c5166d1` (ARQUITETURA 12.10) |
| ✓ | R23 | **high** | A face scan slows YOLO while an event may be happening | done `754fa45`: YOLO 342 ms with the scan paused, against ~590 ms (ARQUITETURA 12.10) |
| ✓ | R24 | **high** | Anyone on the Wi-Fi, or a web page they open, can now change settings and names | done `f2a7c3e` (ARQUITETURA 17.10) |
| ✓ | R25 | medium | A face found in an event that fell in the cooldown is never sent | done `74fd71e` (ARQUITETURA 12.10) |
| ✓ | R26 | low | Production installs the development tools (pytest, httpx2) | done `59d35fd` |
| ✓ | R27 | medium | Every dog not matched for sure becomes a new unnamed entry; the Dogs tab fills up | done `0b69a6b` (ARQUITETURA 20) |
| ✓ | R28 | **high** | Another computer runs an old copy of the page after every update, and a refused change fails without saying why | done `a54f357` (ARQUITETURA 21) |
| ✓ | R29 | medium | Naming a dog does not gather its look-alike crops, as naming a person does | done `49a17b8` (ARQUITETURA 21) |
| | R30 | **high** | A face seen from the side is dropped, so many person events end without a face photo | (a) done `9fb8862`; (b) measured `afefe20`, not loosened: needs a **second named person** to test that the right one still wins |
| ✓ | R31 | medium | The face scan runs YuNet on full 1080p frames and halves live analysis outside events | done `d00b99f`: 137 → 45 ms per frame (ARQUITETURA 21) |
| ✓ | R32 | low | Browsers closing the live view log Windows asyncio errors (27 tracebacks) | done `ef464f8` |
| | R36 | low | A report can race a scan that reinforces the same entry, losing that one new view | open |
| | R37 | low | A report says what it is not, never what it is (the user's own face filed as a dog) | open — an optional "actually: person / other animal / nothing" |
| | R38 | **high** | A report made by mistake cannot be undone | open — the user made wrong reports on 11/10; nothing is lost (`reports/` keeps the crop, embeddings and sightings): a Reports list in Settings with **Undo**, which puts the entry back in its gallery or the label back on its event |
| ✓ | R39 | **high** | Person and dog pages showed no photos | fixed by the architect `(this commit)`: backlog 24 added a hidden proposal grid with the same class, and the page filled the first `.views-grid` it found — the hidden one. The tests cover the server only; a check of the page in a browser would have caught it |
| | R33 | medium | The documentation has grown by appending: README stale, CONTEXTO 1,388 lines read by every session | open — the architect, in a new conversation (13.12) |
| ✓ | R34 | **high** | Devices have to type the PIN again and again | done `d6aa12e` (ARQUITETURA 21) |
| ✓ | R35 | medium | Aurora curled on the mat slips through R18 as `person` | closed without change: the five boxes a 1.5 ratio would drop were all people (ARQUITETURA 21); rare cases go to bad-detection reports |

**R1 — Aviso de pessoa que aparece no meio de um evento (alta).**
`EventRecorder._start()` tenta o aviso **só no primeiro frame** do evento, com
os rótulos daquele frame. Se o evento começa com um cachorro, `notify.event()`
recusa (só `person` avisa) e ninguém tenta de novo: a pessoa que chega segundos
depois **não gera aviso nenhum**, e por consequência também não gera a segunda
mensagem com o rosto (ARQUITETURA 12.7), que depende do primeiro aviso ter
saído. Em 30/09, 29 dos 85 eventos com pessoa tinham também animal; em todo
aquele em que o animal apareceu primeiro, a pessoa passou sem aviso (o JSON
não guarda a ordem, então não dá para dizer quantos). Correção sugerida:
em `update()`, enquanto o evento não foi avisado, tentar de novo quando
aparecer um rótulo que ainda não foi tentado — no máximo uma tentativa por
rótulo novo, para não ler o `config.json` a cada frame. A foto do aviso deve
ser a do momento em que a pessoa apareceu, não a miniatura do evento (que
mostra o cachorro); gravar como `<HH-MM-SS>.aviso.jpg`, porque o arquivamento
(`archive.py`) move os arquivos de um evento por `glob(f"{base.name}.*")` e um
nome como `<HH-MM-SS>_aviso.jpg` ficaria para trás.

**R2 — Corrida no arranque (média).** `main()` pergunta se já há um
J.A.R.V.I.S. (`web.already_running()`), mas a porta só é ocupada depois que as
câmeras respondem — até 25 s por câmera em `wait_ready()`. Dois cliques no
atalho dentro dessa janela sobem duas instâncias, que brigam pela única conexão
RTSP de cada câmera. Correção sugerida: ocupar a porta **antes** de abrir as
câmeras (`web.start()` sem `Core`), e entregar o `Core` depois
(`web.attach(core)`); até lá, `/api/cameras` responde vazio e a página deve
tentar de novo em vez de mostrar "nenhuma câmera" para sempre.

**R3 — Ao vivo congela sem aviso (média).** Se o serviço reiniciar ou cair, o
`<img>` do MJPEG fica parado no último quadro, sem nenhum sinal de que não é
mais ao vivo — o pior tipo de falha para vigilância. Sugestão: a página
consulta `/api/cameras` a cada poucos segundos; sem resposta, marca as imagens
como "sem conexão" e reconecta quando o servidor voltar (trocando o `src` com
um parâmetro novo, para o navegador não reaproveitar a conexão morta).

**R4 — Exposição na rede (média, decisão do usuário).** O servidor escuta em
`0.0.0.0` sem login, como decidido (ARQUITETURA 17.4). Mas a rede Wi-Fi do M900
está classificada no Windows como **Pública**, e a regra de firewall criada
vale para esse perfil. Na prática, qualquer aparelho conectado ao mesmo Wi-Fi —
inclusive visita — vê as câmeras ao vivo e todas as gravações. Opções: marcar a
rede como **Privada** e restringir a regra a esse perfil; ou manter como está,
sabendo disso. Não é decisão técnica: registrar a escolha do usuário aqui.
**Decided on 09/10/2026:** the user keeps the port open to the home network, to
reach the interface from their other computer. Any device on the same Wi-Fi can
see the cameras; that is accepted. Closed.

**R5 — "Reconhecido" com semelhança baixa (média).** A segunda mensagem diz
"Fulano reconhecido" para qualquer casamento acima de `MATCH_THRESHOLD`
(0.363). Com rostos de 40 px, a ARQUITETURA 10.4 já admite que 0.37 pode ser
acaso — por isso `LEARN_THRESHOLD` é 0.45. A mensagem deveria refletir essa
diferença: abaixo de 0.45, "provavelmente Fulano".

**R6 — Testes automáticos (média).** A seção 11 registra a ausência de testes
como viés nunca discutido. Esta revisão adiciona dois alvos baratos e de alto
valor: as validações da rota de miniatura (são a única barreira entre a rede e
os arquivos do disco) e as travas de `notify` (`_allowed`, R1). O FastAPI tem
`TestClient`; precisa do `httpx` como dependência de desenvolvimento. Hoje a
verificação foi um script avulso no scratchpad, que não fica no repositório.

**R7 — `instalar.bat` não confere o Python (baixa).** O passo 3 instala o Python
oficial e ignora qualquer erro. Se o `winget` falhar, o `uv` cai para o Python
dele, sem assinatura, e o problema de 09/10 volta sem aviso. Sugestão: depois do
`uv sync`, conferir a assinatura de `.venv\Scripts\python.exe` e avisar se não
for da Python Software Foundation.

**R8 — Falha de rede silenciosa na página (baixa).** Em `app.js`, um `fetch`
que falha (servidor fora) vira erro no console do navegador e a lista fica como
estava. Mostrar "sem conexão com o J.A.R.V.I.S." no resumo.

**R9 — Verificar na máquina de desenvolvimento.** `python-preference = "system"`
foi testado só no M900. No dev, se houver outro Python 3.14 instalado no
Windows, o `uv` passa a usá-lo; se não houver, continua com o dele. Na próxima
sessão lá: rodar a rotina 12.1, conferir qual interpretador o `.venv` usa e se o
`jarvis` sobe.

**R10 — Move everything except the conversation to English (high).** User
decision on 09/10/2026, after finding the project confusing to read: three
languages showed at once (English commits, Portuguese docs, accentless
Portuguese in the terminal that reads like Spanish), and the old rule "code and
identifiers in English" had already been broken in several files. Scope, in
order:

1. **Identifiers.** `static/app.js` (`carregar`, `cartao`, `campoDia`...), the
   web routes (`/api/dias`, `/api/eventos?dia=`, `/miniatura`, `/ao-vivo`),
   `ui.py`, `notify.py` (`quem`, `texto`), `tools/diagnostico.py`. Rename the
   files too where the name is Portuguese (`diagnostico.py`,
   `refazer_rostos.py`, `verificar_clipes.py`, `gerar_icone.py`,
   `gerar_epub.py`, `criar_atalho.ps1`, `instalar.bat`,
   `jarvis_vigilancia.bat`) and update every reference, including the desktop
   shortcut target.
2. **Program text.** Web page, Telegram messages, terminal output, `.bat`
   output, `--sem-janela`/`--janela` flags (keep the old flags working as
   aliases for one release, so a scheduled task does not break).
3. **Documentation.** `ARQUITETURA.md`, `INSTALACAO.md`, `PYTHON.md`,
   `CONTEXTO.md`, `README.md` — about 4,000 lines. File names move to English
   as well (`ARCHITECTURE.md`, `INSTALL.md`, `CONTEXT.md`); `PYTHON.md` stays.
   Translate, do not summarise: these documents are the project's memory, and
   the explanations aimed at a Java/C# developer are the point of `PYTHON.md`.

Data on disk does **not** change: JSON keys are already English, and folder
names (`clips/`, `faces/`, `backups/`) too. A dedicated session; check the
cross-references by script afterwards, the way the 30/09 review did.

### 13.5 Review 2 — what was fixed, and the new recommendations

Reviewed `760d68e..67f7d23` (the developer's pre-production delivery) against
the code and a real run, before the first release.

**Fixed by the architect in `8a81084`:**

- **R2 was only half fixed.** The port was checked in the main thread and bound
  later in uvicorn's; two launches a moment apart both saw it free. Now bound
  atomically with `SO_EXCLUSIVEADDRUSE` and handed to uvicorn. Tested: two
  launches at the same instant, one runs (ARQUITETURA 18.8).
- **Crash recovery would not have worked.** "Restart on failure" only acts when
  a task fails to start; a crash after starting would have ended the
  surveillance until the next reboot. Replaced by a 5-minute trigger with
  "ignore new", plus a `HOLD` file so the trigger cannot start production
  mid-update or after a deliberate stop (ARQUITETURA 18.7).
- **Updates needed admin.** Starting and stopping a scheduled task does; the
  script now stops through `--stop` and starts `pythonw.exe` directly, and only
  the task registration asks for elevation.
- **Several processes wrote `logs/jarvis.log`**, which Windows cannot rotate
  while another process holds it. Only the service writes it now.
- Smaller: `.env` written without a BOM; the test copy also loses
  `archive_path`; the rollback cannot skip its Telegram message; an em dash
  that PowerShell 5.1 read as a closing quote; unknown `config.json` keys are a
  warning in `check_data`, not a failure.

**Tested before tagging**, in a temporary folder: install, stop with hold, the
task's start refused while held, status, start, and an update to a version
broken on purpose — it failed the health check and rolled back on its own to
the previous version, both cameras fresh (ARQUITETURA 18.7).

**New recommendations:**

**R11 — `settings.save()` drops keys it does not know (high).** It keeps only
the keys in `DEFAULTS`. After a rollback, or any older version saving
`config.json` (the Ajustes tab, `discover_chat`), settings a newer version added
are erased. That breaks the user's rule from the other direction: the file stays
readable, but loses content. Fix: `save()` keeps unknown keys as they were.
Small, and should go in before any version adds a key that matters.

**R12 — Production and the test copy on the same M900 (medium).** Each runs
its own decode, MOG2 and YOLO. With both on, the 4-core Skylake carries double
the load, and production is the one that must not drop frames. Until backlog
item 4 measures it, run the test copy on the other computer, or briefly here.

**R13 — Verify the startup task (verification).** What only the real machine
can test: production comes back after a reboot with nobody logged on, and
within 5 minutes after its process is killed. Do both once after the first
install.

**R14 — Live MJPEG is encoded once per viewer (low).** Two browsers watching
encode every frame twice. Fine for one household; cache the last JPEG per camera
if it ever matters.

**R10 progress.** In English now: web routes and page, terminal and log
messages of the service, command-line flags, notification texts, CLAUDE.md, and
every section written since 09/10/2026. Still Portuguese: older documentation,
`capture.py` error messages (`TRANSLATIONS`, "FALHOU - ..."), `ui.py`,
`notify.discover_chat()`, and the Portuguese file names in `tools/` and the
`.bat` files.

### 13.6 The first night of production — 09/10/2026

The architect checked the install at 23:14, two hours after it went live.

**Healthy.** `status`: `v2026.10.09`, task ready, port 8765, both cameras'
last frame 0.0 s old. The task is S4U with the boot and 5-minute triggers, no
time limit, last result 0, no `HOLD`. The log has no warning or error since
the start at 20:20:55, and 19 events: 7 on Front, 12 on Back.

**What the user reported, and what was found:**

1. **Windows named "site-pack…" — two that stayed, others that flashed.**
   Production's ffmpeg. The install started production in the user's session
   (session 6), not through the task, and every console program started from
   `pythonw.exe` gets a window of its own (ARQUITETURA 18.7). The two that
   stay are the captures, the ones that flash are clip assembly and the face
   scan. Closing one kills that ffmpeg. → **R15.**
2. **"Not recorded going out for a delivery, nor coming back."** **It was
   recorded — both ways, in one event.** The user sent the trip exported from
   the Tapo app (two clips, 22:29:22 and 22:29:54). Production's
   `Front/2026-10-09/22-29-22.mp4` covers all of it and more, 56 s at 1080p:
   out of the door at 22:29:19, the gate, back with the order from 22:29:43,
   in at 22:29:57. What failed is everything the user *sees* of an event:
   - **The picture was the dog.** The event's thumbnail — the Recordings card
     and the Telegram photo — is the first analysis frame of the event. This
     one started a second before the user stepped out, on the dog lying on
     the mat detected as `person 0.72` (item 3). → **R19.**
   - **No face message.** Probed frame by frame (an architect's script, not in
     the repository): walking towards the camera for ~6 s, YuNet finds the
     face in almost every frame, but only **4 of ~90 frames** pass both
     `MIN_FACE_WIDTH` (36 px) and the frontal check — faces of 33–41 px while
     far, then turned towards the door and blurred when close (up to 77 px,
     not frontal). The scan reads **one frame in 14** (`MAX_SAMPLES` 60 spread
     over the 56 s clip) and hit none of the four. No sighting, so no face
     message. → **R20.**

   Also established while looking: **nothing recorded anything between
   30/09 22:54 and 09/10 20:21** — the test copy only ran for tests (its last
   clip is from 30/09), and production started at 20:20:55.

**Found while looking:**

3. **The white dog lying on the dark mat (or bed) at the bottom of the Front
   frame is detected as `person`** — 0.64 at 20:29:03, 0.72 at 22:29:22 (the
   thumbnails show the box around the dog and the mat). Each one records as a
   person event and notifies "person". → **R18.**
4. **Nobody can tell whether a notification went out.** `notify.event()` sends
   in a thread and throws the result away; a failed send leaves no trace. →
   **R16.**
5. **R13, crash test not run.** The architect tried to kill production's
   process to time the restart; Claude Code's auto mode refused it as
   interfering with a running workload. Left for the user: a reboot tests the
   boot trigger and, as a bonus, brings production back in session 0, without
   windows, until R15 ships.

**New recommendations:**

**R15 — ffmpeg console windows (high).** Start every subprocess in `src/` with
`creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)` — the flag only
exists on Windows, hence the `getattr`. Four places: `capture.py`
(`FFmpegCamera.start`), `clips.py` (`_concat`), `faces.py` (`_describe`,
`_sampled_frames`). Not `clips.reveal`, which opens Explorer on purpose. One
shared constant, not four copies. Acceptance: reproduce first — start the test
copy with `pythonw.exe -m jarvis --headless` from PowerShell
(`Start-Process`), and `Get-Process | Where-Object MainWindowTitle -like
'*ffmpeg*'` lists the windows; after the fix it lists nothing, also while a
clip is assembled. Production gets it with the next release.

**R16 — Log every notification outcome, without the token (high).** Log at
INFO, per attempt: camera, labels, and `sent`, `failed: <Telegram's
description>` or `skipped: cooldown`. Same for each face message of
`faces_seen`. **Security:** a `requests` exception message contains the URL,
and the URL contains the bot token (`/bot<token>/sendPhoto`). Redact it inside
`_call()`, before the detail reaches anyone — the log, a future Settings page,
a Telegram error — not at each caller. Acceptance: in the test copy, with a
wrong token and with the network cut, the log shows the failure and the token
appears nowhere (`Select-String` for the real token in `logs/` finds nothing).

**R17 — A replay tool: why was this not recorded? (medium).** First written as
high, when the trip looked like a miss; it was not (item 2), so it drops to
medium. Still wanted: R18 needs it, and so will the next real miss, which
today could only be diagnosed by hand, as item 2 was. Add
`tools/replay.py <video>`: it reads any video (a clip, or one exported from the
Tapo app), scales it to the analysis size the way `capture.py` does, feeds it
at `ANALYSIS_FPS` through the **real** `MotionDetector` and
`SubjectDetector`, and prints, per frame, what each layer kept and what it
dropped, and why — too small, not confirmed, lighting change, below
`MIN_PERSON_HEIGHT_FRACTION`, no motion overlap, static spot. If the classes
do not expose the reason, add an optional trace (a callback or a list) that
changes nothing when absent. `people.py` uses the clock (`MIN_INTERVAL`,
static spots): drive it with the video's time, not the wall clock, or a replay
faster than real time will decide differently from production. Acceptance: on
`Front/2026-10-09/20-29-03.mp4` it shows the dog detected as `person`; on
`20-23-07.mp4`, the person at the door; on `22-29-22.mp4`, the dog as
`person` in the first second, then the user.

**R18 — Dog on the mat as `person` (medium).** Do not tune before R17 shows
which frames and scores produce it. Candidate fixes, to choose with the data:
backlog item 1 (zones), or a rule against "persons" that never stand up in a
spot where a static object lives. Note that `notify_labels` is `person`, so
every one of these is a false alarm on the phone too.

**R19 — The event's picture should show the person (high).** Today the
thumbnail is the event's first analysis frame (`EventRecorder._start`), and
the first frame is whatever triggered the event — on 09/10 at 22:29, the dog.
The user looked at the event and saw no one. Direction: during the event, keep
the best view of a person in memory (confidence and box size; persons only,
falling back to the first frame when there is none), and at the end write it
as `HH-MM-SS.best.jpg`, with an optional `best_thumbnail` field in the event
JSON. **Additive, as the rule demands:** the first-frame `HH-MM-SS.jpg` stays
(it shows what triggered the event, which is what R18 needs), older events
without the field keep showing it, and the `base.*` name moves with the event
when archived. The page shows the best view when there is one. On the phone,
the first message must stay immediate, so it keeps the first frame; when the
event notified and the scan found no face, the follow-up message carries the
best view instead, so the phone always ends with a picture of the person.
Acceptance: on a copy of the 22:29 event in the test copy, the card shows the
user, and `check_data.py` reads old and new events.

**R20 — The face scan misses short frontal moments (high).** Measured on the
22:29 clip (item 2): 4 usable frames out of ~90, none of them sampled. One in
14 frames, spread evenly over the clip, is too coarse when a face is frontal
and large enough for a fraction of a second. Direction: sample densely where it
pays — the recorder already knows when persons were detected; pass those
moments to the scan and read every frame or every other one there, keeping the
sparse pass for the rest. Measure the cost on the M900 (YuNet on 1080p frames,
on the 4-core Skylake) and report it in `HANDOFF.md`. Acceptance: rescanning
a **copy** of `22-29-22.mp4` in the test copy finds the user's face. Never
write into `C:\JARVIS` from a test — copy the event into the test copy's
`clips/` first.

### 13.7 Review 3 — developer session 1

Reviewed `2ed3fb4..87e736b`, the whole diff, against the HANDOFF's claims.
Nothing needed fixing: the code does what the HANDOFF says, `check_data`
reads all 150 events, no comments, and the two pieces worth re-running by
hand behaved — the token is redacted both literal and `%3A`-encoded, and the
`select` expression for a person seen 36–44 s into the clip comes out as
`not(mod(n\,14))+(between(t\,34.50\,45.50))*not(mod(n\,2))`. The developer
reproduced every problem before fixing it, which is what the `dev` skill asks.
What changed is in ARQUITETURA 12.9, 18.7 and 19.2.

**What the review weighed hardest:**

1. **R20's cost is real and unmeasured where it matters.** A dense scan is
   ~45 s of multi-threaded DNN per event with a person, on the same 4 cores as
   live analysis. Capture drops frames rather than queueing them, so the cost
   would show as fewer analysed frames — and temporal confirmation counts
   frames, so a fast walker right after an event could go unconfirmed. On the
   first night, 9 of 19 events had a person label. Released anyway: the face
   message is what the user asked for, the sparse scan already took 12 s, and
   the measurement needs production-like load. → **R21.**
2. **R19 doubles R18's false alarms.** An event started by the dog on the mat
   (detected as `person`) now sends its first message with the dog and, with no
   face found, a follow-up with the best view — the dog again. → **R18 raised
   to high.**
3. **Where did the dense scan look?** Nothing logs or stores the spans, so the
   clock alignment (spans and segment names both use the PC clock, so it
   should hold) can only be confirmed by replay. → **R22.**

**R21 — Measure what the dense scan costs live analysis (high, verification).**
Count analysed frames per camera per minute — a counter in the `Core`, exposed
in `/api/status` and logged once a minute while a scan runs — and compare the
rate during a dense scan with the rate without one, on the M900 with
production's load. If it falls by more than a third, options in order of
cost: run the scan's DNN with fewer threads (`cv2.setNumThreads` is global, so
this needs care), run YuNet only on the head region of person boxes, or scan
with a lower priority.

**R22 — Log where the dense scan looked (medium).** One INFO line per scan:
the clip, the spans in seconds, frames read and time taken. Storing the spans
in the event JSON, as the developer proposed, would also let
`refazer_rostos.py` rescan densely; it is additive, so allowed, but not needed
until a rescan is.

**R10, left:** older documentation, `ui.py` (including its Telegram test text),
`cameras.build_camera_list()`'s `SystemExit`, `tools/diagnostico.py`, and the
Portuguese file names.
### 13.8 Review 4 — developer session 2

Reviewed `5d91305..1b8822d`. No code fixed. The trace hooks in `motion.py`
and `people.py` change no decision (the developer compared old and new on all
561 frames of the 22:29 clip); every module imports, `ui.py` included after
its translation; no comments; the version reads `v2026.10.10-12-g1b8822d` in
the test copy. Integrated into ARQUITETURA 12.10.

**R21's fix, decided by the architect — R23.** The developer measured that a
dense scan makes YOLO 1.6× slower and that fewer threads only make YOLO slower
still, and left the choice to the review. It is a design call, not the
user's. The options weighed:

| Option | Verdict |
|---|---|
| Fewer OpenCV threads for the scan | measured wrong: the setting is process-wide |
| YuNet only on head regions | cheaper scan, but needs person boxes per clip frame, aligned in time — complex, and the scan still overlaps events |
| Lower thread priority | does not reach OpenCV's shared worker threads |
| Wait to start the scan while a camera records (the developer's idea) | good, but a 45 s scan that has started still collides with the next event |
| **Pause the scan between frames while any camera records** | chosen: the collision only matters during an event, and this removes it wherever the event starts |

**R23 — Pause the face scan while any camera is recording (high).** Before
each frame, `_scan_clip()` asks a callable `busy()` and sleeps in short steps
while it is true; the ffmpeg feeding the pipe simply blocks meanwhile.
`clips` provides `busy()` — any `EventRecorder` recording — and passes it in,
so `faces` knows nothing of cameras. A ceiling, 10 minutes of pause per scan,
keeps a busy evening from starving it; the R22 log line gains the pause total.
The face message arrives later during long activity; the first message is
untouched. Acceptance: with the measurement of R21 repeated during an event,
YOLO's time is back to its unloaded value while the scan is paused.

**R18 — decided.** The user first chose to wait, then asked the architect to
set the rule. The replay's data: the dog's `person` boxes are 3.3–4.2× wider
than tall and their bottom touches the frame's bottom edge (y ≈ 538 of 540);
every real person seen was taller than wide (110–152 × 267–320). The rule, in
`SubjectDetector.detect()`: **drop a `person` whose box is more than
`WIDE_PERSON_RATIO` = 2.5× wider than tall and whose bottom lies within
`BOTTOM_EDGE_FRACTION` = 3 % of the frame's bottom**, with the trace reason
"wide at the bottom edge". Both conditions, not one: a wide box alone could be
a person lying on the lawn mid-frame — rare, but worth keeping; the mat is at
the bottom edge, where a standing person's box is always tall. The margin from
2.5 to the dog's 3.3 is deliberate. Acceptance: `tools/replay.py` drops the dog
on `20-29-03` and `22-29-22` and keeps the user; then replay **every** event
with a `person` label from 09/10 and 10/10 (copies, in the test copy) and list
each detection the rule changes — none may be a real person.
**Lesson worth keeping:** "give the scan fewer threads" sounded obviously
right and measured wrong. Measure before choosing, even the obvious.
### 13.9 Review 5 — developer session 3

Reviewed `11c6663..5f3c356`: R23, R18 and web stage 4. No code fixed. The new
routes check every input, the face route stays inside `faces/`, the page never
builds HTML from data (no `innerHTML`), and the token is write-only. Integrated
into ARQUITETURA 12.10 and 17.9. The three points the developer left open,
decided here rather than handed to the user:

1. **R18 at 2.0 instead of 2.5 — accepted.** The replay found the dog sitting
   up at 2.42–2.48; real persons measure 0.4–0.6.
2. **A paused scan keeps the lock — accepted.** Late face messages on a busy
   evening are the price of an undisturbed YOLO; the first message never waits.
3. **Writes from the network — R24.** R4 accepted that anyone on the Wi-Fi can
   *see* the cameras; stage 4 lets them also rename faces (and a merge cannot
   be undone yet) or point the notifications elsewhere. Restricting writes to
   the M900 would lock out the user's other computer, which R4 wanted to keep.
   There is also a second door: a web page the user opens could make the
   browser post to the service (cross-site request forgery). The solution
   keeps both the convenience and the safety:

**R24 — Guard every write (high).** (a) Every `POST` must carry a custom header
(`X-Jarvis-Request: 1`), which `app.js` adds; a foreign page cannot add it
without the browser first asking permission, and the service never grants it —
that closes the forgery door for free. (b) Writes from any address other than
127.0.0.1 need the device to be **paired once**: a PIN set on the M900's own
page, kept in `config.json` as `write_pin` (an additive key), typed once on
the other computer, remembered by that browser and sent with each write;
compared with `hmac.compare_digest`. With no PIN set, writes from the network
are refused with a message saying how to set one. Reading stays open, as R4
decided; shutdown stays local only. Acceptance: a write from the other
computer fails without the PIN and works after pairing; a `POST` without the
header fails even from 127.0.0.1; `check_data` reads the new key.

Released anyway as `v2026.10.10.3`: the user wants People on the web, the
exposure needs someone on the home Wi-Fi who knows the address, and R24 is
the next session's first item.
### 13.10 Review 6 — developer session 4, and the face messages

Reviewed `3a91964..5eb8964`. No code fixed: every path that touches a
person's `embeddings` goes through `_take` or `remove_view`, both inside the
gallery lock and both saving; imports, comments and `check_data` clean.
Integrated into ARQUITETURA 17.10 and 19.2. The threat model of R24 is
accepted as written there.

**"Fewer face messages — is that normal?" (the user, 10/10).** Measured on
production's log, from 13:31 to 15:15: 10 events with a person, 6 first
messages sent, 4 skipped by the cooldown, 21 face scans, **2 with a usable
face**, 1 face message and 4 best-view messages. Mostly normal: a face must be
frontal and at least 36 px wide, which daytime walkers seen from the gate
rarely are, and sightings per person event are about the same as on 30/09
(4 of 18 against 15 of ~85). R18 also removed the dog's false person events,
so there are fewer notifications overall. One part is a real gap: a face
message is only sent when the event's own first message went out, so a face
found in an event that fell in the 120 s cooldown is never announced — and a
face is the most valuable message there is.

**R25 — Send a found face even when its event was in the cooldown (medium,
decided by the architect).** The cooldown exists against repeated events, not
against faces, which are rare (2 of 21 scans). Rule: after the scan, send the
face message whether or not the event's first message went out, with its own
cooldown per person — the same person is not announced twice within
`notify_cooldown`. The best-view follow-up keeps today's rule (only after a
sent event), so the volume barely changes.
### 13.11 Review 10 — the user's three reports (11/10/2026)

**"The pages fail on the other computer."** Root cause found: the service
sends no cache instruction for the page, `app.js` or `style.css`, so a browser
may keep running a stale copy for hours after an update, by its own heuristic
on `Last-Modified` — and on 10/10 the routes changed in seven releases, so an
old `app.js` calls routes that no longer exist. A second, smaller cause: a
change refused by the R24 guard (an unpaired browser) fails without a visible
reason. Testing "another computer" needs no second machine: the M900's own
browser at `http://192.168.0.18:8765` is not 127.0.0.1, so the guard treats it
exactly as the other computer.

**R28 — The page is always current, and every refusal says why (high).**
`Cache-Control: no-cache` on `/` and `/static/*` (the browser revalidates by
ETag every load, a cheap 304 on the LAN), and the version from backlog 18 in
the asset URLs (`app.js?v=<version>`), so an update can never leave an old
script running. Every failed write shows the server's reason on the page; a
403 from the guard says "this device is not paired — enter the PIN in
Settings". Acceptance: after a deploy, a browser at 192.168.0.18 loads the new
script without a hard refresh; an unpaired write shows the message.

**"The Dogs tab should behave like People: favourite photo, 40 views,
grouping."** The first two exist — the Dogs tab is the same code as People
(ARQUITETURA 20) — and the other computer's stale page (R28) can hide them.
Grouping does not: naming a person gathers the unnamed faces that clearly
look like them (`_absorb`), but the developer turned it off for dogs.

**R29 — Naming a dog gathers its clear look-alikes (medium).** Enable
`_absorb` for dogs with the **sure** rule of `match` (distance and margin),
never the probable one, and only within the same lighting. A wrong grouping is
undone by Dismiss or a rename, as with people. **Widened by the user's idea (11/10):** every naming or merge re-examines all the unnamed crops against the dog's updated views, repeating until nothing more joins — a new view can make other crops recognisable — exactly as `Gallery.rename` already does for people (`_absorb` loops until no change). And past recordings must follow: today a dog sighting stores its words at recording time, so an event recorded as "unidentified dog" would keep saying so after its crop joins Mirana. Show the current name from the sighting's `dog_id` (sightings are repointed on merge, as for faces), keeping the stored certainty only for "probably".

**"Face detection seems much weaker."** The log shows no regression: scans run
and find faces when there are frontal ones (21:05 on 10/10: 58 face views),
and most person events at night have none — infrared faces are small. What
changed is visible, not measured: the gallery restarted empty on 10/10, so
every face is "unknown" until named again. To tell a regression from the
night, the user is asked for one or two events where their face was clearly
visible and no face came; `tools/replay.py` and the face probe then show which
filter dropped it.
### 13.12 Review 11 — a general review, and the missing face messages (11/10/2026)

The user asked, with no new feature in the queue, for a general review —
efficiency, performance, UX, documentation — and pointed at the person
notifications that are never followed by a face.

**The faces: found, then dropped as "not frontal".** Since 10/10 13:31, 43
person events: every one was scanned, 16 found a usable face, 27 did not. A
sheet of the 27 best views shows the night ones are what infrared allows, but
several daytime Front ones show a person close and well lit. Replaying three
of them (17:51:51, 15:50:37, 15:47:40) through YuNet: faces in 61 frames,
37–65 px wide, score about 0.8 — **and every one dropped by `is_frontal`**:
nose offset 0.47–1.01 against the 0.35 limit, eye spread 0.14–0.27 of the face
width against 0.38. Three-quarter and side views of someone walking to the
door. The filter is strict on purpose (an embedding of a profile describes
nobody, 10.9), but it also costs the user the face photo.

**R30 — Show the face even when it cannot be recognised (high).** Two parts.
(a) When a person event's scan keeps no recognisable face but YuNet saw faces
on a person (score ≥ 0.75, width ≥ 36 px), send the best of them — closest to
frontal, then largest — as a face photo ("face, side view"), **without adding
it to the gallery**; it replaces the best-view message for that event. (b)
Measure whether the frontal limits can be loosened for recognition: with the
user's views named, compute the match score of the three-quarter faces of
their own clips; loosen `MAX_NOSE_OFFSET` / `MIN_EYE_SPREAD` only as far as
the right person still wins.

**Performance — R31 (medium).** Outside events the scan is not paused, and
live analysis dropped to ~270 frames a minute per camera while one ran
(21:06 on 10/10), against ~580. YuNet runs on full 1080p frames (~143 ms
each). Run detection on the half-size frame and only the alignment on the
full-size crop, which should cut the scan's cost several times; measure
before and after with the R21 counter.

**Log noise — R32 (low).** 27 "Exception in callback
`_ProactorBasePipeTransport._call_connection_lost`" tracebacks at ERROR: Windows'
asyncio reporting a browser that closed the live view. Install a loop
exception handler that drops `ConnectionResetError` there, so ERROR means a
real problem.

**UX.** The main failure is R28 (stale page, silent refusals); not clicked
through beyond it. Worth a pass with the built-in browser after R28 lands.

**Documentation — R33 (medium, the architect's own).** README still describes
three OpenCV tabs and `jarvis.bat` opening a window; ARQUITETURA (2,909 lines)
and CONTEXTO (1,388) grew by dated appendices (12.9, 12.10, 17.9, 17.10, 20).
CONTEXTO is read by every session's resume routine — about 25k tokens each
time. Plan: README rewritten in English; CONTEXTO cut to the current brief
(rules, state, backlog, open recommendations, plan), with the review history
and usage log moved to a `docs/HISTORY.md` read on demand; ARQUITETURA
reorganised by subject with the dated sections folded in; and R10's
translation done along the way. To be done in a new conversation, where the
documents can be read whole without this one's 750k of context.
### 13.13 Pairing a device once (11/10/2026)

The user has to type the PIN again "all the time" on their devices and asked
for one validation, or at least 30 days per device. The page keeps the PIN in
`localStorage`, with no expiry of its own — but browsers do clear it: Safari
deletes script-written storage of a site unused for 7 days, private windows
and "clear data on close" settings drop it, and a different address
(`192.168.0.18` against the M900's name) is a different store. Re-typing the
PIN is the symptom; storing the secret in the page is the cause.

**R34 — Pair a device once, for 30 days that renew with use (high).** Pairing
with the PIN makes the server set a cookie — `HttpOnly`, `SameSite=Strict`,
`Max-Age` 30 days — holding a random device token; the server keeps only its
SHA-256 hash, with a label and the last use, in a new file `devices.json`
(additive). Every write from a paired device renews the 30 days, so a device
in use never asks again; one unused for 30 days asks once. A cookie set by the
server survives where `localStorage` does not (Safari's 7-day rule applies to
storage written by scripts). The custom header of R24 stays, so cross-site
forgery is still blocked; the PIN header keeps working as before. Settings on
the M900 lists the paired devices with "forget" (and changing the PIN forgets
them all). Acceptance: pair once through 192.168.0.18, close and reopen the
browser, write without typing anything; a forgotten device is refused; tests
for expiry and renewal.
---

## 14. Sessions and token budget

### 14.1 Why — decided by the user on 09/10/2026

The plan is **Claude Pro**: a usage limit that resets every **5 hours**, and a
weekly one. The user wants to learn how many developer and architect sessions
fit in one 5-hour window, so each session can be scoped to use it well instead
of stopping halfway. Nothing here is guessed: a row is a measurement.

### 14.2 How to measure

At the start and at the end of every session, Claude reads the plan usage with
the desktop app's `get_usage` tool (5-hour %, weekly %, reset time) and the
conversation's context size. A session is one role's stint — a developer
delivery or an architect review — even when both happen in the same
conversation. The architect fills its own row of 14.3; the developer, who
never edits `docs/`, writes its numbers in `HANDOFF.md` (the `dev` skill asks
for them), and the architect copies them into 14.3 when integrating.

What drives the cost, as far as one night shows: every turn re-sends the whole
conversation, so a long conversation makes every later step expensive. In this
one, ~50k of the context are tool definitions alone. **Start each session in a
new conversation**: the resume routine (section 12) reads what is needed from
disk, which is exactly why the roles hand over through files.

### 14.3 Log

| # | Role | Effort | Date | Scope | 5-hour window | Weekly | Context |
|---|---|---|---|---|---|---|---|
| — | both | high / ultracode | 29/09–09/10 | everything before this table | not measured | — | one conversation since 29/09, compacted several times |
| A3 | architect | ultracode | 09/10 23:10–23:40 | finish review 2's docs, check production's first night, diagnose the windows, R15–R18, plan dev session 1 (to 23:25: 25%); then the user's Tapo videos — contact sheets, a frame-by-frame face probe, R19–R20, plan revised (+9 points); then pandoc, the EPUB and its checker, the `dev` skill (+3 points) | 0% → 37% at 23:46 (the window opened at 23:10 and resets at 04:10; the first 22% includes resuming a compacted conversation) | 30% → 32% | 106k → 223k tokens |
| A4 | architect | ultracode | 09/10 23:50 – 10/10 00:31 | user's Tapo videos already counted in A3; here: the raid log, issue 1 (6 pages of SVG, page renders checked as images), its tool and section 15 | 37% → 61%, **shared with developer session 1 running at the same time** in another conversation — its own numbers are in its HANDOFF | 32% → 35% | 223k → 314k tokens |
| D1 | developer | high | 10/10 00:00–00:30 | session 1: R15, R16, R10 in part, R19, R20, R11 (HANDOFF) | 39% → 52%: R15 3, R16 + R10 2, R19 4, R20 4, R11 and HANDOFF under 1 | 32% → 34% | 66k → 210k tokens |
| A5 | architect | ultracode | 10/10 00:52–01:00 | review 3, HANDOFF integrated, release `v2026.10.10` | 77% → 82%: review and docs, about 5 points | 37% → 37% | 404k → 445k tokens |
| A6 | architect | ultracode | 10/10 00:55–01:15 | production update to `v2026.10.10`, R13 reboot and crash checks, EPUB | 82% → 87% | 37% → 38% | 445k → 470k tokens — at this size every turn costs about a point, the strongest reason yet for a new conversation per session |
| D2 | developer | high | 10/10 04:10–04:40 | session 2: R21 measured, backlog 18, R22, R17, R10 code part; R18 deferred by the user | 0% → 11% (new window): R21 3, backlog 18 + R22 2, R17 3, R18 question + R10 3 | 39% → 41% | 241k → 330k tokens, carried over from session 1 |
| A7 | architect | ultracode | 10/10 13:25–13:35 | review 4, R23 decided, release `v2026.10.10.2`, comic scripts 2 and 3 (one failed shell append re-sent them) | 9% → 15% | 43% → 44% | 500k → 540k tokens, in the old conversation |
| D3 | developer | high | 10/10 13:45–14:20 | session 3: R23, R18, web stage 4 | 22% → 34%: R23 2, R18 2, stage 4 8 | 45% → 46% | 336k → 405k, old conversation again |
| A8 | architect | ultracode | 10/10 14:25–14:45 | backlog 19, review 5, R24, release and production `v2026.10.10.3`, script 4 | 35% → 38% | 47% → 47% | 557k → 580k tokens |
| D4 | developer | high | 10/10 14:35–15:30 | session 4: R24, backlog 19 and 20, window removed | 43% → 62%: R24 5, backlog 19 10, backlog 20 2, window 2 | 48% → 50% | 412k → 505k, old conversation |
| A9 | architect | ultracode | 10/10 15:35–15:55 | the face-message question, review 6, R25, release and deploy `v2026.10.10.4`, gallery deleted, script 5 | 64% → 68% | 50% → 51% | 610k → 645k tokens |
| D5 | developer | high | 10/10 15:40–15:50 | session 5: R25, R6 (23 tests) | see its HANDOFF; small | — | 509k at the start, old conversation |
| A10 | architect | ultracode | 10/10 16:00–16:50 | review 7, httpx2 check, backlog 21, release and deploy `v2026.10.10.5`, script 6 | 68% → 78% (shared with developer session 5 in the same window) | 51% → 52% | 650k → 663k tokens |
| D6 | developer | high | 10/10 16:10–16:20 | session 6: backlog 21, R26 | 81% → 84% | 53% → 53% | 542k → 560k, old conversation |
| A11 | architect | ultracode | 10/10 16:25–16:35 | review 8, release and deploy `v2026.10.10.6`, script 7 | 86% → about 89% | 53% → 53% | 669k → 680k tokens |
| D7 | developer | high | 10/10 evening | session 7: backlog 22 parts 1 and 2 | 10% → 23% (new window) | 56% → 57% | 564k → 635k, old conversation |
| A12 | architect | ultracode | 10/10 21:00–21:20 | review 9, R27, release and deploy `v2026.10.10.7`, dog crops in production, script 8 | 36% → ~43% | 59% → 60% | 705k → 720k tokens |
| D8 | developer | high | 11/10 morning | session 8: R27, dog tuning tool | 11% → 15% | 61% → 61% | 638k → 655k, old conversation |
| A13 | architect | ultracode | 11/10 morning | review 10: the three reports, R28, R29, release `v2026.10.11` | 29% → ~36% | 63% → 64% | 720k → 740k tokens |
| D9 | developer | high | 11/10 08:00–10:30 | session 9: R28, R30 (a); a built-in browser call hung for an hour | 36% → 76% (shared with the architect) | 64% → 70% | 659k → ?, old conversation |
| A14 | architect | ultracode | 11/10 09:30–10:50 | the side-view finding, general review, settings help, automatic handover, review 11, release `v2026.10.11.2` | shared window, ~81% → ~85% | 70% → 70% | 750k → 790k tokens |
| D10 | developer | high | 11/10 12:23–12:55 | session 10, started by the architect: R34, backlog 5, R29 | 0% → ~43% | 72% → 77% | old conversation |
| A15 | architect | ultracode | 11/10 12:55–13:10 | review 13, release and deploy `v2026.10.11.3`, script 9 | ~43% → 47% | 77% → 78% | 820k → 832k tokens. **The first automatic cycle cost ~47 points of the 5-hour window, ~43 of them the developer's old conversation** |
| D11 | developer | high | 11/10 13:00–14:50 | session 11, **a new conversation**: backlog 23, 24, R31, R32, R35 and R30 (b) measured | 47% → ~72% for six items | 78% → 81% | started light |
| A16 | architect | ultracode | 11/10 14:50–15:15 | review 14, release `v2026.10.11.4`, a rolled-back deploy diagnosed and fixed, script 10 | 72% → ~78% | 81% → 82% | 860k → 880k |

### 14.4 Next sessions

**Developer 12:** R38 (undo a report) → R40 (after Analyse, the proposal offers both "Keep these 40, the rest waits" and "Keep these 40, discard the rest" — on 11/10 the user expected the 9 left over to disappear, and they went to the queue as designed) → R37 → R36. R30 (b) waits for a second named person. **Architect:** R33. **Waiting for the user:** backlog 1–2.

Test the other-computer path with the M900's own browser at 192.168.0.18.

---

## 15. Raid log — the comic script of each release

**The user's idea, 10/10/2026, revised the same night.** Every release gets an
issue of a comic: the architect and the developer talking through what really
happened in that version, simplified. **The architect writes the script, not
the drawing**; the user draws it later with a tool made for comics. A first
issue was drawn here as SVG and printed to PDF, and the user replaced it with
scripts after seeing what a drawn issue costs in tokens.

Two files, and only two: `docs/raidlog/script.en.md` and
`docs/raidlog/script.pt.md`, the same story panel for panel — the one
document kept in both languages. Each opens with the series bible (cast,
style, the truth rule: simplified, never invented); a new issue is appended to
both when the architect tags a release, from that version's `HANDOFF.md`,
review and commits.

| Issue | Version | Title | Script |
|---|---|---|---|
| 1 | `v2026.10.09` | The First Night Shift / O Primeiro Turno da Noite | written |
| 2 | `v2026.10.10` | The Dog Who Wore a Person's Face / O Cachorro com Cara de Gente | written |
| 3 | `v2026.10.10.2` | The Watcher's Instruments / Os Instrumentos do Vigia | written |
| 4 | `v2026.10.10.3` | The House Gets a Front Desk / A Casa Ganha uma Recepção | written |
| 5 | `v2026.10.10.4` | The Lock and the Album / A Tranca e o Álbum | written |
| 6 | `v2026.10.10.5` | The Safety Net / A Rede de Proteção | written |
| 7 | `v2026.10.10.6` | The Favourite / A Favorita | written |
| 8 | `v2026.10.10.7` | Mirana and Aurora / Mirana e Aurora | written |
| 9 | `v2026.10.11`, `.2` and `.3` | The Front Desk Learns Manners / A Recepção Aprende Modos | written |
| 10 | `v2026.10.11.4` | The Evidence Box / A Caixa de Provas | written |
