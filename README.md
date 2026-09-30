<img src="assets/jarvis.png" width="96" align="right" alt="">

# J.A.R.V.I.S.

Vigilância doméstica com câmeras TP-Link Tapo via RTSP. Detecta movimento,
decide se é pessoa ou animal, grava o evento sem recodificar o vídeo da câmera,
reconhece rostos e permite cadastrar nomes.

Interface com três abas: **Live**, **Records** (gravações por dia) e
**People** (rostos, com cadastro de nome).

## Começar

```bat
git clone https://github.com/OlorinGyn/jarvis.git
cd jarvis
instalar.bat
jarvis.bat
```

O `instalar.bat` instala o que falta, baixa os modelos e cria o `.env`, onde
vão o IP e as credenciais de cada câmera. Detalhes em
[docs/INSTALACAO.md](docs/INSTALACAO.md).

## Estrutura

```
src/jarvis/   o programa
tools/        diagnóstico, ícone e manutenção dos rostos
assets/       ícone
docs/         toda a documentação
```

## Documentação

| Documento | Conteúdo |
|---|---|
| [INSTALACAO.md](docs/INSTALACAO.md) | Instalar, configurar, resolver problemas |
| [ARQUITETURA.md](docs/ARQUITETURA.md) | Como funciona e por quê, camada por camada |
| [PYTHON.md](docs/PYTHON.md) | Python e bibliotecas para quem vem de Java/C# |
| [CONTEXTO.md](docs/CONTEXTO.md) | Histórico, decisões e caminhos já descartados |
