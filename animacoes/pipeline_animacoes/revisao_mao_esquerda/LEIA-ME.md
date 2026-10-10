# Revisão da mão esquerda — personagem deitado com AK

## Personagem ajoelhado com AK

A cópia corrigida desta postura é `ajoelhado_r01/ajoelhado_ak_mao_esquerda.blend`. A ação selecionada é `REVISAO_apoio_esquerdo_ajoelhado_r01` e o disparo usa `REVISAO_recuo_ajoelhado_r01`.

A palma, o pulso, a rotação do antebraço e os dedos seguem a pegada revista sob o guarda-mão. A correção permanece durante os 30 quadros do recuo. O contato do pulso com a arma varia menos de 0,001 mm no clipe; a pose das pernas e a mão direita mantêm os movimentos anteriores. Os arquivos `surface_check.json`, `surface_recoil_5.json` e `surface_recoil_10.json` registram zero cruzamentos de superfícies na mira, no pico do recuo e no retorno.

Os PNGs numerados mostram as laterais, a frente, a pose inteira e um quadro do recuo. Esta revisão modifica a mira e o recuo na cópia do Blender; a recarga e os arquivos instalados no FiveM ainda não foram alterados.

## Personagem deitado com AK

A revisão atual é `r08/deitado_ak_mao_esquerda.blend`.

Abra a cópia no Blender e mantenha a ação `REVISAO_apoio_esquerdo_r08`, quadro 1. A mesma pose fica disponível nos quadros 1–30 para inspeção. Os PNGs em `r08` mostram as duas laterais, a frente, a vista inferior, a vista superior e o personagem inteiro.

Foi ajustado apenas o braço esquerdo, o pulso e os dedos. A palma apoia a parte inferior do guarda-mão, sob o cano. A rotação do antebraço acompanha o punho. As pontas dos dedos usam a direção medida na malha da mão, em vez de assumir que todos os ossos possuem o mesmo eixo.

O esqueleto nativo, seus identificadores, a mão direita, o fuzil e o restante da pose foram preservados. `r08/ajuste.json` registra os parâmetros utilizados e as verificações do esqueleto e da pose. `r08/surface_check.json` registra zero cruzamentos entre as superfícies da mão esquerda e do fuzil na pose inspecionada.

Esta cópia é uma revisão visual da pose de mira. Ela ainda não foi incorporada às animações de recarga/recuo nem instalada no FiveM. Os arquivos de jogo e as fontes v5 permanecem como estavam.

`review_grip.py` reproduz a pose e os renders a partir da fonte v5, com os parâmetros em `r08/ajuste.json`. `check_overlap.py -- r08`, executado pelo Blender em modo de fundo, inspeciona a mão já deformada e a superfície da arma. As demais pastas contêm tentativas intermediárias.
