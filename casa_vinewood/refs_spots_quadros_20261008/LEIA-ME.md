# Spots embutidos e quadros — 08/10/2026

Modelos criados no Blender e instalados no recurso `server-data/resources/cidade_mansao`. A fonte editável é [mansao_spots_quadros.blend](../mansao_spots_quadros.blend). A instalação foi verificada a partir dos próprios arquivos nativos instalados. A conferência visual dentro do FiveM ainda está pendente.

## Aplicação no jogo

No console **do servidor**, execute:

```text
restart cidade_mansao
```

Depois, saia e conecte novamente à cidade para carregar os novos arquivos de mapa. O comando acima pertence ao console do servidor. O F8 do jogador não reinicia recursos do servidor.

## Modelos e posições

| Referência | Aplicação | Dimensões |
| --- | --- | --- |
| Print 1 | Substitui os 88 spots circulares do teto, nas posições existentes | Diâmetro de 17 cm; cavidade de 12,4 cm; encaixe de 4,8 cm |
| Print 2 | Parede interna do escritório, térreo | 98,6 × 150,6 cm; moldura bronze com filete |
| Print 3 | Parede oeste da sala de jogos/TV, térreo | 103,9 × 133,6 cm; moldura bronze com filete |
| Print 4 | Hall do térreo, à esquerda do par novo | 105 × 140,6 cm; moldura preta |
| Print 5 | Hall do térreo, à direita do par novo | 100,8 × 140,6 cm; moldura preta |

Os spots têm aro branco chanfrado, refletor metálico côncavo, lente com pequenas facetas e núcleo LED quente emissivo. As cavidades foram abertas na geometria visual dos tetos; o topo do piso superior e as colisões originais de piso/teto continuam iguais.

Os quadros têm tela com 8 mm e molduras de aproximadamente 4,5 cm de profundidade. O centro fica a 1,75 m do piso. A arte foi extraída das próprias referências, sem o fundo transparente e sem reproduzir a moldura como uma imagem plana. Cada tela preserva sua proporção e orientação. As molduras e o fundo são malhas fechadas, com colisão simples de 12 triângulos por quadro.

Os objetos anteriores, a cozinha, os vasos e os quadros existentes foram preservados. Os 20 perfis e 20 tiras de LED da escada continuam no drawable original de iluminação decorativa. Os pendentes não foram substituídos.

## Qualidade e desempenho

- Um único modelo de spot é reutilizado 88 vezes no mapa. Ele contém quatro LODs nativos: 2.400, 1.200, 600 e 400 triângulos, com transições a 5, 12, 30 e 70 m.
- Os quatro quadros compartilham `mansao_quadros_refs.ytd`. Cor em BC1, 1.024 × 2.048; relevo discreto em BC3, 512 × 1.024. Mipmaps completos para o limite do formato GTA Gen8 e todas as cores opacas.
- Os novos spots não criam laços de iluminação adicionais. O controlador da iluminação ampla foi preservado byte a byte, com limite de 24 luzes ativas, preenchimento ambiente e luz quente. O núcleo emissivo é o detalhe visual da lâmpada; a iluminação ampla do cômodo continua separada dele.
- A revisão acrescenta 12,008 MiB à alocação gráfica declarada dos arquivos RSC7, reduz 0,727 MiB da alocação de sistema e acrescenta aproximadamente 5,073 MiB em disco. Esses valores vêm dos cabeçalhos de streaming; não são uma medição de FPS ou do consumo real de VRAM.

## Verificação

[verification.json](verification.json) confirma os 88 encaixes por interseção de raios contra as malhas nativas, o apoio dos quatro quadros em nove pontos por quadro, UVs frontais, mipmaps, shaders e referências de textura. Os materiais e colisões originais de piso/teto foram comparados com o backup anterior à revisão. Todos os 12 arquivos nativos foram recarregados após a instalação.

[installation.json](installation.json) registra os hashes dos 13 arquivos instalados, incluindo o manifesto. Os outros 64 arquivos do recurso foram preservados. O backup completo anterior está registrado em [baseline.json](baseline.json); um backup imediato das substituições fica em `backup_imediato_instalacao`.

As imagens abaixo são prévias do Blender. A iluminação é uma aproximação para inspeção dos modelos e não substitui a conferência dentro do FiveM.

![Spot](previa_spot_embutido.png)

![Quadros no hall](previa_quadros_hall.png)

![Quadro no escritório](previa_quadro_escritorio.png)

![Quadro na sala de jogos](previa_quadro_jogos.png)

## Reconstrução

Na raiz do projeto, a sequência de fontes é `prepare_textures.py`, Blender em modo background com `build_models.py`, `package_models.py` e `verify_models.py`. `render_previews.py` gera as prévias. Depois da instalação, `verify_models.py --installed` valida os arquivos do recurso e compara com o backup original. `install.py` instala somente os arquivos listados em `package.json`, valida o manifesto e preserva alterações concorrentes em outros arquivos.
