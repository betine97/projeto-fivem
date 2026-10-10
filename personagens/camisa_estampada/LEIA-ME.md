# Camisa estampada — segunda peça

Comando: `/camisaestampada`. Equipa a camisa com a calça bege aprovada, mantendo o personagem Freemode, rosto, cabelo e pés descalços. `/calcabege` volta à calça sem camisa. `/roupaanterior` restaura o traje anterior à sequência de testes.

Blender: `PERSONAGEM_COM_CAMISA.blend`. A peça original está em `CAMISA_ORIGINAL.blend` e o GLB recebido está preservado em `source/ORIGINAL_CAMISA.glb`.

Mantidos os 254.753 vértices e 460.706 triângulos no detalhe máximo, UV original e imagens originais. Ajustados largura, profundidade, altura e folga de 2 cm nos ombros para vestir o corpo. Pesos contínuos ligam tronco e mangas ao esqueleto GTA; os LODs distantes são simplificados. A exportação DDS utiliza o mesmo processo validado da calça.

Slot de teste: componente 11, coleção `Male_Heist`, drawable local 9, textura 0. Arquivos instalados com prefixo `mp_m_freemode_01_male_heist^` em `server-data/resources/cidade_roupas/stream`.

## Processo reutilizável

`export_config.json` configura componente, textura, modelo Blender e objeto. A conversão e auditoria usam os scripts compartilhados já validados:

```
python personagens/calca_bege/work/extract_textures.py personagens/camisa_estampada
blender --background --python personagens/calca_bege/work/export_fivem.py -- personagens/camisa_estampada
python personagens/calca_bege/work/audit/verify_pants_native.py personagens/camisa_estampada
```

Verificações: `work/validation.json` (UV e movimento), `work/audit/verification_native.json` (texturas, cores e pesos nativos), `preview_exportada.png` (arquivo exportado reimportado no Blender). A validação visual no FiveM fica com o jogador antes da próxima peça.
