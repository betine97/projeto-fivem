# Crash high-sad-wolfram — 08/10/2026

## Evidências locais

Três relatórios de crash consecutivos registram a mesma falha `GTA5_b3258.exe+93419F`, exceção `0xc0000005`, operação de escrita no endereço `0x48`.

Dumps preservados em `%LOCALAPPDATA%/FiveM/FiveM.app/crashes`:

- `4f1afc18-abaa-4821-b293-bae77286b967.dmp`
- `f5e615d2-1780-4d3d-84ae-adb540900754.dmp`
- `b0eb84ab-d00d-4b3f-b309-118060082aa7.dmp`

A instrução da falha é `mov qword ptr [rax + 0x48], rdi`, com `rax=0`. Ela ocorre na construção de uma entidade de mapa, antes de o wrapper `ConstructEntity` do FiveM retornar. O deslocamento `0x48` corresponde ao campo `instance` de `CInteriorProxy` para builds a partir de 2060. Isso é compatível com um proxy de interior ausente. A identidade do modelo não está disponível nas páginas de heap incluídas nesses minidumps.

Fontes primárias conferidas:

- https://github.com/citizenfx/fivem/blob/master/code/components/extra-natives-five/src/GamePrimitives_MapData.cpp
- https://github.com/citizenfx/fivem/blob/master/code/components/extra-natives-five/src/InteriorExtraNatives.cpp

O bloco de pilha que contém coordenadas próximas do jogador não foi confirmado como `CEntityDef`. Seus primeiros bytes não devem ser usados como identificação de um modelo.

Não foram encontradas mensagens de memória esgotada ou erros Lua imediatamente antes dos três crashes. Isso não demonstra que a carga de memória está adequada; apenas não confirma memória como causa destes crashes.

## Estado do pacote

`cidade_mansao.ymap` contém cinco entidades BASE e uma `CMloInstanceDef` para `mansao_teto`, com contentFlags=73. `cidade_mansao.ytyp` define esse mesmo nome como MLO. Uma leitura independente com CodeWalker confirmou o tipo CMloInstanceDef e seus campos. Portanto, a validação de ida/volta do serializador não é suficiente para confirmar inicialização válida no GTA.

A alteração recente de BASE para MLO feita para proteção climática continua suspeita. A última alteração de iluminação adicionou luzes ao drawable; os dumps não confirmam essas luzes como causa.

## Teste de isolamento pendente

1. No console do servidor, executar `stop cidade_mansao`.
2. Fechar completamente o FiveM, abrir e conectar novamente.
3. Repetir a conexão e o percurso que provocavam o crash.
4. Se o crash parar, o recurso foi isolado; então comparar a estrutura MLO com a versão anterior, mantendo backup e restaurando somente os arquivos necessários.
5. Se persistir, investigar os outros recursos de mapa e o próximo dump, sem assumir que a mansão é responsável.
6. Para reativar o recurso, executar `ensure cidade_mansao` no console do servidor e reiniciar o cliente antes de reconectar.

Nenhum arquivo instalado do servidor, asset da mansão, configuração de memória ou cache foi alterado durante este diagnóstico. Somente scripts e relatórios locais foram criados. O teste de isolamento e a reprodução no jogo ainda não foram executados.
