# Inventário de roupas nativas — 05/10/2026

Servidor consultado em `127.0.0.1:30120`: `sv_enforceGameBuild=3258`.
Inventário somente leitura dos arquivos locais GTA, usando a lista de DLCs do update.rpf em cache do FiveM (até mp2024_01). Foram percorridos 90 arquivos/pacotes raiz, sem erros de leitura. Não foi aberto Blender nem alterado o servidor.

## Interpretação

Cada modelo contado é uma combinação de personagem, pasta da coleção, categoria e índice de drawable encontrada em arquivos YDD. Cópias de atualização com a mesma chave são deduplicadas; sufixos de pele do mesmo índice não criam outro modelo. Texturas são arquivos diffuse YTD, não o total de imagens internas.

Estes números NÃO são uma contagem certificada dos drawables selecionáveis em tempo de execução ou de silhuetas únicas. Incluem entradas vazias, variantes técnicas, coleções G9EC presentes nos pacotes e peças semelhantes. O inventário não interpreta regras de ativação de content.xml/YMT. DLCs instalados podem ter revisões de arquivo diferentes das originais do build 3258. A lista do build restringe os pacotes pesquisados, mas não certifica cada peça como selecionável.

Escopo: Freemode masculino e feminino. Exclui roupas de NPCs/personagens de história e peças personalizadas do servidor. Camisas, camisetas e jaquetas compartilham JBIB; calças e shorts compartilham LOWR; gorros, bonés, chapéus e capacetes compartilham P_HEAD. Subcategorias exigem inspeção visual.

| Categoria de arquivos | Masculino | Feminino |
|---|---:|---:|
| JBIB — tops externos | 505 | 563 |
| TEEF — tops internos/complementos | 178 | 149 |
| LOWR — calças, shorts e outras peças inferiores | 191 | 209 |
| FEET — calçados/pés | 146 | 157 |
| P_HEAD — itens de cabeça | 243 | 235 |
| P_EYES — óculos | 49 | 51 |
| P_EARS — itens de orelha | 43 | 26 |
| P_LWRIST — pulso esquerdo | 50 | 39 |
| P_RWRIST — pulso direito | 17 | 24 |
| ACCS — acessórios | 194 | 231 |
| BERD — máscaras | 237 | 241 |
| HAND — bolsas/paraquedas | 96 | 107 |
| TASK — coletes/equipamentos | 61 | 61 |

`inventory.json` contém caminhos completos dentro dos RPFs, coleções, índices e texturas. `resumo.csv` contém todas as categorias, inclusive corpo, cabelo e decalques. `active_dlclist.xml` registra a lista de pacotes consultada. `inventory.py` reproduz a leitura.

## Uso recomendado

Escolher uma peça nativa com formato adequado ao personagem Freemode de destino, registrar os braços/pele e complementos compatíveis, e criar novas texturas usando seu UV. Preservar geometria, pesos e LODs. Usar uma coleção própria para as novas variantes. Conferir o resultado parado e em movimento no FiveM.

Mudar estampa/cor não muda comprimento de mangas, gola ou silhueta. Mudanças de brilho e material também precisam dos mapas normal/specular compatíveis com o shader GTA. O molde nativo masculino não deve ser tratado como compatível automaticamente com o feminino, NPCs ou person2.

Para quantidade exata disponível ao jogador, a próxima etapa é enumerar coleções/drawables/texturas pelas natives no cliente FiveM e cruzar os resultados com este inventário. Um catálogo visual pode excluir duplicatas/vazios e separar semanticamente camiseta, camisa, jaqueta, gorro etc.
