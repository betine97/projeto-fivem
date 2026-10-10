# Mansão — mezanino, sofá ampliado, TV e portas

Revisão `piso-tv-portas-2026-10-07`. A versão anterior está preservada em `casa_vinewood/backup_antes_piso_tv_portas`. A confirmação visual no FiveM depende de recarregar o recurso e reconectar.

## Alterações

- Madeira somente na área delimitada do mezanino: 39,60 m². Os demais 323,22 m² do piso superior usam o mármore bege do térreo. Degraus e patamares continuam em madeira.
- Paredes superiores com o mesmo reboco creme do térreo; tijolo no pé-direito duplo atrás da TV.
- Conjunto sofá/chaise/mesa ampliado de 4,40 m para 5,20 m, com escala uniforme, aproximadamente 96 cm de altura e 3,49 m de profundidade incluindo a mesa. Apoio a 5 mm do piso e circulação conferida.
- Painel, TV, rack e decoração do GLB enviado na parede de tijolos, de frente para o sofá. Largura 4,60 m, sem atravessar a parede.
- Cinco portas de madeira: escritório, lavabo, despensa, sala de TV/jogos e lavanderia. Folhas de 45 mm, sete faixas horizontais, batentes, guarnições, dobradiças e ferragens pretas conforme as referências. **E** abre/fecha suavemente; estado compartilhado entre jogadores. O fechamento é recusado enquanto alguém ocupa o vão.
- Entrada principal junto ao deck e porta de vidro à esquerda do sofá reservadas para outros modelos. Os vãos largos de sala, jantar e cozinha permanecem abertos.

## Falhas do sofá e da mesa

O GLB tinha vértices duplicados nas costuras de textura. Reduzir a malha antes de uni-los abriu frestas. A preparação agora une os vértices antes da otimização: sofá de 1.044.086 para 120.000 triângulos; TV de 1.405.278 para 99.998. Os arquivos nativos têm zero bordas abertas ou não-manifold, zero triângulos degenerados e zero tangentes nulas.

As texturas originais de cor e relevo desses conjuntos mantêm 4.096 pixels, com filtragem para distância até 4×4 no arquivo nativo. Mapas especulares de 2.048 pixels, brilho moderado e efeito de molhado desativado. UVs originais preservados, com uma correção localizada no triângulo da tela da TV que amostrava indevidamente a área de madeira do atlas. Mármore, reboco, tijolo e metal usam as imagens fornecidas em 2.048 pixels com filtragem; seus mapas de relevo são aproximações derivadas da cor.

## Fontes e verificações

`mansao_encaixada.blend` contém a fonte editável. `mansao_fivem_preparada.blend` contém materiais de exportação, portas colocadas para visualização e fachada nativa corrigida numa coleção oculta. `source_assets/` guarda os GLBs e imagens originais.

O pacote contém 39 arquivos nativos. As portas móveis têm física própria na origem da dobradiça, sem uma colisão imóvel atravessando o vão. Batentes pertencem à estrutura fixa. A colisão da câmera permanece separada, sem duplicar a física de caminhada.

Relatórios: `verificacao_malha_mobiliario.json`, `verificacao_materiais_sofa.json`, `verificacao_portas_moveis.json`, `verificacao_espessuras_exportadas.json`, `verificacao_encaixe.json`, `verificacao_camera.json`, `verificacao_portas_instaladas.json` e `audit_janelas.json`. A validação dos arquivos é distinta da confirmação no jogo.

Paredes de 20/25 cm, piso térreo de 30 cm e laje superior de 45 cm preservados. A limitação de corrida, limpeza dos obstáculos e vegetação nativos e correção de oclusão continuam ativas.

## Carregar

Console do servidor: `restart cidade_mansao`. Depois reconecte o FiveM e use `/mansao`. Perto das novas portas, pressione **E**.

`/mansaoverificar` registra colisões observadas pelo GTA. Contatos com portas fechadas são identificados separadamente de bloqueios inesperados; abra as portas para conferir a circulação completa. Renders Blender são prévias, não capturas do jogo.
