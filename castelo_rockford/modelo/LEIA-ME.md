# Castelo Rockford — modelo editável no Blender

Abra **castelo_rockford.blend**. O arquivo usa metros reais e contém as duas imagens de acabamento da mansão incorporadas, além de materiais procedurais de cantaria e ardósia. As coleções separam implantação, térreo, suítes, reunião, cobertura, referências de escala e iluminação.

## Distribuição

| Pavimento | Ambientes e medidas aproximadas |
| --- | --- |
| Térreo | Salão de festas 184 m²; foyer 104 m²; cozinha principal 104 m²; apoio de funcionários 43 m²; despensa 29 m² |
| Primeiro andar | Quatro suítes de aproximadamente 90 m² cada, com espaços de banheiro; quarto de funcionários de 53 m², com duas camas; circulação e escada |
| Último andar | Sala de reunião de 334 m², mesa com 28 lugares, antessala para escolta e área de apoio/copa |

As áreas são envelopes dos ambientes para distribuição arquitetônica; ainda não descontam todas as divisórias, equipamentos e mobiliário. As torres acrescentam pequenas áreas além dos retângulos dos cômodos.

## Proporção e circulação

- Referências humanas de **1,80 m**.
- Três pavimentos com **4,20 m entre pisos** e cerca de 3,95 m até a laje seguinte.
- Portas internas com **2,70 m de altura**, passagens de 1,40 m ou mais e portas principais maiores.
- Escadas com lances de **1,80 m**, degraus de 17,5 cm e pisos de 30 cm, com patamar e guarda-corpos. Os corredores laterais da escada têm aproximadamente 1,55 m.
- Via de **5 m pela esquerda**, contornando o castelo até os fundos; área de manobra traseira com 5,8 m de profundidade.
- Quatro vagas de visitantes à direita da frente e quatro vagas cobertas nos fundos. Veículos de referência: 1,90 × 4,80 m.
- A garagem está deslocada à direita nos fundos para evitar a quadra existente. O projeto foi comparado à projeção da quadra extraída do modelo original.

## Implantação medida

O lote original tem envelope aproximado de **78,77 × 60,95 m**. O corpo do novo castelo ocupa cerca de **580 m²**, com bloco principal de 28 × 20 m e quatro torres. Ele foi encaixado no polígono liberado anteriormente. A garagem e os acessos também permanecem dentro do envelope medido do lote.

O arquivo é modelado perto da origem para facilitar a edição. A correspondência planejada com o mapa é:

```text
Âncora GTA: X -946,00 / Y 207,00 / Z 66,47
Rotação Z: 60 graus
Pisos locais: Z 0,70 / 4,90 / 9,10 m
```

Os valores também estão nas propriedades da cena e em **projeto_medidas.json**. O envelope retangular do lote e o piso externo são referências de projeto, não uma reprodução final de todas as cotas e limites do terreno original. Antes da instalação serão necessários o ajuste das alturas externas, a abertura dos portões e a integração com os muros/vegetação existentes.

## Arquivos de conferência

- `castelo_exterior.png`: vista externa com materiais.
- `castelo_reuniao.png`: último andar.
- `castelo_salao.png`: salão de festas.
- `planta_0.png`, `planta_1.png`, `planta_2.png`: plantas dos três pavimentos.
- `verificacao_blender.json`: conferência do arquivo reaberto e das passagens.

Para editar um andar, oculte a coleção da cobertura e as coleções dos pavimentos acima dele. O mobiliário é volumetria simples de referência; cozinha, banheiros e decoração ainda admitem detalhamento. As legendas das plantas ficam ocultas nos renders de perspectiva.

**Esta entrega é o modelo Blender. Não foi instalado no FiveM nesta etapa.** A conversão dos materiais para texturas do GTA, colisões, LOD, portas interativas e validação dentro do jogo são etapas posteriores.
