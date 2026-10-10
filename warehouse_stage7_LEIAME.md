# Stage 7 — mangueiras e cabos no piso

O script `warehouse_stage7_completo.py` gera o ambiente completo com as etapas anteriores, incluindo LEDs rosas, grandes ventilações no teto e infraestrutura das paredes.

Esta etapa acrescenta dois barris genéricos fechados atrás dos racks, pequenas caixas de conexão, duas mangueiras principais no piso, dois cabos mais finos com folga e uma mangueira visual até cada vaso. Na configuração padrão são 18 derivações, com trechos corrugados e conexões nas bordas dos vasos.

As rotas seguem as bordas internas dos racks e deixam o eixo da canaleta livre. As mangueiras sobem por fora das plataformas antes de alcançar os vasos. Os objetos são elementos de composição do cenário, sem simulação de líquidos ou funcionamento.

Abra `warehouse_stage7_validado.blend` para usar a cena pronta. Para reconstruir, abra o `.py` no editor de texto do Blender e execute **Run Script**. A reconstrução substitui as coleções geradas; salve uma cópia caso tenha feito edições manuais.

Prévias:

- `warehouse_stage7_visao_geral.png`: distribuição geral em visualização sólida.
- `warehouse_stage7_mangueiras.png`: detalhe das mangueiras e vasos.
- `warehouse_stage7_barris.png`: barris, caixas e conexões no fundo.
- `warehouse_stage7_mangueiras_rosa.png`: detalhe renderizado com as LEDs rosas.

As prévias usam corte temporário da parede frontal e do teto. A arquitetura completa permanece no `.blend`; a laje fica oculta no viewport para facilitar a edição do interior.
