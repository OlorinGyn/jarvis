# Instruções para o Claude Code

Leia `docs/CONTEXTO.md` antes de mexer em qualquer coisa: histórico, decisões
que não devem ser desfeitas sem motivo novo, e o que já foi descartado.

Regras do usuário, detalhadas em `docs/CONTEXTO.md` seção 2:

- **Código sem comentários.** Toda explicação vai para `docs/`. Docstrings de
  uma linha são aceitas.
- **Toda mudança termina em commit + documentação atualizada**, sem precisar
  pedir. A mensagem explica o porquê.
- **O push é sua responsabilidade, não do usuário** (combinado em 09/10/2026).
  Ao concluir uma feature ou acumular commits, envie — e **confirme com o
  servidor**, não com a saída do `push`: `git ls-remote` ou
  `git rev-list --count jarvis/master..HEAD`. O cache local mente depois de um
  push feito de outra máquina. O `pull` está na rotina da seção 12 do
  `CONTEXTO.md`.
- **O `.env` nunca entra no commit.** Tem as senhas reais das câmeras. Confira
  também `models/`, `clips/`, `faces/` e `backups/`.
- **Explique o código, não só o resultado.** O usuário está aprendendo Python
  e OpenCV, vindo de Java e C#.
- Documentação em português; código e identificadores em inglês.

**O backlog é a seção 8 do `docs/CONTEXTO.md`.** É a lista única, e as duas
máquinas a enxergam pelo git. Ao concluir um item, risque-o no mesmo commit da
mudança. Itens marcados **(proposto)** são sugestão do Claude sem decisão do
usuário — não comece nenhum sem perguntar.
**A seção 11 do `docs/CONTEXTO.md` é o registro de vieses**: restrições que o
Claude adotou sozinho, sem decisão do usuário. Ao perceber que está justificando
uma escolha por uma consequência do ambiente em vez de um pedido ou uma medição,
registre lá. Reaproveitar biblioteca conceituada vem antes de escrever à mão;
tamanho da aplicação não é critério.

**Ao abrir nesta pasta, antes de responder qualquer coisa:** rode a rotina de
retomada da seção 12 do `docs/CONTEXTO.md`. Ela é sua, não do usuário — ele não
roda comandos de preparação à mão. Sincronize o ambiente, verifique o que o
plano em andamento exige, e só então diga em que ponto o trabalho está.
