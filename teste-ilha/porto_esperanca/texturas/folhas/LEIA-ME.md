# Folhas — primeira aplicação no Blender

Em 09/10/2026 o usuário enviou dez imagens de copas/frondes e autorizou começar com elas. Os PNG originais foram copiados sem alterações para `lote01/`; o manifesto registra origem, dimensões, transparência e SHA-256.

## Abrir a amostra

- `../../porto_esperanca_texturas_lote01.blend`: versão separada do porto, com dez modelos texturizados e as instâncias desses modelos atualizadas no terreno.
- `../../modelos/texturas_lote01/`: dez projetos individuais completos, com câmera, iluminação e imagens incorporadas.
- `../../previews/texturas_lote01/`: catálogo, árvore de sombra em dois ângulos e vista da praça/porto.
- `../../dados/aplicacao_texturas_lote01.json`: relações entre imagens e modelos, regiões UV e contagens das malhas.
- `../../dados/verificacao_texturas_lote01.json`: conferência de UV, imagens incorporadas, arquivos individuais e preservação da implantação.

No arquivo principal, as cenas `Amostra texturas lote01` e `Detalhe arvore texturizada` permitem examinar a vegetação separadamente. A cena `Porto Esperanca` mostra a implantação no terreno.

## Associações da primeira amostra

As espécies foram relacionadas pela aparência das imagens e pelas pranchas anteriores. São associações iniciais para validação do usuário, não identificação botânica confirmada pelos nomes dos arquivos.

| Imagem de folhas | Modelo | Tronco recebido |
|---|---|---|
| `folhas_01` | `03_caneleira` — Árvore de Sombra | `lote01_03` |
| `folhas_02` | `01_coqueiro` — Palmeira de Coco | `lote01_01` |
| `folhas_03` | `05_flamboyant` | `lote01_05` |
| `folhas_04` | `04_amendoeira` | `lote01_04` |
| `folhas_05` | `02_imperial` — Palmeira Imperial | `lote01_02` |
| `folhas_06` | `07_reseda` | `lote01_07` |
| `folhas_07` | `09_oliveira` | `lote01_09` |
| `folhas_08` | `08_ipe_amarelo` | `lote01_08` |
| `folhas_09` | `10_castanhola` — Amendoeira da Praia | `lote01_10` |
| `folhas_10` | `06_arvore_rua` | `lote01_06` |

## Técnica e limites

Troncos e galhos continuam em geometria 3D. Os materiais usam regiões opacas dos recortes de casca por coordenadas UV, com ajuste de tom e relevo no shader. Os PNG não foram recortados, pintados ou substituídos; as imagens estão incorporadas nos arquivos Blender.

As oito árvores de copa mantêm suas folhas e flores modeladas em 3D. As imagens fornecem cor e detalhe por regiões opacas de folhagem, com UV individual em cada folha; não são a copa inteira aplicada em um plano, nem reconstrução individual de cada folha da fotografia. As flores mantêm seus materiais próprios. As duas palmeiras têm 22 frondes, com folíolos curvos modelados e texturizados individualmente. A iluminação das imagens permanece como parte dos materiais. É uma primeira aplicação de textura sobre as malhas autorais; os recortes de copas completas não têm o detalhe de um atlas fotografado de folhas isoladas.

Os dez modelos receberam materiais próprios; os outros catorze continuam com os materiais anteriores. Posições e escalas das instâncias, terreno, lotes, vias, grama e pedras permanecem na implantação existente. O arquivo procedural anterior e seus modelos individuais foram preservados.

A aparência desta primeira aplicação está sujeita à validação do usuário. O pacote não contém LODs, materiais nativos GTA, colisões de vegetação ou instalação no FiveM. A leitura dos arquivos e os renders não comprovam desempenho ou física no jogo.

Conferência concluída em 09/10/2026: **123 verificações passaram**, incluindo reabertura do arquivo do porto e dos dez projetos individuais, imagens incorporadas, UV, originais intactos e preservação das posições, escalas, lotes, terreno, grama e pedras. As quatro prévias finais foram inspecionadas visualmente. A aplicação direta das copas inteiras em superfícies foi descartada por apresentar bordas artificiais; o arquivo final usa as folhas 3D descritas acima.

## Reproduzir

Na raiz do projeto:

```powershell
& 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe' --background --python 'teste-ilha/porto_esperanca/scripts/aplicar_texturas_lote01.py'
& 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe' --background --python 'teste-ilha/porto_esperanca/scripts/exportar_texturas_lote01.py'
& 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe' --background --python 'teste-ilha/porto_esperanca/scripts/verificar_texturas_lote01.py'
```

O primeiro comando parte de `porto_esperanca.blend` e substitui somente a versão `porto_esperanca_texturas_lote01.blend`. Guardar alterações manuais dessa versão antes de reproduzir. Para refazer apenas as prévias do arquivo texturizado salvo, acrescentar `-- --somente-render` ao primeiro comando.
