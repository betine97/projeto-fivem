# Otimização e iluminação ampla — 08/10/2026

Revisão `otimizacao-luz-ampla-2026-10-08`, instalada em `cidade_mansao`.

Os dez drawables tratados passaram de **544 para 132,625 MiB de alocação gráfica** no cabeçalho RSC7, redução de **75,62%**. Essa medida é a alocação declarada dos recursos, não uma medição de FPS ou do consumo total do computador. Incluindo as páginas de memória de sistema, o conjunto passou de **570,859 para 188,609 MiB**. Os LODs acrescentam dados de malha à memória de sistema, mas reduzem os triângulos renderizados quando distantes. Os arquivos passaram de 126,721 para 83,566 MiB.

| Elemento no jogo | Gráfica antes (MiB) | Gráfica depois (MiB) |
| --- | ---: | ---: |
| Sofá, mesa de centro, TV e rack | 128 | 24 + 6 |
| Pendentes de jantar e cozinha | 128 | 12 |
| Mesa e cadeiras de jantar | 64 | 24 |
| Ilha e banquetas | 64 | 24 |
| Tapete da sala | 64 | 16 |
| Paredes e acabamentos | 40 | 16 |
| Modelo de porta de madeira | 24 | 4 |
| Pisos | 16 | 6 |
| Escada e corrimãos | 16 | 0,625 |

As medidas definitivas, por arquivo, estão em `optimization_report.json`; use esse relatório se o cabeçalho de uma versão anterior apresentar outros valores.

## Abordagens aplicadas

- Cor 4K mantida no sofá, jantar, ilha e tapete; pedra, reboco, tijolo e madeira das portas mantêm a resolução anterior. Mapas auxiliares de relevo e reflexo têm resolução própria, com renormalização dos vetores após reduzir normais.
- Texturas inteiramente opacas usam BC1, com metade do espaço dos blocos BC3. Texturas que precisam de alfa e mapas de normais conservam BC3. As cadeias de mipmaps continuam presentes.
- TV/rack e sofá/mesa têm drawables independentes, sem carregar as texturas de um dentro do arquivo do outro.
- Seis conjuntos recebem LODs nativos HIGH, MEDIUM, LOW e VERYLOW. A geometria HIGH mantém todos os triângulos, normais, tangentes, cores e UVs originais. Reduções preservam bordas e consideram normais e UVs; não há deslocamento dos vértices originais.
- Índices e vértices são reordenados para favorecer o cache de transformação da GPU. Colisões simplificadas, espessuras das paredes/lajes e colisão da câmera permanecem preservadas.
- Alcance de carregamento dos móveis de 180 m, LOD HIGH até 24/28 m, seguintes níveis até 55/100/180 m. Arquitetura conserva seu alcance anterior.
- Um único controlador desenha a luz ambiente, teto, pendentes e escada. Até 20 luzes principais e quatro vagas para transição, com teto absoluto de 24 chamadas por quadro. Seleção a cada 200 ms, transição suave de 450 ms e suspensão quando jogador e câmera estão distantes.

## Luz

Os fachos estreitos e suas passagens de sombra foram substituídos por luzes pontuais amplas, com preenchimento de ambiente que aproxima luz refletida nas paredes. Os volumes têm raio de 5,8–8 m para teto/ambiente e se sobrepõem. As lâmpadas físicas continuam redondas; não projetam um círculo de spotlight no piso. Pendentes próximos compartilham volumes e as vinte fitas da escada usam quatro grupos, preservando a geometria emissiva de cada lâmpada.

O brilho varia suavemente com o horário; a noite recebe mais preenchimento. No chat, `/luzmansao` mostra os parâmetros locais. `/luzmansao 1.3` aumenta 30%; `/luzmansao 1` volta ao padrão. O ajuste fica entre 0,5 e 2 e afeta somente a luz da mansão daquele cliente, sem alterar horário, clima ou exposição da cidade.

## Validar e carregar

`verify_optimization.py` confirmou leitura e exportação nativa, triângulos texturizados HIGH idênticos, colisões preservadas (repartição TV/sofá dentro de 0,1 mm da quantização original), referências do mapa, alfa opaco, mipmaps, Lua e execução simulada do controlador perto/longe, em ambos os pisos, de dia/noite e durante troca de seleção. A conversão dos mapas de cor mantidos na mesma resolução mediu PSNR de 51–65 dB nos mapas principais.

`installation.json` confirma hashes instalados e preservação dos demais arquivos, inclusive o mapa de vasos autorais instalado durante o trabalho. A fonte `../mansao_otimizada.blend` contém o cenário editável, texturas otimizadas e 78 objetos de LOD na coleção oculta `92_LODS_OTIMIZADOS`. `93_PREVIA_LUZ_AMPLA` contém luzes de aproximação para a prévia Blender; não são usadas como luzes nativas no jogo.

**No console do servidor**, execute `restart cidade_mansao`, depois reconecte o FiveM. Não é um comando F8. A instalação está no disco, mas não foi recarregada automaticamente na sessão ativa. A prévia `previa_noite_luz_ampla.png` é uma aproximação Blender; o brilho final e o ganho de FPS ainda exigem verificação no FiveM.

Para reproduzir os arquivos dessa revisão, execute `optimize_assets.py`, `build_lighting_config.py`, `verify_optimization.py` e `install.py`, nesta ordem. O otimizador usa a cópia de origem registrada em `baseline.json`. Para futuras mudanças de geometria, gere uma nova revisão a partir das novas fontes; não reaplique esse snapshot sobre conteúdo novo. Os instaladores antigos de decoração não incluem a otimização nova.

Backup original em `../backup_antes_otimizacao_20261008_094951/`; o instalador também salvou os arquivos imediatamente anteriores em `backup_imediato_instalacao/`.

Algoritmos: [meshoptimizer oficial](https://github.com/zeux/meshoptimizer), cópia fixa com licença em `vendor/`. Luz nativa: [DrawLightWithRange](https://github.com/citizenfx/natives/blob/master/GRAPHICS/DrawLightWithRange.md). A interpretação das páginas RSC7 segue [CodeWalker, RpfResourcePageFlags](https://github.com/dexyfex/CodeWalker/blob/master/CodeWalker.Core/GameFiles/RpfFile.cs).
