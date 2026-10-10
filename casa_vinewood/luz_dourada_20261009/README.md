# Refinamento dourado — perfil v9

Pedido ativo desta conversa lateral: aproximar a iluminação da segunda imagem fornecida após a melhoria de nitidez do perfil v8. Escopo limitado a iluminação e aparência das lentes. Não modifica arquitetura, portas, veículos, árvores, garagem, posições salvas de móveis, clima ou proteção climática.

## Diferenças tratadas

A captura v8 estava mais nítida, mas apresentava preenchimento uniforme, lentes de teto frias, pendentes apagados e pouca separação entre áreas iluminadas e sombras. A referência tem pontos de emissão brilhantes, luz dourada nas paredes e contrastes maiores.

Os logs reais do FiveM registraram o carregamento do perfil v8. Na entrada do interior, ambos os hashes de clima eram -1750463879 (EXTRASUNNY), com filtro principal -1 e slot extra anterior -1. Isso descarta um filtro principal concorrente nessas entradas; não é uma análise completa de todos os efeitos do renderizador.

## Alterações

- Spots com cor 255/165/76 e 90% da potência v8. Suas lentes usam uma pequena amostra uniforme 4x4 de branco quente 255/223/160, com emissão 3,6. Molduras, refletores, prismas e geometria em todos os LODs permanecem intactos.
- Pendentes com cor 255/174/72, emissão 2,7 e reforço moderado da luz direta. Mantêm posições e alcance.
- Preenchimento indireto reduzido para aprofundar sombras, mantendo todas as fontes e horários constantes.
- Sete luzes locais das paredes reposicionadas para as faces internas desejadas, incluindo os dois lados da divisória entre jantar e cozinha e a parede da cozinha diante da câmera. As fontes existentes foram reutilizadas; não houve aumento de quantidade.
- Luzes e emissão do painel da TV reforçadas localmente em dourado.
- Quatro fontes adicionais de sombra, além da preexistente: duas nos pendentes e duas no teto da sala. Cinco no total, sem flag de alta resolução e com distância limitada. O custo de FPS no jogo não foi medido.

O perfil óptico v8 foi mantido com os mesmos valores para bloom, ruído e desfoque, agora com nome próprio v9. Continua restrito ao interior pela posição da câmera; preserva filtros de outros recursos e limpa apenas seu próprio filtro ao sair/parar.

## Verificação e instalação

Geometria, índices, UVs, normais, colisões, LODs, esqueletos e programas dos materiais foram comparados e preservados. Mudam parâmetros emissivos e somente a pequena textura uniforme `spot_lente`; todas as outras texturas têm bytes idênticos. Os quatro YDRs foram abertos por dois leitores independentes, incluindo CodeWalker.

Contagem permanece em 149 fontes interiores, incluindo as fontes da escada que não foram alteradas. Testes de Lua verificaram entrada, saída, comparação, ocupação do slot por outro recurso, parada e falhas de inicialização. A aproximação matemática da luz difusa no piso das três salas principais ficou em 82–84% do perfil v8, com maior proporção de vermelho e destaques localizados nas paredes. Não é uma renderização do FiveM nem uma medição de exposição, oclusão ou desempenho.

São sete alvos: teto, pendentes, TV e spot embutido YDR; configuração de ambiente e pendentes; controlador de iluminação. O instalador confere hashes do pacote validado e recusa edição concorrente dos alvos. Os originais estão em `backup`. Não reinicia o recurso ou servidor automaticamente.

**Igualdade visual com a referência ainda não foi verificada.** Necessária nova captura no FiveM após recarregar os arquivos. As câmeras das imagens fornecidas diferem, então os recortes servem somente como guia de cor/contraste.

Carregar no console do servidor: `restart cidade_mansao`; fechar e reabrir o FiveM. No F8, `luzmansao` deve mostrar `PERFIL v9`. `luzmansao original` e `luzmansao limpo` continuam comparando somente o controle óptico, sem alterar as luzes físicas.
