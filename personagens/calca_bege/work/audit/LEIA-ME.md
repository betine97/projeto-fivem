# Auditoria do pipeline de texturas

Auditoria somente leitura dos arquivos existentes. Nenhum arquivo do traje de guarda ou do servidor foi modificado.

## Falhas comprovadas no traje de guarda

- `extract_textures.py` aplicou `FLIP_TOP_BOTTOM` ao converter PNG para DDS. O DDS nativo exportado tem erro médio RGB de 49,52/255 contra o PNG original e de 2,50/255 contra o PNG invertido. Em `(100,100)`, o original contém `[243,7,105]` e o arquivo nativo contém `[24,24,24]`. Isso desloca as áreas pretas do atlas para regiões vermelhas da roupa.
- O Sollumz já converte `V` para `1-V` ao exportar UVs. A verificação de 2.000 amostras de posições e UVs provou erro UV zero após desfazer essa conversão. PNG e DDS não devem ser invertidos novamente.
- `export_guard.py` escolhe a cor com `a.name.endswith('0')`. Os nomes do Sollumz são `Color 1` e `Color 2`; portanto ambos foram pintados com zero. A leitura do YDD final comprovou `Colour0=[0,0,0,0]` e `Colour1=[0,0,0,0]` em todos os LODs. Usar `get_color_attr_name(0)` e `get_color_attr_name(1)` de `Sollumz.tools.meshhelper`, e verificar `Colour0=[255,128,0,255]`, `Colour1=[0,0,0,0]` no arquivo final.
- As referências de textura do YDD de guarda resolvem corretamente no YTD; a causa principal não é nome ausente. O atlas original já contém um vermelho com azul forte, média RGB `[153,14,71]`, mas a conversão incorreta acrescentou áreas pretas não correspondentes.
- GLTF usa normal map OpenGL. Converter para GTA DirectX invertendo somente o canal verde (`G=255-G`), sem inverter linhas. O shader de prévia do Sollumz desfaz essa inversão ao mostrar a normal no Blender.

## Regras para a calça

- Extrair texturas pela semântica JSON. Na calça, índices são diffuse=0, metallicRoughness=1, normal=2. No guarda eram diferentes.
- Preservar o atlas diffuse e os UVs originais. Converter JPEG para DDS sem `FLIP_TOP_BOTTOM`.
- Usar `ped.sps`. Manter normal e specular EMBUTIDOS no YDD, diffuse no YTD separado, conforme o fluxo oficial para roupas MP.
- Diffuse com nome consistente: `lowr_diff_008_a_uni`. A exportação atual da peça `_u` usa `calca_bege_normal` e `calca_bege_spec` embutidos e referências explícitas corretas nos samplers; os scripts de verificação conferem os samplers reais. Peças `_r` que mudam o tom de pele exigem atenção adicional aos nomes Rockstar, por exemplo `lowr_normal_008`, `lowr_spec_008`.
- Converter apenas a semântica PBR necessária para o shader GTA; não usar roughness como diffuse e não inventar cores novas.
- DDS com largura/altura potência de 2 e sem canais de suor/metálico não desejados no specular alpha.
- Conferir os arquivos nativos de TODOS os LODs, não apenas a cena Blender.

## Verificação da calça

Executar somente após terminar a exportação:

1. `python personagens/calca_bege/work/audit/verify_pants_native.py`
2. Blender em background com `personagens/calca_bege/work/audit/render_reimported_pants.py`.

O primeiro script compara os pixels dos DDS extraídos dos arquivos nativos contra o GLB, confere as referências e as cores de vértices. O segundo compara 3.000 UVs/posições com a cena de trabalho e renderiza o YDD/YTD reimportado. Esses checks não substituem o teste visual no FiveM.

## Fontes e implementação consultadas

- https://docs.sollumz.org/tutorials/basic-clothes-editing
- https://github.com/Sollumz/Sollumz/issues/166
- Código local: `ydr/vertex_buffer_builder.py`, `ydr/mesh_builder.py`, `ydr/shader_materials.py`, `tools/meshhelper.py`, `ytd/properties.py`.

Relatórios detalhados: `audit_native.json`, `audit_uv.json`, `verification_native.json` e `verification_uv.json` (os dois últimos aparecem depois da exportação da calça).
