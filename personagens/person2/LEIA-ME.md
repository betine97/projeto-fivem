# Person2

GLB original: `C:\Users\erons\Downloads\Meshy_AI_hazmat_worker_lowpoly_1005172433_texture.glb`.

Conversão direta por Python e szio, sem abrir ou executar Blender. Malha e triângulos originais preservados. Apenas conversão de eixos/UV para GTA e ligação ao esqueleto nativo para permitir movimentos. Os PNGs originais ficam preservados em `textures`. O atlas de cor permanece em 4096 × 4096, convertido para DDS BC1 para reduzir a memória de streaming. O mapa metallic/roughness é convertido para o specular de 1024 × 1024 usado pelo jogo. O relatório registra o erro de cor da compressão GPU.

Digite `person2` no console F8. Use `roupaanterior` para restaurar o personagem anterior. A prévia `preview_native.png` é uma verificação dos arquivos nativos, não uma captura dentro do FiveM.

Arquivos exportados em `exports`, instalados no resource `cidade_roupas`. O script `work/convert_direct.py` permite repetir a conversão sem Blender; `exports/validation.json` registra a verificação da geometria, UV, texturas e esqueleto.
