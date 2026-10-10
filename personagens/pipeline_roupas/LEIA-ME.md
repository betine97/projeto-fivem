# Pipeline de variações de roupas

Objetivo: partir de uma peça nativa aprovada com **OK**, usar a referência artística e os componentes enviados, produzir uma variação independente e conservar a base original. A aprovação da base não aprova automaticamente a variação.

## Análise da última calça

A revisão 3 está em `../calca_tatica`. Partiu de Business2 / lowr_001_r, preservando os buffers originais de geometria, UV, pesos e índices em todos os LODs. A base contém 2.135 triângulos somando os LODs. Os bolsos são superfícies adicionais com até 9 mm de relevo e pesos interpolados da malha; a altura foi reduzida a 66,8% da anterior. A difusa mudou; normal e especular nativos foram mantidos.

Três objetos YDR — duas fitas de bolso e uma ponta de cinto — acompanham ossos nativos e recebem balanço por mola amortecida no cliente. Não são tecido com colisões. A fivela nessa revisão é parte de uma imagem recortada sobre uma superfície fina; uma fivela com espessura e silhueta próprias exige geometria específica. A última revisão foi construída por scripts Szio diretamente, embora o projeto tenha bases Blender preparadas.

O original Business2 permanece, mas a instalação ocupa o drawable 6 de Male_Heist, substituindo outra peça naquele slot. Esse atalho de teste não será usado como padrão da pipeline: os candidatos saem com prefixo e coleção próprios. A revisão da calça possui validação de arquivos e teste de movimento com natives simuladas; a validação visual do balanço dentro do FiveM permanece pendente no relatório anterior.

## Entrada mínima para cada trabalho

1. Referência da base do acervo: ID ou ped / coleção / YDD / YTD. Precisa continuar com OK na preparação e exportação.
2. Imagem da nova peça. Frente, costas e laterais quando disponíveis; regiões ausentes são decisões registradas, sem inventar uma aprovação.
3. Textura de tecido e imagens de bolsos, logos, fitas, fivelas e reforços, quando existirem. Referência com fundo é preservada; o arquivo de aplicação usa recorte com alpha.
4. Intenção por elemento: lado do personagem, frente/costas/lateral, tamanho, volume e movimento. Se não houver medidas, estimar pela referência e registrar a hipótese para revisão.

Não é necessário enviar o personagem inteiro nem outro GLB quando a malha aprovada já tem o formato adequado. A referência artística não é um atlas UV: primeiro adaptamos a arte ao mapa da base.

## Processo

| Etapa | Trabalho | Saída e condição de avanço |
|---|---|---|
| Receber | Identificar base OK, sexo, componente, textura e referências | Projeto versionado, imagens originais copiadas e decisões registradas |
| Preparar | Extrair uma vez, registrar hashes, materiais, rig e LODs | Cache protegido, mapa UV por região e Blender de autoria quando necessário |
| Planejar | Separar tecido/arte, detalhes planos, volumes e partes móveis | Componentes com âncoras, região 3D, medidas e orçamento |
| Criar arte | Ajustar tecido, costuras, logos e recortes ao UV | Atlas final; conservar normal/especular quando adequados |
| Acrescentar volumes | Superfícies skinned ou geometria específica no Blender | Pesos herdados; normais/tangentes do relevo recalculadas; LODs coerentes |
| Acrescentar movimento | Objeto separado, osso, pivô e mola amortecida | YDR/YTYP próprios, regra de roupa, limpeza e integração da prévia |
| Conferir | Checagens numéricas, quatro vistas e flexões | Relatório com erros, avisos, decisões e fotos de comparação |
| Exportar candidato | Reabrir YDD/YTD e comparar com a base | Arquivos isolados; base intacta; nenhum arquivo do jogo sobrescrito |
| Empacotar addon | Produzir/conferir YMT e shop metadata da coleção | Coleção reconhecida no build e comando de teste da variação |
| Testar | Repouso, andar, correr, sentar, girar, trocar peça e reconectar | Registro do teste real; depois a variação pode receber OK |

O processo evita reiniciar a cidade para cada ajuste. Exportamos uma candidata por revisão e carregamos o recurso de teste quando for necessário; alterações de streaming podem exigir reconexão. Identificação por coleção + índice local segue as [natives de coleção do FiveM](https://docs.fivem.net/docs/scripting-manual/using-new-game-features/collection-based-natives/). O rig externo e os materiais seguem o [fluxo de roupas do Sollumz](https://docs.sollumz.org/tutorials/basic-clothes-editing).

## O que está automatizado agora

- Filtrar bases OK, conferir aprovação atual e reutilizar extração por hashes do inventário, arquivos e versão do adaptador.
- Abrir Blender em segundo plano somente quando necessário, importar o esqueleto nativo, proteger originais, duplicar malhas/rig/LODs e preparar uma ação técnica de flexão.
- Criar revisões independentes `jobs/nome/r001`, `r002` etc. As saídas têm identificações distintas.
- Verificar âncoras UV em todos os pontos que serão exportados: 81 por componente no LOD alto e 25 em cada LOD inferior, cruzando lado, direção das normais e altura 3D. Detectar UV fora da base e ilhas ambíguas que caem em partes diferentes do corpo.
- Compor componentes já recortados no atlas e gerar relevo de superfície com pesos interpolados, LODs e normais/tangentes adequadas.
- Exportar candidatos YDD/YTD e reabrir para confirmar buffers originais, paletas de ossos, índices, pesos, materiais nativos, vínculo do atlas e orçamento. Um build idêntico reutiliza a saída.

O empacotador `package_addon.py` produz YMT e shop metadata de uma coleção independente, compila o YMT com o CodeWalker local e reabre o arquivo para conferir componente, índices e texturas. Os perfis de teste disponíveis neste primeiro ensaio são camisetas masculinas (11, com braços e peça interna compatíveis) e calças masculinas (4, sem alterar outros componentes). Outros componentes e personagens precisam de um perfil de aplicação validado. Os comandos são exclusivos por trabalho e podem ser definidos em `test_commands`.

Movimento secundário tem especificação e referência de runtime existentes em `templates/motion.json` e `cidade_roupas/tactical_straps.lua`. **O adaptador genérico de objetos móveis ainda depende da autoria dos objetos e integração por variação.** O build bloqueia esse ramo enquanto não estiver pronto. Renders comparativos e teste real continuam como etapas explícitas: um candidato nativo não é declarado aprovado automaticamente. Não há uma simulação genérica de tecido ou uma aprovação visual automática escondida no processo.

## Erros que a pipeline procura

Erros automáticos: bolso interno quando deveria ser externo; lado invertido; reforço atrás quando deveria estar à frente; altura errada; UV inexistente/ambíguo; componente com fundo opaco; pesos inválidos; LODs/índices inválidos; base modificada; modelo de sexo incompatível; atlas exagerado; prefixo de saída que substituiria uma peça nativa.

Revisão visual obrigatória: tecido esticado, costura sem continuidade, volume de balão, brilho de plástico, logo espelhado ou ilegível, interseção em joelho/cotovelo, buraco na manga/tornozelo, ponta de fita escondida pela camisa e detalhes sumindo nos LODs. Superfícies em ângulos muito variados e peças que cruzam UVs precisam de autoria específica, em vez de forçar o retângulo de um bolso sobre qualquer base.

Elementos móveis precisam ainda ser observados em repouso, aceleração, parada, giro, veículo, distância e troca de roupa. O runtime anterior acompanha jogadores ativos; para aparecer no boneco clonado do tablet, uma variação móvel precisa registrar também essa entidade de prévia.

## Uso

Na pasta da cidade, com Python já instalado:

```powershell
C:\Python313\python.exe personagens/pipeline_roupas/pipeline.py bases --category lowr --sex male
C:\Python313\python.exe personagens/pipeline_roupas/pipeline.py prepare --base ec240957694f --blender
C:\Python313\python.exe personagens/pipeline_roupas/pipeline.py new --name minha_variacao --base ec240957694f --reference "C:\caminho\referencia.png"
```

No `job.json`, definir `material.albedo_atlas` como o arquivo UV final dentro de `inputs`. Componentes fixos usam o formato de `templates/component.json`; as coordenadas do exemplo pertencem à calça anterior e devem ser verificadas para qualquer outra base.

```powershell
C:\Python313\python.exe personagens/pipeline_roupas/pipeline.py check --job personagens/pipeline_roupas/jobs/minha_variacao/r001
C:\Python313\python.exe personagens/pipeline_roupas/pipeline.py build --job personagens/pipeline_roupas/jobs/minha_variacao/r001
```

Para autoria manual, copiar o arquivo indicado em `result.blender.project` pela preparação para `jobs/nome/revisao/work/variacao.blend`. Nunca editar o cache. Fontes ficam em `bases/ID/versao-do-cache`; projetos Blender ficam em `blender/versao-do-preparador` dentro dessa pasta. Atualizar um adaptador cria um cache novo e conserva as revisões anteriores. A rota de superfície é adequada para bolsos/patches seguindo a roupa; formas salientes, penduradas ou rígidas exigem um adaptador de geometria específico. O build atual não consome silenciosamente edições feitas no `.blend`.

O projeto conserva separadamente os três LODs da calça e seus materiais, além do rig nativo. `VolumeSampler/givemechecker` é uma referência externa não ligada ao shader de prévia dessa base; ela é registrada no relatório. A difusa, normal e especular efetivamente utilizadas estão empacotadas. O material nativo do arquivo exportado permanece intacto, exceto pelo vínculo da nova difusa.

Exceção registrada por material: bases com `ped_palette.sps` podem recolorir uma arte RGB. O adaptador explícito `material.adapter: "palette_to_rgb"` troca os presets por `ped.sps`/`ped_default.sps` e remove apenas o sampler de paleta; normal, especular, parâmetros restantes, rig e geometria são conferidos. Sem essa opção, os shaders permanecem nativos. O relatório distingue preservação integral do material de preservação dos mapas e do rig.

Depois de inspecionar as quatro vistas e as flexões, registrar `review.positions` e `review.appearance` como verdadeiros e empacotar:

```powershell
C:\Python313\python.exe personagens/pipeline_roupas/package_addon.py --job personagens/pipeline_roupas/jobs/west_texas/r002
```

O pacote fica em `package/resource`, com manifesto, cliente de teste, shop metadata e streaming. A instalação copia somente esse recurso para sua pasta própria em `server-data/resources` e adiciona um `ensure` no `server.cfg`. Uma instalação não aprova a aparência no jogo: `review.in_game` continua falso até o teste real. Atualizações de streaming precisam ser carregadas pelo servidor e podem exigir reconexão do cliente.

Primeiros ensaios: `jobs/west_texas/r002` (`camisetatexas`, `roupastexasanterior`) e `jobs/jeans_washed/r001` (`calcajeans`, `jeansanterior`). As bases originais continuam disponíveis. A camiseta usa a arte enviada e um retalho sem estampa para tecido uniforme; a calça registra a referência frontal na silhueta nativa e conserva bolsos/costuras das costas, com contribuição dos três painéis enviados. As imagens em `qa` são renders técnicos, separados do teste FiveM.

## Rapidez e economia

Variações solicitadas como exclusivas podem ser registradas no tablet depois de instalar o pacote revisado: `register_exclusive.py --job jobs/nome/r001`. O registro confere hashes dos arquivos instalados, a coleção e as miniaturas reais; não modifica tags nem favoritas. As peças ficam em `roupas → Masculino → Exclusivas`, além da categoria normal. A camiseta usa braços compatíveis, preservando calça, roupa interna e acessórios. O Acervo web também inclui essas variações, com as mesmas tags de revisão. Recarregar o recurso e o servidor web para ler o manifesto atualizado.

Para lotes de camisetas com painéis de tecido quadrados, `bake_textile_batch.py` reutiliza a base Blender e produz atlas UV, quatro vistas e duas flexões. Tecidos lisos usam coordenadas contínuas no torso e nas mangas; a camiseta listrada usa `projection: "native_uv"` para acompanhar as ilhas originais sem cortes artificiais no peito. O UV nativo permanece como destino do bake e da exportação. As referências completas servem para comparação, não são tratadas como atlas prontos. A escala da trama e a escala das listras podem ser separadas para evitar fibras exageradas.

Textura simples segue a rota nativa sem abrir Blender. A base, o rig e o mapa UV não são reconstruídos em cada tentativa. A ficha registra medidas, âncoras e hipóteses para não redescobrir o problema. Só a etapa afetada é refeita; mudanças de geometria refazem sua própria checagem. Logs completos ficam nos arquivos, e na conversa relatamos resultado e pendências.

As metas são extração/importação uma vez por base e correções localizadas nas seguintes tentativas. Tempos medidos ficam nos relatórios; não se promete duração fixa para modelagem, recortes complexos ou criação de novo addon.

`bake_pants.py` registra referências transparentes na silhueta nativa. Para fotos com desgaste ou rasgos, `clean_back_crop` separa um retalho sem arte; o tom do tecido e a trama com contraste reduzido evitam repetir grandes marcas nas costas. Rasgos desenhados na difusa não abrem buracos na geometria. `flame_art` permite duas imagens independentes com alpha, sem repetição, num enquadramento físico comum: a arte maior vai à frente e a menor às costas. As miniaturas e o teste `tests/jeans_arte.py` verificam essa diferença nos renders; o teste real no FiveM continua necessário.

## Verificação da pipeline

`C:\Python313\python.exe tests/clothing_pipeline.py` exerce aprovação atual, isolamento de revisões, cache e detecção de alteração, rejeição de entradas inválidas, UV ambíguo, posição incorreta e uma exportação real com relevo, seguida de releitura do YDD/YTD. `validation.json` registra os resultados. O ensaio usa uma imagem sintética apenas para verificar o mecanismo; não representa a aprovação de uma nova roupa.

## Entrega de cada variação

Base identificada e conservada; projeto Blender quando usado; originais das referências; atlas e componentes; YDD/YTD e eventuais YDR/YTYP; metadados da coleção; comparação frente/costas/lados; flexões relevantes; relatório de posicionamento; teste do runtime; resultado no FiveM. A aprovação da nova peça depende da revisão da aparência e do teste real, sem inventar um percentual de semelhança a partir de uma única vista.
