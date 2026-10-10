# Apenas luminárias do teto

A pedido do usuário, os preenchimentos gerais e as luzes decorativas da mansão foram removidos. Apenas os 88 spots brancos e os pendentes amarelos indicados nos prints iluminam o ambiente. As fontes nativas existentes desses aparelhos foram reconfiguradas para feixes estreitos para baixo, com abertura calculada pela altura da lâmpada até o piso. Raio direto no chão: 1,10 m nos spots/cilindros e 0,80 m no linear. Intensidade entre 7 e 15, pelo menos 4,44 vezes a anterior; alcance com margem além do piso. Esses parâmetros não garantem aparência visual ou FPS antes da avaliação no FiveM.

Retirados: 19 preenchimentos nativos, quatro fontes nativas do aparador, todos os reforços Lua e as fontes locais do bar/adega. Também foram desativados nove materiais emissivos decorativos (cozinha, bar, adega, escada, aparador e substituto da fachada). As lentes das luminárias do teto continuam acesas. Não existem luzes de volume/coronas ou novos filtros de atmosfera. Clima, mapas, arquétipos, manifesto, móveis, texturas, colisões e posições salvas não foram alterados.

Os comandos `luzmansao` e `mansaoluzes` mostram o modo atual. Argumentos antigos de reforço não criam fontes. Não há loop Lua de iluminação ou seleção por cômodo; as fontes nativas permanecem constantes em todos os horários.

Verificação: dados nativos lidos por pymateria/szio e pelo leitor independente CodeWalker; 388 amostras geométricas dos feixes no piso, cores/tipos/ângulos/intensidade conferidos, preservação exata de malhas, índices, UVs, normais, cores, texturas e colisão. Todo o recurso foi examinado para excluir outras fontes de luz e emissão decorativa. Comandos e scripts executados com mocks que rejeitam qualquer desenho ou thread de luz.

Após instalar, execute `restart cidade_mansao` no console do servidor. Feche completamente o FiveM e conecte novamente. A revisão visual no jogo e medição de FPS permanecem pendentes.

Backup em `backup/`, pacote em `package/`, fontes `build.py`, `controller.lua`, testes `verify.py` e `verify_codewalker.ps1`. `install.py` protege contra alterações concorrentes nos alvos e verifica todos os arquivos não relacionados. Relatórios: `verification.json`, `codewalker_verification.json`, `installation_verification.json`.

Referência das flags usadas: [Sollumz — Light Flags](https://docs.sollumz.org/2.6/documentation/lighting-.ydr/light-flags).
