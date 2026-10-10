# Controles conferidos e troca da mesma arma corrigida

O comando de selecionar uma arma pode restaurar os clipsets em pé mesmo quando
o hash da arma não muda. Os comandos `arma` e `desarmar` agora notificam o módulo
de movimento, que reaplica imediatamente o agachamento quando estiver ativo.

Controles da revisão instalada nos arquivos:

- C alterna agachado/em pé, com ou sem arma. Soltar C mantém o agachamento.
- Shift acelera o passo agachado; WASD continua usando a colisão nativa.
- Z deita. W/S rasteja para frente/trás; A/D vira durante o rastejo.
- Deitado, C muda para agachado; Z levanta pela transição animada.
- Sacar/guardar carabina ou fuzil preserva a postura deitada, inclusive em movimento.
- R recarrega sem levantar; deitado, a recarga pausa temporariamente o rastejo.
- A busca de cobertura foi removida; Q não inicia cobertura a pé.

Agachado e em pé, armas/mira/recarga usam o sistema nativo. A mira deitada autoral
tem animações e encaixes específicos para CARBINERIFLE e ASSAULTRIFLE.

Validação: quatro scripts Lua analisados; seis YCD instalados conferidos por
hash; testes de controles/troca/rastejo e 24 ciclos de tiro e recarga aprovados.
Relatório desta correção: `correcao_troca_arma_validacao.json`.
Os testes simulam natives; não substituem o teste visual e físico no FiveM.

O último log consultado ainda mostrava `v9-movimento-mira-vertical`.
Para ativar, execute `restart cidade_core` no console do servidor e reconecte.
Nenhum processo de servidor foi reiniciado durante esta correção.

Backup local anterior ao ajuste: `backup_correcao_troca_mesma_arma/`.
