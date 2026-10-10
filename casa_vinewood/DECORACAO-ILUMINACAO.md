# Vasos, spots embutidos e LED na escada

Revisão `tapete-quadros-noite-2026-10-08`, seguindo as referências enviadas.

- 17 vasos de plantas nativos do GTA, em três modelos, distribuídos pela sala, jantar, cozinha, hall, escritório, sala de jogos, mezanino, leitura, quartos, closet e banheiros.
- 88 spots de 14 cm, com aro discreto e difusor emissivo, ajustados ao teto real de cada ambiente. Luz quente aproximada de 3000 K.
- 20 fitas LED nos 18 degraus e nos dois patamares, com perfil fino sob as bordas.
- Tapete Meshy de 6,20 × 5,10 m sob o sofá e a mesa de centro, com espessura visual de 16 mm. A malha foi reduzida de 6.057.414 para 45.000 triângulos; UVs preservadas, albedo e normal em 4K com mipmaps. Sem colisão para evitar tropeços.
- Quatro quadros nativos distintos no térreo: dois no hall junto ao escritório, um no hall junto à sala e um no jantar. Molduras orientadas para os ambientes e afastadas 11 mm da parede.

O jogo usa os vasos e suas texturas originais. Os modelos nativos são referenciados por um mapa adicional, sem substituir assets do GTA. Os spots e perfis LED são exportados em um drawable sem colisão, para não criar obstáculos. As colisões originais dos vasos continuam ativas.

O script limita a iluminação dinâmica a 18 spots próximos, seis deles com sombras, e acende os LEDs da escada nas proximidades. Os spots usam RGB 255/211/156 e chegam a quatro vezes a intensidade diurna entre 20h e 5h. Há transições graduais entre 18h–20h e 5h–8h. Os LEDs da escada sobem moderadamente (1,45×) à noite. Todos os difusores e fitas permanecem visíveis na geometria. Os pendentes existentes continuam ativos.

`mansao_iluminada.blend` é a nova cena editável com a decoração. As cenas e assets anteriores permanecem preservados. `verificacao_decoracao_iluminacao.json` contém a verificação dos arquivos nativos, trajetos com as colisões reais dos vasos e comportamento do script; `instalacao_decoracao_iluminacao.json` confirma cópia e hashes.

As imagens `noite_tapete_sala.png` e `noite_quadros_hall.png` são prévias Blender. A luz do FiveM precisa de confirmação visual no jogo, especialmente a intensidade e as sombras. Os testes executam o script Lua real com horários diurnos, noturnos e transições, além de conferir os arquivos nativos e 29 trajetos com as colisões da casa, vasos e quadros.

Para carregar, execute `restart cidade_mansao` no console do servidor e reconecte no FiveM. A instalação não reinicia o servidor.
