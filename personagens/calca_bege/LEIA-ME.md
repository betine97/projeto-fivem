# Primeira peça: calça bege

Modelo recebido: `Meshy_AI_pleated_beige_trouser_1005054816_image-to-3d-texture.glb`.

Esta etapa equipa somente a calça no personagem original `mp_m_freemode_01`, sem camisa e com pés descalços nativos. A cabeça e o cabelo existentes do jogador Freemode são preservados. Os macacões anteriores permanecem guardados; camisa, mocassins e relógio aguardam a validação desta primeira peça.

## Testar

Reconecte ao servidor atualizado e use `/calcabege`. Ande, corra, agache e observe cintura, joelhos e barras. Use `/roupaanterior` para restaurar o traje e modelo anteriores.

## Blender

`PERSONAGEM_COM_CALCA_BEGE.blend` contém o personagem, os pés nativos e a calça vinculada ao esqueleto original. Foi salvo na pose de repouso. `CALCA_ORIGINAL.blend` preserva a importação inicial da peça.

O ajuste ao corpo altera apenas a escala e posição da malha, e adiciona pesos para animação. No nível de detalhe mais próximo, os 120.843 vértices e 221.146 triângulos recebidos são mantidos. As coordenadas UV e as três imagens originais são preservadas. Os arquivos DDS de jogo usam a compressão exigida pelo formato e a conversão do mapa normal para DirectX.

## Arquivos de jogo

- `exports/lowr_008_u.ydd`: calça, esqueleto compatível, mapas normal e especular embutidos, quatro níveis de detalhe.
- `exports/lowr_diff_008_a_uni.ytd`: textura de cor original convertida para DDS, em 4096 × 4096.
- Instalação: `server-data/resources/cidade_roupas/stream/mp_m_freemode_01_male_heist^lowr_008_u.ydd` e textura correspondente.
- Componente 4, coleção `Male_Heist`, drawable local 8, textura 0. Este é um slot de teste que substitui uma peça nativa dessa coleção. O nome retornado pelo jogo usa maiúsculas; o comando normaliza a comparação e preserva o nome original ao equipar.

## Verificação

`work/validation.json` registra integridade da malha, UV, imagens e teste dos joelhos. `exports/validation.json` registra a exportação. `work/audit` contém a conferência das texturas, cores de vértice, UV e a reimportação dos arquivos finais. `work/test_command.py` testa a seleção dos componentes e a restauração do personagem.

As prévias são renders do Blender. A aparência e os movimentos no FiveM dependem da validação do jogador.

Correção de integração: `work/base_audit/collection_names.json` registra os nomes reais `Male_Heist` e `Male_Apt01` extraídos dos YMTs originais. Os testes de comando incluem essas grafias, além de variantes em minúsculas e com prefixo completo.
