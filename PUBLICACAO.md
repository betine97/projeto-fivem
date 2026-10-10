# Conteúdo deste repositório

Este primeiro envio versiona o código dos recursos FiveM, painéis, scripts de
produção, testes, documentação, configurações-modelo, projetos Blender, modelos,
texturas, prévias e exportações. Os arquivos grandes usam Git LFS no mesmo
repositório.

O GTA V e o cliente FiveM não são distribuídos aqui. Cada integrante usa sua
própria instalação do jogo e do FiveM. A base que este projeto fornece são os
recursos e sistemas do servidor; o FXServer é obtido separadamente dos artifacts
oficiais. Fontes Blender servem para editar os modelos e não são necessários
para executar o servidor. Veja `docs/EXECUTAR.md` para baixar só o runtime.
Os assets LFS de `server-data/resources` somam cerca de 2,6 GiB únicos nesta
primeira revisão. O acervo completo de criação é maior e fica no mesmo repositório.

Os arquivos originais continuam preservados no projeto local. Não entram no Git:

- Chaves Cfx.re, credenciais, banco de jogadores e marcações pessoais do editor.
- FXServer, dependências instaladas, caches, logs e backups de versões antigas.
- Dependências e extrações auxiliares que podem ser obtidas novamente.
- Componentes de terceiros já excluídos do projeto versionado, conforme
  `THIRD_PARTY.md`.

Para clonar com os modelos e texturas, instale Git LFS e execute `git lfs install`
antes do clone; em um clone existente, use `git lfs pull`. Para montar uma nova
instalação, obtenha o FXServer e instale as dependências dos scripts usados.
Crie suas próprias configurações privadas; não reutilize credenciais de outra
instalação. O serviço de captura gera seus índices locais a partir da instalação
do GTA V.

Os arquivos `iniciar-ilha.cmd`, `iniciar-los-santos.cmd`, `iniciar-painel.cmd` e
`iniciar-captura.cmd` iniciam os serviços correspondentes na instalação preparada.
A ilha usa a porta 30120 e Los Santos usa a porta 30121. O comando `editorilha`
abre o editor; `capturarobjeto` marca elementos em Los Santos ou Cayo Perico.

O Git LFS mantém os arquivos grandes no armazenamento LFS do GitHub e pequenos
ponteiros no histórico Git. O download desses arquivos depende da cota LFS da
conta que hospeda o repositório.
