# Traje de guarda

Fonte: Meshy_AI_guard_character_3d_1005050026_image-to-3d-texture.glb.

`GUARDA_ESQUELETO_GTA.blend` contém a malha original, as imagens originais incorporadas e o esqueleto masculino Freemode do GTA. A geometria não foi esculpida, reduzida, soldada ou reconstruída. Foi aplicada apenas uma translação global de 1,002028 m para alinhar o personagem ao chão do GTA. A escala permanece 1:1.

O arquivo mantém 318.137 vértices e 597.401 triângulos, os UVs e os materiais originais. Os hashes das imagens incorporadas e os testes de preservação estão em `work/validation.json`. Os pesos usam no máximo quatro ossos por vértice. O teste de braços, cotovelo, coxa e joelho terminou sem arestas com esticamentos extremos segundo o critério registrado no script. Isso não substitui a conferência de todas as animações dentro do jogo.

`GUARDA_FIVEM.blend` contém a versão exportável. A divisão em componentes e blocos exigidos pelo GTA conserva todos os triângulos. Os arquivos de jogo usam shaders GTA e texturas DDS na resolução original: 4096×4096 para cor e normal, 2048×2048 para o mapa convertido de rugosidade/especular. A compressão BC3 necessária ao formato de jogo não é uma cópia pixel a pixel dos PNGs; os PNGs e o material do arquivo de autoria permanecem intactos. Iluminação e resposta do material também variam entre Blender e GTA.

O modelo é pesado porque a malha inteira foi mantida em todos os níveis de distância, conforme solicitado.

Recurso da cidade: `server-data/resources/cidade_roupas`.

- `/guardavermelho`: veste o modelo enviado com o esqueleto GTA.
- `/macacaobranco` ou `/trajelab`: veste a versão atual do macacão branco; o refinamento visual foi suspenso pelo usuário.
- `/roupaanterior`: restaura o modelo, componentes e acessórios anteriores à primeira troca.

O GLB não contém um rosto. Nenhum rosto ou máscara adicional foi inventado para esta versão.

Os testes de comando são executados por `python personagens/traje_guarda/work/test_outfits.py`. Os renders são prévias do Blender; não são capturas do FiveM.
