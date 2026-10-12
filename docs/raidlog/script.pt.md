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

---

## Edição nº 2 — O Cachorro com Cara de Gente

`v2026.10.10` · 10 out 2026, uma noite longa

### Capa

Close na tela de um celular mostrando a foto de uma notificação: o cachorro
branco dormindo no tapete escuro, uma caixa verde em volta escrita
"person 0.72". Refletido na tela, o olho de J.A.R.V.I.S., intrigado. Selo:
**EDIÇÃO #2**.

### Capítulo 1 — O Caso do Dono Desaparecido

**Quadro 1.** Noite, a casa. A coruja numa mesa, lanterna acesa, logs
desenrolados.
O DONO: Saí para buscar uma entrega e voltei. Não fui gravado — nem na ida,
nem na volta!
ARQUITETO: Primeira noite da produção: 19 eventos, nenhum erro. Vamos ver.

**Quadro 2.** A área de trabalho do Dono: duas janelas pretas de console
ficam abertas, outras piscam e somem. Os títulos dizem
"…site-packages\imageio_ffmpeg…".
O DONO: E essas janelas não param de aparecer.
ARQUITETO: São o ffmpeg das câmeras. Não feche — você cortaria uma câmera.

**Quadro 3.** A coruja assiste a dois vídeos lado a lado: o clipe do app Tapo e
o da produção. A mesma cena: o Dono saindo, o portão, a volta com uma caixa.
ARQUITETO: Você foi gravado. Ida e volta. Cinquenta e seis segundos.

**Quadro 4.** O cartão do evento no navegador: a foto é o cachorro no tapete.
ARQUITETO: Mas a foto é o primeiro quadro do evento — e quem o começou foi o
cachorro, vestindo a etiqueta de pessoa.

**Quadro 5.** Uma tira de filme com noventa quadros; só quatro brilham em
verde.
ARQUITETO: E o seu rosto ficou de frente e grande o bastante em só 4 de 90
quadros. A varredura lia um em catorze. Perdeu todos.

### Capítulo 2 — A Noite do Construtor

**Quadro 1.** O castor com lanterna no capacete, cinco tarefas presas num
quadro.
DEV: Primeiro as janelas. CREATE_NO_WINDOW em todo ffmpeg.
CHEFÃO (um enxame de janelinhas pretas): A GENTE ABRE QUANDO QUISER!
DEV: Não mais.

**Quadro 2.** Um avião de papel arrastando uma URL comprida; dentro da URL,
uma chave brilhando.
CHEFÃO (a chave): TODA MENSAGEM DE ERRO ME CARREGA — /bot<token>/!
DEV: Censurada onde você entra. E toda mensagem agora deixa uma linha no log.

**Quadro 3.** J.A.R.V.I.S. folheia quadros como um fotógrafo e escolhe um: o
Dono, em pé, carregando a caixa.
J.A.R.V.I.S.: best view: person, standing. Saved as .best.jpg.

**Quadro 4.** A varredura fica densa nos momentos em que uma pessoa foi vista:
os quadros brilham onde o Dono caminha.
J.A.R.V.I.S.: face found. probably Dono.

**Quadro 5.** Um pergaminho escrito config.json, protegido sob uma redoma de
vidro.
DEV: E os ajustes que esta versão não conhece são mantidos, não apagados.

### Capítulo 3 — Duas Formas de Cair

**Quadro 1.** A produção no telhado, uma tag nova: v2026.10.10. Nenhuma janela
na área de trabalho lá embaixo.
LEGENDA: 00:56. A atualização leva dez segundos.

**Quadro 2.** A casa escurece, depois as luzes voltam.
LEGENDA: 00:58. O Dono reinicia a máquina.
J.A.R.V.I.S.: Back: ok. Front: ok. (59 s depois do Windows)

**Quadro 3.** A mão do Dono (só a mão) clica em "Finalizar tarefa" no
"Python" do Gerenciador de Tarefas. J.A.R.V.I.S. desaba.
LEGENDA: 01:01. O Dono puxa o fio de propósito.

**Quadro 4.** Um grande tambor escrito "a cada 5 minutos" bate; J.A.R.V.I.S.
se levanta de novo.
LEGENDA: 01:06. O tambor o traz de volta.
ARQUITETO: Reboot ou queda: ele volta sozinho.

**Quadro 5.** A coruja olha um cronômetro marcando "45 s" sobre a nuvem de
pensamento da varredura, enquanto os drones continuam vigiando lá fora.
ARQUITETO: Quarenta e cinco segundos de raciocínio por varredura de rosto…
nos mesmos quatro núcleos que vigiam as câmeras?
LEGENDA (faixa preta): CONTINUA — EDIÇÃO #3: OS INSTRUMENTOS DO VIGIA

### Ficha final — Raid Log, Edição nº 2

**Habilidades desbloqueadas:** **Maquinário Silencioso** — sem janelas de
console (R15) · **Boca Fechada** — o token do bot nunca vira texto (R16) ·
**O Melhor Ângulo** — a foto do evento é a melhor vista da pessoa (R19) ·
**Leitor Paciente** — a varredura lê denso onde houve pessoa (R20) · **Memória
Longa** — ajustes de uma versão nova sobrevivem a uma antiga (R11) ·
**Inquebrável** — volta depois de reboot e de queda (R13).

**Chefões derrotados:** O Enxame de Janelas · A Chave na URL · O Rosto
Perdido.

**Ainda à espreita:** o cachorro no tapete, agora duas mensagens falsas por
evento (R18) · o custo de uma varredura de 45 s (R21).

**Os decretos do Dono:** "Prepare a sessão do Dev; quem prioriza é você, me
diga os critérios." · "Conte quantas sessões cabem numa janela de tokens." ·
"Quero ver a versão vigente em algum lugar." · "Pese o custo antes de
desenhar."

**Números:** 6 correções · 1 release · 1 reboot e 1 queda, os dois superados.

**Próxima:** Edição nº 3 — Os Instrumentos do Vigia (`v2026.10.10.2`).

---

## Edição nº 3 — Os Instrumentos do Vigia

`v2026.10.10.2` · 10 out 2026, antes do amanhecer

### Capa

O castor numa bancada construindo instrumentos: um contador de quadros com
ponteiro, uma lente de aumento num tripé, uma plaquinha de latão gravada com
um número de versão. J.A.R.V.I.S. observa, curioso. Selo: **EDIÇÃO #3**.

### Capítulo 1 — Meça Antes de Escolher

**Quadro 1.** Um mostrador escrito "quadros por minuto" no peito de
J.A.R.V.I.S.; o ponteiro mal se mexe durante a varredura.
DEV: Cena parada: 584 quadros por minuto, 578 durante uma varredura. Tudo bem.

**Quadro 2.** Um segundo mostrador escrito YOLO: o ponteiro vai para o
vermelho.
DEV: Mas o YOLO vai de 280 para 454 milissegundos durante uma varredura.

**Quadro 3.** O castor gira um botão escrito "threads: 1"; os dois mostradores
pioram.
DEV: Menos threads para a varredura? O botão é compartilhado — o YOLO fica
mais lento também.
LEGENDA: Parecia obviamente certo. A medição disse que não.

**Quadro 4.** A coruja, de noite, com uma lista de cinco opções, quatro
riscadas.
ARQUITETO: A varredura pausa entre os quadros sempre que uma câmera estiver
gravando. A colisão só importa durante um evento — então é ali que a gente a
tira.

### Capítulo 2 — Instrumentos

**Quadro 1.** Uma plaquinha de latão no canto da página web diz
v2026.10.10.2.
O DONO: Quero ver a versão vigente em algum lugar.
DEV: git describe, uma vez ao iniciar. A produção mostra a tag dela.

**Quadro 2.** Um diário de bordo: "face scan 22-29-22.mp4: dense 7.3-15.7 s,
36.3-42.1 s, 162 frames, 23.1 s, 3 face view(s)".
J.A.R.V.I.S.: agora eu anoto onde olhei.

**Quadro 3.** A máquina de replay: o clipe das 22:29 passa por ela; uma fita
imprime motivos — "too short", "static spot", "no motion overlap".
DEV: Cada quadro, e por que foi mantido ou descartado.

**Quadro 4.** Na tela do replay: a caixa do cachorro, bem larga, encostando na
borda de baixo; ao lado, a caixa do Dono, alta e estreita.
DEV: O cachorro é três ou quatro vezes mais largo que alto. Toda pessoa de
verdade é mais alta que larga.
O DONO: Deixa ele dormir por enquanto. Depois.

**Quadro 5.** A coruja devolve os desenhos do castor como um roteiro escrito.
O DONO: Não desenhe o gibi. Escreva o roteiro — eu desenho com uma ferramenta
própria.
ARQUITETO: Mais barato, e só o roteiro precisa saber o que aconteceu de
verdade.

**Quadro 6.** Noite. O cachorro ainda dorme no tapete, um olho meio aberto.
Uma caixa verde pisca em volta dele.
LEGENDA (faixa preta): CONTINUA — EDIÇÃO #4

### Ficha final — Raid Log, Edição nº 3

**Habilidades desbloqueadas:** **O Pulso** — quadros analisados por minuto, no
`/api/status` (R21) · **Plaquinha** — a versão vigente na página (backlog 18) ·
**O Diário de Bordo** — onde cada varredura de rosto olhou (R22) · **O
Replay** — `tools/replay.py`, por que cada quadro foi mantido ou descartado
(R17) · **Fala Clara** — o código fala inglês, a janela antiga inclusive
(R10).

**Chefões derrotados:** A Resposta Óbvia e Errada (menos threads).

**Ainda à espreita:** o cachorro no tapete (R18, esperando o Dono) · a
varredura que colide com os eventos (R23, decidida, a construir).

**Os decretos do Dono:** "Mostre a versão vigente." · "Escreva o roteiro do
gibi, não o desenho." · "Antes de me devolver uma decisão, procure uma solução
melhor."

**Próxima:** Edição nº 4.

---

## Edição nº 4 — A Casa Ganha uma Recepção

`v2026.10.10.3` · 10 out 2026, à tarde

### Capa

Dentro da janela do navegador, J.A.R.V.I.S. atrás de um pequeno balcão de
recepção. Atrás dele, duas portas novas com placas: PEOPLE e SETTINGS. O
cachorro dorme no tapete na frente do balcão, finalmente sem caixa verde.
Selo: **EDIÇÃO #4**.

### Capítulo 1 — Dar Licença

**Quadro 1.** A varredura de rosto, desenhada como uma bibliotecária lendo uma
pilha de quadros, para e põe um marcador quando a luz vermelha REC de um drone
acende.
DEV: Enquanto alguma câmera grava, a varredura espera entre os quadros.

**Quadro 2.** O mostrador do YOLO da Edição nº 3 sai do vermelho.
DEV: 590 milissegundos durante uma varredura. 342 com ela pausada — quase tão
rápido quanto sozinho.

**Quadro 3.** A tela do replay: o cachorro branco sentado no tapete, a caixa
com o rótulo "2.4".
DEV: O cachorro senta, e a caixa deixa de ser tão larga. Com 2,5 ele escapava.
ARQUITETO: Pessoas de verdade medem de 0,4 a 0,6. Use 2,0 — a folga continua
sendo de quatro vezes.

**Quadro 4.** O cachorro boceja no tapete; nenhuma caixa em volta.
J.A.R.V.I.S. faz joinha.
J.A.R.V.I.S.: wide at the bottom edge — dropped. Em 25 eventos, todo descarte
foi o tapete.

### Capítulo 2 — A Recepção

**Quadro 1.** A porta PEOPLE abre para uma parede de cartões de rosto, cada um
com um campo de nome.
DEV: People na web. Digite um nome; o mesmo nome duas vezes junta os dois.

**Quadro 2.** A porta SETTINGS: um pequeno cofre com uma fenda de moeda
escrita TOKEN — as coisas entram, nada sai.
DEV: O token pode ser gravado, nunca lido de volta. Qualquer um no Wi-Fi
consegue abrir esta página.

**Quadro 3.** Dois carregadores levando a mesma caixa em direções opostas,
com os rótulos "web" e "Housekeeper".
DEV: E nada de botão "Archive now": dois carregadores na mesma pilha de
arquivos é como caixas se perdem.

**Quadro 4.** O balão dourado do Dono entra de fora do quadro, apontando para
um cartão de rosto sem nome.
O DONO: Às vezes o meu próprio rosto chega sem nome. Quero poder dizer "este
também sou eu" — e o mesmo para os cachorros.
ARQUITETO: Rostos, sim: a junção já existe, falta uma lista para escolher.
Cachorros precisam de uma camada nova antes.

**Quadro 5.** Noite. A coruja passa pela recepção e para: nenhuma tranca na
porta, uma chave pendurada no gancho para quem quiser.
ARQUITETO: Qualquer um no Wi-Fi pode renomear um rosto aqui… ou uma página
que você abrir pode fazer isso por ele.
LEGENDA (faixa preta): CONTINUA — EDIÇÃO #5: A TRANCA DA RECEPÇÃO

### Ficha final — Raid Log, Edição nº 4

**Habilidades desbloqueadas:** **Boas Maneiras** — a varredura de rosto dá
licença durante os eventos (R23) · **O Cachorro Dormindo** — "pessoa" larga na
borda de baixo é o tapete (R18) · **Recepção** — People e Settings na web
(estágio 4) · **Cofre de Mão Única** — o token só é gravado, nunca lido.

**Chefões derrotados:** A Colisão · O Cachorro que Sentou.

**Ainda à espreita:** a recepção sem tranca (R24) · uma junção não pode ser
desfeita (backlog 9) · nenhuma identidade para os cachorros (item 15).

**Os decretos do Dono:** "Você define a regra do cachorro." · "Um rosto meu
que não foi reconhecido deve poder ir para o meu nome — e o mesmo para os
cachorros."

**Próxima:** Edição nº 5 — A Tranca da Recepção.

---

## Edição nº 5 — A Tranca e o Álbum

`v2026.10.10.4` · 10 out 2026, fim de tarde

### Capa

A coruja instala uma pequena fechadura com teclado na porta da recepção. Atrás
do balcão, J.A.R.V.I.S. segura aberto um álbum cheio de fotos de rostos.
Selo: **EDIÇÃO #5**.

### Capítulo 1 — A Tranca

**Quadro 1.** O castor na bancada, levantando a pata a cada poucos segundos;
acima dele, uma pilha de cartõezinhos "Posso?".
DEV: Posso? … Posso? … Posso?
O DONO: Cinco vezes seguidas! Isso é absurdo!

**Quadro 2.** A coruja lê um pergaminho comprido de comandos, todos começando
com `cd`.
ARQUITETO: 124 comandos começavam com um cd para a pasta em que a gente já
estava. Era isso que pedia autorização. Não mais.

**Quadro 3.** Uma página estranha tenta passar um bilhete por baixo da porta
da recepção; a porta só abre para bilhetes carimbados "X-Jarvis-Request".
DEV: Toda mudança precisa do nosso carimbo. Uma página estranha não consegue
carimbar.

**Quadro 4.** O celular de uma visita é barrado no balcão; o outro computador
do Dono digita um PIN curto uma única vez e entra.
DEV: De outro aparelho, um PIN — definido no M900, digitado uma vez.

### Capítulo 2 — O Álbum

**Quadro 1.** A página People: uma grade arrumada de rostos com nome; embaixo,
uma fileira dos sem nome, cada um com um botão "Belongs to…".
DEV: People por pessoa agora. E um rosto desconhecido entra num nome com um
clique.

**Quadro 2.** A página do Dono aberta como um álbum: fileiras de fotos de
rosto, uma marcada com uma lixeirinha; uma fila curta de fotos espera na
borda.
DEV: Quarenta vistas. Tire uma, e a próxima da fila entra no lugar.

**Quadro 3.** Uma caixa de renomear: "Izabel" digitado sobre "Gustavo"; um
aviso amarelo aparece: "This will merge with Izabel — continue?"
DEV: Um nome que já é de outra pessoa pergunta antes. 409: conflito.

**Quadro 4.** Um cartão de gravação na aba Recordings, com uma linha nova:
"People: Gustavo · Animals: dog".
J.A.R.V.I.S.: agora cada gravação diz quem estava lá.

**Quadro 5.** Dois carregadores levam a velha janela do OpenCV para fora da
casa, como uma TV antiga.
LEGENDA: A janela antiga se aposenta. A página web é a única porta.

**Quadro 6.** A mão do Dono varre da mesa os cartões de rosto antigos.
O DONO: Apague os rostos antigos. Eu cadastro a gente de novo — desta vez com
foto.

**Quadro 7.** A coruja estuda um gráfico: 21 varreduras de rosto, 2 com rosto,
1 mensagem.
O DONO: Tô recebendo menos mensagens com rosto… é impressão minha?
ARQUITETO: Em parte, de dia os rostos são raros mesmo. Mas um deles se perdeu
no cooldown.
LEGENDA (faixa preta): CONTINUA — EDIÇÃO #6

### Ficha final — Raid Log, Edição nº 5

**Habilidades desbloqueadas:** **O Carimbo e o PIN** — toda alteração
protegida (R24) · **O Álbum** — People por pessoa, 40 vistas com foto e uma
fila (backlog 19) · **Chamada** — quem aparece em cada gravação (backlog 20) ·
**Uma Porta Só** — a janela do OpenCV aposentada.

**Chefões derrotados:** Os Cem "Posso?" · O Bilhete Falsificado.

**Ainda à espreita:** um rosto perdido no cooldown (R25) · uma junção não pode
ser desfeita (backlog 9) · nenhum teste protege o álbum (R6).

**Os decretos do Dono:** "People por pessoa, com todas as minhas fotos." ·
"Quero poder renomear uma pessoa." · "Apague os rostos antigos, sem backup." ·
"Parem de me pedir autorização."

**Próxima:** Edição nº 6.

---

## Edição nº 6 — A Rede de Proteção

`v2026.10.10.5` · 10 out 2026, começo da noite

### Capa

Embaixo do álbum de fotos de J.A.R.V.I.S., o castor estica uma grande rede de
proteção com 23 nós, cada nó um pequeno visto verde. Selo: **EDIÇÃO #6**.

### Capítulo 1 — O Rosto Perdido, Encontrado

**Quadro 1.** Um cartão de rosto preso atrás de uma catraca escrita
"cooldown 2 min".
ARQUITETO: A catraca é para eventos repetidos, não para rostos. Rostos são
raros.

**Quadro 2.** A catraca agora tem um portãozinho lateral com um ícone de
rosto; o cartão passa. Um pequeno cronômetro por pessoa pendurado no portão.
DEV: Um rosto encontrado sempre é enviado — mas a mesma pessoa só uma vez por
cooldown.

### Capítulo 2 — A Rede

**Quadro 1.** O castor dá nós na rede: "40 vistas", "a fila", "junção", "a
tranca", "cooldowns".
DEV: Vinte e três testes. Rodam em três segundos, em pastas que somem depois.

**Quadro 2.** Um pacote suspeito chega à porta com a etiqueta "httpx2". A
coruja o examina com uma lupa: o remetente é o mesmo do antigo "httpx", e o
próprio Starlette pediu por ele.
ARQUITETO: Um nome a uma letra de um famoso é a cara de pacote falso. Este é
verdadeiro.

**Quadro 3.** O balão dourado do Dono vem de fora do quadro, apontando para o
álbum.
O DONO: Quero escolher qual das quarenta fotos é a minha favorita — a que
aparece na página People.
LEGENDA (faixa preta): A SEGUIR — EDIÇÃO #7

### Ficha final — Raid Log, Edição nº 6

**Habilidades desbloqueadas:** **Nenhum Rosto Fica Para Trás** — um rosto
encontrado sempre é enviado, uma vez por pessoa a cada cooldown (R25) · **A
Rede de Proteção** — 23 testes automáticos (R6).

**Chefões derrotados:** A Catraca · O Pacote Sósia (alarme falso, conferido).

**Ainda à espreita:** uma junção não pode ser desfeita (backlog 9).

**Os decretos do Dono:** "Quero escolher a minha foto favorita." (backlog 21)

**Próxima:** Edição nº 7.

---

## Edição nº 7 — A Favorita

`v2026.10.10.6` · 10 out 2026, à noite

**Quadro 1.** A página da pessoa: quarenta fotos de rosto; a mão do Dono toca
numa estrelinha em uma delas, e ela fica dourada.
O DONO: Esta. É assim que eu quero aparecer na página People.
DEV: A estrela lembra a foto em si, não a posição dela na fileira — então
continua certa quando outras vistas entram e saem.

**Quadro 2.** Um caminhão de mudança sai da casa com caixas escritas "pytest"
e "httpx2".
DEV: E a produção para de carregar as ferramentas de teste. --no-dev.

**Quadro 3.** O Dono, na rua, digitando no celular.
O DONO: Sem botão de desfazer. Só me avise antes de juntar, e se eu disser
sim, segue o baile.
ARQUITETO: Esse aviso já existia. Nada a construir.

**Ficha final.** Habilidades: **A Favorita** — uma foto escolhida por pessoa
(backlog 21) · **Bagagem Leve** — produção sem ferramentas de teste (R26).
Decretos: "Quero escolher minha foto favorita." · "Sem desfazer; me avise e
siga no sim." Próxima: Edição nº 8.
---

## Edição nº 8 — Mirana e Aurora

`v2026.10.10.7` · 10 out 2026, à noite

**Quadro 1.** A coruja ergue uma folha de recortes de cachorro em duas
fileiras, uma escura, uma branca. O balão dourado do Dono vem de fora do
quadro.
O DONO: Na primeira linha é a Mirana, a preta. Na segunda é a Aurora, a
branca. Mas cuidado — esse software não é só pra mim.

**Quadro 2.** O balão do Dono cresce.
O DONO: Nada de regra de cor no código. Me dá uma aba Dogs, e eu ensino as
minhas cadelas. Qualquer outro ensina as dele.

**Quadro 3.** O castor na bancada com uma tesoura, recortando um cachorro da
caixa — o tapete e o chão caem fora.
DEV: GrabCut: o cachorro, não a caixa. Depois uma impressão digital do pelo —
os tons, e as cores de dia.

**Quadro 4.** Duas balanças, uma escrita DIA, outra NOITE; a impressão de um
cachorro só é pesada na balança dela.
DEV: Dia com dia, infravermelho com infravermelho. Nunca misturado.

**Quadro 5.** Três notificações de celular lado a lado: "Front: Mirana",
"Front: probably Aurora", "Front: unidentified dog".
O DONO: O alerta é porque tem um cachorro. A certeza só muda as palavras.

**Quadro 6.** A aba Dogs nova, cheia de recortes sem nome se empilhando para
fora da tela; a coruja franze a testa.
ARQUITETO: Todo cachorro de que ele não tem certeza vira um cartão novo.
Trinta por dia…
LEGENDA (faixa preta): A SEGUIR — EDIÇÃO #9

**Ficha final.** Habilidades: **O Canil** — uma aba Dogs onde cada casa nomeia
os seus cachorros (backlog 22) · **Três Palavras** — nome, probably nome,
unidentified dog. À espreita: a pilha de cartões sem nome (R27); limites ainda
não testados com nomes reais. Decretos: "Nada de regra de cor no código." ·
"Notifique quando tiver cachorro; a certeza só muda as palavras."
---

## Edição nº 9 — A Recepção Aprende Modos

`v2026.10.11` → `v2026.10.11.3` · 11 out 2026

**Quadro 1.** O outro computador do Dono mostra uma cópia velha e amarelada da
página; um calendário na parede ainda marca "10 out".
O DONO: As telas falham no meu outro computador.
ARQUITETO: Seu navegador guardou o script de ontem. Sete releases depois, ele
batia em portas que não existem mais.

**Quadro 2.** Toda página agora leva um pequeno carimbo com a versão; o
navegador confere na porta a cada visita.
DEV: No-cache quer dizer "pergunte antes", não "não guarde". Um 304 rápido, e
nunca velho.

**Quadro 3.** Uma pessoa passa pela câmera, o rosto virado para a porta; o
detector desenha o rosto, e um filtro sisudo carimba "NÃO FRONTAL".
O DONO: Um monte de alerta de pessoa, quase nenhum rosto.
ARQUITETO: O rosto estava lá em 61 quadros — todos de lado.

**Quadro 4.** Um celular mostra "Front: face, side view" com uma foto de lado
nítida.
DEV: A foto de lado vai para o seu celular. Ela nunca ensina a galeria.

**Quadro 5.** Um crachá de visitante (um cookie) pendurado no notebook do Dono,
com um calendário marcando "30 dias" ao lado.
O DONO: Parem de pedir o PIN em todo aparelho.
DEV: Pareie uma vez. Trinta dias, renovados toda vez que você usa.

**Quadro 6.** Uma pequena tela de cinema abre dentro do cartão de Recordings;
o Dono assiste a um clipe do sofá, no celular.
O DONO: E eu não consigo ver as gravações de outro aparelho.
DEV: Nunca existiu uma porta de vídeo. Agora existe — e dá para avançar.

**Quadro 7.** A coruja acorda numa hora marcada e manda um avião de papel para
a oficina do castor; mais tarde o castor manda um de volta.
LEGENDA: 12:23. O primeiro ciclo que rodou sozinho.

**Ficha final.** Habilidades: **Sempre Fresca** (R28) · **De Lado** (R30 a) ·
**O Crachá** — pareie o aparelho uma vez (R34) · **O Cinema** — as gravações
tocam na página (item 5) · **A Matilha** — nomear um cachorro junta os
parecidos (R29) · **Partida Própria** — o Dev e o Arquiteto se passam a vez
sozinhos. À espreita: a Aurora enrolada no tapete ainda passa por pessoa de
vez em quando (R35). Decretos: "Olhe todo alerta de pessoa sem rosto." ·
"Pareie uma vez, ou 30 dias." · "Quero ver de qualquer aparelho." · "Comecem
a próxima sessão sozinhos."
---

## Edição nº 10 — A Caixa de Provas

`v2026.10.11.4` · 11 out 2026, à tarde

**Quadro 1.** A aba Dogs; entre os recortes, um é claramente o Dono. A mão do
Dono aperta um botão vermelho: "Bad detection".
O DONO: Alguns aqui nem são cachorro. Um sou eu.
DEV: Não apague — reporte. Vai para a caixa de provas, com de onde veio e o que
você disse.

**Quadro 2.** A coruja joga cinco fotos na mesa: pessoas agachadas, curvadas,
sentadas perto da câmera.
ARQUITETO: Um limite mais baixo teria chamado essas cinco de "o cachorro no
tapete". São pessoas. A regra fica.

**Quadro 3.** O castor espalha cem fotos de rosto e escolhe quarenta, cada uma
o mais diferente possível das outras.
DEV: Analyse: as quarenta vistas mais diferentes. Ângulos e luz, não quarenta
cópias.

**Quadro 4.** Um cronômetro: 137 ms vira 45 ms. Os drones seguem vigiando lá
fora, tranquilos.
DEV: Ache o rosto numa cópia pequena, refine na grande. Três vezes mais
rápido.

**Quadro 5.** A coruja segura dois cartões de rosto — "Gustavo" e um vazio com
um ponto de interrogação.
ARQUITETO: Rostos de lado batem com você na maioria das vezes. Para saber que
não bateriam com um estranho, preciso de um segundo nome.

**Ficha final.** Habilidades: **A Caixa de Provas** (backlog 23) · **As
Quarenta Melhores** (backlog 24) · **Olhos Rápidos** — varredura de rosto mais
barata (R31) · **Log Silencioso** (R32). Decidido contra: baixar o limite do
cachorro no tapete (R35). À espreita: um relato nunca diz o que a coisa era de
verdade (R37). Decretos: "Reporte, não apague — e lembre de qual tela veio."
## Edição nº 11 — Segunda Chance

`v2026.10.11.5` e `v2026.10.11.6` · 11 out 2026, noite

**Quadro 1.** Noite, azul profundo. Na porta da casa, o J.A.R.V.I.S. antigo
ainda carrega para fora uma caixa marcada CLIP enquanto o novo espera no
degrau; Front e Back pairam sobre os dois, cada um com uma plaquinha: BUSY. Um
cronômetro no canto marca 22 s.
LEGENDA: O primeiro deploy da `v2026.10.11.4`. A versão antiga ainda montava um
clipe quando a nova pediu as câmeras.
ARQUITETO: Ela mesma voltou atrás. De agora em diante a atualização espera até
nada rodar de C:\JARVIS — até três minutos.

**Quadro 2.** A página de uma pessoa: molduras vazias onde deviam estar as
fotos. Embaixo, uma gaveta fechada, vazando luz, cheia de fotos.
CHEFÃO (a gaveta): MESMO NOME, PRIMEIRO ACHADO!
ARQUITETO: Duas grades com a mesma classe, e a página encheu a primeira — a
escondida. Os testes só olhavam o servidor.

**Quadro 3.** O castor monta duas prateleiras, CHOSEN (40) em cima e WAITING
embaixo, com setas ↑ e ↓ pintadas entre elas.
O DONO: Fotos esperando só fazem sentido se eu puder comparar com as
escolhidas.
DEV: Lado a lado, então. Nada passa de uma para a outra sozinho — quem escolhe
é você.

**Quadro 4.** A caixa de provas da edição passada, aberta. Um cartão de
cachorro voa dela de volta para o álbum, arrastando suas fotos e seus
avistamentos como rabo de pipa.
LEGENDA: Alguns relatos daquela tarde foram engano.
DEV: Undo. Ele volta com as vistas, a favorita, os avistamentos. A caixa agora
guarda cópia de cada foto, então tem o que devolver.

**Quadro 5.** Um cartão de relato com o rosto do Dono, arquivado como "not a
dog". Um menu pequeno abre ao lado: "Actually…" — person.
DEV: E um relato enfim pode dizer o que a coisa era de verdade.

**Quadro 6.** O castor bate uma gaveta, uma entrada segura lá dentro; um drone
chega um instante tarde com mais uma foto e esbarra na gaveta fechada.
DEV: Primeiro tira, com a trava, depois escreve o relato. A varredura que chega
atrasada encontra a porta fechada — e nada se perde.

**Quadro 7.** Vermelho escuro. O portão de pedra da edição nº 1, o escudo azul
SAC de novo, agora barrando uma figurinha marcada `pytest.exe`. A coruja
contorna o portão segurando um pergaminho: `python -m pytest`.
CHEFÃO (o portão): LANÇADORES SEM ASSINATURA NÃO PASSARÃO!
ARQUITETO: Então o Python assinado roda os testes ele mesmo. Noventa e dois,
verdes.

**Ficha final.** Habilidades: **Segunda Chance** — desfazer um relato (R38) ·
**Escolhidas e Esperando** (R40) · **"Actually…"** (R37) · **A Porta Fechada**
(R36) · **O Deploy Paciente**. Chefões derrotados: **A Grade Escondida** (R39)
· **A Atualização Apressada** · **O Portão das Assinaturas**, de novo. À
espreita: com a fila cheia, um clique mirado numa foto pode cair na vizinha
(R41). Decretos: "Fotos esperando só fazem sentido se eu puder comparar com as
escolhidas."

## Edição nº 12 — A Casa Aprende Quem Mora Aqui

`v2026.10.12` · 12 out 2026, manhã

**Quadro 1.** Creme quente, interior. Um celular na mesa soterrado por uma
pilha de balões de mensagem que transborda para o chão, quase todos dizendo
"Gustavo recognized". A coruja os conta num pergaminho que se desenrola para
fora do quadro.
LEGENDA: Dois dias de produção: 143 mensagens. 34 nomearam um rosto — 21
delas, o Dono.
ARQUITETO: A casa vive anunciando quem mora nela.

**Quadro 2.** O castor prende um pequeno distintivo dourado, RESIDENT, em três
cartões: o do Dono (uma silhueta, nunca desenhado), Mirana (pelo escuro) e
Aurora (pelo claro).
DEV: Só quem tem nome. E só conta a certeza — "probably Gustavo" continua
tocando, porque pode ser outra pessoa.

**Quadro 3.** Um grande painel de interruptores na parede: sete linhas de
chaves, três colunas com as letras HOME, AWAY, SILENT. A coluna HOME está
acesa.
O DONO: Pessoa sem rosto reconhecível avisa em casa também. Um estranho no
escuro tem que chegar ao celular.
DEV: A gravação nunca muda. O modo só decide o que chega ao celular.

**Quadro 4.** Quadro dividido. À esquerda: um cachorro entra e um cronômetro
marca 0,1 s, uma plaquinha já na coleira: AURORA. À direita: uma pessoa entra,
e o drone Front leva o clipe para uma bancada com uma ampulheta em cima.
DEV: O cachorro tem nome desde o primeiro frame. A pessoa, só depois que o
clipe é varrido. Então, em Home, a mensagem da pessoa espera a varredura.

**Quadro 5.** Noite, azul profundo. A mão do Dono (só a mão) digita `/away` no
celular. Uma longa linha de pesca vai da antena do J.A.R.V.I.S. até uma nuvem
marcada TELEGRAM; a linha dá um puxão, e a lâmpada do painel salta para AWAY.
DEV: Nenhuma porta aberta. A gente pergunta, e o Telegram segura a linha até
chegar alguma coisa.
CHEFÃO (uma segunda linha de pesca, enroscada na primeira): DOIS LEITORES?
409!

**Quadro 6.** Vermelho escuro. A coruja, lanterna erguida, encontra um chefão
em forma de relógio sentado na vaga de mensagem da câmera. Atrás dele, uma
figura apagada, sem rosto, espera na porta sem ser anunciada; um balão do
cachorro já voou para o celular.
CHEFÃO (o relógio): O CACHORRO PEGOU A VAGA. VOLTE DAQUI A DOIS MINUTOS.
ARQUITETO: Mesmo evento, mesma visita. A mensagem da pessoa é continuação — o
intervalo vale para o próximo evento, não para este. E se o clipe não montar,
a melhor vista vai mesmo assim.

**Quadro 7.** A página de pessoa da edição nº 11, com a fila cheia. Um cursor
mira o × numa foto enquanto um drone enfia uma foto nova, empurrando a fileira
um passo para a esquerda. O × agora leva uma etiqueta com nome; o servidor
ergue uma placa: 409.
DEV: A página diz qual foto viu. Se ela mudou de lugar, nada é apagado — a
página recarrega.

**Cartão final.** Habilidades: **Morador** (backlog 25a) · **Home, Away,
Silent** (25b–d) · **O Painel de Interruptores** — a aba Notifications (25e) ·
**Comandos do Celular** (25f) · **O Clique com Nome** (R41). Chefões
derrotados: **O Intervalo Emprestado** · **O Silêncio do Clipe Perdido** ·
**A Vizinha que Escorrega** (R41). À espreita: em casa, o Dono sai com alguém
cujo rosto nunca aparece — e a varredura, achando só o Dono, não diz nada
(R42); e duas mãos escrevendo o `config.json` no mesmo instante (R43).
Decretos: "Um estranho no escuro tem que chegar ao celular."
