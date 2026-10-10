# Saída de postura restaurada — v8

O log `CitizenFX_log_2026-10-07T194654.log` confirmou uma falha da revisão v7:
`ClearPedLookAt` não existe no runtime. Ao soltar C, a chamada interrompia a
limpeza antes de liberar `active`/`held` e restaurar o IK. Também encerrava o
coroutine principal. Novas entradas não ajoelhavam; a entrada deitada ficava
sem atualização dos clipes/ossos.

A chamada correta é
[TaskClearLookAt](https://raw.githubusercontent.com/citizenfx/natives/master/TASK/TaskClearLookAt.md).
Ela substitui as duas chamadas inválidas: na saída e na recomposição da pose.
Agora a saída libera primeiro o estado e invalida entradas pendentes; executa
cada limpeza separadamente com proteção contra erros. Uma falha é registrada
sem impedir as demais limpezas nem a próxima entrada.

A pegada aprovada, os três YCD v6 do AK, as montagens da arma e os arquivos
Blender foram preservados. A recarga continua sem levantar nas posturas
personalizadas. A medição da inclinação e a recomposição limitada permanecem.

## Verificação

- `test_runtime_v8.py`: 72 ciclos de recarga e 80 ciclos físicos C/Z, duas armas,
  três posturas, interrupções de tarefa/recarga, inclinação persistente,
  restauração do IK, limite do histórico e integração de Alt com cobertura.
- `test_exit_failure_v8.py`: reproduz a falha antiga usando o arquivo v7 real;
  o coroutine termina e o IK fica preso. Na v8, 60 sequências de tiro →
  ajoelhar → levantar → ajoelhar novamente → deitar passam, inclusive 30
  exceções injetadas durante a limpeza do olhar.
- Os mocks têm uma lista explícita de natives permitidos. Um nome inexistente
  causa erro; o fallback permissivo antigo havia mascarado a falha.

São testes Lua simulados, sem renderização do FiveM. O erro antigo foi
observado no log real; o resultado visual da v8 ainda precisa ser conferido.

## Carregar

Arquivos instalados em disco; não reiniciei o servidor/jogo. Execute
`restart cidade_core` no console do **servidor** e reconecte o cliente.
No F8, `combateinfo` deve informar `v8-saida-restaurada`. Os dicionários do AK
continuam v6, pois suas animações foram mantidas.

Teste tiro → C → soltar C → C novamente; depois Z, tiro e recarga. Repita
mantendo a mira e também soltando-a. `combatehistorico 80` mostra transições
recentes; `combatedebug 1` ativa a impressão automática.

A cobertura Q foi revisada também: consulte
`animacoes/cobertura_rapida/V2-LEIA-ME.md` para `cobertura-v2-carros-muros`.

`runtime_v8_checks.json`, `exit_failure_v8_checks.json` e `v8_installation.json`
registram testes e hashes. O backup v7 mantém o erro histórico e não deve ser
reinstalado sem corrigir a chamada inválida.
