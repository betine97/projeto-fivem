# Editor ADM de objetos e iluminação — 08/10/2026

Instalado no recurso `server-data/resources/cidade_mansao`. Para carregar os mapas e scripts novos, execute `restart cidade_mansao` **no console do servidor**, e reconecte o FiveM. Os testes locais passam; o resultado visual e as colisões em movimento ainda precisam ser observados no cliente GTA/FiveM.

## Usar no jogo

1. Abra F8, digite `editarobjetos` e feche F8.
2. Aproxime-se de uma peça e olhe para ela. O alvo recebe um contorno verde.
3. Pressione **CAPS LOCK** para selecionar. Ao andar, a peça acompanha seu deslocamento, preservando a distância inicial e sem saltar para seu personagem.
4. **Setas esquerda/direita** giram a peça; **Page Up/Down** ajustam a altura. **Home** retorna à posição original do mapa.
5. **CAPS** confirma e salva; **Backspace** cancela e restaura a posição anterior. `editarobjetos` novamente desliga o modo, cancelando um movimento pendente.

`moverobjetos` é um alias. `objetosajuda` imprime os controles no F8. `objetosdebug` imprime o alvo, seleção, modelo e transformação atuais, além do número de peças carregadas.

## Peças e limites

36 peças/conjuntos da mansão são carregados como objetos controlados pelo recurso: vasos (incluindo o pequeno vaso da cozinha), oito quadros, sofá/chaise/mesa de centro, jantar, ilha/banquetas, TV, tapetes e piano. A escala, as malhas, texturas e LODs originais foram preservados. Uma malha exportada como conjunto se move inteira: por exemplo, a mesa de jantar e suas cadeiras não são peças separadas neste modelo.

Objetos estáticos comuns do mapa também podem ser selecionados por proximidade e direção da câmera. Para persistir suas mudanças, o original é ocultado localmente e uma cópia do mesmo modelo aparece na posição compartilhada. Há um limite de 512 registros. Objetos de outros scripts e objetos de rede, portas animadas da mansão e estruturas fixas (paredes, lajes, vidros, escadas, armários embutidos e luminárias) não são substituídos pelo editor. Objetos grandes de cenário não são elegíveis para o modo genérico.

A permissão `cidade.admin` é verificada no servidor ao ativar, selecionar, mover e salvar. Dois administradores não podem editar a mesma peça ao mesmo tempo. Desconexão, morte, perda da permissão, teleporte durante o arraste e inatividade restauram a posição anterior. O editor funciona na instância principal, bucket 0.

As posições confirmadas são gravadas em `server-data/resources/cidade_mansao/objetos_posicoes.json`, com a revisão anterior em `objetos_posicoes.backup.json`. Entrantes recebem o layout salvo e os movimentos ativos. Falha de gravação cancela a mudança e mostra uma mensagem. Se ambos os arquivos forem inválidos, a edição é bloqueada para não sobrescrevê-los.

## Colisões e instalação

Seis YMAPs tiveram apenas as entradas de peças móveis retiradas; as estruturas ficaram nas mesmas posições. As 356 faces duplicadas de colisão de câmera dos quatro conjuntos originais foram retiradas do YBN fixo: as colisões embutidas passam a acompanhar os objetos. Durante o arraste, a colisão da peça é temporariamente desativada; confirmar/cancelar a restaura.

`backup/` preserva a versão anterior, incluindo os mapas de piano/tapetes adicionados durante o trabalho. `package/` contém o pacote desta revisão. `catalog_verification.json`, `installation.json`, `tests.json` e `lighting_tests.json` registram as verificações. `build_catalog.py` reconstrói a partir do backup; não deve ser usado para incorporar futuras mudanças sem atualizar as fontes.

## Iluminação

O controlador recebeu oito fontes difusas para sala, jantar, paredes altas e cozinha. Essas fontes permanecem selecionadas ao atravessar a área integrada, evitando que somente o canto mais próximo da câmera receba luz. O orçamento prioriza 14 fontes difusas, 2 luminárias, 2 pendentes e 2 luzes de escada; quatro posições ficam reservadas às transições, mantendo o máximo de **24 luzes** por quadro e nenhum desenho quando o jogador está longe da mansão.

O multiplicador noturno passou de 2,2 para 3,8; as fontes difusas também ganharam alcance e intensidade. `luzmansao 1` usa o novo padrão; valores de 0,5 a 3 ajustam localmente o brilho. Não são fachos pontuais direcionados ao chão. A avaliação de brilho final depende de teste no jogo, com o horário e pós-processamento do cliente.

## Referências das APIs

- [Teclas e CAPS LOCK — Cfx.re](https://docs.fivem.net/docs/game-references/input-mapper-parameter-ids/keyboard/).
- [SetEntityMatrix — Cfx.re](https://github.com/citizenfx/fivem/blob/master/ext/native-decls/sdk/SetEntityMatrix.md), usado para preservar escala e orientação.
- [CreateModelHideExcludingScriptObjects — Cfx.re](https://github.com/citizenfx/natives/blob/master/ENTITY/CreateModelHideExcludingScriptObjects.md), usado somente para objetos genéricos do mapa.
