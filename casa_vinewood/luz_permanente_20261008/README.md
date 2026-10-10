# Iluminação permanente da mansão — 08/10/2026

Instalada em `server-data/resources/cidade_mansao`. O resultado visual no GTA/FiveM ainda precisa ser conferido após recarregar o mapa.

## Causa e correção

O controlador anterior ordenava 196 candidatos por distância ao personagem/câmera e dava preferência ao andar ocupado. Só uma parte era desenhada. Isso retirava as fontes do cômodo visto à distância e concentrava pontos fortes e de alcance grande perto do personagem, especialmente no piso e nas paredes brancas.

O novo projeto está incorporado ao drawable existente `mansao_teto.ydr`, raiz do MLO. São 58 volumes de luz distribuídos nos 19 ambientes e 10 fontes de destaque para paredes, pé-direito alto, bancada, ilha e escada. Todas têm emissão constante e horários 0–23 habilitados. Não há seleção de cômodo por posição do personagem. O renderizador GTA administra os volumes nativos e seu descarte fora da vista; as definições continuam acesas em toda a casa enquanto o mapa está carregado.

As luzes podem ser vistas tanto de dentro quanto de fora do MLO, permitindo observar cômodos acesos pelo hall, pelas janelas e pelo mezanino. Não dependem da intensidade do sol nem de uma lista Lua de luzes próximas.

Preenchimento branco quente, alcances menores e posições mais altas evitam a sobreposição excessiva dos antigos volumes grandes na altura do personagem. Os destaques quentes alcançam paredes e teto. A iluminação difusa não adiciona reflexos especulares ao mármore. Somente três fontes usam sombras de resolução reduzida; os demais volumes são difusos. Coronas e volumes de névoa são zero; não há cones de spotlight desenhados no piso.

O loop Lua anterior foi substituído. No padrão, faz **zero chamadas de desenho de luz por quadro**. Não se adicionaram malhas ou texturas: o arquivo do teto aumentou 818 bytes comprimidos. O custo real da GPU e a qualidade final precisam ser medidos no jogo; esses números não são uma medição de FPS.

## Ativação e controles

1. No console do servidor, execute `restart cidade_mansao`.
2. Desconecte e reconecte o FiveM para carregar o drawable com suas luzes nativas.
3. No F8, `mansaoluzes` mostra a versão do projeto e o reforço opcional.
4. `luzmansao 1` usa o padrão nativo. `luzmansao 1.5` até `luzmansao 3` acrescenta reforço local uniforme nos 19 ambientes, sem alternar fontes ao mudar de cômodo. Esse controle agora é aditivo; valores abaixo de 1 voltam ao padrão. O reforço é uma preferência local do cliente, como o controle anterior. A iluminação nativa é igual para todos.

Confira os mesmos enquadramentos dos prints: hall olhando sala/jantar; sala olhando cozinha; mezanino olhando térreo. Depois percorra quartos e cômodos menores em ambos os andares, mantendo o horário 23h. A sala ao fundo deve conservar suas luzes sem exigir que o personagem entre nela. Confira de fora pelas janelas e confira a iluminação diurna.

Não foi encerrado o FXServer nem aplicado um filtro global de exposição ou clima. A proteção contra chuva/névoa, os mapas, as portas, as colisões e o editor ADM foram preservados.

## Verificações e fontes

- `projeto_luminotecnico.json`: posições, regiões, cores, intensidade, alcances e sombras; fonte editável da iluminação.
- `build_lighting.py`: gera o pacote nativo e compara dados gráficos com o backup.
- `native_verification.json`: 68 luzes recuperadas do arquivo exportado; geometria, UVs, normais, índices e bytes das texturas idênticos.
- `lighting_tests.json`: cobertura de 5.098 pontos no piso/altura do corpo em 19 ambientes; 45 casos de ambiente/horário usando o Lua real; câmera de drone, padrão sem chamadas e reforço uniforme.
- `installation_verification.json`: hashes instalados e preservação dos demais arquivos.
- `backup/`: recurso anterior, já contendo o MLO de proteção climática. Para desfazer apenas esta iluminação, restaure `stream/mansao_teto.ydr`, `iluminacao_ambiente.json` e `iluminacao_decorativa.lua` deste backup e recarregue/reconecte. Não restaure o recurso inteiro sobre posições de móveis mais recentes.

Referências primárias usadas: [luzes incorporadas aos drawables](https://docs.sollumz.org/2.6/documentation/lighting-.ydr), [flags de renderização, sombras e reflexos](https://docs.sollumz.org/2.6/documentation/lighting-.ydr/light-flags), [propriedades de iluminação e escala de intensidade do exportador](https://github.com/Sollumz/Sollumz/blob/main/ydr/properties.py).
