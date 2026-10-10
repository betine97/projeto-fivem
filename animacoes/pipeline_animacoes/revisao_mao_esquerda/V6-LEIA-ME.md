# Apoio da mão e transições de combate — v6

O jogo ainda usava os YCD v5: as revisões `r08` e `ajoelhado_r01` estavam somente
no Blender. Os novos arquivos v6 do fuzil AK incluem o apoio sob o guarda-mão na
mira, no recuo e na saída/retorno da recarga, em três posturas (ajoelhado,
deitado e sentado no chão). A carabina mantém seus assets v5; o controlador de
transições foi corrigido para ambos os fuzis.

O controlador `server-data/resources/cidade_core/prone.lua` agora encerra o
clipe anterior e força seu sucessor, sem a opção de animação não interrompível.
Cada quadro de recarga/recuo vem de um tempo absoluto, retomando o progresso
quando uma tarefa é interrompida. O bloqueio do IK nativo dos braços/tronco é
reaplicado durante a postura e após mudar munição. Ao sair, os controles e o IK
são restaurados. A montagem original da arma na mão direita foi preservada.

Na exportação, os limites do clipe foram corrigidos para começar em zero e
terminar dentro da duração do arquivo. Os canais dinâmicos usam floats sem
quantização, pois a conversão anterior introduzia erro nas rotações dos dedos.
O addon instalado e os arquivos Blender originais não foram modificados.

## Verificação

- `test_runtime_v6.py`: 72 ciclos simulados, dois fuzis, três posturas,
  tarefas assíncronas, interrupção de recarga/recuo e limpeza/saída.
- `validate_binary_v6.py`: lê o YCD convertido de volta, reconstrói todos os
  quadros no esqueleto nativo de 98 ossos e compara com as ações de origem.
- Verifica os dois extremos da recarga/recuo contra a mira, a orientação do
  cano e interseções da mão nos quadros inspecionados. Os JSON de verificação
  ficam dentro de `ajoelhado_v6`, `deitado_v6` e `sentado_v6`.
- As imagens `01_apoio_lateral`, `02_apoio_frente`, `03_apos_recarga` e
  `04_durante_tiro` são renderizadas no Blender a partir dos dados do YCD
  convertido, não são capturas do FiveM.

## Aplicação

`package_v6.ps1 -Install` confere hashes e testes antes de copiar os três novos
YCD para `cidade_core/stream`. O resultado fica em `v6_installation.json`.
Os scripts anteriores estão em `../backup_v5_pose` para recuperação.

Nenhum servidor ou jogo foi reiniciado por este ajuste. Para carregar os novos
scripts e dicionários, reinicie `cidade_core` no **console do servidor** e
reconecte o cliente FiveM. A validação visual em jogo ainda precisa ser feita.
`combateinfo` deve identificar `v6-apoio-transicoes` e um dicionário v6 para AK.
