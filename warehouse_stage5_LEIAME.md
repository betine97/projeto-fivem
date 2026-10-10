# Warehouse — Stage 5

O arquivo `warehouse_stage5_completo.py` gera o ambiente inteiro no Blender, sem depender dos scripts anteriores ou de complementos.

## Abrir

- Cena já construída: `warehouse_stage5_validado.blend`.
- Para gerar do zero: abra `warehouse_stage5_completo.py` no editor de texto do Blender e use **Run Script**.
- A execução reconstrói as coleções geradas do ambiente. Guarde alterações manuais em uma cópia do `.blend` antes de reconstruir.

## Composição

- Dois racks contínuos de 2,55 × 7,40 × 2,05 m, com três módulos por lado.
- Corredor central de 2,40 m e folgas laterais de 0,25 m.
- Padrão: três vasos com copas geométricas por módulo, 18 no total.
- `PLACEHOLDERS_PER_MODULE = 4` usa quatro vasos em 2 × 2 por módulo, 24 no total. As duas configurações são simétricas sob a luminária.
- Seis ventiladores laterais, três em cada parede, com a face voltada para os racks.
- Seis luminárias transversais com duas barras LED, corpo metálico, driver superior, suportes e cabos. Cada AREA emite no eixo vertical global -Z.
- Zona do fundo: tanque azul, painel elétrico, armário técnico, bancada metálica, estante, recipientes fechados e balde genérico. A passagem da porta permanece livre.

Os volumes verdes representam somente ocupação visual. Não são modelos finais de plantas. A versão é uma etapa de composição para o cenário de jogo.

## Prévias

`warehouse_stage5_preview.png` mostra a distribuição geral; `warehouse_stage5_modulo.png` mostra um módulo de perto. São prévias sólidas de geometria, sem simulação da iluminação final. A parede frontal é ocultada temporariamente nessas imagens para revelar o interior e continua completa no arquivo `.blend`.

## Verificação

O relatório `warehouse_stage5_validacao.json` registra a quantidade de objetos de composição, a distância vertical entre copas e luzes, a orientação das luzes e dos ventiladores, a passagem da porta e a ausência de duplicações ao reconstruir.
