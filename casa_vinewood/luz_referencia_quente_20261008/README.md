# Iluminação quente da referência — 08/10/2026

Escopo desta conversa lateral: somente iluminação da mansão. O primeiro print fornecido é a referência de cor e distribuição; o segundo mostra o estado anterior no jogo.

O pacote muda os spots para branco quente, amplia e suaviza sua distribuição até o piso, reforça os pendentes amarelos e o preenchimento indireto. Sete fontes nativas alongadas iluminam paredes existentes. O painel da TV recebe quatro fontes amarelas acompanhando sua moldura. Os locais das luminárias existentes são preservados.

São 149 fontes internas, incluindo as 20 fontes existentes da escada que não foram alteradas. Não há iluminação desenhada por Lua a cada quadro, volumes de luz nem coronas. A geometria, colisões, texturas, materiais não emissivos, esqueletos e limites de LOD foram preservados. Somente o multiplicador emissivo dos pendentes e da TV mudou.

## Arquivos instalados

- `stream/mansao_teto.ydr`
- `stream/mansao_pendentes.ydr`
- `stream/mansao_tv.ydr`
- `iluminacao_ambiente.json`
- `luzes_pendentes.json`
- `iluminacao_decorativa.lua`

Os originais desses seis arquivos ficam em `backup`. `install.py` recusa instalação se algum alvo mudar desde a preparação. Nenhum arquivo de árvore, garagem, porta, arquitetura, clima ou objeto reposicionável é escrito pelo instalador. O servidor e o recurso não são reiniciados automaticamente, para não interferir no trabalho em andamento na conversa principal.

## Verificação

`verification.json` registra comparação estrutural dos modelos, preservação de colisões e texturas, teste dos comandos Lua e amostragem analítica da distribuição. `codewalker_verification.json` registra abertura dos três YDRs pelo leitor nativo CodeWalker e as contagens de luzes. `installation.json` registra hashes dos arquivos efetivamente instalados.

A amostragem de luz é uma aproximação matemática baseada no shader do visualizador CodeWalker; não é uma captura de gameplay e não mede exposição, oclusão ou aparência final do GTA. As medianas calculadas de iluminação no piso das salas e cozinha aumentaram aproximadamente 1,6–2,1 vezes. Esses números não comprovam FPS nem igualdade visual.

**Comparação visual no FiveM ainda não realizada.** Não afirmar que a referência foi igualada sem uma captura atualizada, com horário, clima, câmera e configurações gráficos comparáveis. Se necessário, ajustar o pacote depois dessa comparação.

Para carregar os novos arquivos, reiniciar `cidade_mansao` no console do servidor quando o trabalho da conversa principal permitir e reconectar o cliente. O comando F8 `luzmansao` imprime o perfil e o clima/filtros observados, sem alterar clima nem filtros.

Referências técnicas: [flags de iluminação Sollumz](https://docs.sollumz.org/2.6/documentation/lighting-.ydr/light-flags) e [shader do visualizador CodeWalker](https://github.com/dexyfex/CodeWalker/blob/master/CodeWalker.Shaders/LightPS.hlsli).
