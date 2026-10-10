# Castelo Rockford — prévia na cidade

Recurso `cidade_castelo_previa`, dependente de `cidade_castelo_livre`. O novo castelo usa a escala original do Blender: corpo principal de 28 × 20 m, quatro torres e três pavimentos. Âncora GTA: -946, 207, 66.47; rotação de 60 graus. O último remate está perto de 90.82 m no mundo.

Materiais externos convertidos: calcário com juntas e relevo, cantaria clara, ardósia com relevo, madeira, vidro transparente, bronze, ferro e superfícies da chegada. O dicionário compartilhado contém texturas DDS comprimidas e mipmaps. As texturas vêm dos materiais do modelo; não foram substituídas por texturas genéricas de outro edifício.

Para ativar com um servidor já iniciado, digite no console do servidor:

```text
refresh
ensure cidade_castelo_livre
ensure cidade_castelo_previa
```

Reconecte o FiveM após ativar o mapa. No F8 do jogador administrador use `castelo`; use `voltarcastelo` para voltar ao local anterior. O comando aguarda streaming e colisão e não altera clima, horário ou filtros visuais.

Esta é uma prévia para tamanho e proporção. Pisos, escadas, aberturas e mobiliário possuem colisões básicas. As portas internas estão abertas como no Blender; não são portas interativas nesta etapa. Cozinha, banheiros e móveis seguem o estágio do projeto. Não inclui os carros de referência, bonecos de escala nem uma quadra duplicada: a quadra original foi preservada. Geometria simplificada de distância, integração final do terreno e interiores continuam pendentes. A imagem de conferência é render dos arquivos convertidos no Blender, não captura do FiveM.

Para ocultar somente a prévia: `stop cidade_castelo_previa` no console do servidor. Para remover da próxima inicialização, comente apenas `ensure cidade_castelo_previa` no server.cfg. O recurso que libera o terreno pode permanecer ativo.
