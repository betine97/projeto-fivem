# Mansão — espessuras, colisão e acabamentos

Revisão `espessuras-solidas-2026-10-07`. Recurso: `server-data/resources/cidade_mansao`. Fonte editável: `mansao_fivem_preparada.blend`. A versão anterior ao ajuste das espessuras está preservada em `backup_antes_espessuras`, incluindo os arquivos Blender e o recurso completo. As revisões anteriores estão em `backup_antes_acabamentos_camera` e `backup_antes_frestas_render`.

## Espessuras e faces laterais

As divisórias internas têm 20 cm, e os painéis exteriores, 25 cm. O piso térreo tem 30 cm; a laje superior e a chegada da escada, 45 cm; o patamar intermediário, 35 cm; e a cobertura, 20 cm. Esses valores são dimensões de modelagem adaptadas à circulação no jogo. Os níveis de caminhada e as larguras livres das portas foram mantidos.

O aspecto de lâmina também vinha da orientação inconsistente das faces: as laterais de volumes já existentes podiam ser descartadas pelo renderizador do GTA. Foram soldados e recalculados os 169 sólidos estruturais, exigindo volumes fechados e faces voltadas para fora. Os contornos externos foram refeitos com recortes compatíveis com as janelas nativas e cinco portas. Pequenos segmentos inferiores a meio milímetro nos recortes dos vidros foram simplificados para evitar triângulos quase degenerados e normais instáveis na exportação.

`espessuras_estruturais.json` registra as dimensões e o fechamento das malhas Blender. `verificacao_espessuras_exportadas.json` relê os YDR nativos, confirma 96 espessuras de paredes e dez de lajes/patamares, e compara 4.784 triângulos visíveis com a geometria de origem. Não houve face ausente, face invertida ou normal de iluminação incorreta. Quatro raios que consideram apenas a frente das faces verificam as bordas da escada e do mezanino; esse teste detecta o descarte visual das laterais que os antigos testes de colisão de dois lados não detectavam. Os hashes associam a verificação ao pacote instalado.

A chegada da escada também tinha uma sobreposição de 20 cm com a laje, incluindo faces superior e inferior coincidentes que geravam uma faixa escura na prévia. O patamar agora termina exatamente na borda do vão. O teste dos YDR exige área zero de sobreposição entre essas superfícies de madeira, nos níveis 2,358 e 2,808 m, preservando o apoio contínuo de caminhada.

## Acabamentos e circulação

A laje superior e a chegada da escada passaram de 25 para 45 cm de espessura. O patamar intermediário passou de 20 para 35 cm. A espessura foi acrescentada para baixo, preservando os níveis de caminhada, as soleiras e os vãos. Os fechamentos do mezanino acompanham a nova espessura. A madeira original do GTA continua aplicada.

O modelo de janelas continha 1.224 triângulos de retornos e caixilhos que haviam recebido o mesmo shader transparente dos vidros, criando a borda parcialmente invisível vista no print. Esses trechos agora usam acabamento opaco; os 174 triângulos das lâminas de vidro permanecem transparentes. A verificação dos 43 conjuntos de janelas distingue os caixilhos das áreas efetivamente envidraçadas.

As camadas de mapa `apa_ch2_09b_*` e `hei_ch2_09b_*` ainda continham o vaso e o arbusto nas posições antigas. Agora as três variantes base/APA/HEI recebem os mesmos ajustes locais: arbusto `prop_bush_med_03` afastado 1,50 m, folhagem `prop_plant_cane_02a` afastada 1,20 m e vaso `prop_pot_plant_02d` afastado 40 cm. Foram preservadas as outras entidades de cada mapa. `correcao_plantas_camadas.json` registra nove ajustes em nove mapas. `audit_vegetacao_todas_camadas.json` examina a malha visível de 88 instâncias num raio de 35 m, com rotação e escala reais, sem superfície restante dentro dos cômodos.

A física embutida usa o conjunto de tipos de mapa estático nativo, incluindo cobertura, para o reconhecimento das paredes pela câmera. Um arquivo mundial `cidade_mansao.ybn`, alinhado à mesma geometria, tem máscara exclusiva `CAMERA_TEST`: ele fornece colisão estática para a câmera sem adicionar uma segunda colisão de caminhada. O acompanhamento continua sendo a câmera normal do GTA. `verificacao_camera.json` confirma 6.668 raios atravessando os dois lados das paredes e cinco portas exteriores livres; também confere que nenhum material ignora a colisão de câmera. A confirmação da distância e da suavidade da câmera no FiveM depende de recarregar esta revisão.

`movimento_interior.lua` bloqueia o sprint e limita a mistura da velocidade a 1,35 apenas dentro dos contornos dos dois pavimentos, enquanto o personagem caminha com colisão. Ao sair, entrar num veículo, ativar voo sem colisão, trocar de personagem ou parar o recurso, o comportamento comum é restaurado. Treze casos de comportamento foram executados no interpretador Lua, além da análise sintática de todos os scripts do recurso. Referências das funções: https://github.com/citizenfx/natives/blob/master/PED/SetPedMaxMoveBlendRatio.md e https://github.com/citizenfx/natives/blob/master/ENTITY/GetEntityCollisionDisabled.md.

## Ajuste das frestas e do desaparecimento do interior

O revestimento feito com faces independentes deslocadas da fachada foi substituído por 41 painéis fechados, com espessura de 25 cm e encontros contínuos nos cantos. As aberturas seguem as projeções dos vidros nativos e os cinco recortes das portas exteriores. As divisórias que terminavam nas medidas do estudo foram estendidas ao contorno real; as portas internas continuam com suas larguras. Pequenas sobreposições com os pisos e tetos eliminam as frestas nas junções. As duas bordas expostas do vazio da sala receberam fechamento contínuo. O guarda-corpo do mezanino foi alinhado à borda da laje, corrigindo o deslocamento de 1,12 m herdado do estudo inicial.

O DLC `mpapartment` ainda carregava três caixas de ocultação em `apa_ch2_occl_02.ymap` dentro da casa, mesmo com o mapa base corrigido. Essas caixas foram removidas apenas na região da mansão. O diagnóstico examina os 16 mapas de ocultação CH2 das camadas base e apartamento. `correcao_oclusao.json` compara os volumes originais com os arquivos exportados. O cliente também chama `DisableOcclusionThisFrame()` quando a câmera ou o personagem está na região local da casa (X -12,5..17; Y -18,5..12; Z -2..9, relativos à origem). A função só vale por um frame; ao sair, o jogo retoma a ocultação normal. Na região ativa o jogo pode desenhar mais objetos, com algum custo de desempenho. Referência: https://github.com/citizenfx/natives/blob/master/GRAPHICS/DisableOcclusionThisFrame.md.

Na revisão das junções, o vaso dos fundos foi afastado 40 cm no mapa base. A revisão atual aplica esse mesmo afastamento às variantes APA/HEI, que ainda recolocavam o vaso na posição antiga.

O diagnóstico Lua normaliza o retorno BOOL do teste de colisão para aceitar `true` ou `1`. O valor numérico `0` é verdadeiro em Lua, mas significa ausência de colisão nesse retorno; antes ele podia gerar falsos bloqueios em posição mundial zero. A revisão atual do diagnóstico é `espessuras-solidas-2026-10-07`.

## Correções

Revisão de colisão dos DLCs: os arquivos `apa_ch2_09b_*` de `mpapartment` e `hei_ch2_09b_*` de `mpheist`, inclusive as versões `hi@`, também ocupam o mesmo espaço da casa. A revisão anterior só recortava os arquivos sem prefixo; por isso a verificação anterior não representava todas as camadas presentes no FiveM. Foram encontrados bloqueios na entrada principal, na saída da sala para o deck, nos antigos suportes internos e no quarto superior. Os setores 1 e 3 das oito variantes adicionais receberam os mesmos recortes locais, preservando as áreas vizinhas. A extração prioriza os arquivos mais recentes de `update.rpf`.

`diagnostico_colisoes_dlc_antes.json` reproduz os obstáculos em 39 amostras de cinco percursos; `diagnostico_colisoes_dlc_depois.json` confirma zero bloqueios nesses mesmos percursos. Os testes agora exigem as 24 fontes de colisão do setor (base, mpheist e mpapartment), incluindo fontes que não precisam de alteração.

As pequenas pontas de suportes da casa original que surgiam no piso foram recortadas na malha visual. Suas cápsulas de colisão, parcialmente enterradas abaixo da laje, foram removidas do espaço ocupado. A seleção agora considera o contorno completo da casa; não depende de o poste caber inteiro em uma única célula de recorte.

As grades originais dos modelos de sacada que atravessavam os cômodos foram recortadas dentro do contorno do interior. As partes externas das sacadas permanecem. Faixas de terra, pedras, bases e sobreposições originais que cobriam a madeira também foram recortadas, incluindo a malha de terreno `ch2_09b_l2`. A geometria de iluminação original que atravessava esse espaço recebeu o mesmo recorte.

O portão na reentrância da fachada é separado da porta dos fundos. Seus elementos visuais e físicos foram removidos na passagem, com uma soleira contínua. O percurso entra pelo portão, contorna o canto da parede no pátio e segue à porta lateral dos fundos; não atravessa a parede original do pátio.

A instância de `prop_bush_med_03` que penetrava no cômodo recebeu o afastamento de 1,50 m nas três variantes do mapa `ch2_09b_long_0.ymap`; as outras plantas desse modelo permanecem em suas posições.

As lajes foram trianguladas respeitando os limites e os vãos da planta. A laje superior tinha uma pequena região omitida pela triangulação anterior; a nova malha cobre o contorno previsto. Pisos e degraus continuam com a madeira original `im_wood_panels_05` e seu mapa normal. As rampas físicas das escadas e as colisões das paredes permanecem ativas.

## Validação e limites

`audit_janelas.json`: o vidro instalado usa transparência uniforme (alfa 48/255). Foram examinadas 43 regiões de painéis por raios atravessando a fachada nos dois sentidos, sem painel totalmente fechado por uma camada opaca. As três janelas superiores dos fundos estavam cobertas por planos originais de iluminação; esses planos e faixas residuais nas bordas foram removidos de `ch2_09b_emissive_05.ydr`. O substituto nativo sem modelos foi exportado e relido. Algumas amostras encontram bordas de divisórias reais próximas às janelas; elas estão registradas separadamente de opacidade do vidro. A confirmação visual no FiveM permanece pendente após recarregar e reconectar.

`verificacao_encaixe.json`: 25 percursos aprovados, com apoio do piso e espaço para o corpo em três alturas, incluindo a entrada pelo portão, os antigos postes, a área perto dos vidros, as escadas, as portas e as sacadas.

A varredura dos dois pavimentos examinou 15.109 pontos em uma grade de 25 cm. Dos 10.921 pontos com apoio e espaço livre no interior modelado, nenhum apresentou obstáculo adicional nas colisões nativas. Foram incluídos triângulos, caixas, esferas, cápsulas, cilindros e as colisões próprias dos objetos próximos. Janelas fechadas e paredes reais continuam tendo colisão.

As superfícies dos pisos dos dois andares cobrem os contornos previstos, descontando os vãos superiores, com tolerância de 2 mm para a quantização da colisão nativa.

`verificacao_juntas.json`: 160 raios atravessam os cantos da fachada, em quatro alturas de cada pavimento, usando a geometria exportada. Não há canto aberto. `verificacao_limpeza_nativa.json`: os seis modelos nativos modificados foram relidos após a exportação; não há superfície restante dentro dos volumes de limpeza, com tolerância de 1 mm. `verificacao_fivem.json`: 37 arquivos nativos relidos e hashes conferidos na instalação. `verificacao_portas_instaladas.json`: 21 portas/acessos examinados nos dois sentidos, usando também as variantes dos DLCs. `audit_janelas.json` verifica o material transparente e a passagem da visão pelos 43 painéis/regiões de janela.

Essas verificações usam os arquivos exportados. O teste visual e de movimento com o personagem no FiveM após esta revisão ainda está pendente. Os relatórios `verificacao_antes_limpeza.json` e `audit_intrusions.json` são diagnósticos da versão anterior.

## Carregar a revisão

No console do servidor:

```text
restart cidade_mansao
```

Desconecte e conecte novamente o FiveM para recarregar as substituições dos arquivos nativos. No F8, `mansao` retorna à entrada com o voo desligado. Confira os locais dos prints caminhando, além da passagem pelo portão e das escadas.

O servidor não foi reiniciado automaticamente. Os arquivos estão instalados em disco; uma sessão já conectada pode continuar usando a versão anterior até recarregar e reconectar.

Depois da reconexão, o recurso consulta as colisões do próprio GTA ao se aproximar da casa. Esse teste não teleporta nem altera a física do personagem. O resultado fica em `server-data/resources/cidade_mansao/diagnostico_colisoes_runtime.json`. No F8, `mansaoverificar` repete o diagnóstico; são cápsulas atravessando os acessos e os percursos internos nos dois sentidos, em três alturas. Esse relatório só existe depois de executar o recurso atualizado no jogo; os testes dos arquivos não substituem essa confirmação.

## Blender

Em `mansao_fivem_preparada.blend`, View > Navigation > Fly Navigation permite explorar o interior. WASD movimenta; E/Q sobe/desce; a roda ajusta a velocidade. A coleção 06 contém o teto, a 09 as rampas físicas ocultas e a 90 a referência original anterior às correções. A coleção 91 contém a fachada nativa corrigida que está no pacote, oculta por padrão; habilite-a para conferir a casa com sua estrutura externa.
