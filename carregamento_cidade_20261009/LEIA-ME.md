# Tela de carregamento da Minha Cidade

Recurso instalado: `server-data/resources/cidade_loading`.
As configurações dos modos ilha e cidade já iniciam esse recurso antes de `cidade_core`.

## Comportamento

- Background original enviado, copiado sem alterações.
- Playlist com os três MP3 enviados, na ordem do pedido: arquivo sem sufixo, `_2`, `_1`.
- Reprodução automática no FiveM, próxima/anterior, seleção direta da playlist, pausa, silêncio e volume.
- As preferências de volume e silêncio são salvas localmente.
- O progresso do motor permanece no máximo em 95% até o spawn confirmar personagem e colisão.
- A tela mostra **Tudo pronto** e libera **Assumir personagem** após essa confirmação.
- Não há avanço automático, nem timeout que dispense o clique. O personagem permanece congelado, protegido e sem controles até a confirmação.
- O clique é conferido novamente no Lua, inclusive se a colisão deixou de estar disponível. Música e tela desaparecem com um fade ao entrar.
- Falhas no ponto de entrada oferecem **Tentar carregar novamente**.

## Ativação e limites da verificação

A instalação foi feita nos arquivos. O servidor em execução foi preservado porque há uma sessão conectada; a mudança entra em vigor na próxima inicialização do FXServer. Depois disso, reconecte o FiveM para ver a tela durante o carregamento.

As verificações executam a interface no Chrome e o Lua real com nativos simulados. As três músicas foram decodificadas e reproduzidas no teste de navegador. O diagnóstico do cliente CEF identificou os problemas abaixo; a versão corrigida ainda precisa ser carregada em uma nova conexão para confirmar a interação final no FiveM.

Reiniciar apenas o recurso de carregamento numa sessão já aberta não exibe retroativamente a tela. O código evita prender o jogador nesse caso.

## Arquivos de integração

- `server-data/resources/cidade_core/client.lua`: comunica espera, falha e spawn pronto; preserva a tela durante a entrada.
- `server-data/resources/porto_esperanca/client.lua`: preserva a tela se o comando do porto for executado durante a espera.
- `server-data/server-ilha.cfg` e `server-data/server-cidade.cfg`: `ensure cidade_loading` antes de `cidade_core`.

Backups das quatro versões anteriores: `carregamento_cidade_20261009/backup`.
A integração do porto foi aplicada ao recurso instalado; uma futura reinstalação pelo gerador de assets deve preservar a condição de `cidade_loading` na função `release`.

## Verificação

```powershell
node carregamento_cidade_20261009/verificar_ui.cjs
& 'C:/Python313/python.exe' carregamento_cidade_20261009/verificar_fluxo.py
```

Resultados e capturas: `carregamento_cidade_20261009/verificacao`.

## Correção dos controles e da entrada — 09/10/2026

O cliente conectado mostrou `GetParentResourceName()` igual a `loadingScreen`, embora o recurso Lua se chame `cidade_loading`. Os callbacks estavam usando o nome do frame e não chegavam ao Lua. A tela também estava abaixo de seis interfaces transparentes, sem foco. Além disso, a mensagem indicava personagem pronto, mas o JavaScript exigia booleano `true` e rejeitava o valor nativo `1`.

- Os callbacks do frame inicial agora apontam para `cidade_loading`.
- Os nativos usados para liberar entrada são normalizados para booleanos no Lua. O JavaScript também aceita `true`/`1`, rejeitando `0` e strings.
- Depois que os scripts iniciam, a mesma tela continua em um `ui_page` com foco e cursor próprios. O frame inicial só é fechado depois que a interface confirma que está visível.
- A transferência preserva faixa, posição, volume, silêncio e pausa. A interface oculta começa transparente e sem reproduzir áudio; só fica visível ao receber a ativação do Lua.
- Ausência de resposta do áudio permite abrir a interface, mas não dispensa a confirmação do spawn nem avança automaticamente o personagem.
- Ao entrar ou parar o recurso, o áudio para, a interface fica transparente e o foco é devolvido ao jogo.

Foram aprovados 14 casos Lua e 13 casos de interface, incluindo `GetParentResourceName() = loadingScreen`, nativos `1`/`0`, perda de colisão, a transferência do áudio e cliques reais de navegador com outros frames sobrepostos. Esses testes não substituem a verificação no cliente FiveM após reconectar.

Para aplicar, reinicie o servidor e reconecte o FiveM. Apenas mudar os arquivos não atualiza o HTML nem o Lua que já estão na sessão atual. O servidor e a conexão do usuário não foram reiniciados durante esta correção.

Backup anterior à correção: `carregamento_cidade_20261009/backup_interacao`.
Diagnóstico somente de leitura do CEF: `diagnosticar_cef.cjs` e `verificacao/cef-diagnostico.json`.
O [código oficial do root NUI](https://github.com/citizenfx/fivem/blob/master/ext/ui-build/data/root.html) confirma o nome especial do frame; o [código de foco NUI](https://github.com/citizenfx/fivem/blob/master/code/components/nui-resources/src/ResourceUIScripting.cpp) aplica `SetNuiFocus` aos frames normais dos recursos.

Integração baseada na documentação oficial [Loading Screens](https://docs.fivem.net/docs/scripting-manual/nui-development/loading-screens/) e [NUI Callbacks](https://docs.fivem.net/docs/scripting-manual/nui-development/nui-callbacks/).
