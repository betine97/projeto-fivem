Abra `iniciar-los-santos.cmd`. Este servidor usa a porta 30121, configuração e cache separados em `servidor-los-santos`. A ilha usa 30120.

Ao trocar entre os mundos, encerre o FiveM e abra novamente para descarregar as substituições de mapa. No F8: `connect 127.0.0.1:30121` para Los Santos e `connect 127.0.0.1:30120` para as ilhas. Para amigos na mesma rede/VPN, use o mesmo endereço do computador e troque somente a porta por 30121.

Em Los Santos ou Cayo Perico, com sua autorização ADM:

1. Use `capturarobjeto` no F8. Aponte com o mouse até aparecer a marcação verde e clique.
2. Informe um nome e categoria, depois clique em **Adicionar ao catálogo da ilha**.
3. Esc fecha a seleção para caminhar ou voar. Abra o comando novamente no próximo objeto.
4. `capturas` mostra no F8 as últimas 50 marcações e seu estado de processamento.
5. No servidor das ilhas, abra `editorilha` e clique em **Meus itens capturados**. Os modelos identificados aparecem com sua imagem. As marcações em preparação ou análise estão na lista expansível acima das imagens.
6. O mesmo catálogo pode ser usado na nossa ilha e em Cayo Perico. No servidor das ilhas, `cayo` leva à ilha vizinha e `capturarobjeto` abre a seleção lá também.
7. **Posicionar** cria somente uma prévia: caminhar ou voar move o objeto junto. ↑/↓ ajustam a altura; ←/→ giram; +/- alteram a escala; F fixa ou volta a acompanhar; Enter salva; Backspace cancela. V muda a câmera. Caps Lock retoma um objeto salvo próximo. Escolher outro modelo abandona a prévia anterior.

Os arquivos RPF, modelos e dicionários de textura são identificados a partir do GTA instalado. O editor reutiliza os modelos que o jogo já carrega, preservando os materiais e texturas originais. Não é necessário copiar esses modelos para cada ilha. O cache local contém a geometria e as texturas extraídas para renderizar a imagem, além do relatório com os caminhos originais.

Quando um clique não fornece um modelo, o serviço consulta o índice das entidades do mapa e compara os triângulos da geometria original com o ponto clicado. Peças HD independentes confirmadas entram no catálogo. Terreno, peças muito grandes, interiores ou estruturas agrupadas que não puderem ser confirmadas permanecem **aguardando análise**, sem substituir o objeto por uma peça diferente.

Marcações persistentes: `captura_los_santos/data/capturas.json`. Catálogo integrado: `server-data/resources/cidade_admin/data/catalogo_capturado.json`. Relatórios e imagens: `captura_los_santos/cache/NOME_DO_MODELO`. Logs: `service.log` e `service-error.log`.

O serviço de captura escuta somente no computador, porta 8788; as chamadas do jogo passam pelo servidor e exigem a autorização ADM verificada e a chave privada da ponte de acesso.
