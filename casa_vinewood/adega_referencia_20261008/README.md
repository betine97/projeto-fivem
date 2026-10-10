# Adega com quatro vitrines na parede marcada

Reconstrução 3D no Blender 5.2 baseada na referência enviada. Foram modelados
quatro expositores com molduras pretas e portas de vidro, 52 garrafas horizontais,
prateleiras centrais de madeira, bebidas e decantadores, taças, quadro pequeno,
planta pendente, vaso de folhagem, bancada e fundo de mármore claro, três portas
de armário, uma adega refrigerada com 25 garrafas internas e abajur de latão.
Os canais de LED e difusores são geometria com material emissivo.

O móvel mede **4,715 m de largura × 2,96 m de altura**, com corpo de 0,60 m
e profundidade total aproximada de 0,647 m incluindo os puxadores. A largura
e altura preservam a proporção da referência. Ele ocupa a parede marcada no
lado oposto ao bar anterior: origem local da casa `(9.444, -0.968, -0.800)`.
A passagem à esquerda permanece livre, com 44 mm até seu limite. Há 18 mm
até a parede posterior, 27 mm na lateral direita e 198 mm até o teto.
O móvel e suas colisões ficam fixos para manter o encaixe.

É uma reconstrução a partir de uma única imagem, com materiais próprios.
As proporções e a composição seguem a referência; inscrições pequenas dos
rótulos, reflexos e microdetalhes não constituem reprodução fotográfica exata.

## Fontes e prévias

- `adega_vitrines_editavel.blend`: 1.157 peças separadas e editáveis.
- `mansao_com_adega.blend`: cópia independente da cena com o móvel instalado.
- `adega_frontal_blender.png`: prévia frontal renderizada no Blender.
- `adega_na_parede_blender.png`: prévia do encaixe renderizada no Blender.
- `reference.png`, `game.png`, `marked_wall.png`: referências fornecidas.
- `spec.json`: medidas, posicionamento, colisões e orçamento de geometria.

## Exportação e desempenho

O arquivo nativo reúne as peças em um modelo com 17 geometrias por material
em cada LOD. Isso evita exportar 1.157 modelos separados. Foram gerados quatro
LODs reais: **93.661 / 48.667 / 20.534 / 6.467 triângulos**, com transições
a 18 / 35 / 65 / 120 metros. As texturas DDS têm compressão BC e mipmaps;
o drawable usa 2,5 MiB gráficos e aproximadamente 11,38 MiB de memória de
sistema segundo os cabeçalhos nativos. Colisões simplificadas incluem as
quatro portas de vidro, sem usar a malha decorativa detalhada como colisão.

O script próprio possui oito luzes quentes locais, com limite de distância,
restrição ao térreo e ao lado interno da parede. Longe do móvel, a rotina
aguarda 750 ms. Não altera o controlador de iluminação geral da mansão.

## Instalação e conferência

`install.py` instala somente `mansao_adega_vitrines.ydr`, `.ytyp`, `.ymap`,
`.ybn` e `adega_vitrines_luzes.lua` no recurso `cidade_mansao`, acrescentando
as respectivas linhas ao manifesto atual. Acrescenta o modelo à lista de
proteção do editor para preservar a montagem fixa. IDs, posições, escalas e
demais objetos do catálogo permanecem iguais. Os backups imediatos ficam
em `backup_preinstall`; `installation.json` registra os hashes instalados.

`verification.json` registra a leitura dos quatro formatos nativos, os quatro
LODs, índices, normais, tangentes, áreas dos triângulos, payloads DDS, mipmaps,
colisões, encaixe e execução simulada do script de luzes perto/longe.
Esses testes passaram. A validação visual dentro do FiveM ainda depende da
ativação e não foi realizada: as imagens são prévias do Blender.

Para ativar os arquivos instalados, executar **`restart cidade_mansao` no
console do servidor** e reconectar ao FiveM. Esta instalação não reinicia
o servidor completo nem altera os comandos, o clima ou os outros recursos.

## Textura de mármore derivada da referência

Modo usado: **ferramenta imagegen integrada (edição)**, sem CLI.
Entrada: `reference.png`, a imagem da adega enviada pelo usuário.
Saída final preservada: `textures/marmore_referencia.png`.
Prompt final enviado:

```text
Use case: precise-object-edit. Asset type: seamless albedo texture for the marble backing and countertop of a physically modelled 3D wine cabinet. Use the supplied wine cabinet reference ONLY to match the cream-beige marble in the bottom center niche and behind the four vertical bottle vitrines. Deliver ONLY a square flat frontal marble surface: the same rich soft beige brecciated marble with fine irregular white/cream veins, restrained tan patches, fine mineral grain. Reconstruct unobstructed stone, with even neutral illumination. Remove all objects, furniture, bottles, shelves, wood, gold LED lighting, shadows, reflections and perspective. No lines or seams dividing the canvas. No room, no border, no letters, no watermark. The texture should be detailed, natural and seamless for tiling, with realistic fine texture rather than thick drawn gold lines. Match the stone material and its warm cream palette from the reference. Return a local saved file path.
```
