# Calça tática verde

F8: `calcatatica`. Restaurar: `roupaanterior`.

Cópia da malha nativa `mp_m_freemode_01_male_freemode_business2/lowr_001_r.ydd`, com textura verde oliva de tecido e detalhes táticos pretos adaptados às referências. A base nativa foi preservada; a revisão 3 acrescenta geometria para o relevo dos bolsos e três fitas móveis separadas.

Instalação em `cidade_roupas`, componente 4, coleção `Male_Heist`, drawable 6, textura 0. Substitui um slot de teste nessa coleção, preservando a peça original Business2 e a calça bege personalizada do slot 8. Não cria nova coleção addon.

Vértices, UVs, pesos e índices de todos os níveis de detalhe foram comparados com o original. A textura de cor foi alterada; mapas normal/especular nativos são preservados. `validation.json` registra a conferência. As prévias são renders dos arquivos exportados, não capturas do FiveM.

Revisão 2: bolsos reposicionados nas laterais externas conforme o UV da malha; fivelas pretas e reforço inferior diagonal com faixa cinza adaptados às imagens fornecidas. Conferência visual em `preview.webp`, `preview_back.webp`, `preview_left.webp` e `preview_right.webp`. A revisão 1 foi preservada como backup.

Revisão 3: altura dos bolsos reduzida aproximadamente em um terço (66,8% da altura anterior no UV), relevo de até 9 mm com pesos interpolados da base nativa em todos os LODs. Reforços inferiores transferidos para a lateral voltada à frente. Duas fitas de bolso com fivela e uma fita de cinto de 29 cm usam objetos YDR registrados em `ct_straps.ytyp`. A ponta do cinto se estende abaixo da camiseta; camisetas mais longas ainda podem ocultar parte dela.

`tactical_straps.lua` detecta a peça equipada nos jogadores próximos (35 m), posiciona as fitas pelos ossos nativos e simula balanço leve com mola amortecida, velocidade e aceleração. Trata-se de movimento secundário visual; não é simulação de tecido com colisões. Os objetos são locais para cada cliente, removidos ao trocar de peça, sair do alcance ou parar o recurso. Ocultos dentro de veículos.

`complete_front.webp`, `complete_side.webp` e `complete_back.webp` mostram a montagem exportada em repouso. `test_runtime.py` executa o código Lua real com natives simuladas: criação das três fitas, movimento, estabilização e limpeza. A posição e o balanço no FiveM ainda precisam do teste no jogo. Backup da revisão 2 em `backup_revision2`.

Reinicie `cidade_roupas` no servidor e reconecte para testar. A validação desta revisão dentro do jogo ainda está pendente.
