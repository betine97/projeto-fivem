# Revisão de contraste após o print no jogo

O usuário relatou que a revisão anterior não ficou próxima da referência e parecia suja/enfumaçada. O piso no novo print estava excessivamente claro: uma amostra tem mediana RGB 229/212/190, enquanto uma amostra de piso da referência tem 158/120/86. As câmeras não são idênticas; isso é um indicador de exposição e cor, não uma comparação pixel a pixel.

## Diagnóstico e alterações

O recurso da mansão não desenhava volumes/coronas de luz nem aplicava timecycle. O aumento de luz da revisão anterior se acumulava no piso pálido e as fontes diretas ainda permitiam reflexos especulares. Bloom, somado à luz excessiva, é uma hipótese forte para o véu no print, não uma causa confirmada por captura do renderizador. O clima e os filtros ativos da sessão não foram registrados no log consultado.

As fontes nativas existentes foram mantidas, sem aumentar sua quantidade. A potência dos spots ficou em 48% da revisão anterior, dos pendentes em 68%, dos preenchimentos em 40%, da lavagem das paredes em 70% e das fontes da TV em 58%. O RGB dos spots passou a 255/186/110 e dos pendentes a 255/173/80. O reflexo especular dessas fontes foi desabilitado, preservando os materiais e texturas. Os pontos de preenchimento subiram 85 cm para reduzir a concentração de luz junto às placas do piso. Seu recorte inferior continua no mesmo pavimento. Alcance, posições das luminárias, abertura dos focos e suas horas fixas foram preservados. A emissão das lentes dos pendentes e da TV foi moderada.

Um modificador óptico limpo controla somente cinco variáveis: `postfx_intensity_bloom` (0,08), `postfx_noise`, `screen_blur_intensity`, `dof_blur_mid` e `dof_blur_far` (zero). Os nomes foram conferidos nos arquivos originais locais do GTA, acessados somente para leitura. O modificador é aplicado apenas à câmera dentro do contorno da mansão. Ele sai ao deixar a casa ou parar o recurso. Se o slot extra estiver ocupado por outro script, não o substitui. O filtro principal, exposição, chuva, névoa e clima não são alterados. Nenhuma estrutura MLO ou proteção climática foi adicionada.

## Validação

As três alterações YDR foram abertas por szio/pymateria e pelo leitor CodeWalker. Malhas, índices, UVs, normais, texturas, colisões, esqueletos e LODs foram comparados e preservados. As fontes continuam constantes: 149 fontes internas no total, incluindo a escada que não mudou. A aproximação matemática da luz difusa no piso das três salas principais ficou em 42–44% da revisão anterior; não representa renderização, HDR, oclusão ou FPS no FiveM.

O controlador Lua foi executado em testes de entrada, saída, comandos de comparação, ocupação do slot por outro recurso, parada do recurso, falha na criação e indisponibilidade das variáveis. O teste verifica que não existe mudança de clima nem filtro principal. Os arquivos instalados são os mesmos seis da revisão anterior; originais em `backup`, hashes e resultados em `verification.json`, `codewalker_verification.json` e `installation.json`.

**Resultado visual final ainda precisa de captura atualizada no FiveM. Não foi verificada igualdade com a referência.** Não foram medidos FPS nem testes de gameplay por esta conversa lateral.

## Carregar e diagnosticar

No console do servidor, quando puder recarregar o recurso: `restart cidade_mansao`. Fechar e reabrir o FiveM para recarregar os YDRs. Não houve reinício automático do servidor ou recurso nesta conversa.

No F8: `luzmansao` mostra versão, clima e filtros. `luzmansao original` desliga somente o controle óptico local para comparar; `luzmansao limpo` o reativa. As luzes físicas não são modificadas por esses comandos. A entrada no interior registra hashes do clima e índices dos filtros, permitindo investigar causas externas caso o véu continue.

Referências técnicas: [CreateTimecycleModifier](https://github.com/citizenfx/fivem/blob/master/ext/native-decls/CreateTimecycleModifier.md), [implementação Cfx dos modificadores](https://github.com/citizenfx/fivem/blob/master/code/components/extra-natives-five/src/TimecycleNatives.cpp) e [SetExtraTimecycleModifier](https://github.com/citizenfx/natives/blob/master/GRAPHICS/SetExtraTimecycleModifier.md).
