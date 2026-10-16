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

## Edição nº 13 — O Dono Não É Cachorro

`v2026.10.12.2` · 12 out 2026, noite

**Quadro 1.** Creme quente, interior. A aba Dogs numa tela grande: fileiras de
fotos de cachorro e, no meio delas, um recorte que é claramente as costas de
uma pessoa curvada na porta de um carro — uma silhueta, nunca desenhada —
etiquetado `dog 0.74`. Mais dois iguais.
O DONO: Eu tô sendo captado demais na aba Dogs.

**Quadro 2.** A coruja abre a caixa de provas da edição nº 10: seis
denúncias de cachorro. Quatro fotos são a mesma silhueta curvada. Um medidor
na caixa marca `person 0.00`.
ARQUITETO: Quatro de seis são você, abaixado. E o YOLO tem certeza — não sobra
nenhuma nota de pessoa naquela caixa.

**Quadro 3.** Close, duas caixas transparentes uma sobre a outra: uma caixa
`person`, desbotada, carimbada "2 s atrás", e a caixa `dog` de agora — quase o
mesmo retângulo. Ao lado, um cachorro de verdade aos pés de alguém: uma
caixinha dentro de uma caixa grande, mal se sobrepondo.
ARQUITETO: Mas a caixa não se mexeu. Dois segundos atrás, essa mesma caixa era
uma pessoa. Um cachorro aos seus pés nunca ocupa a sua caixa assim.

**Quadro 4.** O castor encaixa uma pequena ampulheta na lateral do
J.A.R.V.I.S., cheia de caixinhas de pessoa no lugar da areia.
DEV: Toda caixa de pessoa dos últimos dois segundos fica na memória. Uma caixa
de cachorro em cima de uma delas é aquela pessoa.
J.A.R.V.I.S.: `the person's box from a moment ago: dog 0.74`

**Quadro 5.** Noite, azul profundo. A coruja, lanterna erguida, passa num
pequeno projetor um filme de Mirana e Aurora sozinhas no quintal. Um contador
no projetor: `relabelled: 0`.
ARQUITETO: E um cachorro de verdade sem ninguém por perto? Seis clipes, 174
quadros de cachorro. Nenhum rebatizado.

**Quadro 6.** As fotos sem nome, agora separadas em pilhas com placas: "Looks
like Aurora (12)", "No guess". O castor toca nas fotos e elas acendem com
moldura verde; uma barra no rodapé diz "7 selected · Assign to… · Bad
detection · Clear".
O DONO: Selecionar várias fotos e dar todas a um cachorro — não "Belongs to…"
uma por uma.
DEV: Agrupadas pelo palpite do comparador. Só uma dica: o nome continua sendo
seu.

**Quadro 7.** Um arquivo de gavetas com a etiqueta SETTINGS; o castor encaixa
uma gaveta NOTIFICATIONS no topo, ao lado de DEVICES, ARCHIVE e REPORTS. Num
celular no canto, uma barra de abas larga demais para a tela empurra a barra
de baixo para fora da borda.
O DONO: Uma aba Notifications não é o ideal. Faz dela uma parte de Settings.
DEV: E no celular as abas agora quebram linha — a barra tinha caído para fora
da tela.

**Quadro 8.** Vermelho-escuro. Duas mãos — uma saindo da página web, outra de
uma nuvem do Telegram — puxam a mesma folha de papel, `config.json`,
rasgando-a. O chefão é a metade rasgada, acenando.
CHEFÃO (a folha rasgada): MEIO ARQUIVO! O TOKEN SUMIU!
DEV: Escreve uma cópia inteira nova e troca de uma vez. Um escritor por vez.
ARQUITETO (erguendo uma cópia esquecida achada debaixo da mesa, com a chave
ainda dentro): E esta cópia guarda o token. Ela nunca vai para o git.

**Cartão final.** Habilidades: **A Memória de Dois Segundos** (R44) ·
**Selecionar Várias** (backlog 26) · **A Gaveta de Settings** (backlog 27) ·
**A Troca do Arquivo Inteiro** (R43). Chefões derrotados: **O Cachorro
Curvado** (R44) · **Meio Arquivo** (R43) · **A Barra de Abas Fugitiva**. À
espreita: o Dono saindo de casa com alguém que nunca mostra o rosto ainda
espera a escolha do Dono (R42); e todo merge lê todos os avistamentos já
escritos — uma pilha que cresce cinquenta por dia (R45). Decretos:
"Notifications é parte de Settings."

## Edição nº 14 — Todo Nome em Inglês

`v2026.10.12.3` · 12 out 2026, noite

**Quadro 1.** Creme quente, interior. Uma estante de livros grossos cujas
lombadas ainda dizem ARQUITETURA, INSTALACAO, CONTEXTO, e uma fileira de
caixas de ferramentas estampadas `diagnostico`, `refazer_rostos`,
`gerar_epub`. O castor, com uma rotuladora na mão.
O DONO: Tudo em inglês, menos a nossa conversa.
DEV: As páginas estão em inglês desde hoje de manhã. As capas não.

**Quadro 2.** O castor descola ARQUITETURA de uma lombada e cola
ARCHITECTURE. Um fio dourado — a história do livro — sai da etiqueta velha e
entra na nova, sem se partir.
DEV: Só o nome novo neste commit, mais nada. O git continua sabendo que é o
mesmo livro.
ARQUITETO: E traduz as caixas de ferramentas no próximo. Um arquivo que troca
de nome e de palavras ao mesmo tempo parece um estranho.

**Quadro 3.** Um corredor de placas apontando para páginas de livros —
"ARCHITECTURE 18.7", "INSTALL 1.2", "PROCESS 3". Um pequeno robô inspetor
caminha batendo em cada uma; três placas brilham vermelhas, todas na
prateleira do HISTORY.
J.A.R.V.I.S.: `3 broken reference(s)`
DEV: As mesmas três antes e depois do rename. Frases antigas, não minhas.

**Quadro 4.** Noite, azul profundo. A coruja, lanterna erguida, reescreve
três linhas no livro HISTORY. A lâmpada do inspetor fica verde.
J.A.R.V.I.S.: `0 broken reference(s)`
ARQUITETO: Agora o inspetor percorre este corredor em toda revisão.

**Quadro 5.** Uma porta velha com a placa `jarvis_vigilancia.bat`; atrás
dela, um corredor curto até uma porta nova, `jarvis_headless.bat`. O castor
pendura um aviso na velha: MUDOU — SÓ MAIS UMA VERSÃO.
DEV: Quem ainda bater na porta velha é levado até a nova. Uma versão, depois
a porta velha sai.

**Quadro 6.** Vermelho-escuro. O chefão do cartão final da edição nº 13 se
ergue: uma montanha de cartões de avistamento com olhos, cinquenta a mais
caindo por cima todo dia. Cinco castores fantasmas escalam ao mesmo tempo,
cada um com uma foto.
CHEFÃO (a pilha): ME LÊ DE NOVO! E DE NOVO! E DE NOVO!
DEV: Cinco fotos para a Aurora, cinco escaladas por todos os cartões já
escritos.

**Quadro 7.** O castor, ao pé da pilha, anota numa prancheta — "a → Aurora,
b → Aurora, c → Aurora…" — e depois escala uma vez só, com um carimbo. A
pilha volta a ser um montinho.
DEV: Cada merge só anota quem foi para onde. O save escala uma vez.
ARQUITETO: Cinco leituras viraram uma. E uma corrente — a em b, depois b em
c — leva cada cartão direto para c.

**Cartão final.** Habilidades: **As Capas Novas** (R10) · **O Inspetor de
Placas** (`check_doc_refs.py`) · **Uma Escalada Só** (R45). Chefões
derrotados: **A Pilha Sem Fim** (R45) · **As Capas em Português** (R10). À
espreita: o Dono saindo de casa com alguém que nunca mostra o rosto ainda
espera a escolha do Dono (R42); zonas e um vigia de saúde são só propostas; e
depois de mais uma sessão o trabalho decidido acaba — a próxima página é o
Dono quem escreve.

## Edição nº 15 — A Assinatura na Porta

`v2026.10.12.4` · 12 out 2026, noite

**Quadro 1.** Creme quente, interior. A porta velha da edição nº 14, com a
placa `jarvis_vigilancia.bat`, o aviso MUDOU-SE juntando poeira. O castor
escuta nela com um estetoscópio; silêncio. Atrás dele, a porta de
`jarvis_headless.bat` está aberta.
DEV: Uma versão, e ninguém bateu. A tarefa de inicialização nunca a usou; o
atalho aponta para `jarvis.bat`.
SFX: CLUNC — a porta velha sai das dobradiças.

**Quadro 2.** Vermelho escuro. O portão de pedra da edição nº 1, o escudo
azul marcado SAC. Na estrada, uma figura fantasiada de Python — uma roupa de
cobra verde com um zíper nas costas — e sem selo de cera. Atrás dela, um
caixote com a etiqueta `winget` jaz arrombado.
LEGENDA: Quando o Python oficial não se instala, o uv traz o seu, em silêncio.
CHEFE (a fantasia): EU RODEI ONTEM! O PORTÃO ME CONHECE!
DEV: Até o dia em que não conhece — foi assim que o 9 de outubro começou.

**Quadro 3.** O castor constrói uma pequena guarita com uma lupa num suporte,
com a etiqueta `check_python.ps1`. Duas estradas chegam a ela: uma marcada
`install.bat`, outra marcada `production.ps1`.
DEV: Uma guarita, duas estradas. A regra mora num lugar só.
ARQUITETO (fora do quadro): Como levar código comum para uma biblioteca em
vez de copiá-lo duas vezes.

**Quadro 4.** Na guarita, duas figurinhas cinzentas sem selo — `jarvis.exe` e
`pytest.exe` — são mandadas de volta; uma figura alta com um selo de cera
dourado carimbado PSF passa com um aceno.
J.A.R.V.I.S.: `ERROR: C:\JARVIS\.venv\Scripts\jarvis.exe is not the signed python.org build (signature: NotSigned).`
J.A.R.V.I.S.: `python.exe is signed by the Python Software Foundation.`

**Quadro 5.** Noite, azul profundo. A coruja, de lanterna erguida, percorre a
estrada que a guarita não enxerga: antes dela, a fantasia já caiu no portão, e
a placa velha ali diz só "could not install the dependencies". A coruja prega
uma placa nova embaixo: WinError 4551? → INSTALL 1.2.
ARQUITETO: Tua guarita pega a fantasia que o portão ainda deixa passar. Quando o
portão já a barra, o viajante nem chega à guarita — então o portão ganha uma
placa também.

**Quadro 6.** O M900 à noite, dois drones pairando. Um pacote marcado
`v2026.10.12.4` passa pela guarita na estrada da produção; o carimbo brilha
verde.
J.A.R.V.I.S.: `pythonw.exe is signed by the Python Software Foundation.`
J.A.R.V.I.S.: `Production is running v2026.10.12.4.`
LEGENDA: Dez segundos de pausa; as duas câmeras de volta três segundos depois.

**Cartão final.** Habilidades: **A Guarita do Selo** (R7, `check_python.ps1`)
· **A Placa no Portão** (a mensagem do `uv sync` no instalador). Chefes
derrotados: **O Python Fantasiado** (R7) · **A Porta Velha** (o atalho
antigo). À espreita: o trabalho decidido acabou. A próxima página está em
branco, e só o Dono pode escrevê-la — zonas, um vigia de saúde, ou a segunda
pessoa que nunca mostra o rosto (R42).

## Edição #16 — O Botão de Desligar

`v2026.10.13` · 13 out 2026, noite

**Quadro 1.** Creme quente. A página em branco da edição #15, presa na
parede — agora coberta de letra dourada, seis pedidos. A coruja lê com a
lanterna; o castor segura a escada.
O DONO (balão dourado, fora do quadro): Eu não vi nenhum "provavelmente"
errado.
ARQUITETO: Então um "provavelmente" de quem mora aqui ganha um interruptor
só seu.

**Quadro 2.** Vermelho escuro. O chefe: uma faxineira curvada sobre um balde,
a sombra na parede com forma de cachorro. Acima dela, um adesivo descola da
caixa do YOLO: `dog 0.81`. A caixa desliza de lado enquanto ela esfrega,
deixando um rastro de contornos.
CHEFE: EU ME MEXO CURVADA! TEU 0.5 NÃO ME SEGURA!
LEGENDA: O R44 pegou a curvatura parada. A que se mexe manteve 13 caixas de
cachorro em cinco clipes.

**Quadro 3.** O castor numa mesa de luz, dois fotogramas lado a lado. No
primeiro, uma caixa alta marcada `person`; no segundo, a caixa alta sumiu e
uma caixa larga `dog` está sentada no lugar dela.
DEV: Um cachorro de verdade fica ao lado de uma pessoa que continua ali. Aqui
a pessoa sumiu, e a caixa de cachorro pegou a cadeira dela.

**Quadro 4.** O castor parafusa uma placa na cadeira vazia: "took the place
of a person who vanished". O J.A.R.V.I.S. lê em voz alta.
J.A.R.V.I.S.: `kept person 0.81 (581,356 164x180); took the place of a person who vanished: dog 0.81 (581,356 164x180)`
J.A.R.V.I.S.: `totals: {'frames': 722, 'frames with a subject': 555, 'person': 555}`

**Quadro 5.** Noite, azul profundo. A coruja segue a cadeira com a lanterna:
atrás dela, uma corrente de cadeiras iguais, cada uma segurando a próxima,
saindo pela borda do quadro.
ARQUITETO: Cada cadeira renova a próxima. Se um cachorro de verdade sentar
ali um dia, a corrente não acaba.
DEV: Doze cachorros de verdade, e nenhum sentou.
ARQUITETO: Então ficamos de vigia. R47.

**Quadro 6.** A porta da frente da casa, à noite. Uma carta marcada
"probably Gustavo" para num interruptor novo no batente, com a etiqueta
`probable_resident_person`, em OFF sob uma placa HOME. Uma carta marcada
"unknown face" passa direto.
LEGENDA: Em Casa, um provável morador fica em silêncio; Fora, ainda é
enviado. Um toque desfaz.

**Quadro 7.** O J.A.R.V.I.S. com um grande interruptor vermelho nas costas,
virado para OFF; o olho se apaga num anel suave. Front e Back continuam
voando, os cones ainda acesos; a tela do Live na parede ainda se mexe.
J.A.R.V.I.S.: `Analysis Off`
LEGENDA (um celular no pé do quadro): "Analysis Off: no events, recordings
or messages until /on. Live keeps working, and a reminder comes every 3 h."

**Quadro 8.** O M900 à noite, dois drones pairando. Um pacote marcado
`v2026.10.13` entra; o J.A.R.V.I.S. acorda de olho aceso, e o interruptor
nas costas voltou sozinho para ON.
J.A.R.V.I.S.: `Production is running v2026.10.13.`
LEGENDA: O Off nunca é escrito em lugar nenhum: todo reinício acorda em On.
Dez segundos de pausa; as duas câmeras de volta três segundos depois.

**Cartão final.** Habilidades: **A Cadeira Vazia** (R46) · **O Interruptor
do Provável** (backlog 30) · **O Botão de Desligar** (backlog 29, `/on` e
`/off`). Chefes derrotados: **A Curvatura que Anda** (R46). À espreita: a
corrente sem fim de cadeiras (R47, de vigia); e a seguir, as 40 vistas
começam a se cuidar sozinhas — a primeira vez que o sistema apaga fotos por
conta própria, por escolha do Dono.

## Edição #17 — Olhos Novos

`v2026.10.14` · 14 out 2026, meio-dia

**Quadro 1.** Cinza frio. Uma parede de fotos de 300 px. Sete delas nem são
rostos: o topo de uma cabeça, uma risca, um coque — cada uma com um adesivo
"Gustavo, certeza". A coruja ergue uma contra a lanterna.
ARQUITETA: Os olhos antigos chamam o topo da cabeça de rosto, e depois dão
um nome a ele.

**Quadro 2.** Uma bancada de lentes. O castor testa uma depois da outra no
J.A.R.V.I.S.: um par fino marcado SFace, um par pesado marcado R100, um par
marcado R50. Um placar atrás: `R50: 0.275 → 144 de 156, nada errado` ·
`R100: 0.350 → 126`.
DEV: O par pesado enxerga menos aqui, e na metade da velocidade. Fica o R50.

**Quadro 3.** Dois arquivos lado a lado, um velho (`gallery.json`, 128), um
novo (`gallery_arcface_w600k_r50.json`, 512). O castor copia cada foto da
gaveta velha para a nova, relendo uma a uma; a gaveta velha fica fechada e
com cadeado, intocada.
DEV: Se a versão nova cair, a velha abre a própria gaveta, do jeito que a
deixou.

**Quadro 4.** A coruja, lupa sobre uma linha de PowerShell, uma faísca
vermelha de erro saltando do `2>$null`.
ARQUITETA: Pedida uma versão antiga, esta linha devia sair da frente. Em vez
disso, explodiu. Consertada antes de fazer falta.

**Quadro 5.** Um portão diante da casa. Um pacote marcado `buffalo_l.zip`
entra e é desembrulhado em duas caixas *antes* de a porta fechar; só então a
porta fecha para a troca.
LEGENDA: Os modelos chegam antes de a produção parar. Ninguém espera pela
rede.

**Quadro 6.** Interior azul-noite. As sete fotos de topo de cabeça estão na
bandeja de Espera. Uma máquina de regras marcada "28" estica o braço para
elas — e a coruja cobre a bandeja com a asa.
ARQUITETA: A regra guarda o que é mais diferente. Uma vista da pessoa errada
é a mais diferente de todas. Estas esperam a mão do Dono.

**Quadro 7.** O M900. Um pacote marcado `v2026.10.14` entra; o J.A.R.V.I.S.
abre olhos novos, relendo 173 fotos uma a uma.
J.A.R.V.I.S.: `Production is running v2026.10.14.`
LEGENDA: 173 de 173 vistas mantidas. Uns 35 segundos sem câmeras; as duas de
volta três segundos depois da partida.

**Quadro 8.** Creme quente. Um balão dourado de fora do quadro.
O DONO: Na tela onde o status aparece, quero ligar e desligar por lá também.
LEGENDA: O primeiro pedido da próxima edição.

**Cartão final.** Habilidades: **Olhos Novos** (R49: SCRFD + ArcFace R50) ·
**A Segunda Gaveta** (uma migração da galeria que sobrevive a um rollback) ·
**As Quarenta se Cuidam** (backlog 28) · **Os Botões de Sensibilidade**
(backlog 31). Chefes derrotados: **O Topo da Cabeça** (R49). À espreita: a
vista mais pesada que não é a melhor (R51); uma segunda cópia que entra
enquanto a gaveta está sendo enchida (R52).

## Edição #18 — O Botão, a Régua e a Tranca

`v2026.10.14.2` · 14 out 2026, tarde

**Quadro 1.** Creme quente. O balão dourado do Dono, da última página, ainda
paira no alto. O castor, de pé no cabeçalho da página, parafusa um botão de
verdade onde antes ficava a etiquetinha "On".
DEV: Você pediu para ligar e desligar aqui. Desligar pergunta antes. Ligar
é um toque.
Um pequeno diálogo flutua ao lado do botão: "Switch analysis Off? Nothing is
recorded or sent…"

**Quadro 2.** Uma parede com três caixinhas de número — 0.35, 0.45, 0.45 —
sendo desparafusadas. No lugar, três trilhos compridos com uma conta
deslizante cada, a conta parada bem no meio. Sob a ponta esquerda: "More
detections, more false alarms". Sob a direita: "Fewer, stricter".
O DONO (dourado, de fora do quadro): Sem números. O meio é o nosso padrão.

**Quadro 3.** Close num trilho, aberto como um diagrama: dois trechos retos
de inclinações diferentes que se encontram na conta do meio, um curto
descendo até 0.20, um longo subindo até 0.90. O castor conta entalhes
minúsculos.
DEV: Mil entalhes, para que uma conta que ninguém mexeu devolva exatamente o
número que mostrava.

**Quadro 4.** Um corredor comprido de fotos de um mesmo rosto, quarenta
delas, umas nítidas e grandes, outras pequenas. O método antigo apontava a
maior; agora uma lanterna varre todas e para numa foto menor que brilha
"0.42 — certeza".
LEGENDA: Quem decide é a melhor vista, não a maior. Um clipe passou de
"provavelmente" para "certeza".

**Quadro 5.** Uma porta com catraca marcada "portão frontal". Uma mulher
olhando para o celular, olhos encurtados pela perspectiva, batia nela; o
castor abaixa uma barra um entalhe, de 0.38 para 0.30, e ela passa. A outra
barra, a do nariz, fica onde estava.
DEV: Baixe a barra do nariz e entra a pessoa errada. Esta só deixa passar
quem olha para baixo.

**Quadro 6.** O arquivo da edição 17, a gaveta pela metade. Dois
J.A.R.V.I.S. idênticos chegam juntos; o primeiro pendura um cadeado na
gaveta (`.lock`), o segundo espera num banco, depois abre, vê o trabalho
feito e vai embora.
LEGENDA: Uma cópia migra. A outra espera, não acha nada a fazer, e sai.
Agora a linha está no log.

**Quadro 7.** Azul-noite. A coruja à mesa com duas fotos dos moradores e uma
moldura vazia com um ponto de interrogação. Ela escreve um cartão: "R54 —
vigiar".
ARQUITETA: As duas mudanças foram medidas nas duas pessoas que moram aqui.
Um estranho agora tem mais chances de parecer um deles. Ninguém mediu um
estranho, porque nenhum veio ainda.

**Quadro 8.** A coruja diante de uma janela do tamanho de um celular, 375 px
de largura, rolando uma coluna comprida de fotos de cães que escorre para
fora do quadro.
ARQUITETA: Quarenta e seis cães, nove mil pixels. Duas colunas, e vinte e
quatro de cada vez.

**Quadro 9.** O M900. Um pacote marcado `v2026.10.14.2` entra.
J.A.R.V.I.S.: `Production is running v2026.10.14.2.`
LEGENDA: Uns dez segundos sem câmeras; as duas de volta três segundos depois
da partida. 976 eventos, 206 rostos e 412 avistamentos de cães lidos antes e
depois.

**Cartão final.** Habilidades: **O Botão do Cabeçalho** (backlog 34) · **A
Conta Deslizante** (backlog 35) · **Lado a Lado** (backlog 36) · **A Melhor
Vista** (R51) · **Olhos para Baixo** (R30 b) · **A Gaveta com Cadeado** (R52).
À espreita: o estranho que ninguém mediu (R54); os rostos sem nome sem
limite (backlog 37, decisão do Dono).

## Edição #19 — Duas Pessoas, Um Rosto

`v2026.10.14.3` · 14 out 2026, noite

**Quadro 1.** Azul-noite, a porta da Front. Duas silhuetas saem juntas. Uma
vira o rosto para a câmera e uma etiqueta verde aparece sobre ela: "Gustavo
— resident, silent". A outra continua de costas: etiqueta nenhuma. A Front
paira no alto, olho arregalado.
CHEFÃO (balão preto, letras vermelhas): UM ROSTO. UM MORADOR. NADA A DIZER.
LEGENDA: Até hoje, no modo Home, um rosto silenciado cobria a cena inteira.

**Quadro 2.** O castor diante de um placar de duas colunas. À esquerda, "o
YOLO viu de uma vez": dois bonequinhos num só quadro. À direita, "rostos
encontrados": um rosto. Ele risca um ">" de giz entre as duas.
DEV: Eu conto pessoas num quadro só, nunca somando o evento inteiro. Duas
de uma vez, um rosto, todo rosto silenciado: a melhor vista vai para o
celular.
J.A.R.V.I.S.: `Front 14:02:11: 2 people seen, 1 face found, best view`

**Quadro 3.** O mesmo placar; um cachorro passa trotando e uma etiqueta
"person" escorrega para cima dele por engano. O placar agora diz 2 contra 1.
O DONO (dourado, de fora do quadro): Se errar, errou.
LEGENDA: Um cachorro tomado por pessoa custa uma mensagem a mais. Dois
moradores com só um rosto visto também. Aceito.

**Quadro 4.** A coruja ergue a foto que foi para o celular: só o morador
nela, sorrindo. Ela franze a testa e prende um cartão ao lado: "R56".
ARQUITETA: A mensagem diz duas pessoas e a foto mostra uma. Da próxima vez,
mande o quadro em que elas foram contadas.

**Quadro 5.** Creme quente. Um mostrador na parede escrito "sure", o
ponteiro em 0.40, e ao lado um placar: "0.30 — 77 de 80 certos, 0 errados …
0.40 — 66 … 0.60 — 4". O ponteiro está solto, esperando ser ajustado.
LEGENDA: O limiar de certeza agora é do Dono, escolhido numa tabela medida
nas fotos que o próprio Dono nomeou.

**Quadro 6.** A coruja levanta o placar e encontra, atrás de cada foto, a
gêmea do mesmo clipe, soprando a resposta para ela.
ARQUITETA: Cada vista é testada contra todas as outras — inclusive os
quadros do próprio evento. Uma garante a outra. A tabela é boazinha demais
na ponta de baixo.
Ela prende "R55" na moldura do placar.

**Quadro 7.** Uma bancada de laboratório. Quatro lentes em suportes olham a
mesma galeria de fotos de cachorro: uma lente-roda-de-cores escrita
"histogram" e três lentes de vidro escritas "DINOv2", "CLIP", "MobileNet".
Pela lente de cores, os sapatos escuros de um homem levam a etiqueta
"Mirana". Pela DINOv2 e pela MobileNet, os sapatos levam "?" — longe dos
dois cachorros.
DEV: Histograma conta cores, então tudo que é preto vira a Mirana. As redes
enxergam forma. Duas delas acertaram todo cachorro, de dia e de noite.

**Quadro 8.** A coruja pesa a DINOv2 e a MobileNet numa balança: empate
perfeito. Ela solta um cartãozinho no prato da DINOv2 — "dois labradores,
alguma outra casa" — e a balança pende.
ARQUITETA: A MobileNet aprendeu a pôr uma raça inteira numa caixa só. A
DINOv2 aprendeu a distinguir imagens. Para uma casa com dois cachorros da
mesma raça, é ela.

**Quadro 9.** Uma tela de celular, 375 px, fotos de cachorro em duas
colunas, um botão embaixo: "Show 10 more (10 left)". Sob cada régua nas
Configurações, um tracinho discreto no meio.
LEGENDA: Duas colunas no celular, listas longas de vinte e quatro em vinte e
quatro, e um tracinho onde mora cada padrão.

**Quadro 10.** O M900. Um pacote escrito `v2026.10.14.3` entra — e nesse
instante, lá fora, a Front e a Back caem do céu, olhos apagados. O pacote
volta deslizando, carimbado "rolled back".
J.A.R.V.I.S.: `Back: FAILED - Timed out.` `Front: FAILED - Timed out.`
LEGENDA: As duas câmeras saíram da rede entre 16:32 e 16:39. Não foi a
versão: nem ping, nem endereço, nada. E o log não disse uma palavra.

**Cartão final.** Habilidades: **A Contagem de Cabeças** (R42 b) · **O
Mostrador do Dono** (backlog 32, rostos) · **Vinte e Quatro por Vez**
(backlog 37) · **O Tracinho** (backlog 38) · **A Bancada de Lentes** (R53
passo 1). À espreita: a foto que mostra a pessoa errada (R56); as gêmeas que
garantem uma à outra (R55); treze fotos de cachorro no lugar errado
esperando o Dono; um deploy que para uma casa já cega (R57). A seguir: para
onde foram os dois drones?

## Edição #20 — O Cachorro de Sapatos

`v2026.10.15` · 14–15 out 2026

**Quadro 1.** Azul-noite, a casa apagada — todas as janelas pretas, o poste
da rua apagado. Front e Back caídas no gramado, hélices paradas, olhos
escuros. Lá dentro, a luz de energia do M900 está apagada.
O DONO (dourado, de fora do quadro): Faltou energia. O computador desligou
também.
LEGENDA: Para onde foram os dois drones. 14 de outubro, 17:13.

**Quadro 2.** 21:47. O M900 acende sozinho; J.A.R.V.I.S. se levanta, olho
brilhando; Front e Back sobem do gramado. Então uma cortina pesada com a
etiqueta "tela de login" cai sobre o monitor, e uma figurinha marcada
`winlogon.exe` puxa uma alavanca escrita "Sleep".
J.A.R.V.I.S.: `Back: ok` `Front: ok`
CHEFÃO (a cortina): NINGUÉM ENTROU. LUZES APAGADAS.
LEGENDA: Cinquenta segundos depois, o Windows o pôs para dormir. Dezoito
horas sem gravar e sem mensagem.

**Quadro 3.** A coruja, lanterna erguida, lê um pergaminho comprido — o log
do sistema — e circula duas palavras: "ScreenOffGracePeriod",
"SetSuspendState". Ela prende um cartão no pergaminho: "para o Dono".
ARQUITETA: Uma configuração do sistema. Não sou eu quem muda: o Dono aplica,
e testa reiniciando sem ninguém entrar.

**Quadro 4.** Creme quente. Uma bancada de laboratório. A lente de roda de
cores da edição passada vai para uma gaveta etiquetada `dog_bench.py`. O
castor rosqueia uma lente de vidro marcada "DINOv2" no olho do J.A.R.V.I.S.
Através dela, um par de sapatos escuros mostra "?".
DEV: As cores ficam na bancada, para comparar. A casa agora olha a forma:
384 números por recorte, e mais um que diz se é noite.

**Quadro 5.** O castor recebe um pacote de uma nuvem etiquetada "Hugging
Face". Uma impressão digital comprida está carimbada nele; ele segura a
prancheta ao lado, a mesma impressão digital nas duas.
DEV: Preso a um commit, guardado só se a impressão digital bater. Uma
errada, e nada entra na pasta.
LEGENDA: 88,5 MB. Contra a exportação do próprio Dev: cosseno 0,99999988 ou
melhor em todos os 167 recortes.

**Quadro 6.** A coruja com um cronômetro ao lado do loop ao vivo, uma esteira
de quadros. Um quadro espera enquanto a foto de um cachorro passa pela lente
nova.
ARQUITETA: A bancada disse que a lente nova era mais barata que a velha. Não
nas caixas pequenas do loop ao vivo: 121 milissegundos por cachorro, contra
37. Uma vez por evento de cachorro, nada se acumula. Aceito — e o livro
corrigido.

**Quadro 7.** Um quadro de avisos com duas fotos. À esquerda, a da edição
passada: só o morador, sob "2 people seen". À direita, a nova: duas caixas
desenhadas, duas pessoas no quadro. A coruja tira o cartão "R56" do quadro.
J.A.R.V.I.S.: `Front 14:02:11: 2 people seen, 1 face found`
LEGENDA: A mensagem da pessoa escondida agora leva o quadro onde as pessoas
foram contadas.

**Quadro 8.** Uma porta marcada "update" e, na frente dela, um guardinha — o
script novo do castor. Pela janela, Front e Back estão apagadas. O guarda
levanta a mão.
J.A.R.V.I.S.: `Not updating: the service answers, but cameras deliver no frames (Back no frame yet). The cameras are not delivering frames now; nothing was changed.`
LEGENDA: Um update não para mais uma casa que já está cega. `-Force` ainda
abre a porta, para uma versão que conserta os olhos.

**Quadro 9.** Um celular a 375 px: fotos de cachorro em duas colunas, cada
cartão só uma foto e um nome. Um dedo toca uma; uma barra sobe de baixo: "1
selected — Assign to… — Bad detection".
LEGENDA: No celular, um cartão é a sua foto. Toque, e aja na barra.

**Quadro 10.** O M900, 16:53. O pacote `v2026.10.15` entra. Um álbum velho
etiquetado `gallery.json` fica na prateleira, intocado; um novo,
`gallery_dinov2_small.json`, sai da máquina.
J.A.R.V.I.S.: `Dog gallery rebuilt for dinov2_small from gallery.json: {'people': 46, 'views': 205, 'kept': 205, 'seconds': 21.7, …}` `Back: ok` `Front: ok`

**Quadro 11.** A coruja separa as 44 fotos sem nome em três pilhas:
cachorros brancos sob "Aurora", pretos sob "Mirana", e uma pilha pequena,
"sem palpite", com duas pessoas e um recorte com as duas cadelas.
ARQUITETA: Vinte e dois palpites de Aurora: vinte e duas cadelas brancas.
Dezessete de Mirana: dezessete pretas. E as pessoas não são cachorro de
ninguém.

**Cartão final.** Habilidades: **A Lente da Forma** (R53, DINOv2-small) ·
**O Pacote Lacrado** (a impressão digital do modelo) · **A Foto da Contagem**
(R56) · **O Guarda da Porta** (R57) · **O Cartão de Bolso** (backlog 39). À
espreita: as gêmeas que garantem uma à outra (R55, a seguir); treze fotos de
cachorro no lugar errado, quatro delas entre as Escolhidas, esperando o
Dono; a tela de login que põe a casa para dormir. A seguir: os cachorros
ganham um mostrador só deles.

## Edição #21 — Os Gêmeos Fiadores

`v2026.10.15.2` · 15 out 2026

**Quadro 1.** Creme quente. Uma sala de aula. J.A.R.V.I.S., numa carteira,
faz uma prova; a folha mostra o rosto do Gustavo. Ao lado, presa na
carteira, a foto do quadro seguinte da mesma visita — um gêmeo. J.A.R.V.I.S.
responde na hora, radiante.
J.A.R.V.I.S.: `Gustavo — certeza.`
LEGENDA: A tabela da edição passada: 66 de 80 com certeza a 0.40.

**Quadro 2.** A coruja se debruça sobre a carteira e levanta o gêmeo preso
com duas garras.
ARQUITETA: Você não estava reconhecendo ele. Estava reconhecendo o quadro
que acabou de ver. Prova com o gabarito na mesa.

**Quadro 3.** O castor num arquivo, escrevendo uma etiqueta no verso de cada
foto: "Back / 14 out / 11:05:41".
DEV: Agora cada foto diz de qual visita veio — pelo próprio nome, então
nenhuma troca embaralha as etiquetas.

**Quadro 4.** As fotos antigas não têm etiqueta. O castor segura uma contra
uma pilha de fotos de avistamento, apertando os olhos através de uma grade
cinza de 16×16.
DEV: A mesma foto, salva duas vezes: a grade acha, mesmo com os bytes
diferentes. E as que não têm gêmea — o relógio do arquivo diz quem foi
gravado junto.
LEGENDA: 138 fotos de rosto e 205 de cães. Nenhuma ficou sem visita.

**Quadro 5.** A prova de novo. Desta vez uma cortina esconde todas as fotos
da mesma visita. J.A.R.V.I.S. aperta os olhos, pensa e responde menos — mas
toda resposta continua certa.
J.A.R.V.I.S.: `0.40: 39 de 80 com certeza. Erradas: 0.`
LEGENDA: O número honesto. Menor, e ainda sem erro.

**Quadro 6.** A coruja com um cronômetro e dois clipes numa linha do tempo,
as pontas se sobrepondo por alguns segundos.
ARQUITETA: Mais um gêmeo podia se esconder onde dois clipes se sobrepõem.
Contei: três de trinta e nove, e nenhuma resposta errada. A visita continua
sendo a unidade.

**Quadro 7.** Configurações, dois painéis lado a lado. À direita, a tabela
dos rostos; à esquerda, uma nova com colunas Dia e Noite e um botão de
ajuste marcado "0.33". O castor encaixa o botão; a coruja confere num
celular a 375 px.
DEV: Os cães ganham um ajuste só deles. Só a distância — a razão para o
segundo cão fica, é ela que impede foto com dois cães de sair com certeza.
LEGENDA: A 0.33: 44 de 56 de dia, 9 de 24 à noite. Todas certas.

**Quadro 8.** O M900. O pacote `v2026.10.15.2` entra; por onze segundos os
drones pairam, depois sobem.
J.A.R.V.I.S.: `Events of the face views stored before views recorded one: {'same picture': 81, 'written together': 57}` `Back: ok` `Front: ok`

**Cartão final.** Habilidades: **A Etiqueta da Visita** (R55,
`view_events`) · **A Grade de Apertar os Olhos** (a miniatura 16×16) · **A
Cortina** (deixar a visita inteira de fora) · **O Ajuste dos Cães** (backlog
32 para cães). À espreita: treze fotos de cães no lugar errado, quatro entre
as Escolhidas; a tela de login que põe a casa para dormir. Próxima: o Dono
gira os dois ajustes — ou deixa onde estão.

## Edição #22 — O Sino Silencioso

`v2026.10.16` · 16 out 2026

**Quadro 1.** Azul profundo, noite. Um celular no criado-mudo vibrando sem
parar, uma pilha de cartões de notificação escorrendo da tela. Cada cartão
mostra o quintal em infravermelho, ou um cachorro numa caixa marcada
`person`.
O DONO: Muitas notificações em Home.
LEGENDA: 31 mensagens em 23 horas. Nenhuma de um estranho.

**Quadro 2.** Vermelho escuro. Uma cancela de pedágio com uma ampulheta de
dois minutos em cima: o Cooldown. Uma figura sem rosto se aproxima; a
cancela não sobe e um alçapão se abre sob a figura, num poço com as letras
`skipped: cooldown`.
CHEFÃO (a cancela): DOIS MINUTOS POR CÂMERA. O QUE VIER, CAI.
LEGENDA: 291 mensagens caíram em uma semana. Um estranho teria caído do
mesmo jeito.

**Quadro 3.** Creme quente. A coruja lê a regra do Dono num pergaminho, à
luz da lanterna.
O DONO: Um risco nunca pode se perder. E mais de uma notificação em 30
segundos quer dizer que algo está errado.
O DONO: Toda vez que você o vê num lugar diferente, vale uma notificação
nova.

**Quadro 4.** A coruja desenha num quadro-negro: um sino grande e um sino
pequeno com abafador. Setas para o sino grande: "o primeiro", "outra
câmera", "mais gente". Para o abafado: "o mesmo lugar de novo", "o rosto
que vem depois".
ARQUITETA: Nada se perde. Cada mensagem toca, ou chega sem som. E
silenciosa, não editada — cada foto fica nos servidores do Telegram, fora
do alcance de quem levar o M900.

**Quadro 5.** O castor numa bancada de teste. Uma figurinha sem rosto passa
duas vezes por uma maquete da cancela; na segunda, pisca uma luz vermelha.
DEV: Primeiro o teste que falha: duas pessoas sem rosto, um instante
separadas, em Home. Hoje a segunda não recebe nada.
J.A.R.V.I.S.: `returned 0`
LEGENDA: Depois a cancela caiu. O teste passa; a segunda chega em silêncio.

**Quadro 6.** O castor monta uma ampulheta de 30 segundos sobre o sino
grande. As mensagens que chegam enquanto a areia corre entram quietinhas;
quando a areia acaba, o sino toca uma vez, com um cartão.
J.A.R.V.I.S.: `Back 21:03:10: person — and 1 more, sent silently above`
LEGENDA: Um toque em 30 segundos, no máximo. O número do Dono.

**Quadro 7.** Noite. O drone Back se apaga e cai um pouco. Numa torre de
vigia ao lado da casa, uma sentinela pequena com um relógio de bolso
confere os dois drones a cada cinco segundos.
J.A.R.V.I.S.: `Back: no picture since 16:32:10`
LEGENDA: A queda de 14 de outubro não deixou linha no log. Esta deixaria.

**Quadro 8.** A coruja numa mesa, uma semana de log num rolo de papel
comprido, um contador em cada garra.
ARQUITETA: Repassado no log real: em Home, 100 mensagens em vez de 54 — as
que antes caíam. 42 toques em vez de 54. O chat fica mais cheio; o celular,
mais quieto.

**Quadro 9.** O M900. O pacote `v2026.10.16` entra; os drones sobem.
J.A.R.V.I.S.: `Back: ok` `Front: ok` `Surveillance running.`

**Cartão final.** Habilidades: **O Sino Silencioso**
(`disable_notification`) · **O Incidente** (um para a casa, dois minutos de
silêncio para fechar) · **A Ampulheta** (o piso de 30 segundos) · **A Torre
de Vigia** (`camera_down`). À espreita: os cães ainda vestidos de gente, as
caixas gêmeas num corpo só — e, na próxima porta, uma biblioteca cujo
primeiro import leva 89 segundos contra um deploy que espera 90. Próxima: o
Rastreador, e um corpo que guarda o nome.

## Edição #23 — O Rastreador que Nunca Olha

`v2026.10.16.2` · 16 out 2026

**Quadro 1.** Noite, o quintal em infravermelho. Aurora atravessa o
gramado dentro de uma caixa marcada `person`; no quadro seguinte o mesmo
cachorro usa uma caixa `dog`; no próximo, `person` de novo. Cada quadro é
uma foto avulsa presa num mural de cortiça, sem nenhum barbante entre elas.
LEGENDA: Um quadro de cada vez, ninguém lembra quem era quem.

**Quadro 2.** Um personagem novo sai de um caixote carimbado
`trackers 2.6.1`: um mensageiro vendado, com prancheta e cronômetro. Ele
nunca tira a venda.
J.A.R.V.I.S.: `ByteTrackTracker`
LEGENDA: O Rastreador. Nunca vê um pixel. Só adivinha onde cada caixa deve
estar no próximo quadro, e confere.

**Quadro 3.** Vermelho escuro. O caixote espera na porta do M900, e uma
ampulheta enorme marcada 89 s está ao lado de uma menor marcada 90 s.
CHEFÃO (a ampulheta): MEU PRIMEIRO OLHAR EM CADA DLL NOVA LEVA 89
SEGUNDOS. SUA VERSÃO NOVA TEM 90 PARA ACORDAR.
LEGENDA: Smart App Control, primeiro olhar.

**Quadro 4.** O castor monta um galpão atrás da casa, com a placa
`%TEMP%`, desembala ali uma cópia do caixote e gira uma vez a chave de cada
pacote, enquanto o M900 antigo continua vigiando as câmeras.
DEV: Deixa ele olhar agora, enquanto a versão velha ainda grava. Quando a
nova começar, ele já viu esses bytes.
J.A.R.V.I.S.: `Every package imported in 15.6 s.`

**Quadro 5.** A coruja, lupa sobre o `pyproject.toml`, uma linha
circulada: `link-mode = "copy"`.
ARQUITETO: Sua nota diz que hardlinks levam isso adiante. Este projeto
copia.
DEV: Então por que uma cópia nova importou em 9 segundos?
ARQUITETO: Porque o que ele lembra são os bytes, não o arquivo. Seu número
estava certo. O motivo vai corrigido para o livro.

**Quadro 6.** O mensageiro trabalhando numa tela de replay: barbantes
ligam caixas de quadro em quadro. Um barbante amarra sete caixas: dog, dog,
person, dog, dog, dog, dog. Uma urna ao lado diz "dog".
LEGENDA: O voto. Um corpo que o YOLO chama de cachorro na maioria dos
quadros é um cachorro.

**Quadro 7.** Dois problemas, desenhados como diabinhos. Um segura a
primeira caixa de cada barbante, sem crachá (`-1`). O outro monta no
barbante de um morador que saiu de cena e o puxa para cima de um cachorro.
DEV: A primeira caixa de toda trilha volta sem identidade. E uma vez uma
trilha levou uma pessoa para dentro de um cachorro.
ARQUITETO: Então contamos isso direito antes de alguém agir sobre um voto.

**Quadro 8.** Uma caminhada no caminho da frente, cortada em dois clipes
por um buraco de sete segundos. A caixa prevista pelo mensageiro continua
deslizando na linha antiga, para fora do quadro, enquanto a pessoa
reaparece atrás dela.
LEGENDA: Previsão não é memória. Sete segundos fora de vista, e a
caminhada vira duas pessoas de novo.

**Quadro 9.** O M900. O pacote `v2026.10.16.2` entra depois que o galpão é
desmontado; os drones sobem.
J.A.R.V.I.S.: `Back: ok` `Front: ok` `Surveillance running.`

**Cartão final.** Habilidades: **O Rastreador** (ByteTrack, ainda sem uso
ao vivo) · **O Aquecimento** (imports antes da parada) · **A Longa
Ausência** ("picture back, 18 h 5 min without"). À espreita: a primeira
caixa sem nome, a trilha que escorrega de uma pessoa para um cachorro, a
caminhada que nenhum buffer junta. Próximo: a primeira caixa ganha nome, e
as trilhas começam a ser anotadas.
