# Acervo de roupas GTA

3.770 modelos nativos masculinos e femininos, com 7.540 imagens de frente e costas, pesquisa, filtros por categoria/personagem/coleção, ordenação e referência copiável. Inclui todas as peças renderizáveis com malha e textura encontradas no inventário local.

| Categoria | Modelos |
| --- | ---: |
| Camisas e jaquetas | 915 |
| Blusas e camisetas internas | 245 |
| Calças e shorts | 348 |
| Calçados | 301 |
| Chapéus, bonés e gorros | 474 |
| Óculos | 100 |
| Brincos | 69 |
| Relógios | 89 |
| Pulseiras | 41 |
| Acessórios | 415 |
| Máscaras | 448 |
| Bolsas e paraquedas | 203 |
| Coletes | 122 |

## Abrir no computador

Execute `abrir.ps1` no PowerShell. O catálogo abre em http://127.0.0.1:8766/. Requer Python instalado. O servidor escuta apenas no próprio computador.

Os arquivos do app estão em `dist`. As prévias mostram uma textura por modelo e iluminação de estúdio. A combinação com pele e outras roupas deve ser validada no FiveM.

Publicação online pendente: o serviço Sites retornou `project_not_found` para o projeto registrado no manifesto. O catálogo local funciona independentemente dessa publicação.

Máscaras: foram examinadas 478 entradas do inventário. 28 não possuem geometria renderizável e 2 não possuem textura difusa encontrada. Detalhes em `../personagens/catalogo_nativo/expansion_report.json`.

Calças e shorts: examinadas todas as 400 entradas locais. 49 são modelos vazios ou placeholders de dois triângulos; outras 3 não têm textura difusa encontrada. Relatório em ../personagens/catalogo_nativo/lower_expansion_report.json. Prévias de uma textura por modelo.

Camisas, jaquetas, blusas e camisetas internas: todas as 1.395 entradas foram examinadas; 1.160 renderizadas. 217 entradas são placeholders com apenas um ou dois triângulos; 18 não possuem textura difusa nos arquivos locais. Duas peças foram recuperadas usando uma variação visível da textura. Relatório em `../personagens/catalogo_nativo/tops_expansion_report.json`.


Calçados, chapéus/bonés/gorros, óculos, brincos, relógios, pulseiras, acessórios, coletes e bolsas/paraquedas: 1.830 entradas examinadas; 1.814 renderizadas. As 16 restantes não têm textura difusa encontrada nos arquivos locais. Recuperadas 11 variações inicialmente invisíveis e 10 modelos com DDS A8. Relatório em `../personagens/catalogo_nativo/remaining_expansion_report.json`.

Favoritas: marque o check Favorita no cartão da peça. Ative Favoritas nos filtros para mostrar apenas as selecionadas, combinado com categoria, personagem, coleção e busca. A seleção é salva no armazenamento local do navegador; desmarcar remove a peça. Limpar filtros não apaga as favoritas.


Tablet no FiveM: o comando roupas mostra somente peças com a tag OK, independente das favoritas. Calçados, chapéus e acessórios também precisam de OK. As favoritas e todo o catálogo continuam preservados. Execute restart cidade_acervo no console do servidor para carregar esta atualização.

O filtro Revisão possui Todas as tags, Sem tags, OK, PEÇA INCORRETA e DEFEITO NA TEXTURA, combinável com categoria, personagem, coleção, busca e favoritas. As tags são editáveis no jogo e nos detalhes da peça no navegador. OK é exclusivo; as duas tags de problema podem ser combinadas.

A página aberta sincroniza automaticamente a cada três segundos e ao receber foco, sem descartar edições ainda não salvas. O tablet aberto recebe mudanças em até dois segundos. Ao retirar OK de uma peça, ela sai da lista e seu slot é restaurado na prévia, mantendo as demais escolhas.

O arquivo compartilhado é server-data/resources/cidade_acervo/tags.json, atualizado atomicamente pelo serviço server.py. Ele precisa estar iniciado para salvar no jogo. Cada gravação modifica apenas a peça escolhida e preserva as favoritas.

A prévia começa de roupa íntima. Enquadramento fica no canto superior direito. O giro funciona segurando e arrastando a bolinha, sem saltar ao clicar no trilho. Cabelo e barba usam círculos RGB da paleta nativa; tatuagens possuem filtro por região.

Detalhes e testes em ../server-data/resources/cidade_acervo/LEIA-ME.md.
