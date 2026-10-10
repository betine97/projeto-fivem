# Animações de combate

Revisão atual: **v5**, com contatos por arma e recarga ajoelhado, deitado e sentado no chão. Fontes copiadas, esqueleto com controles auxiliares, exportação e relatórios estão em [pipeline_animacoes/LEIA-ME.md](pipeline_animacoes/LEIA-ME.md). Os arquivos v5 estão instalados em `cidade_core`; ainda precisam de conferência visual no FiveM.

## Registro da revisão v4

Fontes: `ajoelhado_refinado.blend` e `deitado_tiro.blend`. Esqueleto e carabina extraídos do GTA local; pose superior originalmente adaptada do pacote Custom Tactical Poses fornecido pelo usuário.

- Alvos das mãos recalculados dentro do alcance dos braços; cotovelos dobrados e clavículas acompanhando a postura deitada. Sem alongar os ossos.
- Arma visual independente da tarefa nativa de recarga/obstrução. O objeto copia cor e acessórios do inventário e acompanha a transformação do punho calculada no Blender. Munição e dano continuam no sistema existente.
- Rajadas reiniciam o tempo do recuo ativo, evitando empilhar tarefas completas a cada projétil.
- Segundo Z: deitado → ajoelhado → em pé em **1,5 segundo**, com todos os 91 quadros reproduzidos a Rate=2. C levanta diretamente se estiver deitado; em pé, segurar C mantém ajoelhado.
- Direção continua corrigida nos clipes, sem giro posterior do personagem.

Dicionários ativos: `cidade_combate_frente_v4` e `cidade_deitado_tiro_v4`.

## Reprodução

Fontes base: `work/pose.py` e `work/prone_pose.py`. Aplicar `work/repair_grip.py`, depois `work/exit_contacts.py`. Exportar com `work/export_study.py` e `work/export_prone.py`, converter com `work/convert-ycd.ps1`. Não reaplicar o antigo `refine_combat.py`.

`exports/weapon_mounts.json` registra a transformação punho/arma; deve corresponder à tabela em `cidade_core/combat_weapon.lua`. Rever a tabela quando o alinhamento da arma no Blender mudar.

## Verificação e limites

Prévia renderizada e inspecionada. Testes de mira, disparo, munição, teclas, tempo de saída, morte, limpeza da arma visual e matriz do punho passaram. Clipes XML e binários relidos. Continuidade dos 91 quadros da saída verificada. A roupa ainda depende da deformação do modelo e da postura.

**A causa intermitente original não foi reproduzida ao vivo, e a v4 ainda precisa de validação visual no FiveM.** O novo encaixe visual remove a dependência da tarefa nativa da arma.

No console do servidor: `restart cidade_core`; se necessário, reconectar. No F8 do cliente, usar `arma carabina 250` e verificar C/Z, mira, rajada e recarga.

Assets do GTA e da pose de terceiros destinam-se ao ambiente local, sem redistribuição. As ferramentas dependem do Sollumz e das bibliotecas locais do projeto `projeto-fivem-3d`.
