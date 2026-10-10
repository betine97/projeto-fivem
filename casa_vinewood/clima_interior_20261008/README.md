# Proteção climática da mansão — 08/10/2026

Instalada em `server-data/resources/cidade_mansao`. Ativação e avaliação visual no FiveM ainda pendentes.

## Implementação

O mapa anterior continha objetos e colisões, mas não definia salas MLO. O teto existente agora é a raiz do interior `mansao_teto`, com uma sala seca conectada para os dois andares, a escada e o pé-direito duplo. A sala externa `limbo` e 40 portais mantêm a vista para o exterior. Não foi acrescentada uma segunda malha de teto.

As 14.928 faces de colisão da estrutura foram transferidas, na mesma posição, dos quatro drawables para o dicionário físico da raiz MLO e identificadas com a sala interna. A colisão estática da câmera e as colisões dos móveis/portas permanecem como antes. Vértices, UVs, normais, índices e bytes das texturas dos quatro drawables foram comparados e são idênticos aos anteriores.

O cliente classifica personagem e câmera separadamente usando os polígonos medidos de cada andar. Deck, recuos descobertos, espaço acima do telhado e abaixo do piso ficam fora da proteção. Câmeras de jogo, voo e câmeras programadas usam a sala apenas quando estão dentro. Ao sair, trocar de personagem, descarregar o interior ou parar o recurso, os vínculos de sala são liberados. O interior é mantido carregado somente nas proximidades.

O modificador de sala `mansao_ar_seco` afasta o início da névoa para 50 metros, além da dimensão interna da casa. Não modifica densidade da névoa distante, céu, exposição ou parâmetros de luz. Não chama `SetRainLevel`, `SetWeatherType*` ou um modificador global de timecycle. Os comandos existentes de clima e horário continuam funcionando.

## Ativar e verificar no jogo

1. No console **do servidor**, execute `restart cidade_mansao`.
2. Desconecte e reconecte o FiveM para recarregar os arquivos de mapa e o MLO.
3. Dentro da casa, execute `mansaoclima` no F8. Deve indicar um MLO diferente de zero, `pronto=true` e personagem/câmera dentro. Se o interior ainda não carregou, o recurso imprime um aviso com limite de frequência.
4. Com os comandos já existentes `clima chuva` e `clima neblina`, percorra térreo, andar superior, escada e sala de pé-direito duplo. Verifique chuva externa pelas janelas e ausência de precipitação dentro.
5. Saia para o deck: o clima externo deve continuar ativo. Mova a câmera para fora com o personagem dentro e repita no sentido inverso.
6. Confira a circulação e o editor `editarobjetos`, especialmente os móveis já reposicionados. As posições e o catálogo não foram alterados por esta revisão.

Não foi encerrado nem reiniciado o processo FXServer nesta instalação. Testes locais não substituem a confirmação de chuva, névoa e visibilidade no renderizador GTA/FiveM.

## Evidências e recuperação

- `backup/`: recurso completo anterior a esta alteração.
- `package/`: arquivos nativos, configuração e código instalado.
- `native_verification.json`: leitura e escrita nativas; colisões e dados gráficos preservados.
- `weather_tests.json`: 31 verificações em Lua e 3.000 pontos comparados aos polígonos medidos.
- `installation_verification.json`: hashes instalados e 80 arquivos existentes preservados, incluindo iluminação, editor, catálogo, câmera, móveis e portas.

Para recuperar, restaure os arquivos listados em `installation_verification.json` que existiam em `backup/` e retire os novos arquivos `clima_*` e `stream/mansao_teto.ybn`. Recarregue o recurso no servidor e reconecte. Não sobrescreva arquivos de posições salvas depois desta revisão.

Referências primárias: [ForceRoomForEntity](https://github.com/citizenfx/natives/blob/master/INTERIOR/ForceRoomForEntity.md), [ForceRoomForGameViewport](https://github.com/citizenfx/natives/blob/master/INTERIOR/ForceRoomForGameViewport.md), [ClearRoomForGameViewport](https://github.com/citizenfx/natives/blob/master/INTERIOR/ClearRoomForGameViewport.md), [GetInteriorAtCoordsWithType](https://github.com/citizenfx/natives/blob/master/INTERIOR/GetInteriorAtCoordsWithType.md).
