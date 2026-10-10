# Como usar o catálogo para gerar texturas

Abra index.html em um navegador. Use a busca por nome e o filtro de coleção. Cada PNG contém apenas uma peça, enquadrada automaticamente, com fundo neutro e sem a iluminação rosa do cenário. A posição e escala da câmera variam por objeto para mostrar melhor a sua forma; as medidas originais estão no índice e no manifesto.

Os nomes foram preservados para vincular as texturas de volta ao Blender. O arquivo original warehouse_stage7_validado.blend não foi alterado. Luzes, câmeras e objetos de organização sem superfície não recebem fotos de textura; os objetos não visuais do ambiente estão registrados no manifesto.

## O que enviar à outra IA

Envie o PNG da peça e descreva o acabamento que deseja: concreto, metal galvanizado, borracha, plástico, pintura, desgaste etc. Use o filtro “Mostrar só geometrias distintas” para evitar pedidos repetidos. Instâncias repetidas também possuem arquivos individuais para rastreabilidade.

As fotos não são texturas prontas nem um mapa UV. Não peça apenas para pintar a foto com sombras: isso gera outra imagem da peça, que não se encaixa automaticamente no modelo. Para paredes e superfícies repetidas, peça uma textura plana e repetível. Para marcas localizadas, rótulos ou detalhes que precisam cair em posições específicas, será necessário preparar o UV da peça antes da aplicação.

## Pedido sugerido

“Use esta imagem apenas como referência de material. Gere uma textura de superfície plana, vista de frente, sem perspectiva, sem fundo de estúdio, sem sombras projetadas, sem luz rosa, sem brilho de iluminação incorporado e sem texto ou logotipo. Material desejado: [descreva aqui]. Imagem quadrada de 2048 × 2048 pixels. Para superfícies contínuas, as bordas devem se repetir sem emendas. Entregue primeiro o mapa de cor base (Base Color/Albedo).”

Mapas Roughness, Normal e Metallic precisam corresponder à mesma superfície. Se a outra ferramenta não gerar mapas PBR coerentes, envie somente a cor base; podemos preparar o restante na etapa de aplicação.

## Como devolver os arquivos

Preserve o nome do objeto como prefixo. Exemplos:

- WALL_RIGHT_basecolor.png
- FLOOR_HOSE_LEFT_MAIN_basecolor.png
- STORAGE_DRUM_LEFT_BODY_basecolor.png

Caso uma textura sirva para várias peças, informe os nomes ou o material compartilhado. Os materiais atuais aparecem no índice e no manifesto. Para uma peça com mais de um material, indique qual superfície deve receber a textura.

As imagens deste catálogo servem para preparar texturas. A aplicação e a conferência visual no Blender serão feitas depois que as texturas retornarem.
