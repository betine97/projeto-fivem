# Sertão

Picape adaptada no Blender a partir da estrutura **Rebel2** extraída da instalação local do GTA V. As referências orientaram a pintura oliva, os faróis redondos, grade, para-choques, reforços da caçamba e a torre. É uma primeira versão inspirada nas imagens, com a cabine/base do GTA preservada; não é uma reprodução exata do veículo fotografado.

## Usar

No F8: `restart cidade_core`. Se o modelo novo ainda não estiver disponível, reconectar ao servidor. Depois: `veiculo sertao` (ou `sertao`). O comando coloca o jogador ao volante; `dv` remove o veículo criado.

Os arquivos `sertao.yft`, `sertao_hi.yft` e `sertao.ytd` estão no `stream` de `cidade_core`. O manifest registra os metadados. Handling, entrada/saída, suspensão e colisões usam a base Rebel. Nenhuma função de disparo foi instalada na torre.

## Editar

- `sertao.blend`: fonte editável para exportação, com referências incorporadas.
- `sertao_studio.blend`: cena de apresentação; as três rodas duplicadas são apenas para a prévia. Não exportar esta cena.
- `work/build_sertao.py`: construção reproduzível de 118 peças novas, materiais e exportação.
- `work/prepare_metadata.py`: registro do modelo novo a partir dos metadados locais.

Ossos reservados: `sertao_turret_yaw`, `sertao_turret_pitch`, `sertao_muzzle`. Os dois primeiros controlam a malha visual; o último é um marcador. Não há assento de artilheiro, câmera ou arma funcional ainda.

## Verificação

Arquivos YFT e YFT de alta resolução exportados e relidos; esqueleto, quatro rodas, estrutura física e ossos da torre conferidos. Metadados XML analisados. Prévia renderizada e inspecionada. **Spawn e condução ainda precisam de validação no FiveM.**

Os componentes extraídos do GTA são para este ambiente local, não para redistribuição.
