# Tablet de roupas aprovadas

No F8 do FiveM, digite roupas. O tablet mostra somente peças com a tag OK, independente das favoritas. Isso vale também para calçados, chapéus e acessórios. Sem tags ou com tags de defeito, a peça fica fora do painel; o catálogo e as favoritas continuam preservados.

A prévia começa de roupa íntima e descalça, sem acessórios, cabelo, barba ou tatuagens. Masculino/Feminino carrega o modelo correspondente. Combine categorias diferentes; cada slot nativo aceita uma peça. Selecionar outra calça preserva camisa, chapéu e acessórios. Clique novamente para retirar somente aquela escolha.

O filtro Revisão no acervo possui Todas as tags, Sem tags, OK, PEÇA INCORRETA e DEFEITO NA TEXTURA. Tags podem ser editadas no jogo ou nos detalhes da peça no navegador. OK é exclusivo; as duas tags de problema podem ser combinadas. A página sincroniza a cada três segundos e ao receber foco, preservando edições ainda não salvas. O tablet aberto recebe alterações em até dois segundos. Se uma peça perder OK, somente seu slot é restaurado na prévia e ela sai da lista. Fechar o tablet interrompe sua assinatura.

O serviço catalogo_roupas_web/server.py grava atomicamente o arquivo tags.json deste recurso e precisa estar iniciado para salvar no jogo. Cada gravação atualiza apenas a peça escolhida. As favoritas continuam independentes em favorites.json.

Cabelo e barba usam círculos com o RGB da paleta nativa. Tatuagens permitem múltiplas seleções e filtro por região. Essas opções de aparência permanecem disponíveis independentemente das tags de roupas.

Enquadramento fica no canto superior direito. Para girar, pressione a bolinha e arraste de 0 a 360 graus. Clicar no trilho não muda o ângulo. Setas, Home, End e Page Up/Down também funcionam. A câmera permanece fixa e os textos sobre o personagem foram removidos.

Restaurar prévia limpa as escolhas, volta à roupa íntima, corpo inteiro e giro zero. Aplicar visual confirma no jogador; ESC fecha sem aplicar e preserva o jogador original. As peças são validadas pelo modelo/build, coleção, índice e textura. Compatibilidade de braços e sobreposição ainda deve ser conferida no jogo.

Para carregar esta atualização: recarregue http://127.0.0.1:8766/ e execute restart cidade_acervo no console do servidor. Depois abra roupas no F8. O recurso já consta em server-data/server.cfg. A página http://127.0.0.1:8766/tablet/index.html mostra somente a interface; o personagem 3D existe no FiveM.

Testes: tests/wardrobe.py, tests/wardrobe_server.py e tests/wardrobe_bridge.py (Python); tests/wardrobe-ui.test.cjs e tests/acervo-tags.test.cjs (Node). Usam dados isolados para validar Lua, API, sincronização, preservação dos demais slots, aparência, restauração, giro e rascunhos de tags.

O serviço escuta apenas em 127.0.0.1. Este recurso segue o servidor individual do projeto e não altera inventário nem persistência após reconexão.
