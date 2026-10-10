# Cayo Perico ao lado da ilha autoral

Recurso instalado: `server-data/resources/cayo_vizinha`.

Cayo foi deslocada 1.300 metros para oeste e 5.200 metros para norte em relação à posição original. Assim, fica a leste da ilha autoral, com mar entre as duas. As casas, árvores e o terreno existentes continuam nos seus recursos.

## Entrar e voltar

Depois de conectar ao servidor, execute no console F8:

- `cayo`: pista de pouso de Cayo Perico.
- `cayo porto`: porto de Cayo.
- `cayo mansao`: região da mansão.
- `ilha` ou `porto`: voltar à ilha autoral.
- `cayodiag`: registrar posição, colisão, chão, mapas e modelos disponíveis.

O teleporte aguarda o chão e a colisão. Se a confirmação falhar, retorna à posição anterior e libera a câmera e os controles.

## Origem e preparação

A pesquisa encontrou a ilha como conteúdo nativo do GTA V a partir da versão 2189. Foi utilizada a instalação local do GTA V, sem substituir os modelos por uma recriação. Referência oficial: [Cfx.re — Enabling the island on build 2189](https://forum.cfx.re/t/enabling-the-island-on-build-2189/1909506).

Foram preservados os bytes de 3.930 arquivos de modelos, texturas e definições. A preparação deslocou 308 mapas e 1.850 arquivos de colisão do mundo; 11 colisões locais de interiores permanecem intactas. Mapas alternativos de eventos e bloqueios da missão não foram ativados junto com a exploração livre.

As coordenadas foram modificadas com leitura e validação pelo [CodeWalker](https://github.com/dexyfex/CodeWalker). Nas colisões, foram alteradas somente as coordenadas necessárias, preservando vértices, materiais e hierarquias de aceleração originais. O recurso usa [definições de manifesto do FiveM](https://docs.fivem.net/docs/scripting-reference/resource-manifest/) e mantém as duas ilhas no mesmo mundo.

## Verificação e recuperação

- `proveniencia.json`: arquivos originais, origem e SHA-256.
- `validacao.json`: resultados das verificações de integridade, dependências, colisão e retorno seguro do teleporte.
- `instalacao.json`: recurso instalado e caminho do backup.
- `backups/`: versões anteriores da configuração do servidor e do cliente da ilha autoral.
- `scripts/`: extração, deslocamento, geração e validação reproduzíveis.

Os arquivos e quatro amostras de chão foram validados. A conferência visual dentro do FiveM ainda depende de uma conexão do cliente. Esta instalação prepara o cenário para exploração; não instala as missões do assalto.
