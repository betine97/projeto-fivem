# Cobertura rápida — carros e muros, v2

**Q** procura uma barreira próxima, corre até o lado protegido e entra em
cobertura. Outro **Q** sai. Funciona armado/desarmado, com a arma equipada.
Backspace/salto cancelam. Mira, tiro e recarga usam os controles normais do GTA
após entrar. Voo, drone e controles de veículos mantêm sua tecla Q.

## Correção da busca

Os prints e o log `CitizenFX_log_2026-10-07T200823.log` mostram várias rejeições
da v1 perto de carros e muros. O log antigo não informava qual teste descartava
cada candidato; a v2 acrescenta esses motivos.

A v1 exigia que a coordenada de navegação quase coincidisse com a barreira.
Agora o destino fica no ponto verificado pela colisão, sem deslocá-lo para a
coordenada de spawn devolvida por
[GetSafeCoordForPed](https://raw.githubusercontent.com/citizenfx/natives/master/PATHFIND/GetSafeCoordForPed.md).
Se a malha não fornece um ponto próximo no mesmo lado, tenta um percurso direto
validado por cápsulas de corpo/ombros e sondagens do chão. Mantém colisão e
cancela se ficar bloqueado.

Sem atacante identificado, a câmera orienta a prioridade, mas não elimina uma
parede ao lado/atrás do jogador. Com um ped em combate ou que causou dano,
escolhe o lado protegido em relação a esse atacante. Carros parados aceitam
superfícies curvas da carroceria; se o carro andar/sair do ponto, cancela.

Confere largura, piso, caminho livre e bloqueio da linha de tiro em altura
baixa. Procura até 7 m. Uma opção próxima válida é aceita logo.

## Entrada e agachamento

Primeiro tenta a cobertura nativa com
[TaskSeekCoverToCoords](https://raw.githubusercontent.com/citizenfx/natives/master/TASK/TaskSeekCoverToCoords.md).
O motor controla a entrada, abaixar e mirar. Confirma com
`IsPedInCover`/`IsPedAimingFromCover`.

Carro/muro com colisão pode não ter ponto aceito pelo motor. Se a entrada não
ocorrer, o jogador tiver chegado ao destino e houver barreira também a 1,10 m,
aplica o movimento nativo `move_ped_crouched` e seu strafe. O estado `crouched`
é distinto da cobertura nativa `covered`. Ao sair ou iniciar C/Z, restaura
os conjuntos de movimento. O agachamento usa
[SetPedMovementClipset](https://raw.githubusercontent.com/citizenfx/natives/master/PED/SetPedMovementClipset.md).

Não exportei novo YCD/Blender para esta ação. A geometria produz a proteção;
não há teleporte, invulnerabilidade nem desligamento de colisão. O resultado
visual do agachamento, mira e recarga ainda precisa ser conferido no FiveM.

## Carregar e diagnóstico

Instalado em disco; não reiniciei o servidor/jogo. Execute `restart cidade_core`
no **console do servidor** e reconecte. No F8, `coberturainfo` deve mostrar
`cobertura-v2-carros-muros`; `combateinfo`, `v8-saida-restaurada`.

Eventos `[Cobertura]`: `candidato_rejeitado`, `resumo_busca`, ponto, tipo de
barreira, percurso `navmesh`/`direta_validada`, `entrada_nativa`, `protegido`,
`agachar_atras_da_barreira` e saída. Cada motivo tem impressão detalhada
limitada; o resumo mantém contagens. Logs aparecem no F8 e em
`%LOCALAPPDATA%/FiveM/FiveM.app/logs/CitizenFX_log_*.log`.

## Verificação

`tests/quick_cover.py` passou em 45 cenários com Lua/colisões sintéticas:
carro/muro armado/desarmado, superfície curva, junto ao muro, malha de navegação
ausente/grosseira/no outro lado, câmera lateral, ameaça real, entrada recusada,
agachamento alternativo, carro em movimento, saída/restauração, falha de
carregamento, cancelamento, morte, troca de personagem e resultados assíncronos.

São testes simulados; não demonstram o resultado desses prints em jogo.
`test_results.json` registra os cenários e o hash testado. `installation_v2.json`
registra scripts instalados. A v1 está preservada em `backup_v1`.
