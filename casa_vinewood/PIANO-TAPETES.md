# Piano e tapetes — térreo

Modelos criados no Blender a partir das três referências enviadas em 08/10/2026.

- Piano de cauda preto, acabamento dourado, tampa aberta, 88 teclas individuais, 180 cordas, três pedais, rodízios e banco. Posicionado na sala, ao norte do sofá. Dimensões do conjunto com banco e tampa: aproximadamente 1,58 × 2,99 × 2,09 m.
- Tapete de urso com silhueta recortada, espessura e cabeça/focinho em relevo. Entre a sala e o jantar. Aproximadamente 2,50 × 1,85 m, mantendo a proporção da imagem; altura máxima de 16 cm.
- Tapete estampado com superfície texturizada e bainha fechada. No hall do térreo. Aproximadamente 1,85 × 2,21 m, mantendo a proporção da estampa.

Fontes editáveis: `piano_tapetes_autorais.blend` contém os três modelos; `mansao_piano_tapetes.blend` contém os modelos posicionados na mansão e preserva a cena de spots/quadros, com a cozinha anteriormente criada nesta conversa.

## Instalação

O pacote `piano_tapetes_fivem` contém três YDR, um YTYP e um YMAP. A instalação copia somente esses cinco arquivos para `server-data/resources/cidade_mansao/stream` e registra o YTYP em `fxmanifest.lua`. O relatório `instalacao_piano_tapetes.json` registra o backup e a preservação dos demais arquivos do recurso.

Recarregar pelo console do servidor:

```text
restart cidade_mansao
```

Reconectar ao servidor depois. O servidor não foi reiniciado automaticamente.

## Verificação

`verificacao_piano_tapetes.json`: 38 rotas de circulação, apoio no piso, afastamento das paredes, colisões, geometria nativa, materiais e mipmaps conferidos. O piano/banco possuem colisão; no tapete de urso, somente a cabeça elevada possui colisão. O tapete estampado mantém o piso livre para caminhar.

As imagens de prévia foram renderizadas no Blender. A verificação visual no FiveM continua pendente. O piano é um objeto decorativo, sem reprodução de áudio ou interação de tocar.
