# Castelo — estrutura e trajeto de carros

Revisão de 08/10/2026, recurso `cidade_castelo_previa`. A fachada girou 90° para o lado do X enviado pelo usuário. Âncora -944.5, 206.5, 66.47; rotação -30°. O corpo principal mantém 28 × 20 metros, três pavimentos e quatro torres, sem alteração da escala.

Foram removidas todas as folhas das portas, ferragens de portas, camas, bancadas, ilha de cozinha, mobiliário de banquete, palco, tela e acessórios. Permanecem somente mesas e cadeiras de reunião como mobiliário. Paredes, divisórias, pisos, escadas, janelas, guarda-corpos, iluminação fixa e acabamentos arquitetônicos permanecem. A fonte e os vasos soltos foram removidos para liberar a chegada.

A pista tem cinco metros de largura e contorna o edifício. Conecta-se à entrada existente para carros e ao acesso da garagem, cuja posição no mundo foi preservada. A rampa entre a rua e o patamar do lote tem inclinação medida de aproximadamente 12,4%; a borda tem contenção nos desníveis. Não invadiu a quadra. Os pisos e obstáculos antigos que ocupavam a pista foram retirados, incluindo as folhas do portão de carros e um poste que interferia no trecho da entrada; os demais elementos do perímetro foram preservados.

As texturas externas de calcário, cantaria, ardósia, madeira, vidro e metais continuam no pacote. O trajeto usa material de asfalto fosco com agregado fino e passeio de pedra. Os DDS têm mipmaps; o dicionário compartilhado ocupa cerca de 28 MiB de memória gráfica nativa. A geometria simplificada de distância continua pendente; esta revisão serve para avaliar estrutura, circulação e proporção.

## Carregar a atualização

Com o FiveM desconectado, digite no console do servidor:

```text
refresh
stop cidade_castelo_previa
restart cidade_castelo_livre
ensure cidade_castelo_previa
```

Reconecte e use `castelo` no F8 do administrador para visitar a nova entrada. `voltarcastelo` retorna ao local anterior. As linhas existentes no server.cfg permanecem: a revisão também será carregada na próxima inicialização normal.

Foram verificados os arquivos nativos, as referências de textura, os três pisos, os 48 degraus, os acessos internos, a ausência de portas e móveis indesejados e a colisão do trajeto de carros. O teste de condução e a confirmação visual dentro do FiveM ainda dependem de carregar a revisão no jogo. As imagens entregues são prévias dos arquivos convertidos renderizadas no Blender; o terreno original aparece com materiais simplificados nessa prévia.

O instalador guarda cópias dos dois recursos anteriores em `castelo_rockford/estrutura_20261008/backup_instalacao`. Nenhum recurso da mansão, dos jogadores ou da administração foi alterado.
