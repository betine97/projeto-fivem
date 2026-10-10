# Parede do aparador — referência fornecida em 08/10/2026

Conjunto modelado no Blender exclusivamente para a parede marcada entre a
adega e a cozinha: dois quadros abstratos com molduras bronze e arandelas,
aparador de madeira suspenso com LED inferior, vaso com ramos de oliveira,
vaso pequeno, tigela preta, livros, objeto cerâmico e molduras de parede.
Porta de madeira com visor de vidro fumado, puxadores pretos e dobradiças;
abre e fecha com E usando o sistema de portas existente.

O conjunto respeita a abertura original de 1,10 × 2,50 m e mantém 85 mm de
folga da adega perpendicular. A porta tem colisão no espaço da dobradiça e
abre para dentro. Não há colisão fixa atravessando o vão. Nenhuma geometria
arquitetônica existente foi alterada.

- `parede_aparador_editavel.blend`: componentes separados e editáveis.
- `mansao_parede_aparador.blend`: cópia da cena com o conjunto encaixado.
- `parede_instalada_blender.png`: prévia no Blender; não é captura do FiveM.
- `stream/`: cinco arquivos nativos destinados à instalação.
- `verification.json`: geometria, shaders nativos, texturas, colisões e LODs.
- `installation.json`: hashes instalados e preservação dos arquivos atuais.
- `backup_preinstall/`: cópias dos três arquivos compartilhados modificados.

Os dois modelos têm quatro LODs. O conjunto tem 9.812 triângulos na maior
definição; a porta tem 1.848. As telas usam texturas BC1 de 512 × 1.024 com
mipmaps, reconstruídas com geração de imagens a partir da referência.
Quatro luzes nativas quentes alimentam apenas as arandelas e o LED do aparador,
sem iluminação volumétrica, coronas ou alteração da iluminação geral.

Instalação: cinco novos assets, registro adicional no manifesto, uma nova
entrada de porta e proteção dos dois modelos no editor de objetos. As portas
anteriores, os objetos salvos e os demais assets permanecem preservados.

Para carregar no servidor já aberto, executar `ensure cidade_mansao` no console
do servidor e reconectar ao FiveM. A aparência final no jogo ainda requer
verificação após a recarga do recurso.
