# Instruções para o Claude Code

Leia `docs/CONTEXTO.md` antes de mexer em qualquer coisa: histórico, decisões
que não devem ser desfeitas sem motivo novo, e o que já foi descartado.

Regras do usuário, detalhadas em `docs/CONTEXTO.md` seção 2:

- **Código sem comentários.** Toda explicação vai para `docs/`. Docstrings de
  uma linha são aceitas.
- **Toda mudança termina em commit + documentação atualizada**, sem precisar
  pedir. A mensagem explica o porquê.
- **O `.env` nunca entra no commit.** Tem as senhas reais das câmeras. Confira
  também `models/`, `clips/` e `faces/`.
- **Explique o código, não só o resultado.** O usuário está aprendendo Python
  e OpenCV, vindo de Java e C#.
- Documentação em português; código e identificadores em inglês.
