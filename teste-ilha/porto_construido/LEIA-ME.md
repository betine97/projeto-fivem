# Ilha e Porto Esperança construídos

Versão de 09/10/2026. A ilha existente recebeu uma cidade costeira baseada na primeira referência aprovada: cais, píeres, terminal, praça, pátio de cargas, ponte, ruas, bairro e encostas arborizadas. A referência orienta a composição; esta primeira implantação não reproduz seu acabamento fotográfico.

O projeto editável é `ilha_porto_esperanca.blend`. As prévias `previews/porto_construido.png`, `bairro_texturizado.png` e `ilha_completa.png` são renders do Blender, não capturas do FiveM. O relevo mantém a pista e os setores não modificados da ilha anterior.

Foram usados os dez modelos texturizados mais recentes de `../estruturas_porto_20261009/modelos`, com 91 instâncias de casas, sobrados, comércios, posto e galpão. Não foram usadas as casas antigas de Vinewood. Os interiores existentes foram preservados. As portas foram exportadas na pose aberta; ainda não há sistema de abrir/fechar ou sincronização de portas.

O pacote inclui 7.556 árvores, 5.951 instâncias de vegetação baixa e 430 pedras, além da amostra natural anterior preservada. Os 18 modelos de vegetação texturizada receberam materiais nativos de vento, pesos por vértice e colisão simplificada dos troncos/raízes. A folhagem permite passagem. O vento no FiveM é animação de shader; não é uma simulação individual de corpo rígido para cada folha. Espécies adicionais sem texturas aprovadas usam mangueira/coqueiro como substitutos; os 18 modelos fornecidos estão presentes.

Os prédios possuem quatro níveis de detalhe, com interiores e telhas detalhadas nas proximidades e simplificação à distância. Colisões derivam de pisos, paredes, escadas e vãos do projeto, com um volume simplificado para cada cobertura; não existe uma caixa bloqueando o edifício inteiro. Cais, ponte e ruas possuem colisão da geometria. Texturas originais permanecem intactas; o DDS de distribuição ajusta as dimensões para potências de dois e preserva a imagem inteira. Dicionários de textura separados por modelo evitam carregar um único pacote muito grande. Materiais procedurais foram aproximados por cores/texturas novas de solo; o relevo fino dos shaders Blender não foi integralmente convertido.

## Instalação e visita

`scripts/instalar.py` copia os 19 setores de terreno modificados para o recurso `teste_ilha` e instala os demais modelos em `server-data/resources/porto_esperanca`. O terreno tem um único proprietário, evitando arquivos de mesmo nome em dois recursos. `server-ilha.cfg` inicia `porto_esperanca` após `teste_ilha`; o modo da cidade antiga permanece separado.

Os arquivos anteriores ficam em `backups/<data>/`, com inventário e hashes em `restauracao.json`. Para retornar à revisão anterior, com o servidor parado, copiar os arquivos desse inventário para seus destinos originais e restaurar `server-ilha.cfg`. O novo recurso pode permanecer no disco, desativado.

Após conectar à ilha, abrir F8 e executar `porto` para visitar a praça. O comando verifica o piso antes de liberar o jogador; em caso de falha, retorna à posição anterior. `portodiag` imprime o diagnóstico e grava uma cópia em `server-data/resources/porto_esperanca/data/diagnostico_cliente.json`. Ao trocar de revisão de mapa, sair completamente do FiveM e conectar novamente evita manter arquivos antigos em memória.

## Verificação

`dados/validacao_codewalker.json` verifica a leitura dos arquivos nativos. `validacao_nativa_profunda.json` relê os blocos DDS, buffers, níveis de detalhe, texturas e colisões. `validacao_integracao.json` testa os pisos da praça/cais/ponte, pisos internos, passagens das portas, pesos de vento, correspondência do terreno e preservação da pista. `testes_client.json` cobre sucesso, falha, retorno, veículos e liberação do jogador por mocks dos nativos.

Esses testes não confirmam aparência, FPS, colisão em movimento, água ou balanço das folhas no cliente real. Essa conferência ainda requer visitar o porto no FiveM. A configuração de água substitui os trechos que atravessariam o novo bairro, conserva as regiões restantes e mantém o recorte padrão do motor; o carregamento efetivo dos novos setores de água precisa ser conferido pelo diagnóstico do cliente.

Não foram implementadas economia, empresas, profissões, NPCs ou missões. Mercado, farmácia e posto são construções do cenário, com os interiores já existentes.

## Reproduzir

Usar Blender 5.2 e Python 3.13 com as dependências locais do projeto. Executar `gerar_solo.py`, `cache_blender.py`, `construir_ilha.py`, `refinar_implantacao.py`, `acabamento_e_detalhe.py`, `corrigir_terminal.py` e `render.py` no contexto correspondente; depois `empacotar.py`, `preparar_integracao.py`, `manifesto_e_validacao.ps1`, `validar_nativo.py`, `testar_client.py` e `instalar.py`. Não executar o instalador antigo da ilha sobre esta revisão. As rotinas de refinamento operam sobre a montagem inicial e devem ser executadas uma vez após reconstruí-la.
# Correcao da entrada — 9/10/2026

A revisao `ilha-20261009-porto-entrada-2` substitui a entrada da ilha por um fluxo com prazos de carregamento. O personagem permanece protegido durante a preparacao e so e liberado depois de confirmar a altura real da pista. Tanto a tela nativa quanto a NUI de carregamento sao encerradas, e a camera volta ao personagem, inclusive em falhas. `recuperartela` no F8 repete a entrada com seguranca.

O diagnostico do cliente anterior confirmou posicao na pista, solo a 18 m e colisao carregada, mesmo com a imagem preta relatada. A causa visual exata ainda depende da verificacao no FiveM. Os sete testes da entrada e os seis testes do teleporte passaram usando simulacao de natives; isso nao comprova a renderizacao no jogo. O servidor foi reiniciado na porta 30120, mantendo a ilha e o porto ativos. Os relatorios de entrada seguintes sao gravados em `server-data/resources/porto_esperanca/data/entrada_*`. O backup anterior esta em `backups/correcao_entrada_20261009`.
