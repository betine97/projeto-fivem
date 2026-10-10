# Movimento e mira — revisão v9 (histórico)

**Revisão atual: v11.** Veja [os controles e a validação v11](v11/LEIA-ME.md).
Ela usa C pressionado, rastejo lateral e novas animações de deslocamento.
As instruções abaixo documentam a revisão anterior.

Implementado em `cidade_core`. As animações foram refeitas em cópias dos arquivos
Blender e exportadas para seis dicionários YCD. As fontes anteriores v5/v6 e os
encaixes individuais da carabina/fuzil foram preservados.

## Controles

- **Segurar C:** andar agachado com WASD, armado ou desarmado. Soltar C levanta.
  A mira, o tiro e a recarga nessa postura usam o comportamento nativo do GTA.
- **Z:** deitar. W/S rasteja para frente/trás; A/D muda a direção do corpo.
  Funciona desarmado e com a carabina/fuzil já suportados pelo projeto.
- **Deitado com carabina/fuzil:** botão direito mira; esquerdo dispara; R recarrega.
  É possível mirar e disparar durante o rastejar. A recarga pausa o movimento.
- **Z novamente:** levanta passando pelo ajoelhado; **C deitado:** levanta direto.
- **F8 `agachar`:** alterna o agachamento sem precisar segurar C.
- **F8 `ajoelhar`, `ajoelhar2` ou `ajoelharteste`:** conserva a pose ajoelhada
  estacionária. Backspace ou `levantar` encerra a postura.
- **Alt:** olhar ao redor. Não dispara enquanto olha livremente.

## Ângulos

A arma e as duas mãos acompanham a inclinação, com os seguintes limites para
as poses autorais da carabina/fuzil:

| Postura | Para baixo | Para cima |
|---|---:|---:|
| Deitado, parado ou rastejando | −8° | +35° |
| Ajoelhado estacionário | −45° | +45° |

O agachamento com C usa os limites de mira nativos do GTA. As poses autorais
continuam específicas para `WEAPON_CARBINERIFLE` e `WEAPON_ASSAULTRIFLE`.

O tronco da animação nativa `move_crawl` tem orientação diferente da pose
estacionária. A mira de rastejar compensa a posição do esqueleto em 28 fases de
avanço e 32 de recuo, com 44 amostras de inclinação por fase. A tarefa nativa
continua responsável pelo deslocamento e pelas pernas.

O personagem mantém colisão e gravidade normais. O módulo não o teleporta nem
desativa sua física. Antes de um ciclo de rastejar, consulta piso, desnível e uma
cápsula de obstáculos; consultas pendentes não autorizam avanço.

## Validação e aplicação

- `runtime_validation.json`: controles, carregamento cancelável, saída segura,
  troca armado/desarmado, 36 ciclos de tiro/recarga, recuperação de pose e seis
  condições que bloqueiam uma rota. Natives simuladas, sem afirmar teste físico.
- `binary_validation.json`: todos os 270 quadros das quatro miras estacionárias
  decodificados de volta dos YCD reais e comparados às fontes Blender.
- `crawl_binary_validation.json`: 5.280 amostras de mira/rastejo decodificadas e
  recompostas sobre o esqueleto nativo. Erro máximo de inclinação inferior a 0,001°.
- Regressões existentes de cobertura: 45 cenários; encaixe de armas: 12 matrizes.
- Pré-visualizações dos arquivos decodificados em `exports/`.

**Ainda falta o teste visual e de deslocamento dentro do FiveM.** Os seis YCD
ficam em `server-data/resources/cidade_core/stream`. Para carregar esta revisão,
use `restart cidade_core` no console do servidor; depois reconecte se o cliente
mantiver algum dicionário antigo em cache. O servidor inteiro não foi reiniciado.

Antes de testar a movimentação, desligue `voar`/`noclip`. Confira C/WASD armado e
desarmado; Z/W/S/A/D; mira nos limites; tiro; R durante movimento; saída com C/Z;
passagens estreitas, sacada, escada e transição para cobertura com Q.

Backup anterior em `backup_v8/`. Para voltar apenas esta alteração, restaure
`prone.lua` desse backup e remova `posture_movement.lua` da lista de scripts do
manifesto atual. Preserve outras alterações feitas no manifesto depois do backup.
Os novos YCD podem permanecer no stream sem serem usados pela revisão anterior.

As referências nativas foram lidas da instalação local do GTA. O arquivo
`native_move_crawl.ycd` em `exports/` serve somente à validação local e não foi
incluído no stream.
