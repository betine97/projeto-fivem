# Plataforma Petro Esperança

Modelo editável em `plataforma_petroleo.blend`, inspirado na imagem fornecida. A plataforma foi construída em uma pasta independente: esta entrega não altera a ilha, suas casas ou os recursos ativos do servidor.

O conjunto tem três conveses, fundação treliçada, torre de extração, separadores, tanques, módulo de refino, bombas, tubulações, válvulas, sala de controle, alojamento, manutenção, heliponto, doca, escadas e dois guindastes. A torre principal tem aproximadamente 72 m de altura sobre o nível do mar; o convés inferior fica em Z=14 m, o de produção em Z=20 m e o superior em Z=26 m. A escala é em metros e a origem é local.

As superfícies principais usam as cinco texturas fornecidas: chapas brancas nos módulos e equipamentos pintados, amarelo na estrutura e guarda-corpos, ferrugem nas peças escuras, metal cinza nas tubulações e piso antiderrapante nos conveses, escadas, passarelas e doca. As imagens originais estão em `texturas/`, sem alteração, e também estão embutidas no `.blend`. As repetições são ajustadas em metros; o piso repete a cada 0,72 m e as chapas brancas a cada 6 m. O heliponto mantém superfície cinza com sua sinalização.

Foi acrescentado um relevo visual suave no material, aproximado a partir da cor das imagens; não se trata de mapas PBR de altura ou normal fornecidos, nem altera a geometria de colisão. `dados/texturas.json` registra as imagens, suas escalas e hashes; `dados/verificacao_texturas.json` registra a conferência após reabrir o arquivo. A versão anterior está em `backups/plataforma_antes_texturas.blend`.

A geometria, incluindo os interiores acessíveis, é tridimensional. A imagem original permanece copiada sem alteração em `referencias/`. Este modelo é uma reconstrução inspirada na referência, com proporções e distribuição adaptadas à circulação do jogador.

## Abrir e explorar

Abra `plataforma_petroleo.blend`. A câmera inicial mostra o conjunto. As coleções separam estrutura, circulação, extração, refino, alojamento, heliponto, guindastes, carga e apresentação. O mar serve à apresentação e não faz parte da exportação do equipamento.

Na linha do tempo, reproduza os quadros 1 a 216 para ver o guindaste principal erguer um pallet com quatro barris, girar, baixar a carga e retornar. O giro de retorno termina com a carga elevada, antes da descida pelo vão. Os controles `Guindaste principal | GIRO`, `LANCA`, `GANCHO` e `CARGA | pallet articulado` são objetos independentes. O cabo acompanha a altura do gancho por um driver. A carga mostra um pequeno balanceio animado. Trata-se de uma demonstração no Blender, ainda não de uma simulação de carga sincronizada no FiveM.

Há um vão real no convés superior acima da estação de carga: a carga pode ser içada sem atravessar o piso. Escadas externas e uma rampa ligam os acessos. Os barris e pallets possuem origens separadas para futura movimentação.

`12_COLISAO_PREPARADA` contém volumes fechados de pisos, paredes, degraus, rampa e equipamentos, com corpos rígidos passivos no Blender. Está oculta para apresentação. Esses volumes ainda devem ser convertidos em colisão nativa YBN e associados aos modelos do jogo; não comprovam física funcionando no FiveM. Guardas, cabos e pequenos detalhes visuais também precisam de uma decisão de colisão na exportação.

`dados/interacoes.json` registra doze pontos de trabalho em coordenadas locais. `dados/escadas.json` contém as medidas dos degraus. `dados/colisoes.json` descreve os volumes preparados. `dados/verificacao_blender.json` registra as verificações realizadas após reabrir o arquivo.

## Três tarefas da extração

1. **Preparar e operar o poço.** O jogador confere energia e filtros, regula três seletores e liga a bomba. Um painel apresenta fluxo, estabilidade e carga em escalas abstratas de 0 a 100. O desafio é manter os indicadores na faixa do contrato durante pequenos ajustes. Um erro reduz rendimento e exige uma correção curta, preservando o progresso já obtido.
2. **Separar e conferir o lote.** O jogador coleta uma amostra, escolhe o filtro e ajusta dois controles de separação. Ele acompanha barras de impurezas e qualidade. Pode aprovar um lote comum rapidamente ou gastar mais tempo para melhorar um contrato de maior exigência. A troca de filtro é uma ação no equipamento, e a análise acontece na bancada, dando motivo para circular pela plataforma.
3. **Envasar e movimentar a carga.** O jogador posiciona barris, acompanha o enchimento, fecha o lacre e monta um pallet. Cada pallet tem quatro barris. Ele engata o sling e usa o guindaste: girar, levantar, baixar, estabilizar e soltar. Um parceiro pode orientar pelo rádio e conferir a área de recebimento. A carga exige controle suave e pontos de engate; o jogador não precisa transportar cada barril inteiro pelo inventário.

Os números, receitas e controles são regras ficcionais de jogo. O módulo de refino representa o processamento de forma simplificada para servir ao trabalho do personagem.

## Refino e transporte

No **refino**, o jogador escolhe entre combustível, diesel e lubrificante de jogo. Três controles representam aquecimento, alimentação e resfriamento. A receita tem uma faixa de trabalho e uma exigência de qualidade. Produzir mais rápido aumenta o consumo de insumos; uma operação estável dá mais rendimento. Filtros saturam, a energia pode exigir reposição e uma amostra final aprova o produto. É possível reprocessar um lote reprovado, com custo e perda parcial, em vez de apagar a missão.

No **transporte**, o responsável confere lacres, prende os pallets e emite um manifesto com lote, quantidade, qualidade e destino. A embarcação leva a carga ao porto. O guindaste de terra transfere os pallets para um caminhão; a entrega abastece um depósito, oficina ou posto. O pagamento considera quantidade entregue e qualidade, com um bônus moderado por integridade. Uma entrega atrasada perde o bônus, mas continua possível.

Na primeira implementação, barris e pallets presos ao veículo devem usar pontos de fixação. O balanceio do guindaste pode ser calculado de forma limitada e replicado, para oferecer controle previsível entre jogadores. Carga solta com física totalmente livre pode ficar como modo posterior, após validar comportamento e rede.

## Cooperação, variedade e duração

Uma equipe pode dividir operação, refino, guindaste e navegação. Todas as tarefas também devem funcionar solo: o jogador alterna postos, com processamento em paralelo e avisos quando precisa voltar. O primeiro contrato deve durar cerca de 10 a 15 minutos, com um pallet pequeno. Contratos maiores aumentam lotes e rotas, sem repetir o mesmo minigame indefinidamente.

Variações possíveis: contrato urgente de abastecimento; lote de maior pureza; reposição de filtros; janela curta de embarque; inspeção de lacres; vento moderado que exige estabilização da carga; rota de entrega diferente. Falhas leves geram tarefas de recuperação locais. Desconexão e troca de operador não devem destruir o lote.

## Preparação da implementação no FiveM

O fluxo planejado está em `dados/mecanicas.json`. Sua sequência é contrato → preparação → extração → separação → envase → içamento → refino ou transporte do bruto → despacho → entrega.

O servidor deve ser a autoridade sobre lotes, quantidade, qualidade, contratos e pagamento. Cada pallet terá um identificador e um único registro de carga, com sua posição atual. Uma transferência muda esse registro; não cria uma segunda cópia no inventário. O cliente envia ações, e o servidor confere distância do posto, fase, permissões, tempo, capacidade e exclusividade do equipamento.

A exportação ainda exige shaders e texturas próprios do GTA, divisão em setores, LODs, colisões YBN, YTYP/YMAP, volumes e portais para interiores, entidades móveis do guindaste e testes dentro do FiveM. Os destinos no porto e as posições no oceano precisam ser definidos na implantação da ilha. Nenhum recurso foi instalado nesta entrega.

Para reconstruir, execute Blender 5.2 com `scripts/criar_plataforma.py`. `--sem-render` salva somente o modelo. Os arquivos originais da ilha e da biblioteca de casas não são utilizados nem sobrescritos.
