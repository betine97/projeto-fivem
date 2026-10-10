# Conjunto completo

Use `/conjuntocompleto` para vestir camisa estampada, calça bege, mocassins marrons e relógio dourado. `/roupaanterior` restaura o traje anterior. Os comandos `/calcabege` e `/camisaestampada` continuam disponíveis para testar as etapas anteriores.

`CONJUNTO_COMPLETO.blend` contém as quatro peças sobre o esqueleto GTA original. Os GLBs recebidos e suas imagens permanecem preservados; os UVs originais dos acessórios não foram refeitos. O relógio acompanha rigidamente o antebraço esquerdo, e cada sapato acompanha seu pé com flexão leve dos dedos.

Para o jogo, os sapatos usam aproximadamente 181 mil triângulos no detalhe mais próximo, e o relógio 75 mil, com mais três níveis simplificados. Os originais completos permanecem no Blender: 906.590 e 629.048 triângulos, respectivamente. Cor e normal mantêm as imagens originais em 4K, convertidas pelo processo já validado.

Slots de teste na coleção `Male_Heist`: sapatos no componente 6, drawable 1; relógio como acessório separado no componente 7, drawable 1. Ambos usam textura 0. O relógio ocupa o componente de acessórios, vinculado ao osso `SKEL_L_Forearm`.

Cada subpasta (`sapatos`, `relogio`) contém `export_config.json`, os arquivos exportados e a auditoria nativa em `work/audit/verification_native.json`. `preview_exportada.png` e `movimento_exportado.png` mostram os acessórios finais reimportados no Blender.

Validação visual no FiveM pendente do jogador.

Revisão 2: a profundidade da camisa foi reduzida em 32% no tronco, com transição nas mangas e gola. A barra da calça foi estreitada em 30% na largura e 34% na profundidade, com transição abaixo da panturrilha. UVs e imagens das duas peças permanecem iguais. Os mocassins agora incluem pele nativa dos pés/tornozelos apenas abaixo da barra, com materiais e imagens próprios embutidos no YDD. O comando limpa os acessórios do pescoço depois da camisa e em seguida equipa o relógio. `perfil_exportado_corrigido.png` e `barra_exportada_corrigida.png` mostram os arquivos finais reimportados. Os arquivos `.antes-ajuste` preservam a versão anterior.

Revisão 3 substitui o corte de pele da revisão 2: os pés originais completos, seus 660 vértices, UVs e pesos foram restaurados. O tornozelo nativo permanece até 7 cm acima da articulação; apenas a panturrilha coberta pela calça é limitada. O calçado foi ajustado ao volume desses pés, com forro de couro adicional para fechar pequenas aberturas da malha gerada. O pé permanece sob esse forro. A malha de pele e o forro são preservados integralmente nos quatro níveis de detalhe, simplificando apenas o calçado externo.

Nas mangas, os pesos agora vêm da superfície do tronco/braços original, interpolados pelos triângulos do corpo, com no máximo quatro influências por vértice. A manga também foi ajustada ao braço; a textura e o UV original da camisa permanecem iguais. A barra recebeu folga para acomodar o tornozelo preservado.

Processo validado da revisão 3: `work/refine_revision3.py -- --no-render`, depois `work/fit_native_foot_smooth.py`, depois `work/finish_revision3.py`; exportação pelo script compartilhado `../calca_bege/work/export_fivem.py`. O arquivo `work/fit_over_native_skin.py` é um experimento descartado e não faz parte desse processo. `conjunto_exportado_revisao3.png`, `pes_exportados_revisao3.png` e `mangas_movimento_exportadas_revisao3.png` mostram os arquivos finais reimportados.

`work/complete_native_foot_verified.json` compara o pé exportado com o arquivo GTA original: as mesmas 964 faces triangulares e todas as posições foram preservadas em HIGH, MEDIUM, LOW e VERYLOW, com erro máximo de posição inferior a 0,000002 m. O registro de instalação fica em `work/deployment-revisao3.json`.
