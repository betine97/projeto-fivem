# Ilha com identidade Cayo — cidade e vilarejos

Arquivos instalados e recursos ativos: `teste_ilha`, `cayo_vizinha`, `porto_esperanca`, `natureza_integrada`.

- 250 construções na cidade principal, incluindo as 91 construções anteriores preservadas.
- Quatro vilarejos, cada um com 16 casas dos modelos aprovados.
- 18.644 árvores/palmeiras, 64.495 arbustos, 17.349 plantas de sub-bosque, 2.995 pedras e 20 reservatórios nativos.
- 7.014.254 instâncias de vegetação rasteira em lotes nativos de GPU, cobrindo 79,6% da área terrestre utilizável; estradas, pista, água, casas e promontórios rochosos ficam livres.
- 4.500 entidades LOD de árvores/palmeiras em 63 células amplas, com alcance de até 1.600 m para manter a silhueta arborizada visível de barcos e do ar.
- Materiais de Cayo em toda a terra; relevo adaptado à referência, com altura máxima de aproximadamente 56 m e rios rebaixados junto com suas margens.
- 13.507 objetos da antiga floresta autoral removidos do Blender. Dezoito arquétipos e 36 arquivos antigos retirados do recurso ativo e guardados em backup.

## Conferência

838 assets nativos foram lidos pelo CodeWalker e 3.601 raios de colisão comparados ao terreno visível passaram. As posições das 91 construções anteriores e os arquivos de todos os dez modelos de casas foram preservados. Os drawables nativos da natureza mantêm os bytes originais, incluindo shaders e dados de vento. As trilhas usam a textura e o normal map nativos de barro com UV alinhado ao eixo dos caminhos e resposta molhada mais forte.

O FiveM aberto sofreu um crash ao descarregar os dicionários antigos durante a recarga completa dos mapas. A nova versão foi ativada com o cliente desconectado. A conferência visual desta versão exige uma nova conexão. Evitar recargas completas de terreno/dicionários de Cayo com jogadores conectados; consultar `players.json` e fazer esse tipo de atualização com o cliente desconectado.

## Visitar pelo F8

`cidade`, `vila1`, `vila2`, `vila3`, `vila4`, `natureza`, `naturezadiag`, `ilha`, `porto`, `cayo`.

## Blender

- `cayo_perico_referencia.blend`: 190 modelos reais de terreno original, 35.018 instâncias nativas de natureza e posições de infraestrutura marcadas para análise geográfica. As cores de altitude são uma visualização de estudo; não reproduzem todos os materiais e interiores do jogo.
- `ilha_cayo_cidade_vilarejos.blend`: ilha modificada, casas aprovadas, floresta nativa e água alinhada ao novo relevo. A vegetação rasteira completa e o vento são executados pelos recursos nativos no FiveM.

Relatórios e verificações estão na pasta `dados`. Backups preservam as versões anteriores.
