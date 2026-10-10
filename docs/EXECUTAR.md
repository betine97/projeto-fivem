# Rodar Minha Cidade em outra máquina

Este é o documento de entrada para Eron, Renan, Balthor e qualquer Codex.
O servidor contém a ilha autoral, Cayo Perico, o editor e um servidor Los Santos
separado. O cliente FiveM/GTA continua sendo executado no Windows; o Docker
executa os serviços do servidor, não o cliente do jogo nem a interface Blender.

## 1. Clonar e preparar

Instale Git + Git LFS, Python 3.13 e Node 22 para validações. Para Docker, use
Docker Engine com Compose no Linux ou Docker Desktop com containers Linux.
Reserve espaço para o clone completo (cerca de 28 GB de arquivos), o cache LFS
e as imagens Docker; 80 GB livres são uma margem prática para esse trabalho.

```sh
git lfs install
git clone https://github.com/betine97/projeto-fivem.git
cd projeto-fivem
git switch develop
python -m venv .venv
```

Ative o ambiente: PowerShell `./.venv/Scripts/Activate.ps1`; Linux
`source .venv/bin/activate`. Instale e confira:

```sh
python -m pip install -r requirements-ci.txt
python tools/ci.py
```

Para trabalhar só em código, clone com `GIT_LFS_SKIP_SMUDGE=1` no ambiente e
baixe posteriormente apenas o runtime:

```sh
git lfs pull --include="server-data/resources/**" --exclude=""
python tools/bootstrap.py --check-assets
```

## 2. Configurar o ambiente privado

```sh
python tools/bootstrap.py --environment dev --write-env
```

O comando cria `.env.dev`, gera segredos diferentes e não sobrescreve um arquivo
existente. Complete `FIVEM_LICENSE_KEY` com uma chave própria do portal Cfx.re.
Defina `FXSERVER_ARTIFACT_URL` com a URL exata do `fx.tar.xz` Linux oficial e
`FXSERVER_ARTIFACT_SHA256` com o SHA-256 do arquivo. URLs de versões fixas evitam
que cada máquina instale um servidor diferente. Em produção, o checksum é exigido.

Obtendo o hash de um download verificado: PowerShell
`(Get-FileHash ./fx.tar.xz -Algorithm SHA256).Hash.ToLower()`; Linux
`sha256sum fx.tar.xz`. Os dados privados ficam em volumes separados por
`COMPOSE_PROJECT_NAME`; não reutilize as chaves/bancos da máquina de Eron.

Consulte a [instalação Linux oficial do FXServer](https://docs.fivem.net/docs/server-manual/setting-up-a-server-vanilla/)
e os [artifacts Cfx.re](https://runtime.fivem.net/artifacts/fivem/build_proot_linux/master/).

## 3. Docker em desenvolvimento

A implementação atual mantém os bridges em `127.0.0.1`; por isso o Compose usa
rede do host. No Linux isso funciona diretamente. No Docker Desktop 4.34 ou
posterior, habilite **Settings → Resources → Network → Enable host networking**
e use containers Linux. Veja a [documentação Docker](https://docs.docker.com/engine/network/drivers/host/).

```sh
docker compose --env-file .env.dev -f compose.yaml -f compose.dev.yaml config --quiet
docker compose --env-file .env.dev -f compose.yaml -f compose.dev.yaml up --build
```

O código local é montado no container. Reinicie somente o recurso alterado pelo
console FXServer, ou o container se alterar um serviço Python. A versão do
FXServer fica no volume `/state`; os dados do painel/editor/captura são volumes
independentes. O processo termina os demais serviços se algum deles falhar,
evitando uma instância aparentemente pronta com o painel desligado.

| Ambiente | Ilha | Los Santos | Painel local | Captura local |
| --- | --- | --- | --- | --- |
| Dev Docker | 30220 TCP/UDP | 30221 TCP/UDP | 8887 | 8888 |
| Prod padrão | 30120 TCP/UDP | 30121 TCP/UDP | 8787 | 8788 |

No FiveM, F8: `connect 127.0.0.1:30220` para dev. Use `30221` para Los Santos.
O painel fica em `http://127.0.0.1:8887`. Entre com a senha do `.env.dev`,
aprove o ID do personagem e então use `editorilha` ou `capturarobjeto`.
A política atual concede ADM aos jogadores aprovados; esta base é para equipe
de desenvolvimento. Reveja essa política antes de abrir o servidor a jogadores.

Para um servidor remoto, use seu IP e a porta correspondente. O painel fica
restrito a loopback; use um túnel SSH, por exemplo
`ssh -L 8787:127.0.0.1:8787 usuario@servidor`, em vez de expor a administração.

## 4. Captura de novos modelos

O catálogo incluído no Git funciona sem uma instalação de GTA no container.
Para identificar novos objetos nativos e criar miniaturas, configure
`GTA_HOST_PATH` com a pasta da sua instalação **GTA V Legacy**, montada somente
para leitura em `/gta`. Windows aceita caminhos com `/`, por exemplo
`C:/Program Files (x86)/Steam/steamapps/common/Grand Theft Auto V`.
Sem GTA, mantenha a pasta vazia `.state/gta` criada pelo bootstrap.

Defina `ENABLE_CAPTURE_INDEX=1` antes da primeira inicialização. A indexação
dos RPF/mapas demora e usa CPU/disco; só é feita se o índice ainda estiver vazio.
Também pode ser executada explicitamente com o container ativo:

```sh
docker compose --env-file .env.dev -f compose.yaml -f compose.dev.yaml exec cidade python captura_los_santos/build_index.py
docker compose --env-file .env.dev -f compose.yaml -f compose.dev.yaml exec cidade python captura_los_santos/build_world_index.py
docker compose --env-file .env.dev -f compose.yaml -f compose.dev.yaml restart cidade
```

Miniaturas usam Blender em modo background, Pillow, NumPy e szio. O container
inclui essas ferramentas. As miniaturas no Linux sem monitor usam Xvfb e
renderização por software; o Docker também instala NumPy para o Python próprio
do Blender. No Windows, configure `GTA_ROOT` e `BLENDER_BIN` para a instalação
local e instale `requirements-runtime.txt`. Não redistribua a
instalação do GTA dentro da imagem. Os índices/seleções pessoais são gerados localmente.

## 5. Preparação por GitHub Actions e produção

A CI testa PRs e mudanças em main/develop sem baixar os modelos grandes; branches
de funcionalidade são verificadas pelo PR para evitar execuções duplicadas. O workflow manual
**Preparar ambiente** baixa apenas os assets de `server-data/resources`, executa
a CI e cria a imagem `ghcr.io/betine97/projeto-fivem:<ambiente>-<sha>` com cache
de build. Ele entrega um kit Compose + `.env.example` sem segredos; não inicia
nem altera servidores automaticamente. Na primeira execução, habilite Actions
e confira a permissão de publicação do pacote GHCR no repositório.

Se o pacote GHCR for privado, autentique a máquina com `docker login ghcr.io`
usando um token com `read:packages`. No kit baixado, siga `LEIA-ME.txt`: a
configuração específica recebe o nome `compose.environment.yaml`. Crie também
`.state/gta` vazio se a captura não usar uma instalação GTA nesta máquina.

Use o kit ou prepare `.env.prod` com
`python tools/bootstrap.py --environment prod --write-env`. Preencha as
credenciais, o artifact fixo/checksum e `CITY_IMAGE` com a imagem da revisão:

```sh
docker compose --env-file .env.prod -f compose.yaml -f compose.prod.yaml pull
docker compose --env-file .env.prod -f compose.yaml -f compose.prod.yaml up -d --no-build
docker compose --env-file .env.prod -f compose.yaml -f compose.prod.yaml ps
docker compose --env-file .env.prod -f compose.yaml -f compose.prod.yaml logs --tail=100
```

Dev/prod usam nomes e volumes diferentes. O runtime prod é somente leitura,
com dados persistentes nos volumes e rotação de logs. Faça backup dos volumes
do painel, editor e captura antes de atualizar. Reversão: use a imagem da revisão
anterior em `CITY_IMAGE` e execute `up -d --no-build`; preserve os volumes.
Se mudar o esquema de dados, siga a migração específica e restaure o backup quando necessário.
Nunca use `down -v` para uma atualização comum: isso apaga dados persistentes.

Defina `SERVER_HOST` no `.env` com o IP/hostname que os amigos usam para alcançar
o servidor (IP da VPN ou IP público, sem protocolo e sem porta). O painel mostra
os comandos F8 com esse host e as portas específicas do ambiente; o padrão
`127.0.0.1` serve para jogar na própria máquina.

## 6. Execução Windows existente

Os scripts `iniciar-ilha.cmd`, `iniciar-los-santos.cmd`, `iniciar-painel.cmd` e
`iniciar-captura.cmd` preservam a instalação local atual. Em uma máquina nova,
instale FXServer Windows em `.runtime`, Python (os launchers atuais usam
`C:/Python313/python.exe`) e Blender. Crie `server-data/secrets.cfg` a partir
do exemplo e execute `python painel_acesso/app.py --setup` para o bridge privado.
O servidor Los Santos também precisa de `spawnmanager` e `cidade_core` em sua
pasta de recursos; mantenha as dependências locais documentadas em `PUBLICACAO.md`.
Docker é o caminho preparado para evitar esses caminhos Windows fixos em uma máquina nova.

## Diagnóstico

- Falta de assets: `git lfs pull --include="server-data/resources/**" --exclude=""`.
- Erro de conexão “painel indisponível”: confira `/health`, logs e chave do bridge.
- Porta ocupada: use os valores de dev; não encerre a instalação atual de outra pessoa.
- Docker sem engine: inicie Docker Desktop/Engine antes do Compose.
- Editor/miniaturas pendentes: confira montagem GTA, índice e logs da captura.
- Não alegue validação visual se o cliente FiveM não foi aberto e inspecionado.
