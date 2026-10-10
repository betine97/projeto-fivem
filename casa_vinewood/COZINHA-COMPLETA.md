# Cozinha completa da parede — 08/10/2026

Modelada no Blender a partir das seis imagens fornecidas. O conjunto fica na parede marcada atrás da ilha, no térreo, com a torre de eletrodomésticos à esquerda e a geladeira à direita. O vaso grande indicado na seta foi deslocado para o canto à direita.

Inclui armários superiores de madeira, gavetas inferiores greige, bancada escura com recorte real da cuba, revestimento de mármore claro, torneira preta curva, cooktop com cinco queimadores e grelhas, coifa, micro-ondas e forno embutidos, geladeira inox com dispenser e puxadores, tábuas e um vaso pequeno na bancada. As frentes do forno e do micro-ondas usam as referências enviadas; os corpos e puxadores têm geometria tridimensional.

- Largura: 6,536 m incluindo laterais; profundidade de armário: 0,64 m.
- Bancada: 0,91 m de altura. Fechamento superior: 3,15 m, deixando 8 mm sob o teto.
- Portas e divisórias: 18–22 mm. Bancada: 31 mm. Cuba: metal de 1 mm com profundidade de aproximadamente 19 cm.
- LED contínuo emissivo sob os armários, com cinco pontos de luz de apoio no controle de iluminação já instalado. O orçamento existente de 24 luzes simultâneas permanece igual.
- Colisões para armários, torre, bancada e geladeira; caminhos existentes permanecem livres.

## Arquivos

`cozinha_completa.blend`: componente separado, editável em coordenadas locais.

`mansao_cozinha_completa.blend`: cópia da cena otimizada mais recente com o componente encaixado e o vaso reposicionado.

`cozinha_fivem/`: drawable nativo, YTYP e YMAP da cozinha, além da atualização pontual do mapa de decoração e das configurações.

`source_assets/cozinha_completa/`: referências originais preservadas e texturas DDS com mipmaps.

`verificacao_cozinha_completa.json` e `instalacao_cozinha_completa.json`: verificações de geometria, materiais, instalação e 33 trajetos de circulação.

## Ativação e limites da verificação

O componente está instalado no recurso `cidade_mansao`. Para carregar a alteração, executar `restart cidade_mansao` no console do servidor e reconectar os jogadores. O servidor não foi reiniciado durante esta instalação.

As prévias são renderizações do Blender. A aparência e a intensidade final no FiveM dependem da iluminação e das configurações gráficas do jogo; a inspeção visual dentro do jogo ainda está pendente. Forno, micro-ondas, cooktop e geladeira são elementos decorativos, sem interação programada.
