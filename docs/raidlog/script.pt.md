# J.A.R.V.I.S. Raid Log — roteiro do gibi (português)

Uma edição por release: o arquiteto e o desenvolvedor conversando sobre o que
de fato aconteceu naquela versão, de forma simplificada. O roteiro em inglês,
`script.en.md`, conta a mesma história, quadro a quadro. O desenho é feito
fora daqui, numa ferramenta própria para quadrinhos.

## Guia da série

**Regra da verdade.** O diálogo é simplificado, nunca inventado na essência.
Todo chefão é um bug ou limite real daquela versão, toda habilidade é um
recurso real, toda fala do Dono é uma decisão real do usuário.

| Personagem | Aparência | Voz |
|---|---|---|
| **J.A.R.V.I.S.** | robozinho redondo azul-marinho, um olho grande ciano brilhante (o ícone do app), antena curta com ponta amarela, braços e pernas curtos | suas próprias linhas de log, num balão escuro de terminal com letra ciano monoespaçada |
| **Front** e **Back** | dois drones-olho voadores, esferas azul-marinho com olho ciano e hélice — as duas câmeras | nenhuma |
| **O Dev** | um castor de capacete amarelo | balões brancos comuns; constrói coisas |
| **O Arquiteto** | uma coruja de óculos redondos dourados | balões brancos comuns; trabalha de madrugada, com lanterna ou pergaminho |
| **O Dono** | **nunca desenhado**; uma voz de fora do quadro | balão dourado com a etiqueta "O DONO" |
| **Chefões** | cada um desenhado como o que é (um portão, um fantasma, um relógio…) | balões pretos, letras vermelhas maiúsculas |

**Estilo:** contornos pretos grossos, cores chapadas, retícula, letreiramento
de gibi. Cenas noturnas em azul profundo; perigo em vermelho escuro; cenas
internas em creme quente. A saída literal do sistema (linhas de log, mensagens
de erro, `person 0.72`, os nomes das câmeras Front e Back) é escrita
exatamente como o sistema imprime, em inglês.

**Cada edição:** uma capa, três ou quatro capítulos de até seis quadros e uma
ficha final. Termina num gancho que abre a edição seguinte.

---

## Edição nº 1 — O Primeiro Turno da Noite

`v2026.10.09` · 24 set – 9 out 2026 · 52 commits · 2 câmeras · 1 casa

### Capa

Noite. Uma casa roxa num morro, sob a lua cheia. J.A.R.V.I.S. em pé na
cumeeira do telhado, olho aceso. Front e Back pairam à esquerda e à direita
da casa, cada um projetando um cone de luz pálida no chão, com os rótulos
FRONT e BACK. A coruja espia no canto inferior esquerdo, o castor no inferior
direito.
Título: **J.A.R.V.I.S.** — faixa: **RAID LOG** — selo: **EDIÇÃO #1**.
Faixa inferior: **O Primeiro Turno da Noite**.

### Capítulo 1 — O Portão das Assinaturas

**Quadro 1 (largo).** Sala aconchegante. O castor numa mesa com monitor e uma
torre preta pequena com o rótulo M900; uma caneca de café fumegando. Numa
prateleira, os dois drones dormindo, com os rótulos FRONT e BACK.
LEGENDA: 24 de setembro de 2026. Duas câmeras Tapo, um Lenovo M900 — e um
construtor.
DEV: Movimento, YOLO, clipes… tudo roda no PC grande. Agora, no M900—

**Quadro 2.** Vermelho escuro. Um portão de pedra com grades e um escudo azul
com SAC (Smart App Control). O castor, pequeno, carrega uma mochila laranja
enorme escrita PyTorch.
CHEFÃO (o portão): DLLs SEM ASSINATURA NÃO PASSARÃO!
DEV: Mas o PyTorch tem só dois gigabytes…

**Quadro 3.** Céu claro, grama verde. A mochila PyTorch jogada de lado, com
linhas de movimento. O castor segura orgulhoso uma ferramentinha verde escrita
cv2.dnn, brilhando.
DEV: Então viajamos leves: YOLO pelo próprio dnn do OpenCV. Nada de PyTorch.

**Quadro 4.** Noite. J.A.R.V.I.S. à esquerda projeta um feixe pálido; um
enxame de mosquitos zumbe dentro dele.
LEGENDA: 26 set. A primeira noite lá fora.
CHEFÃO (o enxame): BZZZ! TODA ASA É UM INVASOR!
J.A.R.V.I.S.: Visto em vários quadros seguidos, ou não aconteceu.

**Quadro 5.** Noite. O portão de novo, o arco agora aberto e iluminado. O
castor ergue um pergaminho: "python.org — ASSINADO: PSF", com lacre vermelho.
A coruja aparece pela primeira vez, ao lado do portão.
LEGENDA: 9 out. Depois de nove dias parado, o portão se ergue de novo — agora
contra o Python do próprio uv.
CHEFÃO (o portão): ASSINADO. PODE PASSAR.
ARQUITETO: Primeira revisão, primeiro achado: a nossa própria crônica estava
errada. Leia a linha inteira do log, não só a palavra "python".

### Capítulo 2 — Olhos, Rostos e Aviões de Papel

**Quadro 1.** Vermelho escuro. Os dois drones puxam entre si um único cérebro
rosa com o rótulo NET; raios. O castor embaixo.
LEGENDA: Duas threads, uma rede neural.
CHEFÃO: buf.shape() == m.shape()… CRASH!
DEV: Cada thread com o seu cérebro. Os rostos esperam a vez.

**Quadro 2.** Sala aconchegante. J.A.R.V.I.S. sob um leque de três cartões de
rosto; o do meio tem uma etiqueta amarela: DONO.
O DONO: Dê nome a um rosto uma vez — e reconheça-o para sempre.
J.A.R.V.I.S.: galeria: unida pelo nome.

**Quadro 3.** Noite. Dois aviões de papel voam por uma linha tracejada da casa
até um celular. Na tela: uma foto com "Front: person" e depois um rosto com
"Front 20:23: probably Dono". A coruja embaixo do celular.
LEGENDA: Então o celular aprendeu a tocar.
ARQUITETO: Abaixo de 0.45 ele diz "probably". Humildade também é recurso.

**Quadro 4.** Sala aconchegante. Uma janela grande de navegador, endereço
`http://<M900>:8765`, dois quadros ao vivo (FRONT, BACK) com bolinhas vermelhas
LIVE, cartões embaixo. O castor ao lado, com uma chave inglesa.
O DONO: Não quero duas formas de acesso. Tudo na web, um serviço só.
DEV: FastAPI + MJPEG: agora a janela é o navegador.

**Quadro 5 (largo).** À esquerda: outro computador, com o rótulo PC 2, tela
vermelha com "Invalid HTTP request". Um arco vermelho tracejado escrito
https:// com um X vermelho; uma seta verde contínua escrita http:// chegando à
casa à direita, onde está J.A.R.V.I.S. A coruja no meio.
LEGENDA: No outro computador: um erro.
ARQUITETO: Seu navegador bateu com https://. Esta casa atende em http://.
O DONO: Digitei http:// — funcionou!

### Capítulo 3 — Gêmeos, Juramentos e Maldições

**Quadro 1.** Noite. Um J.A.R.V.I.S. grande com o crachá "PROD · stream1 · HD"
e um gêmeo pequeno com o crachá "[TEST] · stream2 · 640×360".
O DONO: Uma cópia sempre de guarda. Outra para treinar.
LEGENDA: A câmera dá o stream1 a um só — o stream2, a muitos.

**Quadro 2.** Dia. Uma lápide de pedra cinza gravada ARQUIVOS / GERADOS /
NUNCA / QUEBRAM. A coruja com um cinzel.
O DONO: Nunca quebre o que uma versão antiga escreveu.
ARQUITETO: Gravado. O check_data relê todos os arquivos antes e depois de cada
atualização.

**Quadro 3.** Roxo escuro. Um pergaminho escrito config.json; um fantasma sai
dele com "U+FEFF" na barriga. O castor com uma lupa.
CHEFÃO (o fantasma): ESCONDIDO NO BYTE ZERO, FIZ SUA CONFIG INTEIRA SUMIR!
DEV: utf-8-sig. Agora eu te vejo.

**Quadro 4.** Noite. A coruja com uma lanterna. Dois J.A.R.V.I.S. idênticos
disputam um único capacete amarelo escrito PORTA 8765.
LEGENDA: Revisão 2, tarde da noite.
ARQUITETO: Dois lançamentos no mesmo instante viram a porta livre. Tome-a num
só movimento: SO_EXCLUSIVEADDRUSE.

**Quadro 5.** Vermelho escuro. Um monstro-relógio bravo com "72h" no
mostrador. A coruja embaixo.
CHEFÃO (o relógio): A CADA TRÊS DIAS, EU ENCERRO A VIGÍLIA!
ARQUITETO: Limite de tempo: nenhum. E para as quedas, um tambor a cada 5
minutos.

**Quadro 6.** Uma janela azul do PowerShell: `PS> .\production.ps1` e, em
vermelho, "The string is missing the terminator: '." Um travessão amarelo
minúsculo, com olhos e perninhas, atravessa a tela rindo. O castor à direita.
CHEFÃO (o travessão): HI HI! O POWERSHELL 5.1 ME LÊ COMO ASPAS DE FECHAMENTO!
DEV: Só ASCII. Adeus, travessão.

### Capítulo 4 — O Primeiro Turno da Noite

**Quadro 1.** Entardecer, do roxo ao rosa. Uma grande etiqueta de bagagem
amarela com v2026.10.09. O castor comemora; a coruja, orgulhosa.
ARQUITETO: Primeira release. A produção só roda tags.

**Quadro 2.** Vermelho escuro. J.A.R.V.I.S. tombando; uma placa riscada diz
QUEBRADA; grandes setas amarelas de rebobinar ◀◀.
LEGENDA: Ensaio geral: uma atualização quebrada de propósito.
J.A.R.V.I.S.: health check falhou. voltando à versão anterior… Front: ok.
Back: ok.

**Quadro 3 (largo).** Noite, estrelas, lua. J.A.R.V.I.S. na cumeeira; Front e
Back saem voando com cones de luz.
LEGENDA: 9 de outubro, 20:20:55. A produção entra no ar.
J.A.R.V.I.S.: Starting 2 camera(s) on stream1… / Back: ok / Front: ok /
Surveillance running.
J.A.R.V.I.S.: primeira noite: 19 eventos, 0 erros.

**Quadro 4.** Visual cinza de infravermelho. Uma silhueta escura sai
carregando uma caixa de entrega; um husky branco vai atrás. Um drone acima,
com um ponto vermelho REC.
LEGENDA: 22:29. O Dono sai para buscar uma entrega…
J.A.R.V.I.S.: evento: Front. 56 s — saída, portão e volta.

**Quadro 5.** Close dramático: o olho enorme de J.A.R.V.I.S. ocupa o lado
esquerdo, encarando uma miniatura à direita — o cachorro branco deitado num
tapete escuro, dentro de uma caixa verde com "person 0.72".
J.A.R.V.I.S.: …person?
LEGENDA (faixa preta): CONTINUA — EDIÇÃO #2: O CACHORRO COM CARA DE GENTE

### Ficha final — Raid Log, Edição nº 1

**Habilidades desbloqueadas**
- **Olhos Pacientes** — movimento pelo MOG2, só aceito quando dura vários
  quadros; YOLO11 pelo cv2.dnn, sem PyTorch.
- **Memória para Rostos** — o YuNet encontra, o SFace reconhece; rosto nomeado
  uma vez fica nomeado para sempre.
- **Aviões de Papel** — Telegram com a foto, depois o rosto e o nome, e
  "probably" quando há dúvida.
- **Uma Janela em Qualquer Lugar** — uma página web para ao vivo e gravações,
  em qualquer computador da casa.
- **Nunca Dorme** — um serviço sem janela, iniciado pelo Windows, de volta em
  até 5 minutos após uma queda.
- **Treino de Gêmeos** — produção em HD no stream1, uma cópia de teste no
  stream2.
- **Juramento dos Pergaminhos Inteiros** — todo arquivo de uma versão antiga é
  relido antes e depois de cada atualização.
- **Vira-Tempo** — a atualização que falha no health check devolve sozinha a
  versão anterior.

**Chefões derrotados:** O Portão das Assinaturas (Smart App Control, duas
vezes) · O Enxame de Mosquitos · A Rede de Duas Cabeças (um modelo, duas
threads) · A Crônica Falsa (nossa própria história, errada) · O BOM Invisível ·
O Gêmeo que Subiu Duas Vezes · A Maldição das 72 Horas · O Travessão.

**Ainda à espreita:** janelas pretas que abrem sozinhas (R15) · o cachorro no
tapete (R18) · um rosto que passou rápido demais (R20).

**Os decretos do Dono**
- "Tudo na web, um serviço só." — sem segunda porta de entrada, 9 out
- "Deixe a porta aberta para a rede de casa." — acesso pelo outro computador,
  R4
- "Uma cópia de guarda, outra para treinar." — produção e teste, backlog 17
- "Nunca quebre o que já foi escrito." — mudanças aditivas, ou uma migração
- "Só a nossa conversa fica em português." — código, docs e telas em inglês
- "O Dev constrói. O Arquiteto registra." — o HANDOFF.md entre os dois

**O grupo:** O Dev — Claude, high; constrói, testa, entrega. O Arquiteto —
Claude, ultracode; revisa de madrugada, cuida dos registros. J.A.R.V.I.S. —
dois olhos, uma casa, guiado por cada decisão do Dono.

**Números:** 16 dias · 52 commits · 2 revisões · 1 release · primeira noite: 19
eventos.

**Próxima:** Edição nº 2 — O Cachorro com Cara de Gente (`v2026.10.10`).
