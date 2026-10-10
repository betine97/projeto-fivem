# Escada, portas e junções — 08/10/2026

A colisão vertical do terreno nativo cruzava a chegada da escada em três variantes de mapa (base, APA e HEI). Sete primitivas por variante foram recortadas somente na faixa útil do acesso. As superfícies horizontais da rua foram preservadas; não há teletransporte, salto automático ou desativação da colisão do personagem.

O coqueiro marcado já havia sido excluído da entrega atual em `reparo_render_acesso_urso_20261008`. Esta revisão confirmou sua ausência no mapa de alta definição e no LOD distante.

A retirada da frente da despensa também apagou os fechamentos das pontas das paredes vizinhas. Foram recompostas as duas faces expostas das junções, mantendo as texturas, shaders, iluminação e aberturas.

As oito folhas de portas atuais abrem para o lado oposto ao jogador que pressiona E. A direção é calculada no servidor conforme a direção real de cada folha, inclusive a entrada principal cujo modelo possui orientação inversa. Estado e ângulo são compartilhados, incluindo jogadores que chegam depois. A presença de qualquer jogador na área varrida impede o movimento. A colisão da folha fica suspensa somente durante os 550 ms da animação, evitando empurrões, e volta ao término. Portão basculante da garagem mantém seu controlador próprio.

Validação: 108 casos executados dos controladores Lua; 372 verificações de passagem, conservação do piso da rua e fechamento visual; quatro arquivos nativos lidos independentemente pelo CodeWalker. Backup em `backup/`. Iluminação, posições de objetos e demais arquivos preservados.

Execute `restart cidade_mansao` no console do servidor e feche/reabra o FiveM para renovar mapas e colisões. A validação final de caminhada e aparência no jogo permanece pendente; nenhum reinício foi executado automaticamente.
