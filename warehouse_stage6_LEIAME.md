# Warehouse Stage 6 — infraestrutura industrial

Abra `warehouse_stage6_validado.blend` para usar a cena construída, ou execute `warehouse_stage6_completo.py` no editor de texto do Blender para gerar o ambiente inteiro. O script é independente dos arquivos das etapas anteriores.

## Alterações

- Duto longitudinal de 68 cm sobre o corredor central, conectado ao duto transversal do fundo.
- Três bocais de teto de 90 cm, com transição cônica aberta, rotor, grade circular, flange e parafusos. As faces estão voltadas para baixo.
- Duto sustentado por canais transversais, tirantes e abraçadeiras.
- Seis ventiladores laterais de 82 cm, com molduras, carcaças abertas, pás e grades; orientação para o interior da sala.
- Dois exaustores traseiros ampliados para 84 cm.
- Três linhas de tubulação na parte alta de cada parede lateral, descidas, abraçadeiras e caixas de junção.
- Bandejas metálicas com feixes de cabos e derivações; tubulações e cabos também na parede do fundo.
- LEDs rosas, vasos, racks e mobiliário técnico preservados.

## Ver o teto

A laje `CEILING_SLAB` está oculta somente no viewport para permitir editar o interior por cima. Ela continua presente nos renders internos. Use o ícone de olho no Outliner para mostrá-la durante a edição.

Há duas câmeras na coleção `STAGE6_REVIEW`: `STAGE6_OVERVIEW`, para a distribuição geral, e `STAGE6_INTERIOR`, para a vista interna das grandes ventilações. A câmera interna é a ativa para renderização.

As imagens de estrutura usam visualização sólida; a imagem `warehouse_stage6_teto_rosa.png` mostra a iluminação renderizada. A visão geral é um corte de apresentação com laje e fachada frontal ocultas temporariamente.

## Ajustes principais

No início do script:

- `SIDE_FAN_DIAMETER`: tamanho dos ventiladores laterais.
- `CEILING_DUCT_DIAMETER`: diâmetro do duto central.
- `CEILING_VENT_DIAMETER`: diâmetro dos bocais do teto.
- `CEILING_VENT_FACE_Z`: altura das faces dos bocais.
- `CREATE_WALL_SERVICES` e `CREATE_CEILING_DUCTS`: ativam cada conjunto.

A execução reconstrói as coleções geradas do ambiente. Salve alterações manuais em uma cópia antes de executar novamente.
