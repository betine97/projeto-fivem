# Hospital de Carcer Way

O conjunto de torres marcado nos prints corresponde a `bh1_22_towerw`, centrado aproximadamente em `-475, -322`. O hospital novo usa esse terreno. O hotel vizinho permanece.

A estrutura foi modelada no Blender com fachada creme, detalhes verde-água e dourados, coroamento escalonado, cruz, marquises e jardins. São dois pisos e 32 salas, além da recepção e espera. Há consultórios, triagem, cirurgia, exames, radiologia, tomografia, laboratório, farmácia, enfermaria, UTI, recuperação, óbitos, descanso, reunião e conversas médicas, vestiários e sanitários.

O arquivo `hospital_carcer_editavel.blend` contém os modelos editáveis. As texturas estão em `textures/`. O recurso instalado está em `server-data/resources/cidade_hospital_carcer`.

As portas de correr usam **E** para abrir/fechar e sincronizam entre os jogadores. A escada fica na extremidade direita da recepção. Digite `hospital` no **F8** para ir à entrada. O recurso usa colisões físicas e texturas DDS comprimidas com mipmaps. Mobiliário e vegetação possuem versões simplificadas para distância. Os recursos próprios do hospital ocupam de 72 KiB a cerca de 17,3 MiB descomprimidos por arquivo, sem os modelos gigantes anteriores.

Foram removidas as torres e suas versões distantes e noturnas, com recortes nas colisões e na oclusão da área. Dois arquivos compartilhados com o mapa do castelo foram atualizados preservando os recortes anteriores; os originais estão em `backup_instalacao`. Não há intervenção nova no sistema de chuva/névoa.

Reinicie a base e reconecte o FiveM para carregar a substituição completa. As prévias são renders do Blender; ainda falta conferir o resultado no jogo. `verification.json`, `native_validation.json` e `runtime_validation.json` registram as verificações geométricas, a leitura dos arquivos pelo CodeWalker e os testes das portas.
