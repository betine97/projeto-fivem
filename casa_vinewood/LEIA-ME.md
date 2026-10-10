# Mansão — sala, jantar e ilha de cozinha

**Spots e quadros — 08/10/2026:** os 88 spots do teto foram substituídos pelo modelo embutido da nova referência, com aro branco, refletor metálico, lente facetada e cavidades reais no teto. Quatro quadros novos foram acrescentados ao escritório, à sala de jogos/TV e ao hall do térreo. Fonte editável desta revisão: `mansao_spots_quadros.blend`. Consulte [a instalação e as prévias](refs_spots_quadros_20261008/LEIA-ME.md). Para carregar no FiveM, execute `restart cidade_mansao` no console do servidor e reconecte. A validação visual no jogo ainda está pendente.

**Atualização 08/10/2026:** otimização de texturas, carregamento independente da TV, LODs nativos e iluminação ambiente ampla. Os modelos tratados passaram de 544 para 132,625 MiB de alocação gráfica. Fonte atual com os novos vasos: `mansao_otimizada.blend`. Consulte [a revisão atual e como carregá-la](otimizacao_20261008/LEIA-ME.md); os valores e a iluminação descritos abaixo registram as revisões anteriores.

Revisão `jantar-cozinha-2026-10-07`. Os quatro GLBs fornecidos foram incorporados ao recurso `cidade_mansao`, usando a última imagem como referência de distribuição. A confirmação visual no FiveM depende de recarregar o recurso e reconectar.

## Componentes novos

| Conjunto | Instalação | Dimensões e altura |
| --- | --- | --- |
| Mesa de jantar | Entre a sala e a cozinha, com oito cadeiras e decoração originais | 3,90 m no sentido longitudinal, incluindo cadeiras; tampo a 83,5 cm do piso |
| Ilha de cozinha | Na cozinha, com as quatro banquetas voltadas para o jantar | 3 m de comprimento; bancada a 93,7 cm do piso |
| Pendente de cilindros | Centralizado acima da mesa, seis cilindros | Comprimento 2,40 m; parte inferior a 2,30 m do piso; suporte no teto do pé-direito duplo |
| Pendente linear | Centralizado acima da bancada | Comprimento 2,50 m; parte inferior a 2,15 m do piso; suporte sob a laje superior |

Os corpos dos modelos usam escala uniforme; somente os trechos dos cabos foram ajustados para alcançar os tetos. Os pendentes têm faces emissivas e nove pontos de iluminação quente, ativos perto da mansão. A instalação inclui os componentes dos GLBs; armários de cozinha e outros itens presentes apenas na imagem de referência não foram modelados nesta revisão.

As malhas foram unidas nas costuras antes da otimização. Os arquivos nativos novos têm zero bordas abertas, zero arestas não-manifold, zero triângulos degenerados e zero tangentes nulas. Mesa: 100.000 triângulos; ilha: 64.998; cilindros: 24.000; linear: 15.998. Cor e relevo originais preservados em 4.096 pixels, especular em 2.048, com filtragem até 4×4. A qualidade dos detalhes pintados segue o conteúdo dos GLBs fornecidos.

Mesa, cadeiras, ilha e banquetas têm colisões simplificadas. Três percursos novos verificam a circulação ao redor dos conjuntos e entre jantar e cozinha. Os pendentes ficam acima da circulação do personagem.

## Ajustes anteriores preservados

- Sofá/chaise/mesa de 5,20 m, com malha fechada e mapas 4K, e painel de TV de 4,60 m na parede de tijolos.
- Mármore bege em todo o térreo e no piso superior, exceto os 39,60 m² delimitados do mezanino. Escadas e patamares em madeira; paredes superiores com o reboco creme do térreo.
- Paredes de 20/25 cm, piso térreo de 30 cm e laje superior de 45 cm, com faces laterais visíveis.
- Cinco portas de madeira de 45 mm: escritório, lavabo, despensa, sala de TV/jogos e lavanderia. **E** abre/fecha suavemente, com estado compartilhado; fechamento recusado enquanto alguém ocupa o vão. Entrada junto ao deck e porta de vidro à esquerda do sofá reservadas para outros modelos.
- Colisão da câmera, limitação de corrida, limpeza de obstáculos e vegetação nativos, transparência dos vidros e correção de oclusão.

A geometria, as normais e as UVs dos sete drawables anteriores foram comparadas com o backup e permanecem iguais.

## Arquivos e verificações

`mansao_encaixada.blend`: fonte editável. `mansao_fivem_preparada.blend`: materiais de exportação, móveis colocados, portas para visualização e fachada corrigida em coleção oculta. `source_assets/`: GLBs originais. `backup_antes_jantar_cozinha/`: versão anterior completa.

O pacote instalado contém 42 arquivos nativos, incluindo nove drawables estáticos e um modelo de porta móvel. `componentes_jantar_cozinha.json` descreve escala, posição e origem dos modelos. `verificacao_jantar_cozinha.json` registra malhas, texturas, circulação, iluminação e preservação dos modelos anteriores. `instalacao_jantar_cozinha.json` e `auditoria_instalacao_final.json` registram os arquivos instalados e seus hashes. As validações anteriores de portas, estrutura, câmera, circulação e janelas foram repetidas.

As imagens `jantar_cozinha_visao_geral.png`, `mesa_jantar_detalhe.png` e `ilha_cozinha_detalhe.png` são prévias Blender, não capturas do jogo.

## Carregar

No console do servidor: `restart cidade_mansao`. Depois reconecte o FiveM e use `/mansao`. Perto das portas, pressione **E**. `/mansaoverificar` registra colisões observadas pelo GTA; portas fechadas são identificadas separadamente de bloqueios inesperados.
