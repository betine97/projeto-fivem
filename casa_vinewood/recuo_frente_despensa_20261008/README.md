# Recuo do acesso e abertura do hall — 08/10/2026

Revisão específica dos dois prints enviados nesta conversa. A escada e o concreto do acesso à garagem acompanham a borda inclinada da calçada. O patamar da escada recuou aproximadamente 2,16 m no centro; a ponta da rampa recuou entre aproximadamente 0,73 e 1,88 m, conforme a posição na largura. Os treze degraus mantêm 30 cm de profundidade. A rampa termina nivelada na aproximação da rua, com as muretas reduzidas à altura do piso na extremidade. Sua inclinação longitudinal máxima é aproximadamente 16,6% junto à borda esquerda.

O terreno e suas colisões originais foram recompostos fora do novo recorte, incluindo as variantes base, APA e HEI. Foram removidos os arbustos, o agave, o caniço, as ervas e duas arandelas que ficaram sobre o vão escavado. O coqueiro foi reposicionado na faixa de solo preservada ao lado do acesso; sua representação distante acompanha a nova posição.

A divisória frontal da antiga despensa, seu batente e suas colisões foram retirados. A folha da porta também foi removida da configuração. Os IDs das demais portas permanecem os mesmos e os controladores agora usam o ID explícito de cada porta, permitindo a lacuna do ID 3. Piso, teto e paredes perpendiculares permanecem. A porta de entrada principal continua no fundo do novo acesso ao hall.

As posições das fontes de luz dos degraus e balizadores acompanham as peças recuadas. Intensidade, cores e demais parâmetros da iluminação atual são preservados.

Fontes e prévias:

- `fachada_garagem_editavel.blend`: peças separadas do acesso, escala em metros.
- `mansao_recuo_despensa.blend`: composição com terreno, escada, garagem e hall atualizado.
- `build_models.py`, `package_models.py`, `patch_assets.py`: geração e recorte desta revisão.
- `verification.json`: testes de continuidade da rampa e escada, passagem de veículos, abertura do hall, piso/teto e funcionamento compartilhado das oito portas restantes.
- `codewalker_validation.json`: leitura independente dos arquivos nativos.
- `installation.json` e `backup_preinstall/`: registro e cópias anteriores à instalação.

Para carregar no jogo, execute `restart cidade_mansao` **no console do servidor**. Feche completamente o FiveM e conecte novamente para renovar os arquivos de mapa. As prévias são renders do Blender; a confirmação visual e a condução de um carro no FiveM precisam ser feitas depois de recarregar.

Esta revisão instala somente os arquivos listados em `verification.json`, com comparação dos hashes atuais antes de cada troca. Não substitua a pasta inteira por uma versão anterior da fachada: isso faria retornar a divisória, os objetos flutuantes ou o acesso avançado.
