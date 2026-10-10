# Continuidade com poucas leituras

1. Ler LEIA-ME.md e o job.json do trabalho, não todos os experimentos antigos.
2. Confirmar a base em pipeline.py bases e reutilizar seu cache. Só bases OK.
3. Guardar imagens do usuário em inputs; separar referência completa de atlas UV e recortes.
4. Registrar posição/medidas/hipóteses de cada componente. Frente -Y; esquerda do personagem +X.
5. Usar rota de textura ou surface_patch quando adequada. Não remodelar nem recalcular automaticamente os pesos da base.
6. Para movimento, implementar um adaptador por variação com YDR/YTYP e regras próprias. A especificação motion.json não constitui física pronta.
7. Executar check/build, corrigir erros antes de exportar, inspecionar quatro vistas e flexões; não alegar detecção de interseções que não foi executada.
8. Candidatos em exports não são recursos instaláveis sem YMT/shop metadata e confirmação da coleção no game build.
9. Não escrever nos arquivos base, slots nativos, tags ou favoritas. Testar a variação pelo recurso/comando próprio; não herdar OK da base.
10. Mostrar comparação e dar instruções de teste curtas. Registrar resultados reais e só repetir checagens afetadas por nova mudança.
11. Quando solicitado, publicar no tablet usando register_exclusive.py após instalar e verificar o pacote. O manifesto exclusives.json separa variações das bases. Exclusivas aparecem sem herdar a tag OK; roupas nativas continuam exigindo OK. Usar miniaturas do modelo final, não a imagem de referência.
