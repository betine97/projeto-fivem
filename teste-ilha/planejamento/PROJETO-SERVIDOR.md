# Projeto do servidor — documento de referência

Atualizado em 09/10/2026. Revisão 5. Fonte: decisões e propostas da conversa com o proprietário do projeto.

## Como consultar e atualizar

Este documento é a referência de continuidade do projeto. Consultá-lo antes de desenhar o mapa ou implementar sistemas. Atualizar as decisões após cada aprovação, registrando a data e a consequência. Preservar decisões anteriores no histórico quando forem substituídas.

Estados usados:

- **Definido:** pedido explícito ou direção aceita pelo usuário.
- **Proposta:** sugestão de desenho; detalhes ainda não aprovados.
- **Pendente:** questão que precisa de decisão ou validação.
- **Existente:** recurso que já consta nos arquivos; isso não implica validação de todas as situações no jogo.

A aprovação de um conceito visual não aprova automaticamente dimensões finais, regras econômicas ou publicação no servidor.

## 1. Identidade e objetivo

**Definido:** servidor FiveM com mundo autoral, sem a cidade/mapa original do GTA. A cidade anterior fica preservada para consulta e retorno em modo separado.

**Definido:** inspiração visual e temática em regiões da Colômbia, Venezuela e Cuba; cidade, ilhas, governo, intervenção dos EUA, facções, cidadãos, profissões e empresas de jogadores. O país pode ser fictício, permitindo combinar essas referências de maneira coerente.

**Definido:** equilíbrio entre RP civil, política, crime, combate e exploração. O jogador precisa ter objetivos e motivos econômicos para agir, com escolhas baseadas em oportunidade versus risco.

**Definido:** presença de Pablo Escobar no universo do jogo. **Proposta:** versão ficcionalizada, com cartel próprio, missões e decisões de NPC; participação de equipe em eventos especiais. Aparência, voz, localização e funcionamento ainda pendentes.

**Definido:** governo e cartel têm poderes relevantes; a intenção é um equilíbrio aproximado entre ambos. Não existe porcentagem mecânica fechada. **Proposta:** governo concentra autoridade urbana e institucional, cartel tem influência econômica e territorial; jogadores podem alterar esse equilíbrio.

## 2. Mundo, tamanho e relevo

### O que existe hoje

- Ilha em `teste-ilha`, construída no Blender e integrada ao FiveM.
- Medidas registradas no projeto existente: aproximadamente 3,37 km² emersos, extensão de 2,00 × 2,39 km, pico de 365 m, rio de 1,86 km e pista de 692 × 31 m.
- A referência anterior de “3 vezes Cayo Perico” foi calculada como multiplicador de área, usando uma estimativa local dos modelos nativos; não é uma medida oficial.
- Existe uma amostra natural em apenas um setor, com árvores, palmeiras, pedras, arbustos, vegetação e mistura de materiais nativos de solo.
- O usuário confirmou que a última correção funcionou. Isso confirma o resultado relatado, não todos os sistemas futuros ou cada detalhe de água e colisão.
- **Implementação autorizada em 09/10/2026:** aproveitar a ilha existente e construir o primeiro porto aprovado, usando os dez modelos texturizados mais recentes de `estruturas_porto_20261009`. A montagem em `porto_construido/ilha_porto_esperanca.blend` tem 91 construções, cais, terminal, praça, ponte, ruas, 7.556 árvores, 5.951 plantas baixas e 430 pedras; aproximadamente 3,315 km² emersos. A pista anterior foi preservada. A preparação nativa inclui colisão e vento; aparência, FPS, água e movimento no cliente ainda estão pendentes de conferência. Ver `porto_construido/LEIA-ME.md` e os relatórios de instalação para o estado efetivo do servidor.

### Desenho sugerido para a evolução

**Proposta:** arquipélago compacto com uma ilha principal e duas menores. Iniciar com a principal e, posteriormente, uma ilha pequena com uma atividade relevante. A divisão em três ilhas ainda não foi aprovada explicitamente.

**Proposta:** principal de aproximadamente 4 × 5 km de extensão e 12–15 km² de terra, ajustada por contorno e testes de deslocamento. Esse tamanho é maior que a ilha existente e não mantém automaticamente a proporção anterior de 3 vezes Cayo. **Pendente:** ampliar, reconstruir ou aproveitar a ilha atual em escala menor.

**Definido:** terreno criado no Blender, com inclinações, morros, montanhas e rio chegando ao mar. Desenvolvimento gradual e aprovação visual antes de gerar o próximo lugar.

**Definido:** locomoção fácil nas áreas cotidianas e acesso mais difícil a regiões especiais. Toda região deve ter função na economia, história ou disputa territorial.

| Região proposta | Relevo e acesso | Funções |
|---|---|---|
| Cidade e porto principal | Planície costeira, vias largas | Governo, comércio, hospital, empresas, desembarque e cargas |
| Interior agrícola | Colinas suaves e estradas secundárias | Alimentos, propriedades, coleta e produção |
| Cordilheira central | Picos de referência entre 250 e 450 m, passagens selecionadas | Minas, expedições e instalações estratégicas |
| Vale do rio | Nascente no interior e foz em baía; travessias selecionadas | Ouro, pesca, agricultura e comunidades |
| Costa afastada | Enseadas e falésias, acesso mais limitado | Contratos especiais, exploração e pequenos desembarques |
| Ilha de recursos futura | Implantação a definir | Minas, energia e comunidades menores |
| Ilha de fronteira futura | Implantação a definir | Porto secundário, pista e eventos de intervenção |

**Proposta:** via principal conectando cidade, porto, aeroporto e interior; caminhos alternativos e passagens montanhosas. Não permitir que uma única passagem paralise toda a economia.

**Proposta:** serviços essenciais separados por poucos minutos; entregas comuns de 4–7 minutos e expedições de 8–12 minutos. São metas de experiência, não tempos garantidos: medir dirigindo e navegando no FiveM.

**Proposta:** espaços difíceis oferecem recompensa específica, sem obrigar todo cidadão a atravessá-los diariamente. Evitar zonas vazias muito grandes e dispersão excessiva de jogadores no início.

## 3. Chegada e liberdade dos personagens

**Ideia original do usuário:** recém-chegados trabalham na colheita, coleta, embalagem e distribuição do cartel até pagar uma cota de serviço; depois ficam livres e podem voltar por remuneração.

**Proposta discutida:** introdução curta com dívida ou obrigação de história, oferecendo trabalhos legais e do cartel. Não fechar o jogador em uma única carreira.

**Pendente:** escolher o fluxo final de chegada, obrigação inicial, prazo, alternativas e maneira de concluir essa fase.

**Definido:** permitir trabalho individual, formação voluntária de grupos e empresas. Possibilitar criatividade e caminhos diferentes de progressão.

## 4. Facções, território e liderança

**Definido:** grupos começam independentes, podem permanecer sozinhos, formar alianças ou se aproximar do cartel do Pablo. Facções podem perder poder e ser destruídas.

**Definido:** organização e estratégia devem influenciar acesso a armamentos, munições, suprimentos e território.

**Proposta:** territórios concedem acesso a instalações, contratos, produção ou influência, e exigem manutenção. A geografia não será dividida simplesmente em uma ilha por facção.

**Ideia do usuário:** adquirir armamentos e munições disputando carregamentos marítimos e aéreos ligados à ajuda externa. **Pendente:** regras de eventos, frequência, conteúdo, participação e condições de vitória; facções exclusivas de armas ou munição não estão decididas.

**Definido como direção:** liderança com moral/confiança e possibilidade de votação para destituir o chefe.

**Proposta:** confiança influenciada por remuneração, acordos, uso do caixa e resultados; voto com quórum e elegibilidade para evitar sabotagem por contas alternativas. Tesouro, base e contratos pertencem à organização. Perder a liderança muda a administração.

**Proposta:** destruição da facção perde ativos e controle da organização, preservando os personagens. Disputas com condições de defesa e horários adequados à população, evitando destruição completa enquanto todos estão offline.

## 5. Economia, empresas e profissões

**Definido:** dezenas de oportunidades de renda e negócios, com relações de oportunidade versus risco.

Atividades solicitadas: extração de petróleo, refinamento, mineração/perfuração, procura de ouro nos rios, produção de alimentos, transporte, medicina e empresas próprias.

**Proposta:** conectar profissões em cadeias de oferta e demanda:

- Energia: extração → refinamento → transporte → postos, veículos e máquinas.
- Mineração: extração → processamento → materiais e manutenção de equipamentos.
- Rio e mar: ouro, pesca, transporte e recuperação de cargas.
- Alimentos: agricultura/pecuária → processamento → mercados e restaurantes.
- Construção: pedra e materiais → transporte → obras e instalações.
- Serviços: mecânica, saúde, segurança, passageiros e entregas.

**Proposta:** contratos limitados de NPC sustentam a economia com poucos jogadores; negócios e contratos entre jogadores ganham espaço conforme a população cresce. Não existem preços ou salários definidos.

**Proposta de primeira fase econômica:** combustível, alimentos e mineração/ouro, contratos e valorização da vida; expandir depois. Essa ordem ainda pode ser revista.

## 6. Necessidades e valorização da vida

**Definido:** combustível, alimentação e outras necessidades devem criar planejamento e demanda.

**Proposta:** água, comida e combustível têm efeitos relevantes, com intervalos confortáveis; expedições e máquinas consomem recursos. Evitar tarefas repetitivas excessivas.

**Definido:** tempo de personagem vivo concede benefícios para incentivar valorização da vida.

**Direção aceita:** personagem continua após uma morte real, mas perde bônus acumulados e recebe consequências; encerramento permanente fica reservado a situações especiais de RP.

**Proposta:** distinguir incapacitação e resgate de morte real; contar tempo ativo, limitar bônus e impedir ganho por AFK. Benefícios pequenos de trabalho, disposição e recuperação, sem superioridade infinita em combate. Critério de morte, perdas e limites ainda pendentes.

## 7. Medicina e governo

**Definido:** médicos escolhem contratos privados, empresas próprias ou atuação exclusiva para o governo.

**Proposta:** contratos definem remuneração, duração, obrigações, exclusividade e rescisão; clínicas dependem de equipamentos, profissionais e suprimentos.

**Definido:** polícia nacional intervém no transporte ilegal. Governo e intervenção externa precisam ter papel na economia e no conflito.

**Proposta:** fiscalização, documentos, apreensões, exames e investigação com informações incompletas, ferramentas de defesa e contrajogo. Competências, penas, hierarquia e regras eleitorais do governo ainda pendentes.

## 8. Produtos fictícios, dependência e concorrência

Todas as substâncias, formulações e efeitos descritos aqui são mecânicas fictícias de jogo. O desenvolvimento usa atributos abstratos, não fórmulas químicas reais ou procedimentos reais de produção.

**Definido como ideia a desenvolver:** personagens começam dependentes de um produto controlado por uma aliança entre governo e cartel do Pablo. Concorrentes tentam conquistar consumidores com produtos próprios e vantagens específicas.

**Proposta:** dependência inicial leve ligada a um programa estatal, com possibilidade de tratamento e escolha de fornecedor desde o início. **Pendente:** obrigatoriedade, apresentação da história, intensidade e duração da condição inicial.

**Definido:** uso repetido cria dependência; uma dependência concorrente pode fazer a anterior perder relevância. Há uma barra de vício com consequências para a saúde.

**Proposta:** três indicadores separados:

1. Dependência por produto: histórico e necessidade percebida.
2. Tolerância por produto: redução do benefício com repetição.
3. Saúde: desgaste acumulado e recuperação.

**Proposta:** interface geral mostra carga de dependência e produto dominante; detalhes exibem vínculos individuais. O concorrente reduz temporariamente a necessidade percebida do anterior, que diminui gradualmente. Troca não funciona como cura automática.

**Definido:** equilibrar efeitos de combate com trabalho, exploração e preparação.

**Propostas antigas de nomes:** Vigor (disposição), Foco (tarefas técnicas), Bruma (estresse fictício). Nomes, efeitos e associação a facções não estão aprovados.

**Proposta:** benefícios limitados, custos, duração, recuperação e tratamento médico. Evitar invencibilidade, enormes bônus de dano, punição por ausência offline ou obrigação de consumo para qualquer carreira. Consumidores NPC também sustentam demanda inicial.

### Descobertas e personalização

**Definido como direção:** cumprir metas libera novas formulações fictícias e possibilidades de especialização; jogadores e facções podem usar criatividade.

**Proposta:** descobertas exigem profissionais, instalações, contratos e recursos. A produção combina atributos abstratos:

| Atributo | Benefício possível | Contrapartida possível |
|---|---|---|
| Duração | Uso menos frequente | Recuperação mais lenta |
| Intensidade | Benefício temporário maior | Mais tolerância e desgaste |
| Menor desgaste | Produto atraente a consumidores preocupados | Custo maior |
| Estabilidade | Qualidade consistente | Equipamentos e especialistas |

Potência é uma especialização; qualidade, preço, menor desgaste e distribuição também podem gerar sucesso. Não há árvore de pesquisa, números ou receitas fechados.

### Produtos alimentares e exposição

**Ideia do usuário:** representar distribuição em frutas, lanches e outros produtos, usando criatividade.

**Proposta:** itens e ingredientes inteiramente fictícios, lotes rastreáveis, sintomas, exames, denúncias e consequências para fornecedores. Exposição involuntária teria efeitos limitados; dependência duradoura exigiria interação continuada. **Pendente:** regras finais, transparência para o jogador e limites de aplicação.

## 9. Suprimentos, cargas e transporte

**Definido:** transportes de drogas e suprimentos fazem parte central da dinâmica; alguns recursos vêm de fora da ilha.

**Proposta:** equipamentos médicos, peças industriais e insumos fictícios importados por navios ou aeronaves. Produção local abastece alimentos, combustível refinado e outras necessidades.

**Proposta:** carga com origem, destino, proprietário, valor e prazo. Sistemas geram trabalho para transporte, comércio, segurança e autoridades, além de disputas por recursos.

**Proposta:** rotas com escolhas de tempo, custo e risco; disponibilidade de eventos proporcional à população. Entregas civis continuam viáveis durante disputas, com alternativas e oportunidades. Regras de contrabando serão abstrações de jogo, ainda não desenhadas.

## 10. Primeiro lugar e método de construção

**Definido em 09/10/2026:** construir aos poucos. Antes de gerar o primeiro local no Blender, entregar descrição detalhada para o usuário gerar imagens e aprovar.

**Proposta visual:** Porto Esperança, nome provisório; baía com porto misto, bairro costeiro, praça de chegada, fiscalização e estrada para o interior. Ver `PRIMEIRO-LUGAR-PORTO-ESPERANCA.md` para implantação, aparência e prompts.

**Aprovação de 09/10/2026:** usuário forneceu uma vista de bairro portuário tropical e duas pranchas de vegetação, autorizando a geração no Blender. Escopo: terreno, disposição das plantas de ambas as pranchas, vegetação rasteira, pedras e reservas para prédios/casas/estruturas. Edifícios ficam para depois.

**Existente:** cena Blender de terreno e vegetação em `../porto_esperanca/porto_esperanca.blend`, com 16 setores, 24 modelos individuais, 4.107 instâncias de plantas, 4.200 tufos de grama, 430 pedras e 25 reservas de futuras estruturas. Há catálogos e prévias para validação visual. A aprovação visual não define ampliação da ilha nem instalação no FiveM; o pacote usa coordenadas locais e preserva o mundo existente.

**Recebido em 09/10/2026:** usuário enviou 16 imagens recortadas de troncos e galhos e uma prancha de vegetação, informando que enviará as folhas em seguida. Cópias preservadas em `../porto_esperanca/texturas/troncos`, com origem, transparência, SHA-256 e associações provisórias no manifesto. São referências de troncos completos; materiais de casca e UV precisam de preparação. **Pendente:** lote das folhas, correspondência definitiva com os modelos e aplicação/validação dos materiais no Blender. O recebimento não altera o servidor nem substitui os materiais da cena.

**Atualização de 09/10/2026:** usuário enviou dez imagens de folhagem e autorizou começar com elas. Primeira aplicação em `../porto_esperanca/porto_esperanca_texturas_lote01.blend`: oito árvores de copa e duas palmeiras, com dez imagens de troncos e dez de folhas incorporadas. Casca aplicada por UV em geometria 3D; árvores de copa preservam folhas e flores 3D, com imagens de folhagem mapeadas nas folhas; palmeiras têm frondes e folíolos curvos modelados. A versão anterior e os demais modelos foram preservados. Há projetos individuais e prévias. **Pendente:** aprovação visual, confirmação das associações das imagens, materiais dos modelos restantes e preparação nativa/instalação FiveM. Detalhes em `../porto_esperanca/texturas/folhas/LEIA-ME.md`.

Fluxo proposto:

1. Escolher a referência visual e resolver ajustes.
2. Aprovar a implantação e dimensões do trecho.
3. Fazer o bloco de terreno, ruas, cais e volumes no Blender.
4. Validar caminhando e dirigindo, com colisão e distâncias reais.
5. Trabalhar fachadas, materiais, vegetação e iluminação.
6. Construir interiores e ligar sistemas em etapas aprovadas.
7. Expandir somente depois de validar o trecho anterior.

## 11. Continuidade técnica e pedidos anteriores

A documentação de mecânicas futuras não significa que esses sistemas estejam implementados.

- Mundo atual: `../LEIA-ME.md` e medidas em `../dados/medidas.json`.
- Amostra natural: `../amostra_natural/LEIA-ME.md`, revisão `ilha-20261009-amostra-natural-3`.
- Cidade anterior: `../cidade-original-preservada`, modo separado; preservar seus recursos e configurações.
- O usuário confirmou o funcionamento após a última correção de crash. Manter os limites internos nativos de recorte da água; não reintroduzir a expansão que precedeu o crash.
- A água de rio/lago no cliente ainda precisa de validação específica; sucesso da chamada de carregamento não prova que a grade customizada carregou.
- Testes de arquivos e mocks não substituem validação visual, desempenho e física no FiveM.
- Preservar backup antes de regenerar terreno; a geração base pode substituir a configuração e exigir reaplicação da amostra.

Pedidos anteriores da cidade, registrados para não perder escopo histórico:

- Administração pelo F8: lista de comandos, puxar/localizar jogadores, armas e automóveis; permissões devem ser conferidas no recurso existente antes de migrar ou expandir.
- Editor ADM de objetos, ativado por comando no F8 e seleção com CAPS para reposicionamento. Existe documentação em `../../casa_vinewood/editor_objetos_20261008/README.md`.
- Mansão: iluminação contínua entre cômodos; teto branco e pendentes amarelos, alcance até o piso; investigação da aparência nublada.
- Proteção de chuva e névoa na mansão: usuário pediu retirada e adiamento após crashes. Não reintroduzir como parte do novo projeto.
- Mansão: portas adicionais com a referência de madeira/vidro, abertura para fora, remoção do coqueiro marcado, correção da barreira da escada, emenda de parede e tremor do portão. Consultar documentação em `../../casa_vinewood` para o estado de cada intervenção.
- Hospital solicitado anteriormente: exterior inspirado na referência e salas de cirurgia, espera, consulta, óbitos, descanso, exames e conversas médicas, com textura e colisão. Há trabalho em `../../hospital_carcer_20261008`; o edifício da cidade antiga não foi aprovado automaticamente para implantação nesta ilha.

## 12. Decisões pendentes

- Nome do país, servidor, capital e locais.
- Escala final da ilha e aproveitamento do terreno atual.
- Quantidade de ilhas no lançamento e distância entre elas.
- Aprovação visual do porto e limite da primeira etapa.
- Tamanho de população pretendido, para calibrar economia e mapa.
- Chegada dos jogadores: obrigação inicial, escolhas e dependência.
- Produtos fictícios, efeitos, tratamento, tolerância e progressão.
- Regras de exposição por alimentos e liberdade de personalização.
- Territórios, pesquisa, armamentos, destruição e votação de facções.
- Governo, eleição, polícia, intervenção externa e justiça.
- Frequência de carregamentos e condições de participação.
- Valores, preços, salários, contratos, necessidades e consequências da morte.

## 13. Histórico

| Data | Registro | Consequência |
|---|---|---|
| 09/10/2026 | Consolidado o conceito discutido na conversa | Decisões diferenciadas de propostas e pendências |
| 09/10/2026 | Usuário pediu aprovação visual antes do Blender | Primeiro lugar descrito para gerar referências |
| 09/10/2026 | Conferida a diferença entre ilha existente e escala sugerida | Ampliação não executada; escala final permanece pendente |
| 09/10/2026 | Usuário aprovou configuração por imagem e duas pranchas de plantas | Autorizados terreno, vegetação, pedras e lotes reservados no Blender; edifícios em etapa posterior |
| 09/10/2026 | Criada a primeira cena Blender e o catálogo de plantas | Artefatos em `porto_esperanca`; implantação no FiveM e edifícios permanecem posteriores |
| 09/10/2026 | Recebidos e preservados 16 recortes de troncos/galhos e catálogo | Origem e associações provisórias registradas; folhas e aplicação dos materiais pendentes |
| 09/10/2026 | Usuário enviou dez copas/frondes e autorizou começar com elas | Primeira aplicação em dez modelos em versão Blender separada; aparência e associações aguardam validação; servidor permanece na etapa anterior |
