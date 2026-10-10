# Posturas — v11

Esta revisão substitui os controles v10. Modifica somente `posture_movement.lua`,
`prone.lua` e adiciona dois YCD ao stream de `cidade_core`.

- **Segurar C:** permanecer agachado, armado ou desarmado. **Soltar C:** levantar.
  Pressionar novamente enquanto já segura não alterna a postura. Soltar durante
  o carregamento cancela a entrada. O comando de diagnóstico `agachar`, sem tecla
  associada, continua disponível separadamente.
- **C + Shift + W/S/A/D:** passo agachado rápido para frente, trás e lados.
  Há versões de braços livres e de arma, com deslocamento na própria animação.
  Sem Shift, permanece a locomocação agachada nativa. A recarga nativa pausa o
  passo rápido e pode terminá-lo sem levantar; depois retoma se as teclas continuam
  pressionadas. Soltar C, Shift ou a tecla de movimento encerra a tarefa correspondente.
- **Z:** deitar. **W/S:** rastejar para frente/trás. **A/D:** deslocar para os lados,
  mantendo a direção do corpo. Nenhuma tecla de movimento significa ficar parado.
  A leitura de teclado usa as teclas pressionadas, sem reaproveitar eixos antigos.
  No controle, usa o analógico. As animações atuais escolhem uma das quatro direções
  do corpo; dois eixos simultâneos usam o eixo predominante.
- Deitado, pode sacar/guardar os fuzis suportados (`WEAPON_CARBINERIFLE` e
  `WEAPON_ASSAULTRIFLE`), mirar, disparar e recarregar. A recarga pausa o rastejo.
  **C deitado:** entra no agachamento enquanto C permanece pressionado; soltar levanta.
  **Z novamente:** levanta usando a transição existente.

## Animações e correções

`cidade_deitado_move_v11.ycd` contém uma pose imóvel e quatro movimentos de rastejo.
A pose imóvel tem todos os quadros iguais e **nenhuma trilha de deslocamento**.
Usar o clipe nativo `onfront_fwd` como pose parada deixou uma trilha de rastejo
no clipe; amostrar uma fase fixa não era garantia de imobilidade no GTA.

Os quatro movimentos foram trabalhados no Blender sobre o esqueleto nativo. Os
movimentos laterais incluem apoio alternado de pernas/braços. As trilhas de
deslocamento são horizontais, têm sentido explícito e nenhuma rotação acumulada.
As máscaras de mira existentes foram recompostas sobre os novos movimentos para
preservar as duas mãos e a orientação dos fuzis.

`cidade_agachado_move_v11.ycd` contém oito movimentos rápidos: quatro direções
armadas e quatro com braços livres. Partem das animações nativas de agachamento,
com trilhas ajustadas para 1,75 m/s à frente e 1,40 m/s nas demais direções. Esses
valores são medidos nos dados da animação; não são uma medição ao vivo do GTA.
O ajuste anterior de taxa/blend não garantia a seleção de uma passada mais rápida.

Colisão e gravidade permanecem ativas; não há teleporte/deslocamento por coordenadas.
Consultas de piso, desnível e obstáculos validam a rota. Ao rastejar, as consultas
abrangem cabeça, tronco e pés, inclusive durante deslocamento lateral. Consultas
pendentes ou falhas não autorizam um novo movimento. Cobertura permanece removida.

## Arquivos e validação

- `sources/posturas_direcionais_v11.blend`: fonte com as 13 ações. Não altera nomes,
  tags, parentesco ou matrizes de repouso do esqueleto. As fontes anteriores foram preservadas.
- `build_locomotion.py`: construção Blender/Sollumz.
- `exports/`: XML, YCD e XML relido de cada binário.
- `previews/`: imagens renderizadas dos dados relidos.
- `test_runtime.py` / `runtime_validation.json`: testes com natives simuladas,
  incluindo teclas, cancelamento, troca de armas, obstáculos, saídas e 24 ciclos
  de disparo/recarga da regressão anterior.
- `validate_binary.py` / `binary_validation.json`: verifica todos os quadros,
  sentidos/velocidades do mover, ausência de mover na pose parada e 10.208 amostras
  das mãos dos fuzis sobre os quatro movimentos de rastejo.

**Ainda não foi testado fisicamente dentro do FiveM.** Os arquivos ficam instalados
em `server-data/resources/cidade_core`. Para carregar os dois novos YCD e scripts,
execute `restart cidade_core` no console do servidor e reconecte o cliente.
O console F8 deve mostrar `v11-segurar-c-rastejo-direcional` ao agachar/deitar.

O backup dos dois scripts anteriores está em `../backup_v10_hold_direcoes/`.
Para retornar aos controles antigos, restaure somente esses dois scripts desse backup.
Os arquivos YCD v11 podem permanecer sem uso. Não é necessário restaurar manifesto,
configuração do servidor ou outros recursos.
