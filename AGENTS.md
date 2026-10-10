# Orientações para qualquer Codex trabalhando neste projeto

Leia `docs/EXECUTAR.md` antes de instalar ou iniciar serviços e `CONTRIBUTING.md`
antes de criar branches. Use português brasileiro com a equipe.

## Estrutura e comandos

- Recursos ativos: `server-data/resources/`. Painel: `painel_acesso/app.py`.
- Captura compartilhada Los Santos/Cayo: `captura_los_santos/service.py`.
- Assets e fontes Blender fazem parte do repositório e usam Git LFS.
- Configure `.env.dev` ou `.env.prod` a partir de `.env.example`; não imprima
  credenciais, não versione dados privados e não copie a instalação de Eron.
- Validação rápida: `python -m pip install -r requirements-ci.txt` e
  `python tools/ci.py` (Python 3.13 e Node 22).
- Preparação: `python tools/bootstrap.py --environment dev --write-env`.
- Docker dev: `docker compose --env-file .env.dev -f compose.yaml -f compose.dev.yaml up --build`.
- Docker prod: `docker compose --env-file .env.prod -f compose.yaml -f compose.prod.yaml up -d --no-build`.

Não reinicie nem encerre processos do jogo ou servidores já em uso sem necessidade
e autorização da tarefa. Não use Ctrl+C em um console compartilhado do Windows.
O ambiente Docker dev usa portas diferentes da instalação atual.

## Qualidade

Preserve a identidade visual Cayo Perico, qualidade dos modelos, colisões,
LODs e desempenho. Não resolva desaparecimento de vegetação simplesmente
criando milhares de objetos de alta resolução permanentemente ativos.
Teste alterações de persistência/autorização com mocks e valide mudanças visuais
no jogo. Se não tiver FiveM/Blender/Docker funcionando, registre o limite da
validação sem alegar que uma inspeção visual ocorreu.

Mantenha `.gitignore`, `.gitattributes` e `THIRD_PARTY.md`. A CI não baixa assets
LFS; baixar assets de runtime é tarefa do workflow de preparação ou da instalação
local. Nunca envie ponteiros sem os respectivos objetos ao armazenamento LFS.
