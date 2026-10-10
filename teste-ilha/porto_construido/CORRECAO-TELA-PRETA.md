# Tela preta com camera e colisao ativas — 9/10/2026

O cliente confirmou a camera de gameplay ativa, fade desligado, personagem na pista e chao a 18 m. O problema reproduzido estava no documento NUI do painel ADM: `:root{color-scheme:dark}` fazia o navegador compor um fundo opaco mesmo com `#app` oculto e `body` transparente.

Em `server-data/resources/cidade_admin/ui/style.css`, o documento agora usa `color-scheme:normal`, e o tema escuro fica restrito a `#app`. O painel conserva sua aparencia e seus controles.

O teste renderizou o HTML real em um frame sobre uma cena de cor conhecida. Antes, os pixels do frame fechado eram RGB 18,18,18; depois, a cena por tras aparece, inclusive apos abrir e fechar o ADM. Os cinco checks do frame, a verificacao de pixels, os 20 checks da interface e os 38 checks Lua do painel passaram. O teste antigo da tecla Escape foi ajustado para aguardar a resposta assincrona do modal antes de verificar o fechamento.

O servidor foi reiniciado e os recursos `cidade_admin`, `teste_ilha` e `porto_esperanca` estao ativos na porta 30120. A confirmacao visual da correcao no FiveM depende da proxima conexao. A divergencia da contagem de agua continua pendente e nao foi tratada como causa desta tela preta.

Backup: `backups/correcao_nui_20261009/cidade_admin_style.css`. Evidencias: `dados/nui_adm_antes.png`, `dados/nui_adm_depois.png`, `dados/nui_adm_aberto.png`, `dados/nui_adm_fechado.png`, `dados/teste_nui_transparencia.json` e `dados/teste_nui_pixels.json`.
