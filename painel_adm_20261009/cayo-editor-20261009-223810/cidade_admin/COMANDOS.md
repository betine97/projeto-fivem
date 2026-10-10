# Comandos ADM no F8

Digite os comandos sem `/`. Os IDs são os IDs permanentes do painel de acesso, e não o número temporário da conexão. Os jogadores autorizados no painel recebem ADM, conforme a configuração atual da cidade.

| Comando | Função |
|---|---|
| `admin` | Ajuda com exemplos de uso. |
| `comandos` | Lista os comandos dos recursos ativos da cidade. |
| `comandos arma` | Filtra a lista de comandos. |
| `jogadores` | Jogadores online: ID, nome, coordenadas e instância. |
| `onde 2` ou `localizar 2` | Localização, região, distância e marcador no mapa para o ID 2. |
| `rastrear 2` | Atualiza o marcador e a posição do ID 2 a cada 2 segundos. |
| `pararrastreio` | Encerra o acompanhamento. |
| `encontrar 2` | Teletransporta você até o ID 2. |
| `chamar 2` | Traz o ID 2 até você. |
| `armas` | Catálogo de armas válidas nesta versão do jogo. |
| `armas pistola` | Filtra o catálogo de armas. |
| `arma pistola 120` | Entrega uma pistola a você com 120 munições. |
| `arma WEAPON_CARBINERIFLE 250` | Aceita também nomes completos de armas. |
| `desarmar` | Remove suas armas. |
| `veiculos` | Catálogo de veículos por categoria. |
| `veiculos moto` | Filtra o catálogo por nome/categoria. |
| `veiculos todos` | Lista todos os modelos registrados, incluindo veículos personalizados. |
| `veiculo adder` | Cria um veículo e coloca você no banco do motorista. |
| `veiculo ambulance` | Cria uma ambulância. |
| `veiculo buzzard` | Cria um helicóptero. |
| `carro sultan` ou `car sultan` | Alternativas de `veiculo`. |
| `dv` | Remove seu último veículo criado. |
| `coords` | Sua posição e direção. |
| `id` | Seu ID permanente. |
| `reviver`, `voar`, `noclip` | Comandos já existentes na cidade. |
| `mansao`, `hospital` | Acessos aos mapas instalados. |

Uma nova localização com `onde` encerra o rastreamento anterior. Um jogador rastreado que sair da cidade perde o marcador. O próximo veículo criado substitui o anterior criado por você. Os comandos de armas e veículos recebem autorização do servidor antes da execução.

## Carregar a atualização

O `server.cfg` já inicia o ADM automaticamente. Como o servidor estava aberto durante a instalação, os novos arquivos precisam ser carregados. No console **do servidor**, execute:

```text
refresh
ensure cidade_acesso
ensure cidade_admin
restart cidade_core
```

A autorização do painel será refeita em até 5 segundos. `restart cidade_core` pode reinicializar o personagem; execute com os jogadores avisados. Como também há uma atualização do mapa do hospital, reiniciar a base e reconectar o FiveM carrega o conjunto completo.

Os testes automáticos verificaram permissões, IDs, rastreamento, armas, veículos e a comunicação entre os recursos. A execução visual no FiveM ainda precisa ser conferida.
