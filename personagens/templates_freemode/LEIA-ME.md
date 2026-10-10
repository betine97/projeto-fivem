# Bases de criação — Freemode masculino GTA V

Dois projetos independentes, extraídos dos arquivos originais da instalação local do GTA. A base escolhida é `mp_m_freemode_01`, com cabeça 000, tronco sem camisa 015, bermuda 014 e pés com chinelos 005. Ela não reproduz o rosto personalizado de um jogador nem o personagem Cartelking.

## Arquivos

- `01_BASE_ROUPAS.blend`: corpo de referência protegido contra seleção, com coleção `03_CRIAR_ROUPAS_AQUI` para as novas peças.
- `02_BASE_ANIMACOES.blend`: mesmo corpo, esqueleto com 128 ossos, aberto em Pose Mode e ação `NOVA_ANIMACAO` com repouso no quadro 1. Timeline em 30 FPS, quadros 1–60.
- `referencia_frente.png`, `referencia_lateral.png`, `referencia_costas.png`: vistas ortográficas para acompanhar a geração de roupas.
- `teste_esqueleto.png`: flexão técnica de braços e perna para verificar a deformação. A ação `TESTE_FLEXAO` fica arquivada no arquivo de animação.
- `PROMPT_ROUPAS.txt`: prompt reutilizável com medidas e campos para definir cada peça.
- `medidas.json`: medidas e alturas das seções utilizadas.
- `source/`: componentes originais, texturas e manifesto SHA-256.
- `work/`: scripts reproduzíveis, logs e relatórios de validação.

## O que foi preservado

Geometria, UV e pesos das quatro peças originais foram comparados entre os objetos importados e os objetos de trabalho. As texturas difusas originais foram carregadas e incorporadas aos arquivos Blender, junto das imagens de material disponíveis. A coleção oculta `00_ORIGINAIS_GTA_NAO_EDITAR` conserva a estrutura importada, inclusive os LODs disponíveis.

O rig de trabalho usa o esqueleto nativo da cabeça 000, com os ossos faciais dessa cabeça e os ossos corporais compatíveis. Os ossos corporais usados pelos componentes foram comparados ao esqueleto externo Freemode; a maior diferença numérica de matriz encontrada foi aproximadamente 0,000041. Nenhum osso foi redesenhado e nenhum peso automático foi aplicado.

Escala: 1 unidade Blender = 1 metro. Frente: -Y. Vertical: +Z. A origem GTA permanece junto à pelve; o personagem não foi transladado para pôr os pés em Z=0. Altura total da composição: 181,8 cm, incluindo chinelos. A bermuda cobre a pelve: não foi inventada uma malha de corpo nu sob ela.

## Criar roupas

Importe a peça nova e coloque-a na coleção `03_CRIAR_ROUPAS_AQUI`. Ajuste a roupa ao corpo, mantendo a pose e escala da referência. Transfira e refine os pesos, confira interseções com o corpo, finalize UV, materiais e LODs. O corpo de referência não deve ser exportado inteiro como parte da roupa.

Geração por IA e medidas no prompt não garantem encaixe exato. O ajuste final é feito sobre esta malha no Blender. Para roupas que substituem componentes do corpo, também será necessário preparar as partes visíveis corretas, evitando pele atravessando o tecido.

## Criar movimentos

Abra `02_BASE_ANIMACOES.blend`, selecione `MP_M_FREEMODE_01_RIG` e trabalhe em Pose Mode na ação `NOVA_ANIMACAO`. O primeiro quadro conserva a pose de referência. Crie os movimentos com chaves de rotação e, quando apropriado, posição do `SKEL_ROOT`.

Não altere os ossos em Edit Mode, seus nomes, tags ou parentesco. Não aplique uma pose como novo repouso. Este é o rig nativo de deformação, sem controles IK adicionais. Animação facial corresponde à cabeça 000; expressões de outras cabeças exigem validação específica.

Para testar o rig, escolha a ação arquivada `TESTE_FLEXAO` no Action Editor e percorra os quadros 1–30. Ela é apenas um teste técnico de deformação. Volte para `NOVA_ANIMACAO` antes de começar o movimento definitivo.

Quando uma animação estiver criada, configure o clip e o dicionário de animação no Sollumz, exporte YCD e teste com o personagem no FiveM. Estes arquivos são bases de autoria: nenhuma roupa ou animação nova foi instalada no jogo nesta entrega.

## Validação

Os renders de repouso e flexão foram inspecionados. `work/validation.json` registra malhas, assinaturas de geometria/UV e esqueleto; `work/pose_validation.json` registra deslocamentos após deformação. `work/reopen_validation.json` registra a conferência dos dois arquivos após reabertura. A validação é de Blender; futuros movimentos e peças ainda precisam de teste no jogo.
