# Rastejo — v12

Os registros reais do cliente mostram deslocamento durante os clipes, mas posições
restritas a aproximadamente uma passada mesmo após vários segundos. A hipótese
para o retorno é a extração da animação sem física cinemática/conservação da posição
ao encerrar. O controlador agora solicita `AF_USE_KINEMATIC_PHYSICS` e
`AF_REPOSITION_WHEN_FINISHED`, além da extração e repetição já existentes. A mesma
combinação é aplicada à passada rápida agachada, que usa o mesmo mecanismo.
Colisão e gravidade continuam habilitadas; não há reposicionamento por script.

Também foi corrigido um erro independente confirmado na consulta de obstáculos:
`GetShapeTestResult` invalida o identificador após retornar 0 ou 2. Antes, se uma
das três consultas terminasse antes das demais, o controlador consultava novamente
seu identificador e podia cancelar o rastejo. Agora guarda apenas consultas pendentes.

As animações YCD e as fontes Blender permanecem as mesmas: suas trilhas de
deslocamento já contêm os quatro sentidos e a sinalização de root motion.

## Carregar e conferir no jogo

Execute `restart cidade_core` no console do servidor. A entrada na postura deve
mostrar `v12-rastejo-posicao-fisica` no F8. Deite com Z e segure W, S, A e D,
separadamente, por pelo menos cinco segundos; solte e confira se permanece no
local alcançado. Teste também troca direta de direção, parede, mira e recarga.

Os logs `[Rastejo]` ficam ativos por padrão e registram início, cada ciclo,
progresso nas coordenadas reais e motivo de parada. `retorno_detectado` indica
recuo maior que 8 cm em até 200 ms; `retorno_apos_parar` indica recuo medido
250 ms após soltar a tecla. São diagnósticos, não teletransportam o personagem.

- F8: `rastejodebug` mostra o estado e os últimos 12 eventos.
- F8: `rastejodebug off` / `rastejodebug on` controla os registros.
- O histórico guarda no máximo 80 eventos.

## Validação

`test_runtime.py` executa a suíte anterior de controles/armas e regressões para
consultas que terminam em quadros distintos e são consumidas uma única vez,
interrupções, troca de direção e detecção de retorno. Coordenadas são injetadas
para testar os logs; não simulam a física interna do GTA. O relatório marca
`game_tested: false`. A correção física ainda precisa ser confirmada no cliente
após recarregar o recurso; não houve reinicialização automática do servidor.

Referências: [flags de TaskPlayAnim](https://github.com/citizenfx/natives/blob/master/TASK/TaskPlayAnim.md)
e [validade de GetShapeTestResult](https://github.com/citizenfx/natives/blob/master/SHAPETEST/GetShapeTestResult.md).
