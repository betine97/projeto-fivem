# Parede da cozinha e tapete do urso

Modelo criado no Blender 5.2 seguindo a composição do print de referência:
quadro abstrato à esquerda com iluminação superior; bar à direita com fundo
de mármore escuro, veios dourados, três níveis de prateleiras, garrafas, taças,
vasos, planta pendente, armários de madeira e adega com vidro e garrafas internas.
Os objetos decorativos são volumes 3D, e o quadro possui tela e moldura separadas.

O bar mede 2,52 × 0,535 × 3,12 m e foi ajustado à parede existente, sem mudar
a cozinha, a ilha, a arquitetura ou as posições dos móveis salvas no editor.
O conjunto é fixo para manter o encaixe das colisões e da iluminação.

O tapete do urso foi ampliado uniformemente em 1,5 vezes: de aproximadamente
2,50 × 1,85 m para **3,75 × 2,77 m**. UVs, textura e posição foram preservados;
a malha de colisão e os limites de seleção foram ampliados junto com o modelo.

## Arquivos editáveis e prévias

- `bar_parede_editavel.blend`: componentes do novo conjunto, editáveis no Blender.
- `mansao_bar_tapete_150.blend`: cópia da cena completa com parede e tapete ampliado.
- `parede_bar_instalada.png`: prévia renderizada no Blender; não é captura do FiveM.
- `tapete_urso_150.png`: prévia do tapete ampliado, renderizada no Blender.
- `textures/arte_restaurada.png`: textura do quadro, restaurada da referência.

## Instalação e validação

`install.py` instala apenas seis arquivos nativos em
`server-data/resources/cidade_mansao/stream`, registra o novo YTYP e um script
local de quatro luzes e atualiza os limites de seleção do tapete no catálogo.
Os backups dos arquivos substituídos ficam em `backup_antes` e `backup_preinstall`.
`objetos_posicoes.json` não é modificado. Os demais comandos, recursos e
controladores de iluminação permanecem sob responsabilidade do trabalho principal.

O bar tem quatro LODs reais: 29.328, 14.448, 5.779 e 2.166 triângulos.
Texturas DDS comprimidas com mipmaps ocupam 4 MiB de memória gráfica no drawable.
Colisões simplificadas: 84 triângulos. As luzes adicionais só são desenhadas
nas proximidades do bar. `verification.json` registra os testes dos arquivos
nativos, geometria, texturas, escalonamento do tapete, encaixe e script de luzes.
`installation.json` registra hashes dos arquivos efetivamente instalados.

**Ativação no jogo:** executar `restart cidade_mansao` no console do servidor e
reconectar ao FiveM. O servidor completo não foi reiniciado por esta tarefa.
A verificação visual dentro do FiveM fica pendente dessa ativação;
a aparência final também depende da iluminação do jogo.

## Restauração da textura do quadro

Modo usado: **ferramenta imagegen integrada (edição)**, sem CLI.
Entrada: `textures/arte_canvas.png`, recorte da arte na referência.
Saída final salva no projeto: `textures/arte_restaurada.png`.
O ajuste removeu a torneira da fotografia que encobria parte inferior da pintura.
Prompt final enviado:

```text
Use case: precise-object-edit. Asset type: flat albedo texture for a 3D framed painting. Edit target: supplied cropped artwork. Preserve exactly its abstract composition, block positions, proportions, palette (cream/beige plaster with dark brown-black angular vertical blocks), and hand-painted weathered surface. Remove ONLY the curved black kitchen faucet that intrudes from the bottom LEFT corner, reconstructing the beige paint behind it. Remove the tiny thin border at the extreme edges so artwork fills canvas. Improve fine plaster/brush texture clarity and resolution, but do not change the artwork design, invent new shapes, or relight. Produce a flat frontal rectified artwork texture in portrait proportions, no room, no frame, no faucet, no text. Save the edited output to a local file and return the file path for use as a Blender texture.
```
