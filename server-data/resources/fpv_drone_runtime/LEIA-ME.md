# Drone físico — como ver funcionando

## Ver agora, sem configurar servidor

Abra `demo_helices.mp4` ou `demo_helices.gif`: partida, quatro RPM independentes, efeito visual de alta rotação e desaceleração. O corpo fica fixo nessa demonstração para facilitar a inspeção das hélices.

Abra `demo_colisao.mp4` ou `demo_colisao.gif`: simulação de corpo rígido do Blender, com lançamento inicial contra uma parede, reação ao impacto e repouso. Não é voo keyframeado: após o lançamento, o solver de física calcula o movimento.

**As demonstrações são do Blender, não uma gravação do GTA/FiveM.** Elas não confirmam que os natives, a estabilidade de voo ou a rede estejam funcionando no jogo.

## Interagir no Blender já instalado

1. Abra o Blender e use **File → Open**.
2. Abra `demo_helices.blend` para ver as hélices, ou `teste_colisao.blend` para o impacto.
3. Aperte **Numpad 0** para olhar pela câmera. Aperte **Shift + seta esquerda** para voltar ao início e **Espaço** para reproduzir.
4. Em `demo_helices.blend`, selecione `DRONE_ROOT` no Outliner. Em **Object Properties → Custom Properties**, altere `motor_FL_rpm`, `motor_FR_rpm`, `motor_RL_rpm` ou `motor_RR_rpm`. A demonstração faz spin-up e começa a desligar aos 3 segundos. O blur é mais fiel no render/vídeo do que na visualização sólida.
5. Em `teste_colisao.blend`, volte sempre ao frame 1 antes de repetir ou mudar massa/colisão. A colisão é calculada durante a reprodução; não foi embutida na animação do asset.

O arquivo principal é **`drone_fisico.blend`**. Ele contém só o drone preparado, sem chão/parede de teste. Seu root é dinâmico; sem chão adicionado, ele cairá quando a simulação avançar. Para manter o drone imóvel enquanto inspeciona hélices, use o arquivo de demonstração.

## Testar no GTA V / FiveM

É necessário ter acesso a um servidor de desenvolvimento FiveM. O cliente instalado sozinho não carrega recursos Lua arbitrários em servidores de terceiros. Nenhum servidor foi instalado ou iniciado neste trabalho.

1. Extraia `fpv_drone_runtime.zip` na pasta `resources/[local]/` de seu servidor. O caminho resultante deve terminar em `fpv_drone_runtime/fxmanifest.lua`, sem uma pasta duplicada no meio.
2. Pare os recursos antigos: `fpv_drone`, `fpv_drone_texturizado` e `fpv_drone_industrial`, se estiverem ativos. Eles usam os mesmos comandos.
3. Adicione `ensure fpv_drone_runtime` ao `server.cfg`. Se o servidor já estiver aberto, execute `refresh` e depois `ensure fpv_drone_runtime` no console do servidor.
4. Conecte-se pelo FiveM. Se for seu servidor local, use F8 e `connect 127.0.0.1:30120`, respeitando a porta configurada no seu servidor.
5. Em uma área aberta, a pé, digite `/drone` no chat. O drone aparecerá à frente e cairá/assentará pela gravidade.
6. Use `/dronevoar` e mantenha **Espaço** para decolar. **WASD** inclina/move, **Q/E** gira, **Ctrl** desce.
7. **Backspace**, `/dronedesligar` ou `/dronevoar` novamente encerram a pilotagem e reduzem os motores gradualmente. O drone continua sujeito à gravidade: não congela no ar.
8. `/droneremover` limpa corpo, hélices, efeitos e câmera.

Testes adicionais:

- `/dronerpm FL 3000` controla apenas esse motor, sai do modo assistido e aplica empuxo individual. Aceita FL, FR, RL, RR; é esperado que um motor isolado faça o corpo tombar. Use `/dronedesligar` para zerar todos.
- `/droneimpacto` aplica um pequeno impulso fora do centro para testar torque/contato. Use perto de uma parede no servidor de testes.
- F8 mostra erros de Lua/carregamento. Se houver falha, registre o texto exato do erro para ajustar o recurso.

O recurso atual é **local por padrão**: serve para um jogador testar a física. Não inclui sincronização das hélices para outros jogadores, permissões de servidor ou persistência. Mudar `networked` para true não resolve a camada multiplayer; mantenha false nesta versão.

## O que foi implementado

- Quatro objetos PROP_FRONT_LEFT, PROP_FRONT_RIGHT, PROP_REAR_LEFT e PROP_REAR_RIGHT, com pivôs nos eixos e rotação em Z local. FL/RR CW; FR/RL CCW, vistos de cima. A geometria e os materiais originais foram preservados e comparados numericamente (`rig_preservation.json`).
- Hierarquia de componentes e `DRONE_ROOT` com massa de 1,8 kg. Centro de massa explícito em (0, 0, 0,005 m), abaixo da bateria e ligeiramente abaixo dos braços. `COM_REFERENCE` não renderiza.
- 13 proxies: corpo, quatro braços, quatro motores e quatro barras da gaiola. As barras mantêm a abertura do frame. No Blender, os motores usam cilindros; a exportação GTA usa caixas conservadoras para esses volumes.
- Um rigid body principal composto. Os proxies filhos descrevem formas; suas massas não são somadas como peças físicas independentes. Hélices sem colisão física.
- Blender: damping linear 0,10/angular 0,20; atrito 0,55; restituição 0,08; margem 0,5 mm; 12 substeps por frame a 60 FPS e 30 iterações.
- Runtime FiveM: corpo, quatro rotores e blur exportados separadamente. Gravidade ligada; forças nos motores, torque de reação e estabilização assistida. Nenhuma atribuição de posição/rotação/velocidade do corpo a cada frame. O ângulo das hélices integra RPM usando deltaTime com resposta exponencial.
- Configuração em `fpv_drone_runtime/config.lua`. Integração testada a 30, 60 e 144 Hz com resultados equivalentes. Faixas RPM: 0/1000/3000/6000/9000/12000.
- Eventos locais `fpv_drone:impact` (velocidade estimada e faixa de dano) e `fpv_drone:predictedContact`. Nenhuma destruição visual.
- Exportação GLB com hierarquia, pivôs e metadados. **glTF não transfere automaticamente o rigid body para qualquer engine**: configure a física na engine usando `physics_config.json`; reconheça/oculte os objetos COL_* como colisores. Não renderize esses proxies como peças do drone.

## Validação e limites concretos

O teste Blender lança o drone a aproximadamente 3 m/s contra uma parede. O centro não ultrapassou y=0,495 m, antes da face em y=0,56 m. Houve mudança de orientação e, no último segundo analisado, deslocamento em repouso igual a zero. Não houve posição não finita nem instabilidade numérica. Dados em `physics_test_results.json`.

O teste cobre o conjunto composto em um cenário; não certifica todos os ângulos, obstáculos finos ou velocidades. No Blender foi usado aumento de substeps, não uma promessa de CCD nativo. No FiveM há varreduras preditivas nos motores e um impulso preventivo para aproximações acima de 4 m/s, além do contato da engine; esse mecanismo também precisa de teste real e não equivale a CCD contínuo garantido.

Os arquivos YDR/YTYP passaram em exportação e releitura (`runtime_export_validation.json`). Não houve execução em FiveM: sustentação, amortecimento, atrito/restituição efetivos do GTA, estabilidade do controlador, transparência e resposta dos natives permanecem pendentes de calibração. Os valores Blender de atrito/restituição não são copiados automaticamente ao GTA. O tensor de inércia da exportação é calculado a partir dos proxies.

Os shaders básicos GTA continuam com as limitações visuais descritas nas versões anteriores; o `.blend` preserva os materiais completos. A malha detalhada permanece com cerca de 92 mil triângulos, sem LODs. O blur é uma aproximação visual. As pás mantêm a geometria original; não houve remodelagem de passo aerodinâmico CW/CCW.

## Fontes primárias usadas

- [Blender: colisões rigid body](https://docs.blender.org/manual/en/latest/physics/rigid_body/properties/collisions.html)
- [Cfx: forças e torque](https://github.com/citizenfx/natives/blob/master/ENTITY/ApplyForceToEntity.md)
- [Cfx: parâmetros físicos de objeto](https://github.com/citizenfx/natives/blob/master/OBJECT/SetObjectPhysicsParams.md)
- [Cfx: centro de massa](https://github.com/citizenfx/natives/blob/master/PHYSICS/SetCgoffset.md)
- [Cfx: varredura por cápsula](https://github.com/citizenfx/natives/blob/master/SHAPETEST/StartShapeTestCapsule.md)

Tudo foi feito com ferramentas gratuitas e dependências isoladas em `work/`, sem serviços pagos ou alterações na instalação do jogo.
