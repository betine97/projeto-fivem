# Minha Cidade — FiveM, ilhas e editor

Projeto FiveM em desenvolvimento com ilha autoral, Cayo Perico, editor de objetos,
captura de elementos do mapa, vegetação, fauna e painéis administrativos.

O servidor da ilha usa `127.0.0.1:30120`; Los Santos roda separadamente em
`127.0.0.1:30121`. Use `editorilha` para posicionar elementos e `capturarobjeto`
para adicionar modelos ao catálogo compartilhado em Los Santos ou Cayo Perico.

Este repositório guarda as fontes, interfaces, modelos e texturas. Arquivos grandes
usam Git LFS; serviços instalados e credenciais permanecem na instalação local. Consulte
[PUBLICACAO.md](PUBLICACAO.md) para o conteúdo do primeiro envio e os requisitos
para preparar outra instalação.

Equipe e branches: [CONTRIBUTING.md](CONTRIBUTING.md). Instalação portátil,
Docker, `.env`, dev/prod e GitHub Actions: [docs/EXECUTAR.md](docs/EXECUTAR.md).

Servidor próprio sem framework de RP, com personagem padrão do GTA e comandos de desenvolvimento. Até 16 jogadores, com ID permanente e aprovação pelo [painel local de acesso](painel_acesso/LEIA-ME.md). Abra `iniciar-painel.cmd` para administrar os jogadores; novos acessos começam pendentes. Reinicie a base após esta atualização e execute `liberar-amigos.cmd` como administrador para liberar a porta do FiveM no Firewall.

Combate v4: braços e encaixe visual da arma revisados; segundo Z levanta passando pelo ajoelhado em 1,5 segundo. Reiniciar `cidade_core` para carregar os arquivos novos.

Picape **Sertão**: `veiculo sertao` ou `sertao`, com torre visual sem disparo. Fonte Blender e detalhes em `veiculos/LEIA-ME.md`. Spawn/condução e aparência final das poses ainda precisam ser conferidos no jogo.

Mansão Vinewood: sala com sofá e TV, mesa de jantar com oito cadeiras, ilha com quatro banquetas e dois pendentes com iluminação quente. Revisão `jantar-cozinha-2026-10-07` instalada em `cidade_mansao`; use `restart cidade_mansao` no console e reconecte o FiveM. Fontes Blender, prévias e verificações em [casa_vinewood/LEIA-ME.md](casa_vinewood/LEIA-ME.md). Confirmação visual no jogo pendente.

## Primeiro acesso

1. Entre em https://portal.cfx.re com sua conta Cfx.re e crie uma chave de servidor.
2. Em `server-data/secrets.cfg`, substitua `COLE_SUA_CHAVE_AQUI` pela chave, mantendo as aspas.
3. Abra `iniciar-cidade.cmd` e mantenha a janela aberta enquanto joga.
4. Abra o FiveM, pressione F8 e digite `connect 127.0.0.1:30120`.
5. Depois de conectar, pressione F8 novamente para fechar o console.

O ponto de entrada depende do ambiente: ilha autoral na porta 30120 e cidade original na porta 30121. IDs, nomes e permissões de entrada ficam no banco SQLite do painel. Amigos na mesma rede Radmin VPN usam o endereço da instalação e aguardam sua aprovação.

## Comandos no F8 (sem barra)

| Comando | Acao |
| --- | --- |
| `reviver` | Revive no local e recupera a vida; tambem funciona vivo. |
| `voar` | Liga/desliga voo sem colisao, a pe. |
| `noclip` | Mesmo comportamento de `voar`. |
| `ajuda` | Mostra os comandos. |
| `veiculo adder` | Cria um carro e coloca voce no banco do motorista. |
| `veiculo luxor` | Cria um aviao. Use em aeroporto ou area bem aberta. |
| `veiculo buzzard` | Cria um helicoptero. |
| `veiculo bati` | Cria uma moto. |
| `veiculo dinghy` | Cria um barco. Use perto da agua. |
| `dv` | Remove apenas o ultimo veiculo criado pelo seu comando. |
| `drone` | Cria seu drone Blender na frente do personagem. |
| `dronevoar` | Inicia/encerra a pilotagem do drone. |
| `dronedesligar` | Encerra pilotagem e desliga os motores. |
| `droneremover` | Remove drone, helices, camera e som. |

`car` e `carro` sao apelidos de `veiculo`. Aceita nomes de modelos de veiculos presentes na versao do GTA em uso.
Cada novo veiculo substitui o anterior criado pelo comando. Modelos invalidos nao apagam o anterior.

### Personagem, armas e ambiente (F8 sem barra)

`ajoelhar` e `ajoelhar2` usam duas poses do Custom Tactical Poses de crunchycat.
Equipe `arma carabina 250` ou `arma fuzil 250`, execute a postura, feche F8,
segure botao direito para mirar e esquerdo para disparar. Mouse orienta a camera e o rumo do corpo.
R recarrega em 2,2 segundos, sem animacao propria de recarga; consome apenas a reserva existente.
`levantar`, Backspace ou repetir o mesmo comando encerram. Comeca em terceira pessoa e fica parado.
Trocar de arma, morrer, pilotar drone ou ativar voo encerra a postura.
O script bloqueia as tarefas normais de mira/disparo que levantavam o personagem e gera projeteis
nativos a partir do cano, para o ponto apontado pela camera, respeitando cadencia e municao.
`prone` continua experimental: o pacote NAO possui pose de tiro deitado; combina move_crawl
com a parte superior da pose aim_weapon. Alinhamento dos bracos, elevacao visual da arma,
colisao dos tiros, efeitos de disparo e primeira pessoa precisam de teste dentro do jogo.
Nao e um conjunto completo de animacoes dinamicas de combate nem uma implementacao multiplayer validada.

- `nightvision`: ativa visao noturna e entra em primeira pessoa. Repita para desligar.
  Ao sair da primeira pessoa, morrer ou trocar de contexto (personagem/veiculo/drone), desliga automaticamente.
  Funciona a pe, em veiculos e na camera do drone. V muda a visao e desliga o efeito.
  Bússola superior acompanha o rumo real da camera; ELEV mostra a elevacao do olhar, INCL a inclinacao lateral.
  A inclinacao lateral normalmente fica perto de zero com o personagem em pe: a leitura nao e inventada.

- `deitar`: animacao deitado de costas; `levantar`: encerra. Nao implementa rastejar.
- `arma pistola 120`, `arma carabina 250`, `arma fuzil 250`, `arma smg 250`, `arma escopeta 60`, `arma sniper 30`, `arma faca`.
- Aceita nomes GTA: `arma WEAPON_CARBINERIFLE 250`. `desarmar` remove suas armas.
- `dia` (12h), `tarde` (17h), `noite` (23h), `hora 18 30`: fixa horario. `tempolivre` retoma o ciclo natural.
- `clima sol`, `clima nublado`, `clima chuva`, `clima tempestade`, `clima neblina`, `clima neve`, `clima automatico`.
- `tempo` e um apelido de `clima`. Alteracoes locais para esta cidade de um jogador.

### Drone e audio

Usa a versao `fpv_drone_runtime` do seu projeto Blender, com quatro rotores e colisao.
Primeiro execute `drone`, depois `dronevoar`. WASD inclina/move, Espaco sobe, Ctrl desce,
Q/E gira e Backspace desliga. Nao ha corte de sinal por distancia do personagem.
O mundo e carregado em torno do drone enquanto pilota. Ao desligar no ar ele cai pela gravidade.
Mouse aponta a direcao (inclusive para cima/baixo); W avanca nessa direcao e S recua.
V alterna Perto, Media, Longe e Primeira pessoa. Velocidade de cruzeiro: 16 m/s (57,6 km/h);
Shift: 28 m/s (100,8 km/h); subida/descida: 7 m/s. Aceleracao, frenagem, giro, camera e inclinacao sao suavizados.
Inclinacao maxima de referencia: 32 graus. Ajustes ficam em `fpv_drone_runtime/config.lua`.
O personagem fica parado enquanto voce pilota. Nao combine pilotagem com noclip ou veiculos.

Seu WAV original esta preservado em `fpv_drone_runtime/html/flight.wav`. A reproducao usa `flight-loop.wav`,
um trecho com volume reforcado/comprimido e transicao de loop. Durante a pilotagem toca baixo em hover
(base 0,22), aumentando ate 0,75 em movimento, multiplicado pelo volume geral (padrao 80%).
Nao depende da altura do objeto nem da distancia da camera enquanto pilota. Fora da pilotagem,
usa distancia ate 60 metros e altura de 0,22 m. Removido ou desligado fica silencioso.
`dronesom 100` ajusta o volume (0 a 100); `testarsomdrone` reproduz um teste por quatro segundos.
O som e local, sem sincronizacao com outros jogadores.

O modelo veio do projeto original. A pilotagem agora usa deslocamento e giro assistidos em `flight.lua`,
independentes das forcas fisicas dos quatro motores. Ao soltar teclas, freia suavemente e mantem a posicao. Uma varredura por capsula
bloqueia deslocamentos contra obstaculos detectados; nao equivale a uma simulacao completa de colisoes.
O audio mede a mudanca real de posicao entre amostras, inclusive no modo assistido.
Os comandos experimentais de RPM/impacto do recurso original permanecem fora do modo assistido.
Os testes de Lua simulam as funcoes do GTA; a resposta, a colisao e o audio precisam ser confirmados no jogo.

Durante o noclip do personagem (comando `voar`): mouse orienta, WASD movimenta, E sobe, Q desce, Shift acelera e Ctrl desacelera.
Desligue perto do solo: a gravidade volta imediatamente. Saia de veiculos antes de ativar.
Nao ha respawn automatico depois da morte: use `reviver`.
Para desligar o servidor, digite `quit` na janela do servidor.

## Estrutura e limites

- `.runtime`: executaveis oficiais FXServer (versao em version.json).
- `server-data/resources/[cfx-default]`: spawnmanager oficial.
- `server-data/resources/cidade_core`: codigo proprio de personagem e comandos.
- `server-data/server.cfg`: configuracao local de uma vaga, restrita a 127.0.0.1.
- `server-data/secrets.cfg`: chave privada, ignorada pelo Git. Esta pasta esta no OneDrive e pode ser sincronizada por ele.

Os comandos sao livres para o unico jogador deste ambiente local. Antes de publicar ou permitir outros jogadores, implementar permissoes no servidor.
O GTA instalado na Steam nao foi modificado. Nao e necessario abrir portas do roteador para este teste local.

Referencias: https://docs.fivem.net/docs/server-manual/setting-up-a-server-vanilla/
e https://github.com/citizenfx/cfx-server-data (origem registrada em THIRD_PARTY.md).

## Teste no jogo

Depois de configurar a chave: verificar entrada e personagem; ativar voo e testar todas as direcoes;
desligar perto do solo e conferir caminhada/colisao; testar `reviver` vivo e depois de morrer;
reconectar e confirmar novo spawn. Esses testes exigem servidor autenticado e o cliente GTA/FiveM.

### Pose Blender em teste
Apos recarregar cidade_core, `arma carabina 250` e `ajoelharteste` usam o novo YCD com pose e recuo. Backspace ou levantar encerram. A recarga ainda nao tem animacao propria. O arquivo passou verificacao binaria; reproducao e encaixe da arma no FiveM ainda precisam de validacao visual. Fonte e limitacoes: animacoes/LEIA-ME.md.

Tiro deitado do Blender: pressione **Z** uma vez para ativar `deitadotiro` e permanecer nessa postura. Pressione **C** para levantar diretamente. Esse toque em C nao inicia ajoelhamento; depois de soltar a tecla, um novo C segurado ajoelha normalmente. Use carabina/fuzil; direito mira, esquerdo atira, R recarrega, Alt olha ao redor. A postura usa `cidade_deitado_tiro.ycd`, com mira e recuo proprios. Fora da mira preserva a camera nativa. As transicoes de deitar/levantar e a recarga ainda nao possuem animacoes especificas. O comando antigo `prone` permanece separado como experimento legado.
