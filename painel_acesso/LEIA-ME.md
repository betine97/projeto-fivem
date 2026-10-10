# Painel de acesso — Minha Cidade

Abra `iniciar-painel.cmd` na raiz do projeto. O painel abre autenticado em http://127.0.0.1:8787 e permanece funcionando em segundo plano. `iniciar-cidade.cmd` também inicia o painel automaticamente antes da base. Não há dependências novas para instalar.

## Primeira utilização

1. Reinicie a base atual usando `iniciar-cidade.cmd` para carregar a nova configuração. Os arquivos já estão instalados; a instância antiga ainda mantém a configuração anterior.
2. Execute `liberar-amigos.cmd` **como administrador**, uma vez, para liberar TCP/UDP 30120 para o FXServer no Firewall do Windows. O painel fica restrito ao próprio computador.
3. Conecte normalmente com `connect 127.0.0.1:30120`. Na primeira tentativa você também receberá um ID e aguardará autorização. Abra o painel, autorize seu próprio nome e conecte novamente.
4. Amigos na mesma rede Radmin VPN usam `connect 26.30.45.250:30120`. Na rede doméstica, `connect 192.168.1.2:30120`. Fora dessas redes, é necessário encaminhar TCP/UDP 30120 no roteador para 192.168.1.2 e usar seu IP público; isso depende do roteador/provedor e não foi alterado.
5. Cada amigo tenta entrar, recebe um ID, aparece como pendente no painel, e você clica **Autorizar**. Ele pode conectar novamente. **Bloquear** impede novas entradas e desconecta um jogador online na próxima atualização, em até aproximadamente cinco segundos.

## Dados e personagem

O painel mostra ID, nome e situação do acesso. O ID é permanente, vinculado à identificação de conta fornecida pelo servidor FiveM, não ao apelido ou IP. O nome pode ser editado; ao reconectar, o nome escolhido no painel é preservado. A licença interna não aparece no painel nem na API administrativa.

O banco real fica em `data/usuarios.sqlite3`. Faça cópia da pasta `data` com o painel encerrado para guardar usuários, permissões e credenciais. Nunca apague essa pasta para atualizar o código. O banco começa vazio e não contém jogadores fictícios.

O personagem inicial continua `a_m_y_business_01`, o mesmo já configurado em `cidade_core`. Não foi criado seletor de personagem. No FiveM, `id` no F8 ou `/id` no chat mostra seu ID e nome cadastrados.

## Acesso ao painel

O atalho abre uma sessão autenticada com um link de uso único que expira em um minuto. Se a sessão acabar, abra o atalho novamente. Existe também login por senha, guardada em `data/config.json` no campo `admin_password`. Essa senha é somente do painel, não é a chave Cfx.re. O painel não escuta na VPN nem na internet.

O recurso FiveM consulta o painel por uma chave privada em `server-data/acesso.cfg`; esse arquivo é lido pelo servidor, não replicado aos clientes. Se o painel estiver indisponível, novas entradas são recusadas, sem liberar acesso por falha. Jogadores já admitidos permanecem conectados durante falhas transitórias. Reabrir o painel recupera o controle.

## Verificação

- Oito testes Python: ID estável, persistência, aprovação, revogação, isolamento de contas, validação de entradas, privacidade, autenticação, proteção CSRF/Host e link de uso único.
- Testes da integração Lua: pendente, autorizado, bloqueado, API indisponível, resposta tardia, ID replicado, expulsão após bloqueio e sessão existente preservada durante indisponibilidade.
- Sintaxe dos três arquivos Lua e JavaScript conferida; painel real aberto e inspecionado no navegador.

Para repetir: `C:\Python313\python.exe painel_acesso/tests/test_access.py` e `C:\Python313\python.exe painel_acesso/tests/test_fivem_bridge.py` a partir da raiz. A conexão real de outra máquina precisa ser conferida após reiniciar a base e liberar o Firewall.

Referências da integração: [playerConnecting](https://docs.fivem.net/docs/scripting-reference/events/list/playerConnecting/), [GetPlayerIdentifiers](https://docs.fivem.net/docs/scripting-reference/runtimes/lua/functions/GetPlayerIdentifiers/) e [PerformHttpRequest](https://docs.fivem.net/docs/scripting-reference/runtimes/lua/functions/PerformHttpRequest/).

## Correção da rejeição "Unknown error"

Corrigida a finalização da autorização: jogadores aprovados usam `deferrals.done()` sem argumentos. Passar `nil` explicitamente é um argumento e provoca rejeição no FiveM, conforme o [código oficial de ClientDeferral](https://github.com/citizenfx/fivem/blob/master/code/components/citizen-server-impl/src/ClientDeferral.cpp). O teste Lua distingue os dois casos e reproduz a falha antes da correção.

Com a base já aberta, digite `restart cidade_acesso` no console do FXServer (a janela do servidor, não o F8 do jogo). Depois, no F8 do FiveM deste PC, use `connect 127.0.0.1:30120`. Amigos na mesma rede Radmin usam `connect 26.30.45.250:30120`.

O atalho `liberar-amigos.cmd` agora solicita elevação pelo Windows, aguarda o resultado, grava `liberar-amigos.log` e mantém a janela aberta com `pause`. O arquivo CMD usa finais de linha CRLF próprios do Windows.

## Administradores entre os convidados

Por solicitação do dono, todos os jogadores aprovados recebem `group.admin` durante a sessão, incluindo o próprio dono. Os comandos atuais, como `voar`, `noclip`, `reviver`, `carro`, `mansao`, `arma`, `hora`, `clima` e `drone`, continuam disponíveis para todos que entram. O recurso também concede as permissões ACE administrativas do servidor e replica `cidadeAdmin` para indicar o perfil.

Para carregar na base já aberta, no console do FXServer execute `exec permissoes-amigos.cfg` e depois `restart cidade_acesso`. Novas entradas recebem ADM ao entrar; jogadores já online são conferidos em até cinco segundos. Bloquear no painel remove ADM antes de desconectar. Sair ou parar o recurso remove a associação da sessão, impedindo que outro jogador herde o perfil pelo mesmo ID temporário.

As permissões seguem os [comandos oficiais ACE](https://docs.fivem.net/docs/server-manual/server-commands/). A configuração é carregada automaticamente no próximo início da base.

## Comandos de ADM para localização

`encontrar ID` teletransporta o ADM até o jogador online com aquele ID permanente. `chamar ID` traz o jogador até o ADM. Os comandos validam a permissão ACE, a identidade FiveM atual e o estado online antes de mover qualquer personagem; há uma pequena proteção contra repetição acidental. O teletransporte carrega a colisão do destino, encerra voo/drone e não permite que o cliente escolha coordenadas.

O voo do personagem foi ajustado para o dobro da velocidade anterior: 24 m/s normal, 100 m/s com Shift e 6 m/s com Ctrl.
