# Lidera — notas de impressão e montagem

## Escala e limite da reprodução

O objetivo é um boneco de **180 mm de altura, sem a base**, dividido em peças por cor e montado depois da impressão. A imagem fornecida mostra várias vistas de uma ilustração, mas não contém cotas, seções ou detalhes internos. A geometria CAD é uma interpretação dessas vistas. A fidelidade de proporções e acabamento deve ser avaliada no modelo; as articulações são uma proposta de engenharia para impressão e não um mecanismo extraído da imagem.

A base CAD tem 126 mm de diâmetro e 11 mm de altura; o conjunto sobre a base chega nominalmente a 191 mm. O casco da cabeça mede 101,4 × 67,6 × 70,2 mm, começa a 95,8 mm acima dos pés e utiliza duas metades brancas com parede nominal de 3,9 mm. As antenas levam a altura do boneco a 180 mm. Corpo e membros foram proporcionados para destacar a cabeça grande da referência.

Características visuais prioritárias:

- Cabeça grande e arredondada; casco branco, faixa azul-marinho no topo e na parte traseira.
- Visor azul-marinho com contorno ciano; olhos grandes com branco, íris ciano, pupila escura e brilho; sobrancelhas ciano e sorriso com dentes brancos e língua rosa.
- Discos laterais concêntricos em branco, azul-marinho e ciano; duas antenas de haste azul-marinho e esfera ciano.
- Peitoral branco com a marca Lidera extraída do SVG oficial; cintura azul-marinho e pequenos detalhes ciano no pescoço e na borda do peitoral.
- Braços e pernas segmentados, com carenagens brancas e juntas azul-marinho; mão estilizada com detalhe circular ciano na palma.
- Botas brancas com ponteira e sola azul-marinho; base circular com topo branco e faixa ciano na lateral.

As poses da referência ajudam a avaliar a silhueta, mas não demonstram a amplitude ou a resistência de uma articulação. Olhos, sorriso e logotipo são elementos decorativos fixos. Letras pequenas como “Tecnologia e Gestão” exigem avaliação em escala real: com bico de 0,4 mm, uma impressão ou decalque costuma reproduzi-las melhor que letras minúsculas em plástico.

## Marca oficial no peito

O arquivo `assets/logo_lidera_vetor01.svg` conserva a arte original enviada. Os contornos cúbicos, os vazios e a proporção foram transferidos para o CAD sem trocar a fonte. A aplicação mede 38 × 20,30 mm e está centralizada sobre a face plana do peito. São cinco componentes de cor (`logo_*`): nome, subtítulo e três elementos do símbolo. O nome e o símbolo têm relevo de 0,70 mm; o subtítulo, 0,55 mm.

O subtítulo tem altura total de 1,76 mm, com minúsculas de aproximadamente 0,98 mm e traços de 0,18–0,32 mm. A espessura do relevo não aumenta a largura desses traços. Recomenda-se **decalque da marca completa** com bico de 0,4 mm: use `exports/decal_logo_escala_real.pdf` a 100%, confira a régua de 50 mm e aplique sobre o peito branco, omitindo os cinco componentes em relevo. O `exports/logo_peito_38mm.svg` também está em escala real. Ambos preservam os degradês do SVG oficial. Bico de 0,2 mm pode melhorar as letras em plástico, mas a legibilidade e os pequenos vazios ainda precisam ser conferidos no fatiador e em uma prova física.

Nos componentes 3D, a marca usa cores sólidas: violeta-azulado `#3F4096`, ciano intermediário `#0BB5F3` e coral `#E74E3B`. Esses tons não equivalem a um degradê de filamento. Para colar letras soltas, use um gabarito impresso a 100% do SVG; não altere a escala de cada arquivo STL individualmente.

## Bambu Lab A1

A A1 tem volume nominal de **256 × 256 × 256 mm**. O boneco de 180 mm cabe em altura; as peças devem ser distribuídas em várias placas conforme a cor e a orientação. Confirme no Bambu Studio o tamanho final de cada peça, incluindo brim, suporte e base. Não é necessário AMS Lite para imprimir peças separadas por cor.

Ponto de partida com bico de 0,4 mm:

| Parâmetro | Recomendação inicial |
|---|---|
| Material das carenagens e decoração | PLA ou PLA+ de boa qualidade |
| Camada | 0,16 mm no corpo; 0,12 mm no rosto e nos detalhes |
| Paredes do modelo nas regiões resistentes | Pelo menos 2,4 mm quando a geometria permitir |
| Perímetros no fatiador | 3–4 para decoração; 5–6 nas peças com pivôs |
| Preenchimento | 15–20% gyroid no corpo; 30–50% nas regiões de juntas, com modificadores locais se necessário |
| Temperatura e fluxo | Perfil do fabricante do filamento, após calibração de fluxo |
| Suportes | Somente onde necessários; preferir apoio em superfícies escondidas |
| Brim | Útil para antenas, peças pequenas e elementos altos |
| Compensações XY/furo | Começar no perfil calibrado; ajustar após imprimir o cupom de folga |

PLA+ facilita acabamento e detalhes. PETG pode ser usado nas peças estruturais de articulação por sua tenacidade, mas pode precisar de mais folga, menor velocidade e melhor controle de fios. A seleção de material não substitui uma validação mecânica. Evite PLA em locais quentes, como um carro ao sol.

## Encaixes e pivôs

Os valores de referência do projeto são **furo de 3,3 mm para parafuso M3**, **lingueta de 4,8 mm** e **vão de 5,4 mm**. A diferença de 0,6 mm fornece **0,3 mm de folga nominal de cada lado**. A precisão real depende do material, da orientação e da calibração da impressora. Esses valores não são garantia de encaixe ou movimento livre.

O conjunto inclui três cupons: `cupom_furos_M3` com furos de 3,2 / 3,3 / 3,4 mm, `cupom_clevis_5p4` e `cupom_lingueta_4p8`. Imprima os três antes do boneco, no material e no perfil escolhidos para as juntas. Verifique se a lingueta gira sem raspar e se o parafuso M3 atravessa sem forçar as camadas. Remova apenas rebarbas; se necessário, regularize cuidadosamente o furo com broca de 3,3 mm. Uma junta excessivamente apertada deve ser corrigida antes da impressão do conjunto completo.

O projeto prevê **13 pivôs M3**: pescoço, dois ombros, dois cotovelos, dois punhos, dois quadris, dois joelhos e dois tornozelos. O pescoço gira em torno do eixo vertical Z; os 12 pivôs dos membros têm eixo Y, com movimento no plano XZ. São juntas de um eixo, não juntas esféricas com movimento livre em todas as direções. Cada mão possui quatro dedos fixos: três dedos e um polegar. A pose exibida no modelo não confirma a amplitude total de movimento.

Como lista inicial de ferragens, separe 13 porcas M3, parafusos M3 e arruelas: **um M3 × 16 mm para o pescoço** é uma estimativa; **12 M3 × 20 mm para os membros** são uma seleção inicial. Os suportes dos membros, incluindo os punhos, têm largura nominal total de 11,4 mm antes das arruelas e da porca. Os quadris possuem rebaixo de 6,2 mm para a cabeça do parafuso e alojamento hexagonal de 6,8 mm de diâmetro circunscrito para a porca. Confira o comprimento no pacote real de cada junta. No pescoço, o assento da cabeça do parafuso está em z = 86,75 mm e o início do alojamento da porca em z = 98,8 mm; uma arruela pode mudar o comprimento necessário. O parafuso deve engatar toda a porca sem atingir a decoração ou bloquear outra peça. Aperte apenas o suficiente para segurar a posição sem esmagar as peças. Não deixe a rosca cortar diretamente a lingueta móvel quando houver alternativa com trecho liso ou bucha.

As carenagens dos membros são meias-capas abertas, separadas por cor, que se colam ao esqueleto azul-marinho. O CAD usa folga nominal de 0,18 mm na cavidade dessas capas; ela é diferente da folga das juntas móveis e também precisa de montagem a seco. Nas botas, a sola e a lingueta do tornozelo formam a estrutura; as capas laterais e a ponteira são decorativas.

Cola serve para unir os elementos decorativos por cor. Ela não deve atingir furos, eixos, linguetas ou superfícies que precisam mover. Antes de colar, faça uma montagem a seco para conferir os lados, as cores e o acesso aos parafusos. Cianoacrilato em pequena quantidade pode esbranquiçar o acabamento; teste em uma sobra e use produto compatível com o plástico.

## Orientação e montagem

1. Imprima os três cupons de tolerância e ajuste o perfil se necessário.
2. Separe as placas por material e cor: branco, azul-marinho e ciano; olhos, sorriso e marca podem acrescentar branco, preto, rosa, coral e violeta-azulado em peças pequenas ou acabamento superficial.
3. Priorize a face visível livre de suportes. Na máscara facial, cabeça e botas, compare as orientações no fatiador para preservar superfícies curvas e reduzir marcas.
4. Posicione linguetas e suportes dos pivôs para reduzir esforços que separem as camadas. Inspecione no fatiador o material em torno de cada furo; o sentido de impressão deve ser escolhido por peça.
5. Faça montagem a seco de todas as carenagens. Para o pescoço, coloque a porca M3 no alojamento interno da cabeça **antes de fechar as duas metades do casco**. Insira o parafuso **por baixo do torso, antes de colar a pelve**. O torso possui furo passante de 3,3 mm e acesso inferior de 6,2 mm para a cabeça do parafuso. Confira se a sua cabeça de parafuso e sua ferramenta cabem nesse acesso. Posicione os colares ciano e azul, engate a porca e ajuste a fricção do pescoço com a cabeça ainda acessível.
6. Monte os demais pivôs com as ferragens, verifique interferências e ajuste o aperto. Após conferir o pescoço, una torso e pelve pelos dois pinos de alinhamento e pela face de colagem. Não deixe cola entrar no pescoço ou nos quadris. Feche a cabeça; as orelhas e a tampa azul superior cruzam sua união e devem ser montadas depois. Preserve o acesso interno sempre que possível para manutenção da porca.
7. Cole as decorações fixas com as superfícies limpas. Instale antenas por último para reduzir risco de quebra durante a montagem.
8. Confira o equilíbrio sobre a base e a retenção dos pés antes de expor o boneco. Não force posições bloqueadas por carenagens ou articulações.

## Checklist de revisão

- [ ] A altura do boneco sem base corresponde a 180 mm.
- [ ] A silhueta da cabeça, visor, orelhas, botas e base se aproxima das vistas da imagem.
- [ ] O visor, os olhos, a boca e a identificação estão legíveis em escala de impressão.
- [ ] Cada peça cabe na placa da A1 com a orientação e os suportes escolhidos.
- [ ] Os STLs importados no Bambu Studio têm escala correta e apresentam volumes fechados.
- [ ] O cupom demonstra folga suficiente para o material e o perfil usados.
- [ ] A contagem e o comprimento das ferragens são conferidos no CAD e na montagem a seco.
- [ ] A porca interna e o parafuso do pescoço estão montados e ajustados antes de fechar a cabeça e colar a pelve.
- [ ] Não há cola, rebarba ou suporte nas superfícies móveis.
- [ ] As juntas mantêm a pose sem apertar a ponto de esmagar camadas.
- [ ] O conjunto permanece estável na base e não apresenta interferências ao mover manualmente.

Estas notas são recomendações de fabricação. Não houve impressão física, ensaio de resistência ou teste real de movimento; esses itens continuam necessários para validar as folgas, a montagem e a estabilidade do protótipo.
