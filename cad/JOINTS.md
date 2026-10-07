# Articulações Lidera — ferragens e montagem

Este guia detalha as **13 juntas do boneco de 180 mm**: um pescoço e dois ombros, cotovelos, punhos, quadris, joelhos e tornozelos. As peças brancas, azul-marinho e ciano são impressas; **parafusos, porcas e arruelas de aço são ferragens comerciais, compradas separadamente**. O pescoço também usa uma arruela deslizante recortada de lâmina de PTFE ou PET. São 52 componentes de ferragens no STEP; eles servem para entender a montagem e não devem ser impressos em plástico.

As vistas técnicas estão em [Guia_articulacoes_M3.pdf](../exports/Guia_articulacoes_M3.pdf). Mostram cortes locais e peças afastadas ao longo do eixo para explicar a montagem. O afastamento da vista explodida não é uma medida de montagem nem a amplitude de movimento.

A [montagem explodida em STEP](../exports/Articulacoes_explodidas.step) permite girar os sete exemplos de juntas em um visualizador CAD. São recortes locais das estruturas e ferragens reais, dispostos em uma grade de inspeção. Não são peças completas para impressão. No pescoço, os cascos frontal e traseiro aparecem separados pela união em Y; a porca é colocada lateralmente nessa união, pois o teto do alojamento impede a saída axial.

## Ferragens

| Item | Medida nominal do projeto | Quantidade |
|---|---|---:|
| Parafuso de cabeça cilíndrica com sextavado interno | ISO 4762 M3 × 16 mm; passo 0,5 mm; cabeça Ø5,5 × 3 mm | 13 |
| Porca sextavada M3 normal | ISO 4032: 5,5 mm entre faces; altura 2,4 mm; passo 0,5 mm | 13 |
| Arruela estreita para M3 | DIN 433 / ISO 7092: externo Ø6; interno Ø3,2; espessura 0,5 mm | 25 |
| Arruela deslizante do pescoço | Lâmina de PTFE ou PET: externo Ø12; interno Ø3,3; espessura 0,3 mm | 1 |

São duas arruelas de aço externas por junta dos membros e uma sob a cabeça do parafuso do pescoço. A porca do pescoço se apoia diretamente no alojamento interno da cabeça. A arruela deslizante de 0,3 mm fica entre o ressalto do torso e o fundo da cabeça; não é uma arruela DIN nem uma peça FDM de 0,3 mm. Uma arruela M3 comum com diâmetro externo de 7 mm não substitui automaticamente a estreita de 6 mm: os acessos rebaixados do modelo têm Ø6,2 mm. Porcas autotravantes com inserto de náilon são mais altas e não substituem diretamente as porcas normais de 2,4 mm.

O comprimento de 16 mm é medido **sob a cabeça até a ponta**, sem incluir os 3 mm de altura da cabeça. Confira no fornecedor as dimensões reais da cabeça, da porca e das arruelas. Use uma cabeça dentro do envelope nominal Ø5,5 × 3 mm dos acessos representados. Uma cabeça escareada altera o apoio e não é uma substituição direta.

Use chave Allen de 2,5 mm compatível com o parafuso adquirido e chave de boca de 5,5 mm para as porcas dos membros. No pescoço, a ferramenta entra pelo fundo do torso: use o braço longo da chave, com pelo menos 25 mm de alcance útil antes de instalar a pelve, ou cerca de 45 mm para acesso pelo furo de serviço após unir a cintura. Uma chave ou soquete largo pode não passar pelo acesso de Ø6,2 mm. O furo de serviço da pelve tem Ø4 mm; ele dá passagem à haste da chave, não à cabeça do parafuso.

Os comprimentos e posições descritos são nominais do CAD. Confirme encaixe e acesso às ferramentas na montagem a seco. Este guia não fornece torque de aperto validado para plástico impresso.

## Como funciona a junta dos membros

Cada junta possui um **suporte com duas orelhas**, fixo ao segmento anterior, e uma **lingueta central**, fixa ao segmento seguinte. O parafuso atravessa os três furos alinhados; as duas arruelas ficam do lado de fora das orelhas.

**Insira a lingueta pela abertura radial do suporte**, aproxime-a do centro do pivô e alinhe os furos. Ela não atravessa axialmente uma orelha. Só então passe o parafuso ao longo do eixo Y. Na vista explodida, a lingueta foi afastada para fora do suporte para mostrar esse caminho; os afastamentos das ferragens ao longo do eixo são apenas de exibição.

| Região | Dimensão nominal |
|---|---:|
| Espessura de cada orelha | 3,0 mm |
| Vão entre as orelhas | 5,4 mm |
| Espessura da lingueta móvel | 4,8 mm |
| Folga de montagem de cada lado da lingueta | 0,3 mm |
| Largura total das duas orelhas e do vão | 11,4 mm |
| Furo para M3 nas peças impressas | Ø3,3 mm |

Da frente do boneco para trás, a sequência é:

**cabeça do parafuso → arruela → orelha frontal → lingueta entre as orelhas → orelha traseira → arruela → porca.**

Na região central existe uma folga de 0,3 mm antes e depois da lingueta; ela não recebe as arruelas externas. A soma axial é 11,4 + 0,5 + 0,5 + 2,4 = **14,8 mm** da face sob a cabeça até o fim da porca. Com M3 × 16, a projeção nominal da ponta além da porca é **1,2 mm**. A rosca representada no CAD é uma referência de montagem; o engate real é feito pelas ferragens comerciais M3.

Comece com a porca frouxa. O parafuso deve entrar com os furos alinhados, sem ser usado para abrir ou deformar o furo. Aperte em pequenos incrementos até controlar a folga e confira o movimento. Não feche à força a folga entre orelhas e lingueta: isso pode flexionar as orelhas ou separar as camadas. A retenção de uma pose depende da impressão, do material e do ajuste; ela ainda não foi ensaiada fisicamente.

## Eixos e peças de cada junta

O boneco fica de pé sobre o plano Z = 0, a frente é −Y e a parte de trás é +Y. Os 12 pivôs dos membros giram em torno de Y, portanto seus movimentos estão no plano XZ. O pescoço gira em torno de Z. Cada mão tem quatro dedos fixos; os dedos e as capas coloridas não acrescentam juntas.

E e D abaixo correspondem aos nomes `left` e `right` do CAD; E usa X negativo e é o lado da mão levantada. A tabela lista as peças estruturais que recebem a ferragem, não todas as capas decorativas do segmento.

| Junta | Qtd. | Suporte fixo | Lingueta / peça móvel | Eixo |
|---|---:|---|---|---|
| Ombro | 2 | `torso_branco` | `left_upper_arm_frame` / `right_upper_arm_frame` | Y |
| Cotovelo | 2 | `left_upper_arm_frame` / `right_upper_arm_frame` | `left_forearm_frame` / `right_forearm_frame` | Y |
| Punho | 2 | `left_forearm_frame` / `right_forearm_frame` | `left_hand_navy` / `right_hand_navy` | Y |
| Quadril | 2 | `pelve_azul` | `left_thigh_frame` / `right_thigh_frame` | Y |
| Joelho | 2 | `left_thigh_frame` / `right_thigh_frame` | `left_shin_frame` / `right_shin_frame` | Y |
| Tornozelo | 2 | `left_shin_frame` / `right_shin_frame` | `left_boot_sole_and_joint` / `right_boot_sole_and_joint` | Y |
| Pescoço | 1 | `torso_branco`, com seus colares | `head_white_front_shell` + `head_white_rear_shell` | Z |

Nos membros, as cabeças dos parafusos ficam orientadas para −Y e as porcas para +Y. Cabeças e porcas são parte do acabamento metálico visível; não devem ser cobertas por cola. O raio menor do pivô do punho, de 4,5 mm, não muda o pacote axial de 11,4 mm.

Os quadris possuem acesso rebaixado de Ø6,2 mm para cabeça e arruela. No lado traseiro há um assento de Ø6,3 mm para a arruela, alojamento hexagonal de 6,8 mm de diâmetro circunscrito (aproximadamente 5,89 mm entre faces) para a porca e acesso de Ø8,4 mm atrás dela para instalação e ferramenta. A porca comercial tem 5,5 mm entre faces. Faça o teste com as ferragens reais antes de colar a pelve ou as capas.

## Pescoço e seus acessos

O pescoço usa um parafuso vertical, inserido **por baixo do torso**, e uma porca alojada **dentro do casco da cabeça**. A cabeça do parafuso fica escondida no acesso inferior do torso; a porca fica escondida no interior da cabeça.

Na posição montada, as referências nominais em Z são:

| Elemento | Intervalo / posição em Z |
|---|---|
| Cabeça do parafuso | 83,25 a 86,25 mm |
| Arruela sob a cabeça do parafuso | 86,25 a 86,75 mm |
| Haste M3 × 16 | 86,25 a 102,25 mm |
| Final do ressalto do torso | 95,50 mm |
| Arruela deslizante de PTFE / PET | 95,50 a 95,80 mm |
| Fundo do casco da cabeça | 95,80 mm |
| Apoio da porca dentro da cabeça | 98,80 mm |
| Porca M3 | 98,80 a 101,20 mm |
| Projeção nominal da ponta além da porca | 1,05 mm |

O furo central é Ø3,3 mm; o acesso inferior tem Ø6,2 mm. O espaço nominal de 0,30 mm entre o ressalto do torso e o casco recebe a arruela deslizante. Verifique a espessura real da lâmina e mantenha essas superfícies livres de cola para a cabeça girar.

A porca fica presa contra rotação no alojamento hexagonal da cabeça. **Cabeça, porca e parafuso devem girar juntos como um conjunto**, deslizando no apoio de PTFE/PET e no apoio inferior da arruela de aço. O giro do pescoço não deve ocorrer soltando ou apertando a rosca: se o parafuso girar em relação à porca, a fricção muda e a junta pode se soltar ou travar.

Depois de ajustar a fricção com a cabeça aberta, use trava-rosca removível de baixa resistência **somente na conexão metal–metal entre parafuso e porca**, conforme o produto escolhido. Aplique quantidade mínima, longe do plástico e das arruelas deslizantes, e respeite a cura do fabricante antes de girar o conjunto. Não use cola para prender o eixo ao torso ou à arruela; essas interfaces precisam deslizar. O travamento de rosca e a fricção final ainda precisam ser verificados fisicamente.

**Monte o pescoço antes de colar torso e pelve e antes de fechar a cabeça.** Depois da união, o furo central de serviço de Ø4 mm da pelve permite passar a haste de uma chave Allen de 2,5 mm para ajustar o aperto. Ele não permite retirar a cabeça de Ø5,5 mm do parafuso; a troca completa poderá exigir separar torso e pelve. Não cubra esse acesso com cola. Os dois cascos da cabeça têm pinos de alinhamento; as orelhas e a tampa superior cruzam a união, por isso são instaladas depois de fechar os cascos.

## Ordem de montagem

1. **Calibre os encaixes.** Imprima os três cupons em `exports/cupons/`, com o material e o perfil das estruturas. Teste Ø3,2 / 3,3 / 3,4 mm com seu M3 e o par lingueta 4,8 / vão 5,4 mm. Remova rebarbas e confira os furos; não force o parafuso através das camadas.
2. **Confira as ferragens.** Meça a cabeça, a porca e as arruelas. Monte um conjunto sobre o cupom. Verifique se a ponta passa pela porca e se a cabeça e a ferramenta entram nos acessos de Ø6,2 mm.
3. **Prepare os esqueletos.** Separe E e D pelas etiquetas dos arquivos. Faça montagem a seco das capas brancas e ciano. Mantenha todas as faces móveis livres de suporte, cola e rebarbas.
4. **Instale o pescoço.** Com a cabeça aberta, coloque a porca no alojamento interno. Posicione os colares ciano e azul sobre o torso e a arruela deslizante no apoio de Z = 95,5 mm. Introduza parafuso e arruela de aço pelo fundo do torso, engate a porca e ajuste com a ferramenta enquanto as duas extremidades estão acessíveis. Trave apenas a conexão entre as duas roscas metálicas com produto removível de baixa resistência. Após a cura, confira se cabeça, parafuso e porca giram juntos sem alterar o aperto.
5. **Monte os braços.** Encaixe a lingueta de cada braço superior nos ombros do torso. Depois una braço superior e antebraço nos cotovelos; termine com as mãos nos punhos. Em cada junta use duas arruelas externas e uma porca. Confirme acesso às ferramentas antes de instalar as capas.
6. **Monte as pernas.** Encaixe as coxas na pelve, depois as canelas nas coxas e as solas estruturais nas canelas. Coloque a cabeça do parafuso e a porca nos rebaixos dos quadris sem forçar. Confira o apoio das solas sobre uma superfície plana.
7. **Faça uma montagem completa a seco.** Una provisoriamente torso e pelve pelos pinos de alinhamento. Verifique posição, equilíbrio, acesso às ferragens e interferências, começando com pequenos movimentos. Ajuste a fricção sem esmagar as estruturas.
8. **Cole as partes fixas.** Após conferir o pescoço, cole a face de união entre torso e pelve e os pinos de alinhamento. Cole as capas por cor ao redor das estruturas, sem alcançar orelhas, linguetas, arruelas, eixo ou porca. Preserve acesso aos parafusos que precisarem de manutenção.
9. **Finalize cabeça e decoração.** Feche os cascos; monte visor e detalhes, painéis, orelhas e antenas. Para a marca pequena, use o decalque oficial em vez dos cinco componentes em relevo se quiser preservar os traços com bico de 0,4 mm.
10. **Monte a base.** Cole suas quatro camadas. Os pés apoiam livremente sobre ela; uma fixação permanente das solas só deve ser feita depois de verificar a pose e o equilíbrio.

## Ajuste e limites

- Um giro áspero pode indicar rebarba, furo desalinhado, cola no encaixe ou atrito entre carenagens. Identifique o contato antes de apertar mais.
- Uma junta frouxa pede conferência da porca e do conjunto de arruelas. Não tente obter rigidez deformando as orelhas impressas.
- As capas têm folga nominal de 0,18 mm em relação ao esqueleto; essa folga de colagem é diferente dos 0,3 mm laterais das articulações.
- Os furos, o apoio das arruelas, o alcance nominal das ferramentas e o engate axial das porcas foram inspecionados digitalmente na pose entregue. Isso não demonstra acesso da ferramenta em toda posição, ajuste real de rosca, torque adequado, retenção de pose ou durabilidade.
- O relatório `exports/movimento_local.json` verifica amostras angulares das 13 juntas contra toda a montagem estacionária, incluindo ferragens e base, movendo os componentes descendentes correspondentes. A pose zero não apresentou colisões. As amostras não certificam o percurso contínuo, movimentos simultâneos ou resistência física. Alguns sentidos colidem com carenagens; não force além do contato.

**Retire o boneco do pedestal antes de articular as pernas.** As inclinações testadas de quadril, joelho e tornozelo colidiram com a base estacionária. O relatório também registra o resultado ao remover somente a base; todas as 13 juntas tiveram pelo menos uma amostra não nula livre nessa condição.

### Amostras digitais livres, sem a base

Os valores abaixo são **posições discretas em graus a partir da pose entregue**, não intervalos completos de movimento. O sinal segue rotação CAD em torno de +Y nos membros e +Z no pescoço. As vistas dos seis tipos dos membros usam o exemplo E; a geometria e o resultado do lado D devem ser conferidos separadamente.

| Junta | E | D |
|---|---|---|
| Ombro | −20, −10, −5, +5, +10 | −20, −10, −5 |
| Cotovelo | −20, −10, −5 | −20, −10, −5 |
| Punho | −20, −10, −5, +5, +10, +20 | −20, −10, −5, +5 |
| Quadril | +5, +10, +20 | −20, −10, −5 |
| Joelho | −5, +5, +10, +20 | −20, −10, −5, +5 |
| Tornozelo | −20, −10, −5, +5, +10, +20 | −20, −10, −5, +5, +10, +20 |
| Pescoço único | −30, −15, +15, +30 | — |

Não houve impressão física nem ensaio de movimento, resistência ou fadiga. Comece por uma junta completa e seus cupons antes de imprimir todo o boneco. Use as vistas técnicas para identificar as peças e a sequência; a montagem física continua necessária para confirmar as folgas e os comprimentos das ferragens.
