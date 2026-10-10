# Cobertura rápida — primeira versão

**Histórico da v1. A revisão instalada agora é v2:** veja
[V2-LEIA-ME.md](V2-LEIA-ME.md), com correção de carros/muros e agachamento.

Implementada no recurso local `cidade_core`, usando as animações de locomoção,
entrada e proteção do GTA. Esta versão é uma ação dinâmica: não é um novo clipe
Blender/YCD de pose fixa. O motor escolhe a postura de cobertura adequada ao
ponto, normalmente abaixado nas barreiras baixas e encostado nas paredes altas.
O resultado visual dessas escolhas ainda precisa ser conferido no FiveM.

## Uso

- **Q**: procurar uma cobertura próxima e ir até ela; outro **Q** cancela/sai.
- Também pode usar `cobertura` no F8. A tecla pode ser alterada nas configurações
  de atalhos do FiveM em “Procurar cobertura próxima / sair”.
- Em cobertura, mira, tiro e recarga usam os controles normais do GTA.
- Backspace ou salto cancelam a busca/deslocamento. Após a entrada, o movimento
  normal também pode sair da cobertura; o script não recoloca o jogador nela.
- Funciona com a arma já equipada ou desarmado. Não entrega nem troca armas.

Reinicie `cidade_core` no **console do servidor** (`restart cidade_core`) e
reconecte o cliente para carregar. O servidor/jogo não foi reiniciado por esta
implementação. O comando `coberturainfo` no F8 mostra revisão `cobertura-v1`.

## Como escolhe o ponto

Procura barreiras com colisão em até 7 m, começando pela direção da câmera.
Quando identifica um ped em combate com o jogador ou que lhe causou dano,
prefere a direção desse atacante. A direção da câmera funciona como indicação
de onde o jogador quer se proteger quando não há um atacante identificado.

Confere chão, espaço para o corpo e ombros, largura da barreira, posição de
navegação no lado protegido e uma linha bloqueada em altura de cobertura baixa.
Uma barreira válida a menos de aproximadamente 4 m é aceita logo para reduzir
o tempo exposto. Peds, folhagem e objetos sem colisão não servem como barreira.

O percurso usa navegação com colisão real. A entrada usa
[TaskSeekCoverToCoords](https://raw.githubusercontent.com/citizenfx/natives/master/TASK/TaskSeekCoverToCoords.md),
e a confirmação usa [IsPedInCover](https://raw.githubusercontent.com/citizenfx/natives/master/PED/IsPedInCover.md)
ou [IsPedAimingFromCover](https://raw.githubusercontent.com/citizenfx/natives/master/PED/IsPedAimingFromCover.md).
Essas tarefas mantêm as animações nativas de arma/cobertura no controle.

Não há teleporte, invulnerabilidade ou desligamento de colisão. A proteção vem
da geometria do cenário; ela não impede disparos por outros ângulos. Barreiras
sem navmesh/acesso ou rejeitadas pelo motor não são anunciadas como cobertura.
Em mapas personalizados sem dados de navegação, a busca pode recusar o ponto.

## Integração e logs

A cobertura encerra as poses de C/Z antes de entrar e entrega novamente o
personagem quando outra ação começa. Alt não inicia a câmera/movimentação das
poses personalizadas enquanto a cobertura está ativa. Q continua disponível
para descer no voo e girar o drone; o comando de cobertura ignora esses modos.

Os eventos `[Cobertura]` aparecem no F8 e no log padrão do FiveM. Incluem busca,
ponto escolhido, barreira baixa/alta, percurso, entrada nativa, confirmação e
motivos de cancelamento. `coberturainfo` imprime a situação atual.

## Testes

`tests/quick_cover.py` executa Lua 5.4 com colisões sintéticas e sondagens
assíncronas. Passaram 28 cenários: armado/desarmado, barreiras baixas/altas,
terreno aberto, postes estreitos, barreira insuficiente, navmesh ausente ou no
lado errado, resultados pendentes, direção do atacante, caminho bloqueado,
recusa da entrada pelo motor, saída natural, troca de personagem, morte,
entrada a partir da pose deitada e 30 cancelamentos rápidos consecutivos.

A regressão das poses v7 também passou: 72 recargas e 80 ciclos C/Z simulados.
O teste adicional de Alt verifica que ele não assume o movimento da cobertura.
Os testes não renderizam as animações nativas nem demonstram o resultado no
FiveM; a primeira validação visual em jogo continua pendente.

`test_results.json` registra os cenários e o hash do controlador testado.
`installation.json` registra os scripts em disco e a ausência de reinício.
