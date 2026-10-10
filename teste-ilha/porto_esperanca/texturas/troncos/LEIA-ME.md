# Troncos e galhos enviados pelo usuário

Recebidos em 09/10/2026: **16 recortes PNG, RGBA, 1.254 × 1.254 pixels**, acompanhados da prancha de 18 categorias de vegetação. As folhas serão enviadas em outro lote.

## Arquivos preservados

- `originais/`: cópias sem alteração de pixels, com identificadores estáveis por lote.
- `referencias/catalogo_usuario_18_especies.png`: catálogo enviado junto aos troncos.
- `manifesto.json`: caminhos e nomes de origem, dimensões, transparência, hashes SHA-256, descrições e associações provisórias.

Os 17 arquivos copiados foram decodificados e comparados com os originais por SHA-256. Os nomes curtos das cópias não substituem os nomes de origem registrados no manifesto.

## Uso nos modelos

As imagens mostram troncos e galhos completos, com silhueta e iluminação. Servem como referência de forma, cor, nós, cicatrizes e detalhes da casca. Para usá-las como materiais de superfície em malhas 3D, será necessário preparar as regiões úteis da casca e ajustar o mapeamento UV. O recorte inteiro não é um mapa plano repetível de casca.

A sequência do primeiro lote sugere correspondência com as categorias 01 a 10 da prancha, mas os arquivos não informam o nome da espécie. As dez associações iniciais foram usadas na versão separada `porto_esperanca_texturas_lote01.blend` depois do recebimento das folhas; a aparência e as associações aguardam validação do usuário. No segundo lote, as associações foram sugeridas pela aparência, incluindo palmeiras, bananeira, caules múltiplos, mangue e arbustos; esses seis recortes ainda não foram aplicados. A numeração desse lote não corresponde automaticamente aos IDs da prancha.

Existem 18 categorias na prancha enviada e 24 modelos distintos no pacote Blender, considerando a outra prancha aprovada anteriormente. Os 16 recortes recebidos não estabelecem, por si só, uma associação individual confirmada para todos os modelos.

## Estado e continuidade

Os originais estão organizados. Em 09/10/2026, após o envio das primeiras dez imagens de folhas e a autorização para começar com elas, dez troncos receberam materiais de imagem via UV na versão separada `porto_esperanca_texturas_lote01.blend`. O arquivo procedural anterior foi preservado. Ver `../folhas/LEIA-ME.md` para associações, técnica, arquivos e limites. Nenhum arquivo do servidor foi substituído nesta aplicação Blender.

Ao preparar a aplicação, relacionar troncos e folhas, criar materiais próprios por modelo e ajustar o UV apenas das superfícies correspondentes. Manter folhas, pseudocaules de bananeira e casca lenhosa separados. Validar primeiro uma árvore completa em uma amostra do cenário, preservando a cena anterior.
