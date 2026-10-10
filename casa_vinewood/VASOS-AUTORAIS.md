# Vasos e plantas modelados pelas referências

Modelo editável: `vaso_planta_autoral.blend`. Cena da mansão com as duas unidades: `mansao_vasos_autorais.blend`. As referências originais e materiais ficam em `source_assets/vaso_planta`.

O modelo tem vaso grafite arredondado com cavidade interna, borda de 28 mm, terra e pequenos grãos, seis troncos curvos com casca, ramos e pecíolos e 306 folhas individuais. As folhas são superfícies curvas com frente, verso e espessura; o contorno e as UVs seguem a imagem de folhas enviada. A copa é volumétrica e pode ser vista de qualquer lado. A altura é aproximadamente 2,2 m; o vaso mede 66,2 cm de diâmetro e 63,2 cm de altura.

Os materiais têm mapas de cor, relevo e especularidade com mipmaps. O material grafite tem microestrutura sem as luzes do estúdio da fotografia incorporadas na superfície. Folhas e casca usam as referências enviadas.

Um drawable compartilhado, `mansao_vaso_folhagem.ydr`, é instanciado duas vezes no mapa `mansao_vasos_autorais.ymap`, junto à sala e no hall da escada, ambos no térreo. O mapa usa `mansao_vasos_autorais.ytyp`. A colisão de 200 triângulos acompanha apenas o vaso; os galhos e folhas não criam barreiras rígidas. Os vasos nativos anteriores são preservados.

`verificacao_vasos_autorais.json` verifica geometria, normais, tangentes, UVs, texturas e mapa nativo, folga da copa nas paredes, apoio no piso e trajetos com a colisão real. `instalacao_vasos_autorais.json` confirma os arquivos copiados e os hashes dos assets anteriores.

As imagens são prévias Blender; a aparência final no FiveM ainda precisa de conferência. Para carregar, use `restart cidade_mansao` no console do servidor e reconecte.
