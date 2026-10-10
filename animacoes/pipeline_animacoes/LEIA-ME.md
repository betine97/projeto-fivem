# Pipeline de animações — revisão v5

Esta pasta contém cópias de trabalho do personagem nativo `a_m_y_business_01`, com 98 ossos, e estudos separados para carabina e fuzil AK. Os nomes, identificadores, hierarquia e matrizes de repouso do esqueleto foram preservados. O personagem do jogo não foi substituído.

## O que foi implementado

- Contatos da arma calibrados por modelo. Na pose deitada, o fuzil foi levado para a frente e a clavícula esquerda acompanha o alcance, evitando alongar os braços.
- Mira, recuo e recarga de 2,2 segundos para ajoelhado, deitado e sentado **no chão**. A recarga mantém pernas e raiz fixas, movimenta a mão esquerda e volta à pose de mira.
- A arma visual acompanha o punho, sem depender da orientação da tarefa nativa de recarga. Cor e acessórios continuam sendo copiados do inventário.
- Recuperação de tarefa nativa de recarga e retomada do clipe no tempo decorrido. Soltar/retomar a mira não encerra a recarga.
- Cancelamento de recarga ao encerrar/trocar a postura, morrer ou trocar de personagem/arma. A recarga redistribui a munição existente e não cria munição.

## No jogo

Arquivos v5 instalados em `server-data/resources/cidade_core`, sem reiniciar o servidor ou interferir na tarefa da mansão. Para ativar na sessão atual, usar **`restart cidade_core` no console do servidor**; reconectar se os novos dicionários não carregarem. No F8 do cliente, `combateinfo` deve mostrar `v5-contatos-recarga` e um dicionário com `v5_ar` ou `v5_ak`. O comando de reinício é documentado em [Server Commands, Cfx](https://docs.fivem.net/docs/server-manual/server-commands/).

Equipar `arma carabina 250` ou `arma fuzil 250`. Segurar C ajoelha; R recarrega na postura. Z deita; R também recarrega deitado. `sentarcombate` senta no chão, com R para recarregar; repetir o comando ou Backspace levanta. Mira no botão direito e disparo no esquerdo. Os antigos comandos `ajoelhar`, `ajoelhar2` e `prone` usam os clipes v5.

## Esqueleto e edição

Abrir `esqueleto_trabalho.blend`. É uma cópia com controles separados do esqueleto que será exportado:

- `CTRL_ROOT` move o corpo e `CTRL_TORAX` orienta o tórax.
- Alvos de mãos/pés e polos de cotovelos/joelhos usam cadeias auxiliares com eixos próprios para IK sem alongamento. No controle de cada mão/pé, a propriedade personalizada `IK` alterna entre FK nativo (0) e IK auxiliar (1). `SOLVER_*` resolve a cadeia e `AXIS_*` converte sua rotação para os eixos nativos, sem modificar a pose de repouso. Ajustar o polo conforme a pose.
- Dedos e face preservam seus ossos nativos e usam FK. Não renomear ossos, alterar tags, parentesco, escala ou matrizes de repouso.
- Criar uma Action para cada animação. As fontes `sources/*.blend` já incluem ações `MIRA_*`, `RECUO_*` e `RECARGA_*`, além da saída deitado → ajoelhado → em pé.

## Construção e exportação

Requer Blender 5.2, Sollumz e bibliotecas locais já usadas no projeto. Os caminhos das dependências e da instalação GTA estão no início dos scripts. A extração lê apenas arquivos da instalação local. Os arquivos originais `.blend` são lidos, sem alterações.

Na raiz do projeto, PowerShell:

```powershell
& 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe' -b --python-exit-code 1 --python 'animacoes/pipeline_animacoes/inspect_rig.py'
& 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe' -b --python-exit-code 1 --python 'animacoes/pipeline_animacoes/build.py'
& './animacoes/pipeline_animacoes/package.ps1' -Install
```

`build.py` regenera as cópias v5; preservar uma cópia com outro nome antes de editar à mão. `package.ps1` converte XML para YCD, relê os binários e instala somente os arquivos de combate. Não reinicia recursos.

Para uma nova Action editada, exportar com bake visual em um rig separado. Os controles e suas restrições não entram no YCD:

```powershell
& 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe' -b --python-exit-code 1 --python 'animacoes/pipeline_animacoes/export_action.py' -- --source 'sources/ajoelhado_ar.blend' --action MIRA_ajoelhado_ar --dictionary cidade_nova_anim --clip mira --start 1 --end 30
& './animacoes/work/convert-ycd.ps1' -InputPath './animacoes/pipeline_animacoes/exports/cidade_nova_anim.ycd.xml' -OutputPath './animacoes/pipeline_animacoes/exports/cidade_nova_anim.ycd'
```

O exportador bloqueia esqueleto incompatível, mudança de escala, valores não finitos e alongamento. `--fps` define a taxa; `--turn-z` define a conversão de direção (180 graus nas fontes atuais). Depois, registrar explicitamente o novo clipe no controlador. O exportador avulso não instala nem altera uma animação ativa.

`preview.py` renderiza mira e recarga sem gravar nas fontes. `validate_template.py` testa os alvos IK e o controle de raiz em memória. Relatórios estão em `reports`; cópias dos scripts anteriores, em `backup_v4`.

## Evidência e limites

Foram testadas 48 sequências de recarga, alternando mira/disparo, nas três posturas e nas duas armas, com interrupção simulada por recarga nativa. Verificados cancelamento, reserva insuficiente e pente cheio. No Blender, todos os 67 quadros de recarga preservam raiz/pernas, contato direito e retorno à pose inicial; braços permanecem dentro do alcance. XMLs e YCDs foram relidos.

**A revisão v5 ainda precisa de teste visual no FiveM.** As verificações automáticas não reproduzem completamente o agendamento de tarefas e a deformação das roupas no motor do jogo. A recarga atual é um primeiro clipe de mãos; não anima a remoção física do carregador nem a queda do carregador como objeto. Os tiros e a arma visual continuam no sandbox local existente; isso não cria sincronização de combate multiplayer.

Sem alterar o esqueleto, roupas rígidas como o paletó ainda podem precisar de ajustes de pesos para poses extremas. Uma animação feita neste rig deve ser conferida em outros modelos de personagem antes de considerá-la compatível com eles.

Referência dos flags e tarefas: [TaskPlayAnim, documentação Cfx](https://github.com/citizenfx/natives/blob/master/TASK/TaskPlayAnim.md) e [ClearPedSecondaryTask](https://github.com/citizenfx/natives/blob/master/TASK/ClearPedSecondaryTask.md). Assets nativos e a referência de terceiros permanecem para uso local no projeto.
