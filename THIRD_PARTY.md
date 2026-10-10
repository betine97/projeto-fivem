# Componentes oficiais

O recurso `server-data/resources/[cfx-default]/spawnmanager` foi copiado sem alteracoes de:

- Repositorio: https://github.com/citizenfx/cfx-server-data
- Commit: c6afa3909c763e3327ed76825e78453286c99f05
- Diretorio: resources/[managers]/spawnmanager

Os avisos originais estao preservados nos arquivos. A copia baixada do repositorio esta em `.downloads/cfx-server-data`.
O FXServer foi obtido do canal recomendado oficial. Consulte `.runtime/version.json` para a versao e URL.

## Assets do usuario

- Drone e controlador: `C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\outputs\fpv_drone_runtime`.
- Audio: `C:\Users\erons\Downloads\Firefly-flight_of_an_FPV_drone.wav`, copiado sem alteracoes como `html/flight.wav`.

Os originais foram preservados. A copia integrada tem audio NUI, mensagens no F8 e coordenacao com os comandos da cidade.

## Referencias do prototipo prone

Implementacao Lua propria, usando natives e animacoes existentes do GTA.
A utilizacao de SCRIPTED_GUN_TASK_PLANE_WING foi investigada em
https://github.com/ItsAmmarB/StanceModifier/blob/master/cl_index.js ; esse projeto registra limitacoes de primeira pessoa e sincronizacao.
Referencia da API: https://github.com/citizenfx/natives/blob/master/TASK/TaskAimGunScripted.md .
O recurso StanceModifier nao foi instalado nem incorporado.

## Custom Tactical Poses 3.0 — crunchycat

Arquivos fornecidos e descompactados pelo usuario em
`C:\Users\erons\Downloads\1c6c16-Custom Tactical Pose`.
Origem: https://www.gta5-mods.com/misc/custom-rifle-poses-add-on
Tres YCD foram copiados sem modificacao para cidade_core/stream: tactical_kneel,
holding_weapon_kneel e aim_weapon. Readme original preservado em TACTICAL-ASSET-README.txt.
O autor descreve poses estaticas e proibe republicacao em outros sites; esta integracao e local.
Nao foi encontrada licenca que autorize redistribuir o pacote. Nao publicar esses assets junto do projeto.
A tarefa PLANE_WING citada acima foi removida da implementacao atual por levantar o personagem.

## Candidato de animacao Blender
A pose superior foi adaptada localmente de anim@male@aim_weapon.ycd do pacote de crunchycat fornecido pelo usuario. As pernas e ajustes de pose/recuo foram feitos no projeto Blender. O candidato cidade_combate_teste.ycd e de uso local, sem autorizacao de republicacao identificada.
Conversao XML/YCD: CodeWalker.Core 1.0.3, NuGet; repositorio https://github.com/dexyfex/CodeWalker, commit baca4c1af822b7df6f6547c939e396beaabcf855. Dependencias SharpDX 4.2.0. Pacotes e avisos preservados em .downloads/codewalker.

## Sertão — veículo adaptado localmente
Chassi, cabine, interior, rodas, física e texturas base: Rebel2 extraído da instalação local do GTA V. Carroceria adaptada, grade, faróis, para-choques e torre visual modelados em `veiculos/work/build_sertao.py` a partir das referências fornecidas pelo usuário. Não redistribuir os componentes do GTA. Exportação nativa usando o Sollumz e szio já presentes no projeto local.
