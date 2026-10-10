# Porto Esperança — terreno e vegetação

Etapa de 09/10/2026, baseada nas três imagens aprovadas pelo usuário. Este pacote preserva a preparação editável do Blender. A montagem da ilha e o pacote FiveM estão em [porto_construido](../porto_construido/LEIA-ME.md), com as construções texturizadas corretas, cais, ponte, vegetação e colisões.

Os dois lotes de folhagem fornecidos estão em `porto_esperanca_vegetacao_vento.blend` e `modelos/vegetacao_vento/`: 18 modelos com texturas empacotadas, raízes fixas e vento. `dados/verificacao_vegetacao_vento.json` registra a conferência no Blender. A exportação nativa incorpora os volumes de colisão dos troncos e os materiais de vento; o balanço no cliente FiveM ainda precisa ser observado. As descrições abaixo documentam a etapa original de planejamento.

## Abrir e consultar

- `porto_esperanca.blend`: cena principal, catálogo e materiais procedurais.
- `porto_esperanca_texturas_lote01.blend`: primeira versão com imagens de troncos/folhas fornecidas pelo usuário, aplicada a dez modelos; inclui cenas de amostra e detalhe.
- `modelos/`: 24 arquivos Blender individuais, um para cada modelo distinto das pranchas.
- `referencias/`: cópias das três imagens fornecidas pelo usuário.
- `texturas/troncos/`: 16 recortes originais de troncos/galhos enviados posteriormente, catálogo e manifesto de origem.
- `texturas/folhas/`: primeiro lote de dez imagens de folhagem, relações com modelos e documentação da aplicação.
- `modelos/texturas_lote01/` e `previews/texturas_lote01/`: modelos individuais texturizados e novas prévias.
- `previews/`: vista geral, praça reservada, foz, planta dos lotes e duas páginas de catálogo.
- `dados/implantacao.json`: medidas, modelos, contagens, lotes, circulação e verificação das exclusões.
- `dados/verificacao_blender.json`: resultado da reabertura da cena e dos arquivos individuais.
- `dados/vegetacao_posicoes.json` e `pedras_posicoes.json`: posições reproduzíveis da vegetação e das pedras.
- `scripts/criar_porto_blender.py`: geração com semente fixa `20261009`.

## Escopo desta etapa

Foi criado um trecho com contexto de aproximadamente 1.040 × 1.030 metros para representar a baía e os morros da referência. O núcleo urbano planejado cabe aproximadamente na área de 600 × 450 metros discutida. Isso não altera o tamanho da ilha existente: as coordenadas deste arquivo são locais e a implantação no mundo ainda precisa ser escolhida.

O terreno está dividido em 16 setores e possui praia, encostas, morros, canal do rio e água de apresentação. A rede de circulação tem avenidas, ruas, ligação ao interior, trilha e passeio costeiro; a travessia elevada é uma superfície de referência para uma ponte futura.

Existem 25 reservas: terminal, praça, pesca/apoio naval, pátio/armazéns, alfândega, oficina, posto de combustível e 18 lotes urbanos. Os edifícios não foram construídos. As áreas aparecem como solo preparado e possuem marcadores em coleção separada. Os marcadores são visíveis no editor e na planta, mas não nas vistas de paisagem.

As árvores foram modeladas proceduralmente em geometria 3D a partir das silhuetas, cores e categorias das referências. Não são modelos 3D extraídos das imagens nem réplicas botânicas exatas. As espécies repetidas nas duas pranchas usam o mesmo modelo correspondente. Troncos, ramos, folhas, raízes aparentes e flores possuem materiais separados; as palmeiras têm frondes e folíolos, as bananeiras folhas largas, o mangue raízes de apoio e os arbustos portes menores.

Instâncias compartilham a malha do modelo original e variam escala e rotação. Distribuição por contexto: palmeiras e castanholas perto da costa, mangue nas margens, árvores de sombra no bairro, copas maiores nos morros, arbustos e vegetação baixa no sub-bosque. Lotes e corredores possuem afastamentos de exclusão. Pedras aparecem principalmente na costa e nas encostas.

Contagens desta versão: **24 modelos distintos, 4.107 instâncias de árvores/arbustos/plantas tropicais, 4.200 tufos de grama, 430 pedras, 25 reservas e 10 rotas de circulação**. Os arquivos individuais incluem cena, câmera e iluminação, permitindo abrir cada planta diretamente no Blender.

Verificação concluída: **67 verificações passaram**, incluindo reabertura da cena principal e dos 24 arquivos individuais, presença de todas as categorias no terreno, contagens, coordenadas finitas e exclusões de lotes/circulação. As seis prévias foram geradas no Blender e inspecionadas visualmente. Isso valida o artefato desta etapa, não desempenho ou física no FiveM.

## Organização no Blender

| Coleção | Conteúdo |
|---|---|
| `01_TERRENO` | 16 setores de terreno e atributo de cor `Bioma` |
| `02_AGUA_VISUAL` | Mar e superfície de rio para apresentação |
| `03_CIRCULACAO` | Vias, passeios e travessia provisória |
| `04_VEGETACAO` | Instâncias de árvores, arbustos e tufos de grama |
| `05_RESERVAS_E_IDENTIFICACAO` | Reservas de futuras estruturas e identificadores |
| `06_PEDRAS` | Instâncias de sete variações de rocha |
| `07_COLISAO_REFERENCIA` | Malhas do solo para preparação de física, ocultas |
| `08_CAMERAS_LUZES` | Quatro câmeras e iluminação de apresentação |
| `09_BIBLIOTECA_VEGETACAO` | Modelos mestres, ocultos na cena principal |

As cenas `Catalogo 01` e `Catalogo 02` mostram os 24 modelos separadamente. Editar uma malha mestre altera as instâncias vinculadas no cenário; os arquivos em `modelos` também permitem abrir cada planta individualmente.

## Relação com as pranchas

Prancha 2: todas as 18 categorias têm modelo correspondente, com IDs `01` a `18`.

Prancha 3:

| Categoria da referência | Modelo |
|---|---|
| Palmeira de Coco | `01_coqueiro` |
| Árvore de Sombra / Caneleira | `03_caneleira` |
| Mangueira | `11_mangueira` |
| Flamboyant | `05_flamboyant` |
| Oiti | `19_oiti` |
| Amendoeira da Praia | `10_castanhola` |
| Figueira | `20_figueira` |
| Palmeira Areca | `21_areca` |
| Palmeira Leque | `22_palmeira_leque` |
| Bananeira | `12_bananeira` |
| Palmeira Imperial | `02_imperial` |
| Palmeira Azul | `16_palma_azul` |
| Jasmim-Manga | `23_jasmim_manga` |
| Resedá | `07_reseda` |
| Arbusto Costeiro | `14_arbusto_costeiro` |
| Vegetação Baixa Tropical | `24_vegetacao_baixa` |

## Limites e próxima etapa

Em 09/10/2026 foram recebidas 16 imagens de troncos e galhos e, depois, dez imagens de folhagem. O usuário autorizou começar com essas folhas. Dez modelos receberam materiais de casca por UV e folhagem na versão separada `porto_esperanca_texturas_lote01.blend`, mantendo as instâncias no terreno. As associações por espécie e a aparência aguardam validação do usuário. Consultar `texturas/folhas/LEIA-ME.md` para técnica, relações, arquivos e reprodução. O arquivo anterior continua com seus materiais procedurais.

A água é visual do Blender. As malhas de colisão são referências e não arquivos YBN. Materiais procedurais ainda precisam de preparação para os shaders nativos; vegetação precisa de LODs e colisões simplificadas dos troncos antes de integrar o FiveM. Nenhum recurso, spawn, configuração ou arquivo da ilha em execução foi substituído nesta etapa.

Após validar aparência, porte das árvores, circulação e posição dos lotes, escolher a implantação na ilha. Depois preparar materiais, física, níveis de detalhe e pacote nativo. Casas, prédios, armazéns, cais e ponte detalhada ficam para etapas seguintes, conforme solicitado.

## Regerar

Na raiz do projeto:

```powershell
& 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe' --background --python 'teste-ilha/porto_esperanca/scripts/criar_porto_blender.py'
& 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe' --background --python 'teste-ilha/porto_esperanca/scripts/exportar_modelos.py'
& 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe' --background --python 'teste-ilha/porto_esperanca/scripts/verificar_blender.py'
```

Regerar substitui este arquivo Blender e os modelos deste pacote. Guardar as alterações manuais antes de executar. Para refazer somente as prévias a partir do arquivo salvo:

```powershell
& 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe' --background --python 'teste-ilha/porto_esperanca/scripts/criar_porto_blender.py' -- --somente-render
```
