# Entrada principal e garagem subterrânea

Alteração local da frente da mansão, conforme as três referências de 08/10/2026. A modelagem e as prévias foram feitas no Blender; a instalação utiliza assets GTA V/FiveM nativos, entidades de mapa comuns e colisões físicas.

## Implantação

- Porta principal no ponto marcado, em madeira com faixa vertical de vidro, moldura em pedra e duas arandelas. A folha abre com **E**, usando o sistema existente de portas sincronizadas.
- O acesso entra pela antiga Despensa, usada como vestíbulo, e segue pela passagem já existente até o hall. Não foi aberta uma passagem através do lavabo ou escritório.
- O volume de tijolos preenche o recuo assinalado e alcança a face frontal do muro existente. Usa a textura original `os_ml_idwall_0005_c` e seu mapa normal, com UVs contínuas na face frontal.
- Garagem sob o lado esquerdo da fachada, com duas vagas, área interna de 6,40 × 11,08 m e altura livre de 2,92 m. Piso 3,40 m abaixo do térreo.
- Rampa externa de 9,67 m, largura útil de 6,40 m, transições suaves e inclinação máxima aproximada de 16,15%. O encontro com a rua acompanha sua inclinação transversal.
- Escada exterior de 13 degraus conecta a rua ao terraço da nova entrada. O pequeno trecho da borda do jardim que bloqueava a chegada foi recortado.
- Portão basculante com abertura para dentro, abaixo da laje. **E** abre/fecha quando próximo, inclusive dentro de veículo. O servidor compartilha o estado e recusa o fechamento se houver pessoas ou veículos na área de movimento.
- Acesso a pé à garagem pela rampa exterior. A escada interna existente permanece inteira.

## Arquivos editáveis e prévias

- `fachada_garagem_editavel.blend`: modelos novos, separação de materiais e malhas de colisão antes da exportação.
- `mansao_entrada_garagem.blend`: composição independente para inspecionar a implantação junto à casa e ao terreno existentes.
- `fachada_garagem_blender.png` e `garagem_interna_blender.png`: prévias renderizadas no Blender. Não são capturas do jogo.
- `spec.json`: medidas, origens, aberturas, volumes de escavação e colisões.
- `verification.json`: verificações geométricas, leitura nativa, quatro níveis de detalhe e testes Lua.
- `installation.json`: hashes instalados, localização do backup e confirmação dos arquivos preservados.

## Atualização no servidor

Após a instalação, execute **`ensure cidade_mansao` no console do servidor** e reconecte o FiveM para recarregar os assets alterados. Não é um comando para o F8 do jogador. A instalação não reinicia o servidor.

O teste final dentro do FiveM ainda precisa confirmar o percurso a pé, a entrada com veículos e a aparência usando a iluminação real do jogo. As prévias e testes físicos locais não substituem esse teste.

## Preservação e desempenho

Os recortes nativos ficam restritos à porta, ao volume subterrâneo, à rampa e à escada exterior. As faces de renderização fora dos recortes foram comparadas com os originais. Os arquivos próprios de escadas e pisos interiores, as portas existentes, o catálogo de objetos, suas posições salvas e a iluminação geral não são substituídos.

Os quatro modelos novos possuem quatro LODs, texturas comprimidas com mipmaps, geometria agrupada por material e colisões simplificadas. O conjunto novo consome aproximadamente 3,01 MiB de memória gráfica de assets, segundo os cabeçalhos nativos; este valor não representa toda a memória utilizada pelo jogo.

As luzes novas são locais à entrada e à garagem, constantes, sem volume de névoa. Não foram adicionadas proteções climáticas ou definições MLO.

## Scripts

`patch_site.py` recorta cópias dos assets originais; `build_models.py` cria os modelos no Blender; `package_models.py` monta LODs, luzes e colisões; `verify.py` valida o pacote; `install.py --check` verifica conflitos sem instalar. A instalação guarda backup e exige que os arquivos nativos de origem não tenham sido alterados por outro trabalho.

Não execute `prepare.py` novamente sobre esta entrega: ele recria o registro inicial usado para verificar conflitos.
