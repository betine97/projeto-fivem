# Portas do bar e da sala — 08/10/2026

Os dois vãos indicados nos prints receberam o modelo da porta de madeira com visor de vidro instalado ao lado do aparador da cozinha. O acesso ao lado do bar tem uma cópia adaptada ao vão de 1,25 × 2,75 m. O acesso da sala, junto à TV/piano, reutiliza o drawable original de 1,012 × 2,427 m em seu vão de 1,10 × 2,50 m. Batentes usam a geometria chanfrada, material e UVs do batente original, extraídos separadamente do aparador.

Folhas têm colisão no espaço da dobradiça e quatro LODs. `E` abre/fecha pelo controlador compartilhado existente. Um jogador no vão impede o fechamento; requisições distantes são recusadas. Os novos modelos fixos/animados ficam protegidos do editor de arrastar objetos.

Porta de referência, sete portas anteriores, estrutura, móveis, posições salvas, iluminação e clima permanecem preservados. A auditoria de colisão foi atualizada para reconhecer os modelos de todas as portas configuradas, inclusive as duas novas, como contato esperado.

`build_install.py` contém o preparo, verificação geométrica/nativa e instalação. `installation.json` registra hashes e preservação de 121 arquivos; `runtime_tests.json` registra testes do servidor Lua. Backup em `backup/`, novos nativos em `package/stream/`. A confirmação visual no FiveM permanece pendente.

Carregar no console do servidor: `restart cidade_mansao`. Reconecte o FiveM para carregar os novos batentes; aproxime-se e pressione `E`.
