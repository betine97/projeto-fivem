# Reparo do acesso e do tapete de urso — 08/10/2026

O coqueiro marcado foi retirado do mapa principal e da entidade usada no LOD. Os outros objetos das ruas mantêm os mesmos pais, posições e propriedades; os índices dos mapas filhos foram ajustados para compensar a remoção de uma entrada do mapa pai.

As faces abertas da escavação foram fechadas com muros de contenção completos. As laterais da escada acompanham os degraus e contêm o terreno até a altura do jardim; a rampa tem paredes completas, capas e acabamento sobre o portão. Foram acrescentados fechos nas quatro pontas dos muros nativos expostas pelo recorte e alinhada a contenção ao nível das duas faixas do jardim. Os trechos restantes da escada antiga foram recortados. A estrutura mantém sua geometria nos quatro níveis de detalhe para evitar que uma simplificação reabra as emendas. A pista continua livre.

O limite físico do tapete cobria apenas a cabeça: aproximadamente 0,72 × 0,86 m para uma malha de 3,75 × 2,77 m. Foi acrescentada uma colisão com a silhueta inteira, de 9 mm de espessura e topo a 12 mm da origem, mantendo a colisão da cabeça e as malhas, UVs e materiais visuais originais. O limite do arquétipo inclui uma margem de 15 mm. O cliente aplica prerenderização apenas a esse objeto e usa a distância de detalhe de 220 m; a rotina normal continua descarregando objetos quando o jogador sai da região. Essa mudança corrige o limite físico incompleto e acrescenta proteção de renderização; a confirmação do desaparecimento precisa ser feita no FiveM.

## Carregar no jogo

No console **do servidor**, execute:

```text
restart cidade_mansao
```

Depois feche e reabra o FiveM e reconecte. Confira as duas laterais do acesso, a chegada da escada e o tapete andando ao redor do sofá e girando a câmera.

Se o tapete ainda apresentar uma falha, `tapeteursodebug` no F8 imprime sua posição, presença, visibilidade, estado de oclusão e dimensões. Esse comando não modifica posições nem permissões.

## Validação e arquivos

- 42 assets nativos lidos pelo serializer e, independentemente, pelo CodeWalker.
- 1.779 verificações de superfícies, fechamento das faces, espaço para carros e passagem de pedestres.
- Estruturas sólidas fechadas e conservadas nos quatro LODs.
- Cliente Lua executado em 72 posições ao redor do tapete, incluindo saída da região e retorno.
- Perfil de iluminação, posições salvas e os demais recursos preservados.
- Prévias revisadas por três ângulos no Blender. Elas servem para conferir geometria; iluminação e materiais podem diferir do jogo.

`fachada_garagem_editavel.blend` contém as peças separadas do acesso. `mansao_acesso_reparado.blend` contém a composição com a geometria nativa recortada. `tapete_urso_render_corrigido.blend` contém o asset do tapete e suas colisões. Os scripts e relatórios desta pasta registram o preparo, a construção, a validação e a instalação. `backup_preinstall` preserva os arquivos anteriores à instalação. Nenhum reinício do servidor ou do recurso foi executado automaticamente.
