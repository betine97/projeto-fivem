# Mansão — sala, jantar e ilha de cozinha

Revisão `jantar-cozinha-2026-10-07`. Os quatro GLBs fornecidos foram incorporados ao recurso `cidade_mansao`, usando a última imagem como referência de distribuição. A confirmação visual no FiveM depende de recarregar o recurso e reconectar.

## Componentes novos

| Conjunto | Instalação | Dimensões e altura |
| --- | --- | --- |
| Mesa de jantar | Entre a sala e a cozinha, com oito cadeiras e decoração originais | 3,90 m no sentido longitudinal, incluindo cadeiras; tampo a 83,5 cm do piso |
| Ilha de cozinha | Na cozinha, com as quatro banquetas voltadas para o jantar | 3 m de comprimento; bancada a 93,7 cm do piso |
| Pendente de cilindros | Centralizado acima da mesa, seis cilindros | Comprimento 2,40 m; parte inferior a 2,30 m do piso; suporte no teto do pé-direito duplo |
| Pendente linear | Centralizado acima da bancada | Comprimento 2,50 m; parte inferior a 2,15 m do piso; suporte sob a laje superior |

Os corpos dos modelos usam escala uniforme; somente os trechos dos cabos foram ajustados para alcançar os tetos. Os pendentes têm faces emissivas e nove pontos de iluminação quente, ativos perto da mansão. A instalação inclui os componentes dos GLBs; armários de cozinha e outros itens presentes apenas na imagem de referência não foram modelados nesta revisão.

As malhas foram unidas nas costuras antes da otimização. Os arquivos nativos novos têm zero bordas abertas, zero arestas não-manifold, zero triângulos degenerados e zero tangentes nulas. Mesa: 100.000 triângulos; ilha: 64.998; cilindros: 24.000; linear: 15.998. Cor e relevo originais preservados em 4.096 pixels, especular em 2.048, com filtragem até 4×4. A qualidade dos detalhes pintados segue o conteúdo dos GLBs fornecidos.

Mesa, cadeiras, ilha e banquetas têm colisões simplificadas. Três percursos novos verificam a circulação ao redor dos conjuntos e entre jantar e cozinha. Os pendentes ficam acima da circulação do personagem.

## Ajustes anteriores preservados

- Sofá/chaise/mesa de 5,20 m, com malha fechada e mapas 4K, e painel de TV de 4,60 m na parede de tijolos.
- Mármore bege em todo o térreo e no piso superior, exceto os 39,60 m² delimitados do mezanino. Escadas e patamares em madeira; paredes superiores com o reboco creme do térreo.
- Paredes de 20/25 cm, piso térreo de 30 cm e laje superior de 45 cm, com faces laterais visíveis.
- Cinco portas de madeira de 45 mm: escritório, lavabo, despensa, sala de TV/jogos e lavanderia. **E** abre/fecha suavemente, com estado compartilhado; fechamento recusado enquanto alguém ocupa o vão. Entrada junto ao deck e porta de vidro à esquerda do sofá reservadas para outros modelos.
- Colisão da câmera, limitação de corrida, limpeza de obstáculos e vegetação nativos, transparência dos vidros e correção de oclusão.

A geometria, as normais e as UVs dos sete drawables anteriores foram comparadas com o backup e permanecem iguais.

## Arquivos e verificações

`mansao_encaixada.blend`: fonte editável. `mansao_fivem_preparada.blend`: materiais de exportação, móveis colocados, portas para visualização e fachada corrigida em coleção oculta. `source_assets/`: GLBs originais. `backup_antes_jantar_cozinha/`: versão anterior completa.

O pacote instalado contém 42 arquivos nativos, incluindo nove drawables estáticos e um modelo de porta móvel. `componentes_jantar_cozinha.json` descreve escala, posição e origem dos modelos. `verificacao_jantar_cozinha.json` registra malhas, texturas, circulação, iluminação e preservação dos modelos anteriores. `instalacao_jantar_cozinha.json` e `auditoria_instalacao_final.json` registram os arquivos instalados e seus hashes. As validações anteriores de portas, estrutura, câmera, circulação e janelas foram repetidas.

As imagens `jantar_cozinha_visao_geral.png`, `mesa_jantar_detalhe.png` e `ilha_cozinha_detalhe.png` são prévias Blender, não capturas do jogo.

## Carregar

No console do servidor: `restart cidade_mansao`. Depois reconecte o FiveM e use `/mansao`. Perto das portas, pressione **E**. `/mansaoverificar` registra colisões observadas pelo GTA; portas fechadas são identificadas separadamente de bloqueios inesperados.

## Editor ADM de objetos — 08/10/2026

No F8: `editarobjetos`. Aproxime-se e olhe para uma peça; **CAPS** seleciona, andar a arrasta e **CAPS novamente** confirma e salva para todos. **Setas esquerda/direita** giram; **Page Up/Down** ajustam a altura; **Backspace** cancela. **Home** retorna à posição original antes de confirmar. `objetosajuda` mostra os controles e `objetosdebug` imprime o estado no F8. `editarobjetos` novamente desliga.

O modo exige `cidade.admin` e inclui 36 peças/conjuntos da mansão, inclusive vasos, jantar, sofá, TV, quadros, tapetes e piano, além de objetos estáticos comuns do mapa. Conjuntos exportados em uma só malha se movem inteiros. Portas animadas e estruturas fixas ficam fora da seleção. As posições confirmadas persistem em `objetos_posicoes.json`, com a revisão anterior em `objetos_posicoes.backup.json`; cancelamento, morte e desconexão restauram a última posição salva.

A iluminação difusa da sala/jantar/cozinha foi reforçada, com oito fontes amplas que continuam ativas ao atravessar a área integrada. O limite permanece 24 luzes por quadro. `luzmansao 1` usa o novo padrão, com ajuste local de 0,5 a 3.

Fontes, backup e testes desta revisão: `casa_vinewood/editor_objetos_20261008/`. Recarregue o recurso no console do servidor e reconecte para aplicar os mapas. Os testes locais passaram; avaliação visual no FiveM pendente.

## Proteção climática removida — 08/10/2026

A pedido do usuário, a proteção contra chuva e névoa foi retirada para investigar o crash ao entrar/aproximar-se da mansão. O teto voltou a ser uma entidade BASE, sem salas ou portais MLO. A colisão original de paredes, pisos, escada e teto foi restaurada nos drawables. O YBN local do MLO e os scripts/configurações de clima foram retirados do recurso; suas cópias permanecem no backup desta revisão.

A proteção climática fica para uma revisão futura. A iluminação permanente, móveis, bar, portas e posições salvas no editor permanecem preservados. Recarregue o recurso no servidor, feche completamente o FiveM e conecte novamente antes de testar `mansao` no F8. A confirmação de estabilidade no jogo ainda está pendente.

Pacote, backup e verificações: `casa_vinewood/remover_clima_20261008/`.

## Iluminação permanente de todos os ambientes — 08/10/2026

Esta revisão substitui a seleção de luzes por proximidade descrita anteriormente. O drawable do teto contém 68 luzes nativas constantes, distribuídas pelos 19 ambientes e ativas nos 24 horários do dia. Sala, jantar, cozinha, quartos, circulação, mezanino e escada conservam suas fontes independentemente do cômodo ocupado. Os reforços verticais iluminam paredes e pé-direito alto; preenchimentos difusos não produzem reflexos especulares excessivos no mármore. Só três fontes usam sombras; coronas e volumes luminosos de névoa estão desativados.

No padrão, o controlador Lua não desenha luzes por quadro. `luzmansao 1` usa o projeto nativo; `luzmansao 1.5` a `3` acrescenta reforço uniforme opcional nos ambientes. Valores menores que 1 retornam ao padrão. `mansaoluzes` mostra a configuração. Recarregue com `restart cidade_mansao` **no console do servidor** e reconecte o FiveM para atualizar o drawable.

Testes locais: 5.098 pontos de cobertura, 45 casos de mudança de ambiente/horário, câmera de drone, exportação nativa e preservação da geometria, texturas, colisões da revisão de iluminação. A proteção climática foi removida posteriormente conforme a seção acima. Avaliação visual e medição de FPS no jogo pendentes. Projeto, código, relatórios e backup: `casa_vinewood/luz_permanente_20261008/`.
