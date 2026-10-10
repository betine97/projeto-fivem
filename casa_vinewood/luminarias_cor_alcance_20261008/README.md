# Correção das luminárias — 08/10/2026

Instalação em `server-data/resources/cidade_mansao`, com backup anterior neste diretório. O pacote altera só três drawables de iluminação e cinco arquivos de configuração/controlador/documentação; mapas, arquétipos, manifesto e posições de objetos salvas permanecem iguais.

Problemas confirmados nos arquivos anteriores:

- `luzes_pendentes.lua` estava desativado e o projeto nativo não continha luzes dos pendentes.
- Os spots tinham apenas emissão em um núcleo de 8 mm, sem fonte luminosa associada. As chaves dos programas emissivos não correspondiam à chave `emissive` de uma lâmpada original do GTA.
- O projeto usava 68 pontos, muitos altos, com intensidade elevada e grande sobreposição; as fontes esféricas também iluminavam para cima. Isso é compatível com o excesso de branco nas imagens, embora não prove que todo o aspecto nublado era bloom.
- As posições dos seis pontos antigos dos cilindros misturavam médias de tampas inferiores e superiores. Agora os pontos ficam logo abaixo das tampas inferiores medidas da própria geometria.

Correções: 88 spots brancos dirigidos para baixo, nove fontes amarelas nos dois conjuntos de pendentes, 19 preenchimentos baixos suaves. As lentes dos spots são emissivas em branco em quatro LODs; pendentes têm emissão moderada para conservar o amarelo. Alcance cobre o piso real abaixo de cada spot, inclusive a sala de pé-direito duplo. Fontes constantes em todas as horas, sem seleção por cômodo; apenas uma fonte usa sombras. Volumes luminosos e coronas zero, sem mudança de clima ou filtros. A proteção climática adiada continua removida.

Validação: importação/exportação nativa e leitor independente CodeWalker; cores, direção, alcance, constantes de horário e materiais conferidos. 3.098 amostras de cobertura geométrica em pisos/altura do personagem, 45 casos Lua de deslocamento/horário, câmera de drone e limite do reforço. Dados da malha, UVs, normais, índices e colisão preservados; só dois programas emissivos, intensidade de emissão e a lente branca foram alterados entre os materiais/texturas.

Esses testes não medem exposição, aparência, limites de luzes simultâneas da GPU ou FPS dentro do GTA. A quantidade de fontes nativas aumentou de 68 para 116 para ligar cada luminária; não há novas chamadas Lua por quadro no padrão e as sombras passaram de três fontes a uma. Avaliação visual e de desempenho no FiveM permanece pendente.

Após instalação: no console do servidor, `restart cidade_mansao`. Feche completamente o FiveM e conecte novamente. F8 `luzmansao 1` é o padrão; `luzmansao 1.5` a `2` adiciona preenchimento baixo; `mansaoluzes` imprime quantidades, clima observado e índices de filtros. Não restaura proteção contra chuva/névoa nem muda o tempo exterior.

Referência técnica primária para flags: [Sollumz — Light Flags](https://docs.sollumz.org/2.6/documentation/lighting-.ydr/light-flags). Também foi comparada localmente a lâmpada nativa `v_res_fa_lamp1on.ydr` do GTA para confirmar o programa emissivo, o tipo SPOT e ângulos serializados em graus.

Arquivos: `build.py` prepara, `verify.py` verifica, `verify_codewalker.ps1` faz a leitura independente, `install.py` instala com proteção contra alterações concorrentes. Relatórios em `verification.json`, `codewalker_verification.json`, `installation_verification.json`; projeto em `projeto.json`.
