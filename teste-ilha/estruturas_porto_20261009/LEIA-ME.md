# Biblioteca de estruturas do porto

Dez reconstruções em Blender, feitas a partir das dez imagens fornecidas em 9 de outubro de 2026. Os originais desta biblioteca permanecem independentes e editáveis. A integração nativa, com 91 instâncias destes dez modelos, colisões e níveis de detalhe, está em [porto_construido](../porto_construido/LEIA-ME.md). As portas dessa implantação ficam na pose aberta; interação e validação visual no cliente estão pendentes.

Abra `Catalogo_10_estruturas.blend` para ver o conjunto. Cada construção também possui um arquivo independente na pasta `modelos/`, com as imagens e fontes necessárias empacotadas. A escala está em metros; o térreo fica em Z = 0. A fachada principal aponta para -Y. As posições do catálogo servem somente para apresentação.

| Referência | Arquivo em modelos/ | Conteúdo interno |
|---|---|---|
| 01 | `01_Casa_creme_varanda.blend` | Varanda recuada, sala, cozinha, quarto e banheiro |
| 02 | `02_Casa_amarela.blend` | Sala, cozinha, quarto e banheiro |
| 03 | `03_Sobrado_azul.blend` | Dois pavimentos, escada, cozinha, quartos e banheiros |
| 04 | `04_Predio_verde_varandas.blend` | Três pavimentos, duas varandas, escadas, quartos e banheiros |
| 05 | `05_Predio_creme_varandas.blend` | Três pavimentos, duas varandas, escadas, quartos e banheiros |
| 06 | `06_Mercado.blend` | Balcão, caixa, estantes, produtos e caixotes de frutas |
| 07 | `07_Farmacia.blend` | Balcão, vitrines, estantes de medicamentos, área de atendimento e piso superior |
| 08 | `08_Mercearia_sobrado.blend` | Loja, balcão, estoque, escada e moradia superior |
| 09 | `09_Posto_combustivel.blend` | Duas bombas com mangueiras, cobertura, proteção de pilares e loja de conveniência |
| 10 | `10_Galpao_oficina.blend` | Bancada, ferramentas, caixotes, estantes e mezanino com escada |

## Geometria e organização

As paredes têm espessura e aberturas reais. As telhas, venezianas, guardas de varandas, calhas, molduras e móveis são geometria editável. Os pavimentos superiores possuem vãos nas lajes para as escadas. Os módulos simples compartilham dados de malha; no catálogo, os materiais e cubos equivalentes também são reutilizados.

Cada prédio tem uma coleção `Modelo_completo`, marcada como asset e dividida em `Arquitetura`, `Cobertura`, `Esquadrias`, `Vegetacao`, `Interior_1` e demais pavimentos, `Iluminacao` e `Metadados`. O controle `Estrutura_XX` move toda a construção, preservando as dobradiças. `Apresentacao` fica separado. `Colisao_preparada` contém volumes de referência de paredes, pisos e escadas, ocultos durante a apresentação. Esses volumes não são arquivos nativos YBN nem confirmam física funcionando dentro do jogo.

As portas possuem controles de dobradiça. O quadro 1 mostra a posição fechada; o quadro 40 mostra a abertura. O portão do galpão tem controle separado de subida. Esses movimentos são estudos no Blender; a interação e a sincronização entre jogadores precisam ser implementadas na exportação para FiveM.

## Materiais e fidelidade

As referências dos prédios foram copiadas sem alteração para `referencias/`. As dez texturas planas enviadas depois foram copiadas sem alteração para `texturas/`. Os PNGs das paredes e madeiras alimentam diretamente a cor dos materiais, preservando seus pixels; o desgaste na base das paredes foi orientado para baixo. As portas, molduras de madeira e lâminas das venezianas têm a textura aplicada em geometria tridimensional.

Os mapas de relevo e rugosidade são aproximações calculadas nos nós do Blender a partir da luminosidade das imagens. Não são medidas físicas da superfície. A iluminação do render também altera a aparência das cores. O telhado cerâmico usa geometria de telhas e variação de material; o galpão usa amostras da sua referência de chapa metálica. As letras dos comércios são geometria própria. Nenhum arquivo original foi sobrescrito.

| Estrutura | Parede fornecida | Madeira fornecida |
|---|---|---|
| Casa com varanda | 07 — creme | 04 — azul petróleo |
| Casa amarela | 08 — amarelo | 01 — verde escuro |
| Sobrado azul | 05 — azul | 03 — verde água |
| Prédio verde | 09 — turquesa | 01 — verde escuro |
| Prédio creme | 07 — creme | 01 — verde escuro |
| Mercado | 05 — azul | 02 — azul claro |
| Farmácia | 06 — verde | 01 — verde escuro |
| Mercearia | 05 — azul | 04 — azul petróleo |
| Posto | 07 — creme, com faixas próprias | 02 — azul claro |
| Galpão | Chapa metálica da referência | Portão metálico da referência |

`Biblioteca_materiais.blend` contém os dez materiais marcados como assets, com os PNGs empacotados. Pode ser anexada pelo menu **File → Append → Material** ou usada pelo navegador de assets. A textura 10, de reboco laranja, fica disponível para futuras variações, mesmo sem aparecer nestas dez referências.

Esta entrega é uma primeira versão tridimensional para revisão. **O conjunto não é uma cópia 100% idêntica das imagens dos prédios.** As texturas planas de parede e madeira são as fornecidas pelo usuário; as faces não visíveis, as medidas e os interiores foram reconstruídos. Telhados, vegetação ornamental, móveis e alguns detalhes de fachada são aproximações editáveis. As referências continuam disponíveis para orientar ajustes de acabamento.

Os materiais de apresentação ainda devem ser convertidos em texturas UV próprias para os shaders do jogo. A implantação na ilha também exige exportação nativa, colisão, LODs, tratamento de interiores e validação no FiveM.

## Conferência visual

`previews/catalogo.png` mostra o conjunto. Para cada referência existem `previews/XX_exterior.png` e `previews/XX_interior.png`. As vistas internas são cortes de apresentação: coberturas e paredes externas são temporariamente ocultadas para enxergar o térreo. Os pavimentos superiores continuam completos nos arquivos Blender.

O relatório `dados/validacao_blender.json` registra a reabertura dos dez arquivos, a geometria, as dependências empacotadas, os degraus, os vãos das lajes e a passagem do portão do galpão. `dados/fontes_originais.json` compara o SHA-256 de todas as vinte imagens copiadas com seus arquivos originais. Essa conferência é do Blender; não é um teste de funcionamento no servidor.

## Reconstrução da biblioteca

Com Blender 5.2, execute `scripts/modelar_estruturas.py`. O argumento `--ids 1,2` gera somente as referências indicadas; `--sem-render` salva os modelos sem renderizar. A geração já aplica as texturas planas e o refinamento. `scripts/aplicar_texturas_fornecidas.py` atualiza modelos existentes e a biblioteca de materiais; `scripts/refinar_modelo.py` atualiza os detalhes e as prévias. Esses dois scripts verificam se suas alterações já foram aplicadas para evitar duplicá-las. `scripts/catalogo_e_validacao.py` reabre e verifica os arquivos e gera o catálogo. `--so-validar` limita essa última etapa às verificações.

`scripts/conferir_passagens.py` atualiza as ligações do telhado e as passagens da varanda e do galpão. Já é chamado pelo refinamento. `scripts/revisar_acabamento.py` é uma etapa antiga de extração de amostras, anterior às texturas planas fornecidas. Não faz parte do fluxo atual.

Os scripts escrevem somente nesta pasta da biblioteca. Não modificam o terreno, os recursos ou a configuração do servidor.
