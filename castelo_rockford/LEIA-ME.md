# Castelo de Rockford Hills — terreno liberado

Recurso instalado: `server-data/resources/cidade_castelo_livre`.

Remove o castelo de três torres e sua garagem destacados com X nas imagens. O recorte inclui telhados, janelas, varanda, escadaria de entrada, estruturas de apoio, acessórios da construção, colisões, oclusão e versões distantes. Mantém a quadra de tênis, o perímetro do lote e construções vizinhas. O espaço descoberto recebeu piso com material do próprio lote e colisão para caminhar.

## Medidas registradas

- Envelope do modelo do lote: aproximadamente **78,77 × 60,95 metros**. São limites do modelo original, não um levantamento cadastral.
- Área liberada: aproximadamente **1.155,38 m²**, incluindo castelo, varanda, entrada e garagem.
- Projeção dos telhados: aproximadamente **562,98 m²**.
- Referência do lote: **X -955,21; Y 209,95; Z 66,17**.
- Altura do piso preenchido: **Z 66,47**.

Coordenadas dos limites e do polígono: `medidas.json`.

## Ativação

A linha `ensure cidade_castelo_livre` está no `server-data/server.cfg`. O recurso inicia junto com o servidor na próxima inicialização.

Para ativar agora, digite no **console do servidor**, um comando por linha:

```text
refresh
ensure cidade_castelo_livre
```

Depois, desconecte e entre novamente no FiveM para recarregar os arquivos do mapa. Esses dois comandos são para o console do servidor, não para o F8 do jogador.

## Verificação realizada

Os 18 arquivos nativos foram carregados pelo CodeWalker. A checagem dos oito arquivos de colisão da região não encontrou superfícies das construções no volume liberado; utiliza tolerância de 3 cm nas bordas devido à quantização nativa. Foram comparados 34 membros não alterados dos dicionários de modelos. O piso exportado tem 376 triângulos e altura conferida.

Foi renderizada uma prévia geométrica no Blender. **Ainda falta conferir o resultado dentro do jogo**, principalmente a caminhada nas transições entre o piso novo e o original. Nenhum servidor ou sessão do jogador foi reiniciado automaticamente.

Relatórios: `alteracoes.json`, `geometry_verificacao.json` e `codewalker_verificacao.json`. Fontes extraídas preservadas em `originais/`; arquivos originais da instalação do GTA não foram alterados.

## Reversão

Remova ou comente apenas a linha `ensure cidade_castelo_livre` em `server-data/server.cfg`, reinicie o servidor e reconecte o cliente. O mapa original do GTA volta a ser utilizado. A cópia do arquivo de configuração anterior à instalação está em `backup/server.cfg`.
