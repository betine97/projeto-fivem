# Amostra natural da ilha

Revisão `ilha-20261009-amostra-natural-3`. Feche completamente o FiveM e abra novamente após a atualização; a sessão anterior pode manter arquivos do mundo antigo. Conecte usando F8: `connect 127.0.0.1:30120`, depois `amostrailha` para visitar o trecho costeiro ao sul da pista. `ilha` retorna à pista. `amostradiag` mostra modelos ausentes, tipos de objetos próximos, mapas antigos ainda ativos e o diagnóstico de solo, água e teleporte.

Foi alterado apenas o setor de terreno `ti_terreno_03_01`. São 55 palmeiras, 12 árvores, 65 pedras, 95 arbustos e 460 tufos de vegetação. O terreno usa cinco texturas originais do jogo, com mapas de normal e mistura de grama, trilha de terra, barro, rocha e areia. O streaming agora inclui cópias dos 12 modelos originais, com nomes próprios `ti_n_*`, seus dicionários de textura, metadados e colisões embutidas. Os arquivos originais da instalação do GTA foram apenas lidos. `_manifest.ymf` declara as dependências dos 45 mapas da ilha.

O teleporte aguarda os modelos e confirma a altura real do chão. Se houver falha, retorna à pista ou à posição anterior; libera câmera, foco, gravidade e controles também em caso de erro. A lista `data/mapas_originais.json` bloqueia os mapas base e adicionais que têm objetos na área da ilha, incluindo os dutos de telhado. A exclusão ocorre apenas no modo ilha; a cidade original permanece preservada.

A água recebe uma declaração de carregamento no recurso e a checagem aguarda a atualização do streaming. O retorno da função de carregamento não substitui a conferência dos setores realmente instalados. Uma falha da água não bloqueia os controles.

Correção da revisão 3: os dois crashes `alaska-quebec-double` ocorreram na entrada, depois da tentativa de carregar a água. O dump mostra uma leitura inválida de uma estrutura com limites de coordenadas de 16 bits, compatível com as regiões de água. Foi retirada a expansão dos limites de recorte para ±8192 introduzida na revisão 2. O jogo permanece com os limites internos originais, inclusive quando só as 559 regiões padrão estiverem carregadas. A resolução do crash ainda depende de confirmação no cliente; os testes simulados não executam a renderização do GTA.

`amostra_natural.blend` contém o terreno editável e a montagem com as malhas originais. As imagens são prévias do Blender; o FiveM aplica os shaders e as paletas nativas de vegetação.

`proveniencia.json` registra os arquivos consultados na instalação local do jogo. `pacote.json` registra os modelos e materiais físicos. `verificacao.json`, `nativo/verificacao_integracao.json` e `nativo/validacao_codewalker.json` registram as verificações do pacote, dos comandos e dos arquivos nativos. A aparência, a água e a colisão durante o jogo ainda devem ser validadas pelo jogador.

O estado anterior desse setor está em `backup/`. Para reconstruir o pacote depois de editar a amostra: execute `scripts/criar_amostra_blender.py` no Blender, depois `scripts/empacotar_amostra_natural.py` com Python, `scripts/criar_manifesto.ps1` com PowerShell e `scripts/instalar_fivem.py` com Python. A geração base do mundo recria a configuração e o terreno; nesse caso, reaplique a amostra por último. `scripts/auditar_mundo_original.py` reconstrói a lista de mapas antigos a partir da instalação local, sem modificá-la.
