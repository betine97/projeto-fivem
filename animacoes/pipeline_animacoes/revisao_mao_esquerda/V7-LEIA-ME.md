# Posturas repetidas e diagnóstico — v7

O log `CitizenFX_log_2026-10-07T185644.log` confirmou que a v6 estava carregada
durante o problema relatado: houve várias entradas/saídas por C/Z e recargas,
mas o log anterior não media a orientação da arma. Ainda não há uma captura
do estado dos ossos no instante do defeito que comprove a causa exata.

Esta revisão altera somente o controlador de combate e sua medição da arma.
A pegada aprovada, os arquivos Blender e os três YCD v6 do AK são preservados.

## Mudanças

- Ao sair, termina imediatamente as tarefas principal/secundária e o olhar
  antes de restaurar os controles de IK. Os dicionários de animação ficam
  carregados durante as trocas e são liberados ao encerrar o recurso.
- O avaliador da animação continua em velocidade 1, com a fase escolhida pelo
  tempo absoluto da recarga/recuo. Isso tenta evitar ossos em cache quando a
  postura anterior era congelada em velocidade zero.
- Na primeira confirmação de cada clipe, pede uma atualização dos ossos.
  A chamada não é feita a cada quadro ou a cada bala de uma rajada.
- Durante o combate mede a inclinação do eixo longitudinal da arma em relação
  ao personagem a cada 100 ms. Depois da entrada, um desvio acima de 8 graus
  sustentado por pelo menos 180 ms dispara a recomposição da mesma postura.
  A recarga continua do tempo já decorrido; sua munição não é alterada pela
  recomposição. Inclinações breves e a animação de levantar são ignoradas.
- Limita a recomposição a três tentativas por janela de 10 s, com intervalo
  mínimo de 1,2 s entre tentativas. Um defeito persistente fica registrado.
- Também bloqueia IK da cabeça e animações ambientais/gestos durante a pose,
  restaurando as opções ao sair.

A atualização usa o native oficial
[ForcePedAiAndAnimationUpdate](https://raw.githubusercontent.com/citizenfx/natives/master/PED/ForcePedAiAndAnimationUpdate.md),
que tem custo alto; por isso é limitada à confirmação de um clipe.

## Carregar e testar no FiveM

Os scripts já foram alterados no recurso `cidade_core` em disco. O servidor e
o jogo não foram reiniciados por esta revisão.

1. No console do **servidor**, execute `restart cidade_core` e reconecte o
   cliente. Isso recarrega o recurso inteiro.
2. No F8 do cliente, execute `combateinfo`. A revisão deve ser
   `v7-postura-watchdog`; os dicionários do AK continuam identificados como v6.
3. Com o fuzil, repita C → Z → soltar C → tiro/recarga → C para levantar.
   Faça também o ciclo de levantar pelo Z. Teste mantendo a mira e soltando-a.
4. Se o defeito ocorrer, execute `combateinfo` e `combatehistorico 80`.
   As linhas `[Combate trace]` e `[Combate historico]` aparecem no F8 e no log
   padrão em `%LOCALAPPDATA%/FiveM/FiveM.app/logs/CitizenFX_log_*.log`.

O diagnóstico imprime automaticamente os eventos e uma amostra a cada 3 s.
`combatedebug 0` reduz a impressão automática; `combatedebug 1` reativa.
As falhas importantes continuam sendo impressas e os últimos 200 eventos
permanecem em memória até o recurso ser reiniciado. `combatehistorico 200`
imprime todo esse histórico, mesmo com a impressão automática desativada.

As linhas incluem postura, arma, munição, clipe desejado/ativo, fase, confirmação
da tarefa, mira nativa, recarga nativa, câmera, coordenadas dos punhos e ângulo.
`pose.barrelPitch` é o ângulo em relação ao personagem;
`pose.worldBarrelPitch` é o ângulo em relação ao mundo. O eixo do modelo é
usado para medir: a diferença de altura entre boca e ponto de empunhadura não
é confundida com inclinação. `pose.ms` identifica quando a medição ocorreu.

Eventos úteis: `inclinacao_detectada`, `recompor_postura`,
`inclinacao_normalizada`, `clipe_enviado`, `clipe_confirmado` e
`postura_saida`. A recuperação de recarga nativa e a recuperação de inclinação
persistente têm motivos distintos nos logs.

## Verificação realizada

- `test_runtime_v7.py`: Lua 5.4 com mocks assíncronos, 72 ciclos de recarga,
  80 ciclos físicos C/Z, dois fuzis e três posturas. Verifica cancelamento,
  restauração do IK, recarga interrompida, inclinação incorreta com tarefa
  ainda ativa, recuperação sem reiniciar a recarga, limites de tentativas,
  histórico e retenção dos dicionários até o encerramento.
- `test_weapon_trace_v7.py`: executa a montagem Lua real com 12 matrizes
  sintéticas. Confere ângulos relativos/absolutos, os dois suportes de arma,
  matrizes degeneradas e preservação da posição da arma.
- Os JSON de testes registram os hashes dos scripts avaliados.
- `v7_installation.json` registra a revisão em disco e confere que os YCD
  aprovados permanecem iguais aos hashes do pacote v6.

Estes testes verificam o controlador e cálculos em simulação. Não substituem a
validação visual das transições no motor do FiveM, ainda pendente.
Os scripts v6 estão preservados em `../backup_v6_pose` para recuperação.
