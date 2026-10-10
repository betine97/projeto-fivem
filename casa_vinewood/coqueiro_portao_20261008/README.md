# Coqueiro e estabilidade do portão — 08/10/2026

A árvore marcada é `prop_palm_sm_01d`, com LOD `ch2_props_combo0126_11_lod`. A entidade já foi excluída dos mapas da entrega anterior. Os mapas atuais foram conferidos. Para impedir que a instância do jogo base ou uma posição anterior reapareça no streaming, `exterior_remocoes.lua` exclui somente esses dois modelos, em raios de 1,25 m, nas posições original e reposicionada. Os demais coqueiros permanecem. A exclusão é reaplicada perto da casa a cada cinco segundos e retirada ao parar o recurso.

O LOD mais distante do portão continha sete triângulos duplicados. Os quatro níveis agora usam a mesma malha compacta de 312 triângulos, sem sobreposição de triângulos. Os frisos têm 10 mm de separação da folha, em vez de 2 mm. O envelope visual inclui os frisos e puxador. A colisão real, dobradiça e posições permanecem.

O cliente mantém a prerenderização apenas dessa folha e evita que uma resposta de estado interrompa o movimento. O servidor bloqueia toggles de outros jogadores enquanto a animação está em andamento. `garagemdebug` no F8 imprime estado, ângulo, animação e informações de visibilidade caso reste alguma falha.

29 verificações passaram: malhas nos quatro LODs, ausência de triângulos duplicados, colisões preservadas, limites, controladores reais Lua, movimentos e snapshots, exclusões localizadas e limpeza ao encerrar o recurso. CodeWalker fez leitura independente dos dois arquivos nativos. Backup em `backup/`.

Para carregar, execute `restart cidade_mansao` no console do servidor. Feche completamente o FiveM, abra e reconecte. A observação visual no jogo permanece pendente; não houve reinício automático.
