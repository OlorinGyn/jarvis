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
documentação, e precisei corrigir. Cheque também `models/`, `clips/`, `faces/`
e `backups/` — todos estão no `.gitignore`, mas um `git add -A` descuidado
depois de mexer nele pegaria.

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
Em 09/10/2026 bloqueou o próprio interpretador no M900, depois de um `uv sync`
trazer o 3.14.7, e a vigilância parou. O do python.org é assinado pela Python
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
| M900 parado, `Failed to spawn: python` (`WinError 4551`), 09/10 | `uv sync` trocou o Python que o uv baixa por 3.14.7, binário sem assinatura e sem reputação; o Smart App Control bloqueou o próprio interpretador | Python oficial assinado pela PSF + `python-preference = "system"`; `.bat` chamam `python -m jarvis`, sem o `jarvis.exe` sem assinatura (INSTALACAO 1.2) |

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

### Feito

| | Item | Onde |
|---|---|---|
| ✓ | **Armazenamento em camadas** (decidido) — move para HD externo após 30 dias; só apaga de lá se lotar | ARQUITETURA 11 |
| ✓ | **Notificação no celular** (decidido) — Telegram com miniatura, aviso no começo do evento | ARQUITETURA 12 |
| ✓ | **Núcleo sem janela** (decidido) — `--sem-janela`; gravar e avisar não dependem mais de ter alguém olhando | ARQUITETURA 15 |

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
   junto, de graça: acesso remoto e os itens 5, 6 e 11. Fazer **ao lado** da
   janela atual, sem removê-la, para comparar antes de descartar.
   **Stack: FastAPI + uvicorn**, decidido por MJPEG e HTTP Range, não por gosto.
   Plano em quatro estágios, cada um com critério de aceite: ARQUITETURA 17.

### Importante

Funciona sem, mas incompleto.

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
  __init__.py     ROOT, a raiz do projeto
  cameras.py      Core (vigilância, sem janela) + run_window / run_headless
  capture.py      ffmpeg por câmera: segmentos originais + frames de análise
  motion.py       camada 1: MOG2 + confirmação temporal
  people.py       camada 2: YOLO via cv2.dnn, pessoas e animais
  clips.py        camada 3: eventos, montagem sem perda, metadados
  faces.py        camada 4: YuNet + SFace, galeria, cadastro de nome
  archive.py      camada 5: move para o HD externo, apaga só lá se lotar
  settings.py     configuração editável pela interface (config.json)
  notify.py       aviso no celular via Telegram, com miniatura
  ui.py           menu lateral e as quatro telas
  geometry.py     tipo Detection e utilitários de caixas
tools/
  diagnostico.py  diagnóstico de captura (variantes, e --local sem câmera)
  probe_rtsp.py   diagnóstico de RTSP puro (DESCRIBE → SETUP → PLAY)
  gerar_epub.py   junta todos os .md num EPUB para e-reader
  epub.css        estilo do EPUB, legível em tela de 7 polegadas
  refazer_rostos.py  reconstrói faces/ a partir dos clipes gravados
  verificar_clipes.py  conta blocos danificados por câmera num dia
  gerar_icone.py  desenha o ícone do olho robótico em assets/jarvis.ico
  criar_atalho.ps1   atalho com ícone na Área de Trabalho
assets/           jarvis.ico e prévia PNG (gerados, mas versionados)
docs/             ARQUITETURA, INSTALACAO, PYTHON e este arquivo
instalar.bat      instalação numa máquina nova
jarvis.bat        atalho para iniciar com janela
jarvis_vigilancia.bat  só grava e avisa, sem janela (--sem-janela)
```

Estrutura explicada em ARQUITETURA seção 3.

Não versionados: `.env` (credenciais), `models/` (~73 MB, baixados sob demanda),
`clips/`, `faces/`, `backups/` (cópias que as ferramentas fazem antes de mexer
em dados).

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

Os `.md` nunca são alterados, e os EPUBs **não são versionados nem mantidos
atualizados** — rode quando quiser uma cópia fresca. O script apaga EPUBs
antigos da pasta e confere, ao final, se a contagem de tabelas e blocos de
código bate com a dos arquivos de origem.

Precisa do pandoc (`winget install --id JohnMacFarlane.Pandoc -e`), que o
script localiza mesmo sem estar no PATH. O `tools/epub.css` é o que deixa o
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
