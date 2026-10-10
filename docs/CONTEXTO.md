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
The old OpenCV window, with **Live**, **Records** and **People** tabs, still
exists behind `--window` until stage 4 replaces it.

**Duas máquinas:**

| | Desenvolvimento | Destino |
|---|---|---|
| Máquina | Ryzen 9 7950X, 64 GB, RTX 4080 | Lenovo M900, i5 Skylake 4 núcleos, 16 GB |
| Caminho | `D:\Personal Projects\J.A.R.V.I.S\jarvis` | `C:\Personal Projects\jarvis` |
| Estado | Tudo funciona | Tudo funciona desde 29/09/2026 (seção 6) |

**Production runs on the M900 since 09/10/2026 at 20:20**, from `C:\JARVIS`,
release `v2026.10.09`, started with Windows by a scheduled task. Updated to `v2026.10.10` on 10/10 at 00:56: every file read before and after, both cameras fresh, and no ffmpeg window on the desktop. The folder
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
   | | **Estágio 4 — People e Ajustes na web** | **próximo** |
   | ✓ | Start with Windows, no console | done by item 17 (production task), 09/10 |
   | | Remove the OpenCV window (`ui.py`, `--window`) | after stage 4 |
   | | Estágio 2 — reprodução do vídeo na página | depois |

   Pendente de teste: abrir pelo celular (`http://192.168.0.18:8765` no M900).

### Importante

Funciona sem, mas incompleto.

18. **The running version on the web page** (decided 10/10/2026) — the user wants to see, somewhere in the interface, which version is running. Design: read `git describe --tags --always --dirty` once at startup (production is a clone checked out at a tag, so it shows `v2026.10.10`; the test copy shows something like `v2026.10.10-6-g906b64b`, which tells the two apart at a glance), add an optional `version` field to `/api/status` (additive), and show it discreetly on the page. The `git` call needs `CREATE_NO_WINDOW` like every other subprocess (R15), and must not stop the service if `git` is missing — show `unknown`.

4. **Medir o M900 rodando** (proposto) — CPU com as duas câmeras em movimento,
   e se `HWACCEL` ajuda (INSTALACAO seção 6)
5. **Reprodução no Records** (proposto) — hoje clicar abre o Explorer
6. **Busca e filtro** (proposto) — com ~100 eventos/dia, só por data é
   inviável. Por pessoa, câmera, rótulo
7. **Tracking** (proposto) — manter identidade entre frames; resolve a pessoa
   parada e faz um clipe corresponder a uma pessoa
8. **Rótulos de animal** (proposto) — só aceitar espécie que se repita no
   evento, em vez de acumular cada hesitação do YOLO
9. **Desfazer junção na tela People** (proposto) — corrigir um merge errado
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
15. **Re-ID de animais** (proposto) — classificador sobre o corpo inteiro
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
  ui.py           old OpenCV window (--window), until web stage 4
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
uv run python -m jarvis --window                        old OpenCV window (until web stage 4)
uv run python -m jarvis --stop                          stop the copy running from this folder, cleanly
uv run python tools/check_data.py                       can the current code read every file on disk?
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

**Whose job — decided on 09/10/2026: the architect's.** The book is made of
the documentation, and only the architect changes the documentation, so the
architect regenerates it as the last step of every session that changed a
`.md`, and tells the user it is ready. A developer session never needs to. The
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
ever runs tags (ARQUITETURA 18.7). The architect's last step, whenever the
docs changed, is the EPUB (section 10). The developer's session is written down
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

**Last review covers up to the `v2026.10.10` release commit.** The next one
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
| | R6 | média | Testes automáticos para as rotas da web e as travas do aviso | open; data is covered by `check_data.py`, routes and notify rules still are not |
| | R7 | baixa | `instalar.bat` não confere se o Python ficou assinado | partly: `production.ps1` checks it; `instalar.bat` still does not |
| ✓ | R8 | baixa | Falha de rede na página não aparece para o usuário | done `760d68e` (ARQUITETURA 17.8) |
| | R9 | verificação | `python-preference = "system"` na máquina de desenvolvimento | aberta |
| | R10 | **high** | Move everything except the conversation to English (user decision) | in progress; left: older docs, `ui.py`, `cameras.build_camera_list()`'s `SystemExit`, `tools/diagnostico.py`, Portuguese file names (13.7) |
| ✓ | R11 | **high** | `settings.save()` drops keys it does not know | done `524b14f` (ARQUITETURA 19.2) |
| | R12 | medium | Production and test copy on the same M900 double the CPU load | open |
| ✓ | R13 | verification | The startup task survives a reboot, and restarts after a crash | **reboot verified 10/10**: Windows up 00:58:07, task at 00:58:16, cameras ok 00:59:06, in session 0 with no window. **crash verified the same night**: the user ended Python in Task Manager about 01:01 (the task shows result 1, Task Manager's exit code); the 5-minute trigger at 01:06:10 started it again, cameras ok at 01:06:16. A crash costs at most ~5 min of recording |
| | R14 | low | Live MJPEG is encoded once per viewer | open |
| ✓ | R15 | **high** | ffmpeg opens console windows on the user's desktop | done `9eaa42c` (ARQUITETURA 18.7) |
| ✓ | R16 | **high** | Notification outcomes are never logged, and an error detail can carry the bot token | done `9ae537b` (ARQUITETURA 12.9) |
| | R17 | medium | No way to tell why something was *not* recorded: a replay tool | open — dev session 2; was high until the "miss" proved not to be one |
| | R18 | **high** since review 3 | The white dog lying on the Front mat is detected as `person` | open — now costs two false messages per event (13.7); needs R17 first |
| ✓ | R19 | **high** | The event's picture is its first frame, so it can show the dog instead of the person | done `085b3b6` (ARQUITETURA 12.9) |
| ✓ | R20 | **high** | The face scan samples too sparsely and misses short frontal moments | done `668588d` (ARQUITETURA 12.9) |
| | R21 | **high** | What the dense face scan costs live analysis on the M900 | open — verification, dev session 2 |
| | R22 | medium | Nothing records where the dense scan looked | open — dev session 2 |

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

### 14.4 Next session: developer 2

Developer session 1 finished its whole plan (R15, R16, R10 in part, R19, R20,
R11), reviewed in 13.7. Same criteria as before (production first, what the
user saw before what Claude predicted, data and security, bundle by file,
cheap and certain first, proposals wait). In order:

| | Item | Why here | Files |
|---|---|---|---|
| 1 | **R21** — measure live analysis during a dense scan | production safety: the release just shipped the cost; cheap, and decides whether anything else must change first | `cameras.py`, `web.py` |
| 2 | **Backlog 18** — the running version on the page | the user asked for it; touches `/api/status`, which 1 already opens | `cameras.py` or `web.py`, `static/` |
| 3 | **R22** — log where the dense scan looked | rides with 1: same moment, same files open | `clips.py`, `faces.py` |
| 4 | **R17** — `tools/replay.py` | the developer already built a replay by hand for R19; make it a tool | `tools/`, maybe a trace in `motion.py` / `people.py` |
| 5 | **R18** — the dog on the mat as `person` | now two false messages per event; needs 3's data | `people.py`, maybe `clips.py` |
| 6 | **R10, the code part** — `ui.py` text, `build_camera_list()` | small, and cleans what the user still sees in Portuguese | `ui.py`, `cameras.py` |

If the budget ends early, stop after 4: R18 deserves a session that starts
with the replay's data in hand.

**Not in this session:** R6 (tests, a session of its own), R12 and R13
(operational; R13 needs a reboot by the user), R14, R7, R9, backlog item 3
stage 4 (the next feature), and backlog items 1–2, which wait for the user.
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
| 2 | `v2026.10.10` | The Dog Who Wore a Person's Face / O Cachorro com Cara de Gente | **to write** — first task of the next architect session |
