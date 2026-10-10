# Proteção climática removida — 08/10/2026

A proteção contra chuva e névoa foi retirada a pedido do usuário, após crashes ao aproximar-se da mansão ou usar `mansao` no F8.

O YMAP e o YTYP principais voltaram à versão anterior à conversão MLO. As quatro estruturas receberam novamente suas colisões embutidas originais. Os drawables atuais mantêm suas malhas, materiais, texturas e luzes; a restauração das colisões usa diretamente os objetos nativos para preservar os hashes dos shaders.

O recurso deixou de carregar salas/portais MLO, o dicionário físico local do MLO, o controlador de clima e seu modificador de névoa. Os cinco arquivos exclusivos da proteção foram removidos da instalação e guardados em `backup_before_removal/`. Os móveis, bar, adega, portas, editor ADM e posições salvas não foram alterados.

As 68 luzes nativas do teto e seus horários/flags/parâmetros foram comparados com a versão instalada antes desta revisão. As 14.928 faces de colisão recuperadas mantêm posições (comparadas a 0,1 mm), orientação, materiais, transformação e flags da versão anterior à proteção climática. A posição das entidades do mapa permanece igual. A sintaxe do manifesto foi validada.

Para aplicar: no console do servidor, usar `ensure cidade_mansao` caso esteja parado, ou `restart cidade_mansao` caso esteja ativo. Fechar completamente o FiveM, abrir e conectar novamente, então testar `mansao` no F8 e aproximar-se caminhando. O servidor não foi reiniciado automaticamente; estabilidade e iluminação no jogo ainda dependem desse teste.

`verification.json` documenta a validação local; `installation_verification.json` registra os hashes instalados e a preservação dos demais arquivos. Os scripts são destinados a esta revisão e recusam sobrescrever alterações posteriores.

A funcionalidade de proteção climática fica adiada. Não executar instaladores de revisões antigas de clima/iluminação/editor sobre esta versão sem reconciliar os arquivos atuais.
