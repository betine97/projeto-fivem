# Teste Ilha

Ilha autoral criada no Blender, com praias, planícies, encostas, montanhas, lago de nascente, rio até o mar e uma pista de pouso simples. Sem árvores nem edifícios nesta versão. A geometria desta ilha não contém Los Santos, Blaine County ou terreno copiado do Cayo Perico.

## Arquivos principais

- `teste-ilha.blend`: projeto editável, com texturas incorporadas, câmeras, iluminação e coleções organizadas.
- `exportacoes/ilha_terreno.glb`: terreno, rio, lago e pista em formato portátil, com textura incorporada.
- `previews/ilha_geral.png`, `ilha_foz.png` e `ilha_mapa_superior.png`: imagens renderizadas no Blender.
- `dados/terreno.npz`: terreno em metros, alturas e dados do rio.
- `dados/altura_16bits.png`: mapa de altura de 16 bits. A linha superior corresponde ao norte; decodificação: `altura = pixel / 65535 × (altura_maxima + 65) − 65`.
- `dados/medidas.json`: medidas, setores e contagens de geometria.
- `dados/verificacao.json` e `verificacao_blender.json`: resultados das verificações estruturais.

## Dimensões

A superfície projetada acima do nível do mar é de aproximadamente **3,37 km²**, calibrada para **3 vezes a área estimada do terreno do Cayo Perico**. O multiplicador foi aplicado à área: não significa triplicar simultaneamente largura e comprimento.

A referência foi estimada nos modelos de terreno nativos do GTA instalado, somando triângulos de solo acima do nível do mar. Resultado aproximado: **1,123 km²**. Não é uma medida oficial; detalhes de vias e construções podem alterar o contorno contabilizado. Os arquivos nativos em `referencia_tecnica` servem apenas para a medição, não integram a ilha nova. A metodologia está em `referencia_tecnica/medicao_cayo.json`.

- Extensão aproximada do terreno emerso: **2,00 × 2,39 km**.
- Pico mais alto: **365 m** acima do nível do mar.
- Rio: **1,86 km**, descendo de aproximadamente 173 m até a foz a 0 m.
- Pista: **692 × 31 m**, com solo nivelado a 18 m.
- Mar: cota **0 m**.

## Edição e desempenho

O terreno foi dividido em **42 setores**. A coleção `01_TERRENO_EDITAVEL` contém o terreno detalhado; três coleções seguintes guardam versões com menos polígonos para distâncias maiores. As versões simplificadas ficam ocultas para não aparecerem sobrepostas ao terreno principal. Os vértices nas bordas usam a mesma grade, e as normais são calculadas globalmente para reduzir emendas visuais.

O terreno detalhado contém aproximadamente **774 mil triângulos**, distribuídos entre setores. A textura de cor tem 4096 × 4096 pixels e é compartilhada. A colisão de referência usa a malha intermediária, com aproximadamente 194 mil triângulos. Isso prepara a divisão dos recursos, mas o desempenho no FiveM ainda precisa ser medido após a integração.

`02_RIO_LAGO_MAR` contém superfícies de água para apresentação no Blender. `03_PISTA_POUSO` contém o asfalto e a sinalização. `07_COLISAO_TERRENO` contém malhas de referência de colisão, ocultas; elas não são arquivos nativos de física do GTA.

## Integração com FiveM — 09/10/2026

**A ilha foi convertida para arquivos nativos e instalada como modo padrão da base. O personagem inicia na pista de pouso.**

O pacote em `fivem` contém 131 arquivos nativos: 44 drawables YDR com níveis de detalhe, 42 colisões YBN, 44 posicionamentos YMAP e um catálogo YTYP. As colisões de jogo usam o terreno detalhado, enquanto as malhas de referência no Blender continuam disponíveis para edição. O total de arquivos nativos é aproximadamente 30 MB. Cada setor usa uma textura comprimida com mipmaps; a textura global de 4K não é duplicada inteira em cada setor.

O recurso `teste_ilha` substitui a definição do nível por `ilha.meta`, excluindo arquivos de posicionamento, colisão e arquivos de mapa da cidade original. Ele mantém os dados necessários aos personagens, veículos, armas, clima e efeitos do jogo. Os recursos da mansão, castelo, laboratório e hospital ficam inativos neste modo.

A água nativa é configurada em `data/water.xml`, com mar na cota 0, lago e regiões do rio. As regiões do rio usam células de água em alturas graduais; não há simulação de correnteza. A apresentação do Blender continua sendo uma referência visual e não comprova o resultado gráfico no jogo.

Há um mapa próprio acessível pelo comando `mapailha`; o radar da cidade original fica oculto. O personagem aguarda o carregamento da ilha e da colisão antes de ser liberado. Se o recurso da ilha falhar, o início na praça antiga fica bloqueado e o diagnóstico aparece no F8.

Verificações: todos os 131 arquivos passaram pela leitura independente do CodeWalker, e 165 verificações de integração passaram, incluindo posição inicial, ausência de retorno automático à cidade, proteção contra queda, níveis de detalhe, associação da colisão aos setores, endereços do pacote, diagnóstico de cidade antiga, falha da água e cópia instalada. **A aparência e a caminhada no cliente FiveM ainda precisam ser confirmadas em jogo.**

## Como iniciar e voltar à cidade

- `iniciar-cidade.cmd` na pasta original inicia **a ilha** por padrão.
- `iniciar-ilha.cmd` nesta pasta também inicia **a ilha**.
- `iniciar-cidade-original.cmd` na pasta original inicia a **cidade preservada**.

Feche a base em execução antes de alternar entre os modos. **Ao trocar da cidade para a ilha, feche completamente o FiveM e abra novamente. Apenas desconectar e reconectar pode manter o nível da cidade na memória**, sobrepondo prédios ao terreno novo. O iniciador detecta o servidor em execução e evita abrir outra cópia na mesma porta.

Correção de isolamento: os arquivos de imagens e água usam o endereço real do recurso (`resources:/teste_ilha/`). A água também é declarada no nível, para carregar antes dos scripts. `ilhadiag` informa a revisão e a quantidade real de regiões de água; isso permite distinguir uma sessão antiga de um problema no pacote. A correção ainda precisa ser confirmada visualmente após fechar e reabrir o cliente.

Conexão local no F8: `connect 127.0.0.1:30120`. A porta continua a mesma para seus amigos. O painel e as permissões ADM continuam disponíveis.

Comandos adicionais no F8:

- `ilha`: volta para a pista de pouso.
- `mapailha`: abre o mapa próprio da ilha; ESC fecha.
- `ilhadiag`: mostra posição, estado de colisão e carregamento da água.
- `amostrailha`: visita a área de teste com vegetação, pedras e materiais de solo originais do GTA.
- `amostradiag`: confere o registro dos modelos nativos da amostra e mostra o diagnóstico do terreno.

A amostra natural ocupa apenas um setor costeiro perto da pista, para validação antes de expandir a decoração. Os detalhes e o arquivo Blender editável estão em `amostra_natural/LEIA-ME.md`. Ao regenerar o mundo base, reaplique o pacote da amostra por último.

A configuração antiga foi guardada em `server-data/server-cidade.cfg`, e os arquivos alterados nesta ativação têm cópia em `backup_ativacao`. Os arquivos originais do GTA instalados no computador não foram modificados.

## Cópia da cidade atual

`cidade-original-preservada` guarda os recursos, configurações, painel e um backup consistente do banco de jogadores. `inventario.json` registra hashes de todos os arquivos copiados. O executável do FXServer permanece em `.runtime`, na pasta original; não foi duplicado. A cópia guarda a cidade no estado existente no momento em que foi feita.

## Regerar

Os scripts usam os caminhos de Python, Blender e dependências já instalados neste computador. Execute na pasta original `cidade fivem`:

```powershell
& 'C:/Python313/python.exe' 'teste-ilha/scripts/gerar_terreno.py'
& 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe' --background --python 'teste-ilha/scripts/criar_blender.py'
& 'C:/Python313/python.exe' 'teste-ilha/scripts/verificar_terreno.py'
& 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe' --background --python 'teste-ilha/scripts/verificar_blender.py'
```

A semente fixa `90321` torna o relevo reproduzível. O código permite alterar tamanho, montanhas, trajetória do rio e pista sem reconstruir manualmente a malha inteira.
