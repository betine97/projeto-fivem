# Trabalho da equipe

| Branch | Uso |
| --- | --- |
| `main` | Versão de produção validada |
| `develop` | Integração e ambiente compartilhado de desenvolvimento |
| `codex/eron` | Base de trabalho de Eron (`betine97`) |
| `codex/renan` | Base de trabalho de Renan (GitHub a informar) |
| `codex/balthor` | Base de trabalho de Balthor (GitHub a informar) |
| `codex/<pessoa>/<funcionalidade>` | Uma alteração específica |

As branches pessoais começam na mesma revisão de `develop`. Para cada
funcionalidade, crie uma branch curta e um PR para `develop`:

```sh
git fetch origin
git switch develop
git pull --ff-only
git switch -c codex/renan/minha-funcionalidade
python tools/ci.py
git push -u origin codex/renan/minha-funcionalidade
```

Renan e Balthor precisam receber acesso ao repositório quando seus usuários forem
informados. Ter uma branch não concede acesso. Atualize `CODEOWNERS` depois disso.

Use PRs pequenos. A CI `validar` precisa passar antes da integração. Faça um PR
de `develop` para `main` após validar no FiveM. Mudanças em Blender/texturas devem
informar os arquivos modificados e o impacto em colisão, LOD e memória. Arquivos
Blender são binários: combine quem editará cada arquivo para evitar conflitos.

O workflow **Preparar ambiente** é manual. Selecione `develop` + `dev` ou
`main` + `prod`. Ele testa a revisão, baixa somente os assets de runtime e
publica uma imagem no GHCR com a revisão no nome, além de um kit sem segredos.
Assim, a mesma revisão pode ser instalada e revertida de forma explícita.

Em Settings → Environments, mantenha `dev` restrito a `develop` e `prod` a
`main`. Para produção, configure aprovação de Eron quando o plano GitHub permitir.
Em Settings → Rules/Branches, proteja `main` e `develop` com PRs e a verificação
`validar`. Habilite uma revisão obrigatória quando a equipe já tiver acesso.
As configurações do GitHub são externas aos arquivos YAML; confirme-as no repo.

Credenciais ficam no `.env` da máquina ou em secrets do ambiente. A imagem
e o artifact de preparação não carregam senhas, chaves Cfx.re ou dados de jogadores.

Referência: [ambientes e regras de implantação do GitHub](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments).
