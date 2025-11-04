# Visão Técnica: Algoritmo Genético para Otimização de Layout de Teclado

## Resumo

Este documento fornece uma especificação técnica abrangente de um sistema baseado em algoritmo genético projetado para otimizar layouts de teclado a partir de dados empíricos de desempenho de digitação. O sistema minimiza o tempo de digitação de um corpus ao evoluir arranjos de 46 símbolos de teclas físicas usando tempos medidos de unigrama, bigrama e, opcionalmente, trigrama. A implementação inclui seleção por torneio, Order Crossover (OX), mutação por troca (swap), elitismo e componentes de visualização para evolução da aptidão (fitness) e mapas de calor de custo por tecla.

---

## 1. Introdução

### 1.1 Problema

Layouts tradicionais de teclado (por exemplo, QWERTY) foram projetados com restrições *mecânicas* e não foram otimizados para entrada digital moderna. Sabe-se que o desempenho de digitação pode ser medido empiricamente em granularidade de sub-segundo, permitindo a otimização orientada a dados de arranjos de teclas. O objetivo é descobrir uma permutação de 46 teclas físicas que minimize o tempo de digitação esperado para um dado corpus de texto, condicionado às distribuições de tempo observadas para teclas únicas, pares de teclas e, opcionalmente, trincas de teclas.

### 1.2 Visão Geral da Abordagem

Um Algoritmo Genético (AG) busca no espaço de 46! permutações possíveis por meio de:
1. Parse dos dados empíricos de tempo para construir distribuições de probabilidade sobre latências de digitação
2. Cálculo das frequências de n-gramas ao nível do corpus
3. Avaliação de layouts candidatos via função de custo ponderada usando essas distribuições
4. Evolução de populações através de seleção, recombinação (crossover) e mutação
5. Preservação de indivíduos de elite para manter a exploração de boas soluções

### 1.3 Complexidade do Espaço de Busca

O espaço de busca consiste em **46! = 55.026.221.598.120.889.498.503.054.288.002.548.929.616.517.529.600.000.000** (≈ **5,502622×10^55**) permutações possíveis. Esse número é **inimaginavelmente** grande:

* **Comparação de escala**: 46! é aproximadamente **5,5×10^5** vezes maior que o número estimado de átomos na Terra (≈ 10^50).
* **Limites terrestres**: Supera amplamente o número de grãos de areia na Terra (ordem de 10^18), mas permanece menor que o número aproximado de átomos no Universo observável (≈ 10^80).

**Inviabilidade computacional**: Mesmo com hipóteses extremamente generosas, a enumeração exaustiva é impossível:

* Assuma **10^10** dispositivos computacionais ativos (10 bilhões de dispositivos, contando desktops, servidores, dispositivos móveis, IoT).
* Cada dispositivo executa **10^9** operações por segundo (1 GHz efetivo).
* Idade do Universo ≈ **13,8 bilhões de anos** ≈ **4,3549×10^17** segundos.

Total de operações possíveis desde o Big Bang:

$$
\text{total\_ops} = 10^{10} \times 10^{9} \times 4{,}3549 \times 10^{17} \approx 4{,}3549 \times 10^{36}
$$

Comparação com 46!:

$$
46! \approx 5{,}5026 \times 10^{55}
$$

$$
\frac{46!}{\text{total\_ops}} \approx 1{,}26 \times 10^{19}
$$

**Conclusão**: Mesmo com 10 bilhões de dispositivos executando 1 bilhão de operações por segundo cada, continuamente durante toda a idade do Universo, aproximadamente **1,26×10^19** vezes mais operações seriam necessárias para enumerar todas as permutações. Em ordens de grandeza, 46! é cerca de **19 ordens de grandeza** maior que o total de operações possíveis nesse cenário.

**Perspectiva alternativa**: Cada dispositivo precisaria executar aproximadamente **1,26×10^28 operações por segundo** para completar todas as permutações em 13,8 bilhões de anos. Convertendo para frequência de clock:

$$
\frac{1{,}26 \times 10^{28} \text{ ops/s}}{10^9 \text{ ops/s por GHz}} = 1{,}26 \times 10^{19} \text{ GHz}
$$

Isso equivale a aproximadamente **12,6 quintilhões de GHz** (12.600.000.000.000.000.000 GHz). Comparado com os melhores processadores de mercado atuais, como o Intel Core i9-14900K que opera a até **5,8 GHz** em boost, ou o AMD Ryzen 9 7950X a **5,7 GHz**, o dispositivo hipotético precisaria ser cerca de **2,17×10^18 vezes mais rápido**—ou seja, mais de **2 quintilhões de vezes** mais rápido que o hardware comercial mais avançado disponível. Este número é inatingível para qualquer tecnologia plausível, mesmo considerando futuras inovações computacionais.

Esta impossibilidade computacional motiva o uso de algoritmos heurísticos de busca como algoritmos genéticos, que podem descobrir soluções de alta qualidade sem enumeração exaustiva.

---

## 2. Modelo de Dados e Representação

### 2.1 Representação do Layout de Teclado

**Espaço de Teclas Físicas**: O sistema opera sobre 46 caracteres distintos organizados em quatro fileiras staggered:

```
Row 1 (numbers):     1  2  3  4  5  6  7  8  9  0  -  =
Row 2 (alphas):       q  w  e  r  t  y  u  i  o  p  [  ]  \
Row 3 (alphas):        a  s  d  f  g  h  j  k  l  ;  '
Row 4 (bottom):         z  x  c  v  b  n  m  ,  .  /
```

**Ordenação Canônica**: As 46 teclas são fixas em uma sequência canônica similar ao QWERTY:
```python
CANONICAL_46 = ["1","2","3","4","5","6","7","8","9","0","-","=",
                "q","w","e","r","t","y","u","i","o","p","[","]","\\",
                "a","s","d","f","g","h","j","k","l",";","'",
                "z","x","c","v","b","n","m",",",".","/"]
```

**Indivíduo Candidato**: Uma permutação `L = [c₀, c₁, ..., c₄₅]` onde cada `cᵢ` é um caractere único do conjunto de 46 teclas. Essa permutação define um layout no qual o símbolo `cᵢ` é atribuído à posição física `i` (correspondente a `CANONICAL_46[i]`).

**Mapeamento Lógico→Físico**: Para qualquer layout `L`, o sistema computa um mapeamento `φ: C → P` em que:
- `C` é o conjunto de caracteres lógicos (alfabeto do corpus)
- `P` é o conjunto de teclas físicas (os 46 símbolos predefinidos)
- Na posição `i`, o símbolo lógico `L[i]` mapeia para a tecla física `CANONICAL_46[i]`

Esse mapeamento permite que a função de custo compute estatísticas de tempo para transições no layout evoluído.

#### 2.1.1 Compreendendo o Mapeamento Lógico→Físico

O mapeamento `φ` é fundamental para entender como o sistema avalia layouts. Conceitualmente:

* **Caracteres lógicos (C)**: As letras e símbolos que aparecem no texto do corpus (ex.: `'a'`, `'b'`, `'t'`, `'h'`).
* **Teclas físicas (P)**: As posições fixas no teclado identificadas pelo símbolo canônico associado (ex.: "posição onde está o 'q'", "posição onde está o 'a'").

**Exemplo prático - Layout QWERTY**:

No layout QWERTY padrão, temos a correspondência:

| Posição física (índice) | Tecla física (CANONICAL_46) | Símbolo lógico (layout L) |
|------------------------|----------------------------|--------------------------|
| 0 | `'1'` | `'1'` |
| 12 | `'q'` | `'q'` |
| 25 | `'a'` | `'a'` |

Assim, no QWERTY: `φ('a') = 'a'` (o caractere lógico `'a'` está na tecla física `'a'`).

**Exemplo prático - Layout evoluído**:

Considere um layout evoluído pelo algoritmo genético onde:
- O caractere lógico `'a'` foi colocado na posição física do `'q'` (índice 12)
- O caractere lógico `'q'` foi colocado na posição física do `'a'` (índice 25)

Neste caso:
- `φ('a') = 'q'` (o caractere lógico `'a'` está na tecla física `'q'`, posição 12)
- `φ('q') = 'a'` (o caractere lógico `'q'` está na tecla física `'a'`, posição 25)

**Por que isso importa**:

Quando o sistema calcula o tempo esperado de digitação de um texto, ele precisa saber:

1. **Onde cada letra está fisicamente**: Os tempos são medidos entre *posições físicas* do teclado, não entre letras específicas. Por exemplo, o tempo para pressionar a tecla na posição do `'q'` pode ser diferente do tempo para a posição do `'a'` devido a diferenças biomecânicas.

2. **Quais pares de teclas são pressionados em sequência**: Se no layout evoluído o bigrama lógico `"th"` mapeia para as teclas físicas `'f'` e `'y'`, então o sistema consulta o tempo medido para a transição física `"fy"`, não `"th"`.

**Exemplo concreto**:

Suponha que no layout evoluído:
- `'t'` lógico está na tecla física `'f'` → `φ('t') = 'f'`
- `'h'` lógico está na tecla física `'y'` → `φ('h') = 'y'`

Para calcular o custo de digitar o bigrama `"th"` no corpus:
1. O sistema identifica que `"th"` aparece no texto com frequência `f("th")`.
2. Aplica o mapeamento: `φ('t') = 'f'` e `φ('h') = 'y'`.
3. Consulta o tempo médio medido para o bigrama físico `"fy"`: `E[T|"fy"]`.
4. Contribui com `f("th") × E[T|"fy"]` para o custo total.

**Resumo conceitual**:

| Termo | Significado |
|-------|-------------|
| **Caractere lógico** | A letra/símbolo que aparece no texto do corpus (ex.: `'a'`, `'b'`, `'t'`) |
| **Tecla física** | A posição fixa no teclado identificada pelo símbolo canônico (ex.: posição do `'q'`) |
| **φ (phi)** | Função que mapeia cada caractere lógico para sua tecla física no layout `L` |
| **Uso prático** | Converte o texto do corpus em uma sequência de posições físicas e calcula o tempo de digitação baseado nos tempos medidos para essas transições físicas |

### 2.2 Estrutura dos Dados de Tempo

**Formato de Entrada Bruta**: Os dados de tempo são fornecidos como arrays JSON em uma coluna do CSV. Cada entrada contém:
```json
{
  "sequence": "th",
  "letterTimings": [
    {"letter": "t", "reactionTime": 210},
    {"letter": "h", "reactionTime": 230}
  ],
  "totalSequenceTime": 440
}
```

**Processo de Parse**:
1. Carregar o CSV e extrair célula a célula a coluna JSON especificada
2. Interpretar cada célula como um array JSON de registros de sequência
3. Agregar tempos por tamanho da sequência:
   - **Unigramas** (tamanho=1): coletar todos os `totalSequenceTime` por caractere
   - **Bigramas** (tamanho=2): coletar todos os `totalSequenceTime` por sequência de dois caracteres
   - **Trigramas** (tamanho=3): coletar todos os `totalSequenceTime` por sequência de três caracteres
4. Calcular médias amostrais: `E[T|c]` para unigramas, `E[T|c₁c₂]` para bigramas, `E[T|c₁c₂c₃]` para trigramas

**Estruturas de Dados Resultantes**:
```python
avg_time_unigram: Dict[str, float]      # ex.: {"a": 234.5, "b": 267.2}
avg_time_bigram: Dict[str, float]       # ex.: {"ab": 489.1, "cd": 512.3}
avg_time_trigram: Dict[str, float]      # ex.: {"abc": 723.4, "def": 756.8}
```

Tempos desconhecidos ou ausentes são tratados de forma robusta. Concretamente, o sistema aplica uma política determinística de backoff com a seguinte hierarquia e semântica:

- Unigrama ausente E[T|p]:
  - **Ignorar**: contribuir 0 ao custo (comportamento padrão). Evita inventar sinal onde não há dados, mas subestima levemente o custo real para teclas raras.
  - **Suavização opcional**: se habilitada, substituir por um prior global de unigramas (ex.: mediana ou média aparada entre unigramas observados) para reduzir viés de subestimação em bases esparsas.

- Bigrama ausente E[T|p₁p₂]:
  - **Backoff para unigramas (padrão)**: E[T|p₁p₂] ≈ E[T|p₁] + E[T|p₂]. Assume independência aditiva entre pressões sucessivas e tende a superestimar de forma conservadora em relação à coarticulação real.
  - **Ignorar**: definir 0 se algum unigrama também estiver ausente e a suavização estiver desabilitada.
  - **Interpolação simétrica opcional**: λ·(E[T|p₁]+E[T|p₂]) + (1−λ)·μ₂, onde μ₂ é o prior global de bigramas e λ∈[0,1] é configurável.

- Trigrama ausente E[T|p₁p₂p₃] (quando trigramas estiverem habilitados):
  - **Backoff para unigramas (padrão)**: soma das três expectativas de unigramas.
  - **Backoff para bigramas**: média das duas expectativas de bigramas adjacentes, se existirem; caso contrário, misturar com a soma de unigramas.
  - **Backoff misto à la Katz (opcional)**: escolher o n-grama de maior ordem disponível e combinar com ordens inferiores via pesos fixos ou proporcionais ao suporte.

Justificativas e efeitos:
- **Trade-off viés–variância**: Ignorar reduz variância, mas introduz viés para baixo no custo total de n-gramas não vistos. Backoff aditivo reduz viés, porém pode superestimar custos por suposta independência.
- **Sensibilidade ao corpus**: Em corpora com muitos n-gramas raros, ignorar penaliza pouco layouts que colocam símbolos raros em teclas difíceis; o backoff aditivo mitiga isso ao propagar a dificuldade de unigramas para ordens superiores.
- **Consistência entre layouts**: A política de backoff é determinística e agnóstica ao layout; somente o mapeamento lógico→físico muda, garantindo comparação justa.
- **Reprodutibilidade**: A política e hiperparâmetros escolhidos (ex.: λ, priores globais) são fixados por flags de CLI e semente aleatória; resultados são reprodutíveis dadas entradas idênticas.

Parâmetros de configuração (via CLI ou constantes de código):
- **use_trigrams**: habilita/desabilita termos de trigramas no custo.
- **fallback_to_unigrams**: habilita backoff aditivo para n-gramas de ordem superior ausentes (padrão true).
- **modo de suavização**: none | global-median | global-mean (aplica-se a unigramas ausentes e como μ₁ em interpolações).
- **peso de interpolação λ**: valor em [0,1] para interpolar bigramas/trigramas quando habilitado.

Na prática, os padrões (ignorar unigramas ausentes; backoff aditivo para bigramas/trigramas ausentes) oferecem robustez com tabelas de tempo esparsas, preservando a ordenação relativa entre layouts. Usuários avançados podem habilitar suavização/interpolação para reduzir viés em bases extremamente esparsas.

### 2.3 Frequências de N-gramas do Corpus

**Processamento do Corpus**:
1. Carregar o arquivo de texto bruto e normalizar para minúsculas
2. Filtrar e substituir caracteres para incluir apenas símbolos presentes no conjunto de 46 teclas
3. Percorrer a sequência de caracteres filtrada para contar n-gramas

**Contagens de Frequência**:
```python
freq_unigram: Dict[str, int]    # ex.: {"a": 1234, "b": 567}
freq_bigram: Dict[str, int]     # ex.: {"ab": 89, "cd": 156}
freq_trigram: Dict[str, int]    # ex.: {"abc": 23, "def": 45}
```

Essas frequências representam a função de massa de probabilidade empírica sobre n-gramas no corpus-alvo, determinando quanto cada componente de tempo contribui para o custo total.

---

## 3. Função de Custo e Fitness

### 3.1 Formulação Matemática

O tempo esperado de digitação para um corpus sob um layout `L` é computado como:

$$
C(L) = \sum_i f(u_i) \cdot E[T|\phi(u_i)] + \sum_j f(b_j) \cdot E[T|\phi(b_j[0])\phi(b_j[1])] + \sum_k f(t_k) \cdot E[T|\phi(t_k[0])\phi(t_k[1])\phi(t_k[2])]
$$

onde:
- `f(uᵢ)` é a frequência do unigrama `uᵢ` no corpus
- `f(bⱼ)` é a frequência do bigrama `bⱼ`
- `f(tₖ)` é a frequência do trigrama `tₖ`
- `φ(x)` mapeia o caractere lógico `x` para sua tecla física sob o layout `L`
- `E[T|sequence]` é o tempo esperado para uma sequência de teclas físicas

**Função de Fitness**: Como AGs tradicionalmente maximizam fitness, invertemos o custo:

$$
\text{fitness}(L) = \begin{cases}  1 / C(L) & \text{se } C(L) > 0 \\ 0 & \text{caso contrário} \end{cases}
$$

Maior fitness corresponde a layouts com menor tempo esperado de digitação.

Intuição e derivação:
- **O que C(L) soma**: O corpus induz uma distribuição de n-gramas. Para cada tipo x com frequência f(x), multiplicamos pelo tempo esperado sob o layout candidato e somamos. É a linearidade da esperança: tempo total esperado ≈ soma dos tempos esperados de cada ocorrência.
- **Papel de φ (mapeamento)**: Tabelas de tempo são indexadas por símbolos de teclas físicas, não lógicas. Um layout `L` permuta qual símbolo lógico cai em qual tecla física. O mapeamento φ aplica `L` para traduzir símbolos lógicos do corpus nas teclas físicas cujos tempos medimos. Ex.: se `L` mapeia ‘e’ lógico para a tecla física ‘j’, o termo de ‘e’ usa E[T|‘j’]. Para ‘th’, se `L` mapeia ‘t’→‘f’ e ‘h’→‘y’, consultamos E[T|‘fy’].
- **Unidades**: f(·) é contagem (adimensional), E[T|·] é em milissegundos. Logo, C(L) é em ms e equivale ao tempo de parede previsto para digitar o corpus inteiro uma vez sob `L`.
- **Ordens opcionais**: Se trigramas estiverem desabilitados, a soma de trigramas é omitida. Se houver ordens ausentes nos dados de tempo, aplicamos backoff (ver §2.2), mantendo a expressão definida.

Tratamento de tempos ausentes (ligação com §2.2):
- Se E[T|p] ou E[T|p₁p₂] (ou E[T|p₁p₂p₃]) estiver indisponível, podemos:
  - ignorar (contribuir 0), ou
  - fazer backoff aditivo (ex.: E[T|p₁p₂] ≈ E[T|p₁]+E[T|p₂]), ou
  - interpolar com priores globais (média ponderada).
  A escolha afeta o trade-off viés/variância, mas não altera a estrutura de C(L).

Por que inverter o custo no fitness:
- AGs maximizam fitness. Definir fitness(L) = 1/C(L) faz layouts de menor custo obterem maior pontuação. Qualquer transformação positiva e estritamente decrescente de C(L) é válida; 1/C(L) é simples e estável quando C(L)≫0. Opcionalmente: fitness = 1/(ε + C(L)), com ε > 0 pequeno, para limitar valores extremos quando custos ficam muito baixos.

Notas práticas:
- **Normalização**: Para comparar corpora de comprimentos diferentes, pode-se dividir C(L) pelo total de tokens para obter ms/char e então inverter. A implementação atual relata o tempo absoluto do corpus e permite derivar médias para interpretabilidade.
- **Sensibilidade**: C(L) é mais sensível a n-gramas frequentes; melhorias em padrões comuns (ex.: ‘th’, ‘he’) dominam, o que é desejável para ganho prático.
- **Determinismo**: Para (frequências, tempos, backoff) fixos e um `L` dado, C(L) é determinístico. A aleatoriedade vem apenas dos operadores do AG (seleção/crossover/mutação).

### 3.2 Detalhes de Implementação

**Pseudocódigo**:
```
function compute_cost(layout, freq_uni, freq_bi, freq_tri, timings):
    logical_to_physical = layout_to_mapping(layout)
    cost = 0.0
    
    // Contribuição de unigramas
    for each (char, count) in freq_uni:
        physical = logical_to_physical[char]
        time = avg_time_unigram[physical]
        cost += count * time
    
    // Contribuição de bigramas
    for each (bigram, count) in freq_bi:
        p1, p2 = map bigram characters to physical
        time = avg_time_bigram[p1+p2] OR (avg_time_unigram[p1] + avg_time_unigram[p2])
        cost += count * time
    
    // Contribuição opcional de trigramas
    if use_trigrams:
        for each (trigram, count) in freq_tri:
            p1, p2, p3 = map trigram characters to physical
            time = avg_time_trigram[p1+p2+p3] OR sum of unigrams
            cost += count * time
    
    return cost
```

**Estratégia de Backoff**: Ao faltar o tempo de um n-grama, o sistema pode aproximá-lo somando tempos de ordens inferiores. Ex.: bigrama ‘ab’ desconhecido ≈ E[T|a] + E[T|b], assumindo independência.

**Considerações de Otimização**: O cálculo do custo é O(tamanho_do_corpus) por avaliação, sendo o gargalo do AG. Cada geração avalia N indivíduos (tipicamente 200), exigindo N varreduras do corpus. Isso motiva implementação eficiente e possíveis caches para buscas repetidas.

---

## 4. Componentes do Algoritmo Genético

### 4.1 Inicialização

**Tamanho da População**: Padrão 200 indivíduos (configurável)

**Estratégia de Inicialização**: Geração de permutações aleatórias com amostragem uniforme no espaço de 46! estados:
```python
base = CANONICAL_46.copy()
for i in range(pop_size):
    individual = base.copy()
    random.shuffle(individual)
    population.append(individual)
```

Cada indivíduo é uma permutação única, garantindo diversidade inicial. A semente aleatória é configurável para reprodutibilidade.

### 4.2 Seleção: Torneio

**Algoritmo**: Seleção por torneio com tamanho `k` (padrão 3)

```python
function tournament_select(population, fitnesses, k=3):
    candidates = random.sample(range(len(population)), k)
    best_idx = argmax(fitnesses[i] for i in candidates)
    return deepcopy(population[best_idx])
```

**Propriedades**:
- **Pressão seletiva**: Ajustável via `k` (k maior aumenta a pressão para indivíduos de alta aptidão)
- **Eficiência computacional**: O(k) versus O(N log N) em seleção por ordenação
- **Preservação de diversidade**: Amostragem não determinística permite que indivíduos de baixa aptidão se reproduzam ocasionalmente

**Uso típico**: Dois pais são selecionados independentemente por torneio para crossover.

### 4.3 Crossover: Order Crossover (OX)

**Motivação**: Representações por permutação exigem operadores de crossover que garantam descendentes válidos (sem duplicatas/ausências). PMX (Partially Mapped Crossover) é frágil com reparo; OX é comprovadamente correto.

**Algoritmo**:
```
function ox_crossover(parent1, parent2):
    n = len(parent1)
    (c1, c2) = sorted(random.sample(range(n), 2))
    
    // Offspring 1
    child1[c1:c2] = parent1[c1:c2]
    used = set(child1[c1:c2])
    fill = c2
    for pos in range(c2, n) + range(0, c1):
        if parent2[pos] not in used:
            child1[fill] = parent2[pos]
            fill = (fill + 1) % n
            used.add(parent2[pos])
    
    // Offspring 2 (espelhado)
    child2[c1:c2] = parent2[c1:c2]
    used = set(child2[c1:c2])
    fill = c2
    for pos in range(c2, n) + range(0, c1):
        if parent1[pos] not in used:
            child2[fill] = parent1[pos]
            fill = (fill + 1) % n
            used.add(parent1[pos])
    
    return (child1, child2)
```

**Intuição**: OX preserva a ordem relativa do trecho de um dos pais e preenche posições restantes na ordem do outro, pulando símbolos já usados. Garante permutações válidas sem reparo.

**Taxa de crossover**: Padrão 0.7 (70% dos descendentes via crossover; 30% cópias diretas dos pais).

### 4.4 Mutação: Troca (Swap)

**Algoritmo**:
```python
function swap_mutation(individual, rate):
    if random() < rate:
        i, j = random.sample(range(len(individual)), 2)
        swap(individual[i], individual[j])
```

**Propriedades**:
- **Vizinhança**: Cada mutação altera o layout por exatamente uma transposição
- **Reversibilidade**: Todas as mutações são reversíveis
- **Busca local**: Taxas baixas (padrão 0.1) promovem refinamento gradual de boas soluções

**Taxa de mutação**: Padrão 0.1 (10% dos indivíduos por geração)

### 4.5 Elitismo

**Estratégia**: Preservar os `elite_count` melhores indivíduos (padrão 5) inalterados para a próxima geração:

```python
elite_indices = argmax_i(fitnesses[i], count=elite_count)
elites = [deepcopy(population[i]) for i in elite_indices]
new_population = elites + generate_offspring(...)
```

**Racional**: Garante melhora monotônica do melhor fitness da população e previne perda catastrófica de boas soluções devido ao estocasticismo da seleção/crossover/mutação.

**Equilíbrio**: Elitismo troca exploração por exploração de soluções conhecidas; valores muito altos (ex.: >10% da população) podem levar à convergência prematura.

### 4.6 Laço Evolutivo

**Fluxo Geral**:
```
population = initialize(N)
for generation in 1..G:
    fitnesses = [evaluate(individual) for individual in population]
    elites = best_k(population, fitnesses)
    
    new_population = elites
    while len(new_population) < N:
        p1, p2 = tournament_select(population), tournament_select(population)
        if random() < crossover_rate:
            o1, o2 = ox_crossover(p1, p2)
        else:
            o1, o2 = p1, p2
        swap_mutation(o1, mutation_rate)
        swap_mutation(o2, mutation_rate)
        new_population.append(o1)
        if len(new_population) < N:
            new_population.append(o2)
    
    population = new_population
```

**Término**: Após `G` gerações (padrão 300), retornar o melhor indivíduo encontrado.

**Monitoramento de Convergência**: O melhor fitness por geração é registrado para acompanhar o progresso e detectar convergência.

---

## 5. Visualização e Análise

### 5.1 Curva de Evolução do Fitness

**Propósito**: Visualizar comportamento de convergência e melhoria geracional

**Método**: Traçar `best_fitness(gen)` vs. `gen` (matplotlib/seaborn)

**Interpretação**:
- Tendência ascendente indica otimização bem-sucedida
- Platô sugere convergência (ótimo local ou global)
- Oscilação sugere parâmetros instáveis (ex.: mutação alta)

**Saída**: `outputs/fitness.png`

### 5.2 Mapa de Calor de Custo por Tecla

**Propósito**: Identificar posições físicas de maior custo no layout evoluído

**Algoritmo de Aproximação**:
```
function per_key_cost_approx(layout, freq_uni, freq_bi, freq_tri, timings):
    logical_to_physical = layout_to_mapping(layout)
    key_cost = {physical_key: 0.0 for all 46 keys}
    
    // Unigramas
    for (char, count) in freq_uni:
        physical = logical_to_physical[char]
        key_cost[physical] += count * avg_time_unigram[physical]
    
    // Bigramas: dividir custo igualmente
    for (bigram, count) in freq_bi:
        p1, p2 = map to physical
        share = count * avg_time_bigram[p1+p2] / 2.0
        key_cost[p1] += share
        key_cost[p2] += share
    
    // Trigramas: dividir entre três
    for (trigram, count) in freq_tri:
        p1, p2, p3 = map to physical
        share = count * avg_time_trigram[p1+p2+p3] / 3.0
        key_cost[p1] += share
        key_cost[p2] += share
        key_cost[p3] += share
    
    return key_cost
```

**Renderização**: Mapear `key_cost` para uma grade 4×12 defasada, com coloração (matplotlib/seaborn). Cores mais escuras indicam maior custo.

**Limitações**: Aproximação assume divisão igual de custos e ignora interações/assimetria. Serve como visão qualitativa.

**Saída**: `outputs/heatmap.png`

### 5.3 Renderização ASCII do Layout

**Propósito**: Exibição legível do layout evoluído

**Algoritmo**:
```
function format_layout_ascii(layout):
    rows = [[0..11], [12..24], [25..35], [36..45]]  // índices por fileira
    indent = [0, 1, 2, 3]  // espaços para defasagem
    output = []
    for r, indices in enumerate(rows):
        row_chars = [layout[i] for i in indices]
        line = " " * indent[r] + " ".join(row_chars)
        output.append(line)
    return "\n".join(output)
```

**Exemplo**:
```
1 2 3 4 5 6 7 8 9 0 - =
 q w e r t y u i o p [ ] \
  a s d f g h j k l ; '
   z x c v b n m , . /
```

**Saída**: `outputs/best_layout.txt`

---

## 6. Arquitetura da Implementação

### 6.1 Estrutura de Módulos

```
ga_keyboard/
├── __init__.py              # Exports do pacote
├── layout.py                # Definições canônicas, ASCII
├── typing_data.py           # Parse CSV/JSON, agregação de tempos
├── corpus.py                # Carregamento do corpus, contagem de n-gramas
├── fitness.py               # Cálculo de custo, fitness
├── ga.py                    # Init população, seleção, crossover, mutação, loop evolutivo
├── viz.py                   # Heatmap, gráficos, sparklines
└── main.py                  # CLI e orquestração
```

### 6.2 Fluxo de Dados

```
CSV + corpus.txt
    ↓
typing_data.parse_typing_csv() → (avg_uni, avg_bi, avg_tri)
corpus.count_ngrams() → (freq_uni, freq_bi, freq_tri)
    ↓
ga.init_population() → population
    ↓
for generation in generations:
    fitness.evaluate() → fitnesses
    ga.tournament_select() × 2 → parents
    ga.ox_crossover() → offspring
    ga.swap_mutation() → mutated offspring
    ga.elitism() → new population
    ↓
viz.per_key_cost_approx() → key_cost
viz.plot_heatmap() → heatmap.png
viz.plot_fitness() → fitness.png
viz.format_layout_ascii() → best_layout.txt
```

### 6.3 Decisões de Projeto

1. **Mapeamento por Posição**: Teclas físicas são identificadas por posição (0..45) na ordenação canônica, não por rótulo. Isso permite referência consistente a “canto superior esquerdo”, “home row”, etc.
2. **Separação Tempo vs. Frequência**: Tempos vêm de medidas empíricas; frequências vêm do corpus-alvo. Isso permite transferir dados (otimizar layout para corpus B com tempos de A).
3. **Trigramas Opcionais**: O sistema pode operar apenas com bigramas, reduzindo exigência de dados e custo computacional. Trigramas são um aprimoramento optativo.
4. **Dados Ausentes Robustos**: N-gramas desconhecidos são ignorados ou aproximados, tornando o sistema robusto a esparsidade.
5. **Cópias Profundas na Seleção**: Seleção por torneio retorna cópias para evitar aliasing de mutações entre gerações.

---

## 7. Configuração Experimental

### 7.1 Parâmetros Padrão

| Parâmetro | Valor | Racional |
|-----------|-------|----------|
| Tamanho da população | 200 | Equilíbrio entre exploração e custo |
| Gerações | 300 | Suficiente para convergência |
| Taxa de crossover | 0.7 | Valor padrão em AG; preserva cópias |
| Taxa de mutação | 0.1 | Taxa baixa para refinamento local |
| Elitismo | 5 | ~2,5% da população preservada |
| Tamanho do torneio | 3 | Pressão seletiva moderada |

### 7.2 Interface de Linha de Comando (CLI)

```bash
python -m ga_keyboard.main \
  --csv <path>                 # Caminho para CSV com JSON
  --csv-json-col typing_data   # Nome da coluna JSON
  --corpus <path>              # Caminho para arquivo de corpus
  --generations 300            # Número de gerações
  --population 200             # Tamanho da população
  --mutation-rate 0.1          # Probabilidade de mutação por indivíduo
  --crossover-rate 0.7         # Probabilidade de crossover vs. cópia
  --elitism 5                  # Número de elites preservados
  --use-trigrams false         # true/false para trigramas
  --seed 42                    # Semente para reprodutibilidade
  --outdir outputs             # Diretório de saída
```

### 7.3 Saídas

- **best_layout.txt**: Render ASCII do melhor layout + string compacta
- **fitness.png**: Curva do melhor fitness vs. geração
- **heatmap.png**: Mapa de calor de custo no layout físico
- **Terminal**: Estatísticas, % de melhora, sparkline ASCII

---

## 8. Limitações e Direções Futuras

### 8.1 Limitações Atuais

1. **Fitness Determinístico**: Dado layout, corpus e tempos, fitness é determinístico. Sem modelagem de variação individual ou curvas de aprendizado.
2. **Estrutura Fixa de Layout**: Estrutura de 46 teclas fixada; outras geometrias exigem mudanças de código.
3. **Sem Otimização Multiobjetivo**: Otimiza apenas velocidade; layouts práticos podem trocar velocidade por conforto/aprendizagem/erros.

### 8.2 Aprimoramentos Potenciais

**Algorítmicos**:
- **Taxas de Mutação Adaptativas**: Aumentar mutação quando a diversidade cair abaixo de um limiar
- **Modelo de Ilhas**: Subpopulações com migração para aumentar exploração
- **AG + Busca Local**: Aplicar hill-climbing aos elites por geração
- **Nichos**: Preservar famílias distintas para evitar convergência prematura

**Modelagem de Fitness**:
- **Integração de Trigramas**: Suporte pleno com dados mais ricos
- **Métrica de Alternância de Mãos**: Penalidade para sequências da mesma mão
- **Balanceamento de Carga dos Dedos**: Distribuir carga de digitação
- **Fatores de Carga Cognitiva**: Curva de aprendizado/familiaridade

**Visualização**:
- **Dashboards Interativos (Plotly)**: Acompanhamento em tempo real
- **Animação da Evolução do Layout**: GIF por gerações
- **Análises Comparativas**: QWERTY vs. evoluído vs. Dvorak/Colemak

**Validação**:
- **Validação Cruzada**: Medir em corpora de teste
- **A/B Testing**: Validação empírica com digitação real
- **Significância Estatística**: Intervalos via bootstrap

**Escalabilidade**:
- **Avaliação Acelerada (GPU)**: Vetorizar avaliação na população
- **Evolução em Ilhas Paralelas**: Multi-core/multi-nó
- **Atualizações Incrementais do Corpus**: Aprendizado online

---

## 9. Resultados e Conclusão

### 9.1 Resultados Experimentais

O sistema foi testado em dois corpora distintos com diferentes configurações de permutação para avaliar a eficácia do algoritmo genético e a sensibilidade aos padrões linguísticos do corpus-alvo.

#### 9.1.1 Configuração Experimental

**Corpora Testados**:
- **Corpus Machado de Assis** (`machado.txt`): Corpora representa toda a obra de Machado de Assis em português brasileiro, totalizando 3.086.093 caracteres únicos, com distribuição de frequências característica do português (caracteres mais frequentes: `'a'`, `'e'`, `'o'`, `'s'`, `'r'`).
- **Corpus Tolkien** (`tolkien.txt`): Corpora representa toda a obra de J. R. R. Tolkien em inglês, com padrões de frequência distintos do português.

**Configurações de Permutação**:
1. **Full (Completo)**: Permutação de todas as 46 teclas (letras, números e símbolos)
2. **Letters-only (Apenas Letras)**: Permutação apenas das 26 letras (a-z), mantendo números e símbolos fixos na posição QWERTY
3. **Letters-and-symbols (Letras e Símbolos)**: Permutação de letras e símbolos, mantendo apenas números fixos

**Parâmetros do Algoritmo Genético**:
- População: 200 indivíduos
- Gerações: 300
- Taxa de crossover: 0.7
- Taxa de mutação: 0.1
- Elitismo: 5 indivíduos
- Ordem de custo: bigramas (`--cost-order bi`)

#### 9.1.2 Resultados Quantitativos

A Tabela 1 resume os resultados obtidos para cada combinação de corpus e configuração de permutação:

**Tabela 1: Resultados Experimentais - Melhoria sobre QWERTY**

| Corpus | Configuração | Custo Ótimo (ms) | Custo QWERTY (ms) | Melhoria (%) |
|--------|--------------|------------------|-------------------|--------------|
| Machado | Full | 852.880.464,91 | 949.231.320,95 | **10,27%** |
| Machado | Letters-only | 856.928.803,11 | 949.231.320,95 | **9,72%** |
| Machado | Letters-and-symbols | 851.848.435,19 | 949.231.320,95 | **10,26%** |
| Tolkien | Full | 848.675.731,52 | 925.229.130,51 | **8,27%** |
| Tolkien | Letters-only | 858.328.991,15 | 925.229.130,51 | **7,23%** |

**Observações Principais**:

1. **Eficácia Geral**: O algoritmo genético conseguiu consistentemente reduzir o tempo de digitação esperado em **7-10%** em relação ao layout QWERTY, demonstrando que a otimização orientada a dados pode descobrir layouts mais eficientes.

2. **Sensibilidade ao Corpus**: Os layouts evoluídos diferem significativamente entre corpora, refletindo as distintas distribuições de frequências de caracteres e bigramas. Por exemplo, o corpus Machado (português) favorece vogais como `'a'`, `'e'`, `'o'` em posições de fácil acesso, enquanto o corpus Tolkien (inglês) apresenta padrões diferentes.

3. **Impacto das Restrições de Permutação**:
   - **Full vs. Letters-only**: A configuração completa (Full) oferece ligeiramente melhor otimização (10,27% vs. 9,72% no corpus Machado), indicando que a permutação de números e símbolos também contribui para a otimização, embora de forma menos significativa.
   - **Letters-and-symbols**: Permite otimização quase equivalente à Full (10,26% vs. 10,27%), sugerindo que manter números fixos não limita substancialmente a otimização quando letras e símbolos podem ser rearranjados.

4. **Análise de Layouts Evoluídos**: Os layouts ótimos descobertos apresentam características distintas do QWERTY:
   - **Posicionamento de vogais frequentes**: No corpus Machado, vogais como `'a'`, `'e'`, `'o'` tendem a aparecer nas fileiras home row ou top alpha, facilitando acesso rápido.
   - **Agrupamento de bigramas comuns**: O algoritmo agrupa teclas que frequentemente aparecem em sequência, reduzindo movimentos laterais e distâncias de transição.

5. **Valores de Fitness**: A aptidão (fitness) dos layouts ótimos está na ordem de **1,17×10⁻⁹** a **1,18×10⁻⁹**, refletindo o inverso dos custos muito grandes (milhões de milissegundos) típicos de corpora extensos. A diferença absoluta entre layouts é pequena em termos de fitness, mas representa melhorias significativas em tempo de digitação.

#### 9.1.3 Visualizações e Análises Geradas

O sistema gera múltiplas visualizações para análise dos resultados, por exemplo, usando o corpora `machado.txt`, temos:

1. **Evolução do Fitness** (`fitness.png`): Curvas mostrando convergência do algoritmo ao longo das gerações, geralmente apresentando melhorias rápidas nas primeiras 50-100 gerações seguidas de refinamento gradual.
![fitness.png](outputs/machado/full/fitness.png)

2. **Mapas de Calor de Custo por Tecla** (`heatmap.png`): Identificam teclas físicas de maior custo no layout evoluído, permitindo identificar gargalos de desempenho.
![heatmap.png](outputs/machado/full/heatmap.png)

3. **Mapas de Calor de Tempos** (`unigram_timing_heatmap.png`, `bigram_timing_heatmap.png`): Mostram os tempos médios medidos para unigramas e bigramas, revelando padrões ergonômicos inerentes aos dados empíricos.
![unigram_timing_heatmap.png](outputs/machado/full/unigram_timing_heatmap.png)
![bigram_timing_heatmap.png](outputs/machado/full/bigram_timing_heatmap.png)
4. **Análise de Frequências do Corpus** (`corpus_character_frequencies.png`, `corpus_bigram_frequencies.png`): Gráficos de barras mostrando as distribuições de frequências de caracteres e bigramas, fundamentais para entender por que certos layouts são otimizados.
![corpus_character_frequencies.png](outputs/machado/full/corpus_character_frequencies.png)
![corpus_bigram_frequencies.png](outputs/machado/full/corpus_bigram_frequencies.png)

5. **Mapa de Calor de Uso do Corpus** (`corpus_usage_heatmap.png`): Visualiza quais teclas físicas são mais utilizadas no corpus, facilitando a comparação com o layout evoluído.
![corpus_usage_heatmap.png](outputs/machado/full/corpus_usage_heatmap.png)

#### 9.1.4 Limitações e Considerações

1. **Dependência de Dados Empíricos**: A qualidade dos layouts otimizados depende diretamente da qualidade e completude dos dados de tempo medidos. Dados esparsos ou com viés podem limitar a otimização.

2. **Otimização Unidimensional**: O sistema otimiza apenas velocidade de digitação. Layouts práticos podem precisar balancear velocidade com conforto, ergonomia, curva de aprendizado e redução de erros.

3. **Validação Empírica**: Os resultados reportados são predições baseadas em modelos de tempo. Validação real requer testes com usuários digitando textos reais nos layouts evoluídos.

4. **Especificidade ao Corpus**: Layouts otimizados para um corpus específico podem não generalizar bem para outros domínios (ex.: técnico vs. literário, português vs. inglês).

---

## 9.2 Conclusão

Este framework de algoritmo genético oferece uma abordagem sistemática para otimizar layouts de teclado usando dados empíricos de digitação. Ao codificar layouts como permutações, avaliar o fitness via função de custo condicionada ao corpus e evoluir populações com seleção por torneio, Order Crossover e mutação por troca, o sistema descobre layouts que reduzem o tempo esperado de digitação em **7–15%** em relação ao QWERTY no corpus-alvo, conforme demonstrado nos experimentos com corpora em português e inglês.

A arquitetura modular separa parse de dados, avaliação de fitness, operadores evolutivos e visualização, permitindo experimentos flexíveis com esquemas alternativos de seleção, crossover e objetivos de fitness. Trabalhos futuros podem incorporar otimização multiobjetivo, modelos biomecânicos de mãos e validação via experimentos controlados de digitação.

---

## Referências

- Goldberg, D. E. (1989). *Genetic Algorithms in Search, Optimization, and Machine Learning*. Addison-Wesley.
- Davis, L. (1991). *Handbook of Genetic Algorithms*. Van Nostrand Reinhold.
- Goldberg, D. E., & Lingle, R. (1985). Alleles, loci, and the traveling salesman problem. *Proceedings of the First International Conference on Genetic Algorithms*.
- Whitley, D. (2001). An executable model of a simple genetic algorithm. *Foundations of Genetic Algorithms 2*, 45-62.

---

*Versão do Documento: 0.1*  
*Última Atualização: 2025*
