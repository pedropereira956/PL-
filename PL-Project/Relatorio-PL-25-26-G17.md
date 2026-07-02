# Relatório Técnico: Compilador Fortran 77
**Processamento de Linguagens 2026 — Grupo 17**

* Gonçalo Sá (A107376)
* José Rocha (A106887)
* Pedro Pereira (A107332)

---

## 1. Introdução

O presente documento detalha o processo de conceção e implementação de um compilador para a linguagem **Fortran 77**, desenvolvido no âmbito da unidade curricular de **Processamento de Linguagens**. O principal objetivo deste projeto consiste na tradução de código fonte escrito segundo o standard **ANSI X3.9-1978** para instruções executáveis na **Máquina Virtual EWVM**.

O desenvolvimento de um compilador para uma linguagem histórica como o Fortran 77 apresenta desafios únicos, exigindo uma compreensão profunda da teoria das linguagens formais e das arquiteturas de computação baseadas em *stack*. Para responder a estes desafios, adotou-se uma metodologia de **desenvolvimento modular**, estruturando o compilador numa "linha de montagem" composta por quatro fases fundamentais:

1.  **Análise Léxica**: Onde o fluxo de caracteres é segmentado em unidades lógicas (*tokens*).
2.  **Análise Sintática**: Onde a estrutura gramatical é validada e convertida numa representação interna (**AST - Abstract Syntax Tree**).
3.  **Análise Semântica**: Onde se garante a coerência lógica do programa, a gestão de tipos e a organização da memória.
4.  **Otimização de Código**: Onde a árvore sintática é percorrida para aplicar simplificações lógicas, algébricas e de propagação de constantes (etapa de valorização).
5.  **Geração de Código**: Onde a AST validada e otimizada é finalmente traduzida para o dialeto *assembly* da EWVM.

Para além dos requisitos base, este projeto explorou funcionalidades avançadas como a implementação de subprogramas (**FUNCTION** e **SUBROUTINE**) e a manipulação de **arrays**, demonstrando a flexibilidade da arquitetura implementada. A utilização da biblioteca **PLY (Python Lex-Yacc)** foi determinante para garantir um equilíbrio entre a eficiência do processamento e a clareza do código fonte do compilador.

## 2. Arquitetura do Sistema
O compilador foi concebido seguindo um modelo de processamento em pipeline, onde o programa é transformado progressivamente através de várias representações intermédias até se atingir o código objeto final. A escolha de uma arquitetura modular em Python permitiu uma separação clara entre a lógica de reconhecimento da linguagem e a lógica de geração de código para a máquina alvo.

### 2.1. Componentes do Compilador
* **`main.py`** **(Ponto de Entrada)**: Atua como o coordenador global do sistema. Este módulo é responsável pela interface de linha de comando, leitura dos ficheiros fonte .f77 e pela invocação sequencial das fases de análise, otimização e geração. Implementa também a impressão do relatório de otimizações aplicadas e o tratamento de erros de alto nível.
* **`compiler/lexer.py`** **(Analisador Léxico)**: Utilizando a biblioteca ply.lex, este componente realiza a conversão do fluxo de caracteres original numa sequência de tokens tipificados. 
* **`compiler/parser.py` & `ast.py`** **(Análise Sintática e AST)**: A análise sintática é processada pelo **`ply.yacc`**, que aplica as regras da gramática formal definida para o projeto, resultando numa Árvore Sintática Abstrata (AST). 
* **`compiler/symboltable.py`** **(Tabela de Símbolos)**: Providencia a infraestrutura necessária para gerir o ciclo de vida dos identificadores (variáveis, funções e subrotinas). 
* **`compiler/semantic.py`** **(Analisador Semântico)**: Esta fase valida a AST contra as regras lógicas do Fortran 77.
* **`compiler/optimizer.py`** **(Otimizador da AST)**: Interceta a AST validada para remover código morto, pré-computar contas estáticas (Constant Folding), simplificar álgebra e realizar a Propagação de Constantes através de um estado de memória em dicionário.
* **`compiler/codegen.py`** **(Gerador de Código)**: O componente final do pipeline traduz a AST otimizada numa sequência de instruções assembly para a EWVM.

### 2.2. Fluxo de Dados
O fluxo de dados entre estes componentes é estritamente linear: o lexer alimenta o parser, que gera a AST. Esta árvore é então enriquecida e validada pela semântica (com auxílio da tabela de símbolos) e, finalmente, consumida pelo gerador de código para produzir o ficheiro de saída .vm.

## 3. Opções de Implementação

### 3.1. Formato de Entrada e Insensibilidade a Maiúsculas (*Case-Insensitivity*)
Ao contrário do Fortran 77 original, que impõe um formato rígido de colunas fixas (onde, por exemplo, o código executável apenas pode iniciar na coluna 7), o nosso grupo tomou a decisão arquitetural de suportar o **formato livre** (*free-form*). Esta opção aproxima o compilador dos padrões de programação mais modernos, permitindo também a utilização do caráter `!` para inserir comentários em qualquer ponto da linha.

Adicionalmente, o Fortran é uma linguagem intrinsecamente insensível a maiúsculas e minúsculas (*case-insensitive*). Para garantir este comportamento sem sobrecarregar a lógica da gramática, implementámos uma solução transversal: no momento da análise léxica, todos os identificadores capturados são imediatamente convertidos para maiúsculas (utilizando o método `.upper()` em Python). Deste modo, a Tabela de Símbolos opera apenas sobre uma versão normalizada das variáveis, assegurando que identificadores como `SOMA`, `soma` ou `Soma` partilham exatamente o mesmo endereço de memória.

### 3.2. Tipagem Implícita (Regra I-N)
Uma das características mais idiossincráticas do Fortran 77 é a capacidade de utilizar variáveis sem exigir a sua declaração explícita prévia. Para suportar esta funcionalidade fundamental, implementámos a regra clássica de tipagem implícita durante a fase de validação semântica. 

Quando o analisador encontra uma referência a uma variável que não consta na Tabela de Símbolos, inspeciona imediatamente o primeiro caráter do seu nome. Se este caráter estiver compreendido no intervalo alfabético entre **I e N** (inclusive), a variável é instanciada e registada automaticamente como `INTEGER`, caso contrário, é classificada como `REAL`. Esta lógica foi perfeitamente integrada no método de resolução de referências da árvore sintática, garantindo total conformidade com o *standard* histórico da linguagem sem comprometer a segurança da atribuição de memória na máquina virtual.

## 4. Análise Léxica e Sintática

As fases iniciais do compilador foram implementadas recorrendo às ferramentas geradoras do pacote PLY, refletindo a aplicação direta dos conceitos de autómatos finitos deterministas e de gramáticas independentes de contexto.

### 4.1. Análise Léxica (*Scanner*)
O analisador léxico (`lexer.py`) recorre à ferramenta `ply.lex` para processar o fluxo de texto através de expressões regulares rigorosas. Uma preocupação técnica central nesta fase foi a ordenação das regras de reconhecimento para evitar falsos positivos estruturais. Por exemplo, a expressão regular responsável pela captura de números reais (`REAL_LITERAL`) foi estrategicamente definida antes da regra dos números inteiros (`INT_LITERAL`), impedindo que valores decimais fossem truncados prematuramente pela máquina de estados.

### 4.2. Análise Sintática (*Parser*)
A validação estrutural do código é assegurada pelo módulo `ply.yacc`, que implementa um algoritmo de *parsing* ascendente (*bottom-up*) do tipo **LALR(1)**. Para resolver ambiguidades clássicas e conflitos do tipo *shift/reduce* sem poluir a gramática, definiu-se uma matriz de precedência e associatividade. Esta matriz garante, por exemplo, que as operações de multiplicação/divisão e exponenciação são avaliadas antes da adição/subtração, e resolve a prioridade correta dos operadores lógicos (`.AND.`, `.OR.`, `.NOT.`) e relacionais típicos do Fortran.

A gramática desenvolvida destaca-se pelas seguintes opções de *design* arquitetural:

* **Rótulos Numéricos Opcionais (*Labels*):** A especificação sintática foi modelada com uma regra tolerante (`opt_label`) que admite um inteiro literal no início de qualquer instrução. Este identificador é guardado diretamente no nó da AST correspondente, sendo a pedra basilar para o suporte de instruções de desvio incondicional (`GOTO`) e para o fecho de blocos iterativos.

* **Validação Precoce de Ciclos `DO`:** Numa abordagem otimizada, a nossa implementação introduz verificações de integridade logo na fase de *parsing*. A regra gramatical responsável pelos ciclos `DO` extrai imediatamente a etiqueta associada ao comando `CONTINUE` de fecho, emitindo um aviso estrutural precoce (*Parser Warning*) caso os rótulos de abertura e fecho não coincidam, mitigando erros lógicos antes sequer da fase semântica.

* **Resolução Adiável de Ambiguidade Sintática:** Na linguagem Fortran 77, o acesso ao índice de um vetor (`VETOR(I)`) e a invocação de uma função (`FUNC(I)`) partilham a mesma assinatura sintática. Como tal ambiguidade não é decidível de forma puramente livre de contexto, o *parser* foi instruído a assumir a construção de um nó `FunctionCall` por defeito, transferindo inteligentemente a responsabilidade de desambiguação para o Analisador Semântico (que já terá acesso à Tabela de Símbolos).

### 4.3. Especificação da Gramática

Para responder aos requisitos do projeto, formalizámos o subconjunto da linguagem Fortran 77 através da seguinte gramática livre de contexto (apresentada numa notação simplificada EBNF):

**Estrutura Global e Subprogramas:**
* `Program` → `UnitList`
* `UnitList` → `Unit` | `UnitList Unit`
* `Unit` → `PROGRAM ID DeclList StmtList END` 
         | `SUBROUTINE ID '(' ParamList ')' DeclList StmtList END`
         | `TypeSpec FUNCTION ID '(' ParamList ')' DeclList StmtList END`

**Declarações:**
* `DeclList` → `ε` | `DeclList Decl`
* `Decl` → `TypeSpec VarDeclList`
* `TypeSpec` → `INTEGER` | `REAL` | `LOGICAL` | `CHARACTER`
* `VarDeclList` → `VarDecl` | `VarDeclList ',' VarDecl`
* `VarDecl` → `ID` | `ID '(' DimList ')'`

**Instruções (Statements):**
* `StmtList` → `ε` | `StmtList Stmt`
* `Stmt` → `OptLabel AssignStmt` | `OptLabel PrintStmt` | `OptLabel ReadStmt` 
         | `OptLabel IfStmt` | `OptLabel DoStmt` | `OptLabel GotoStmt` 
         | `OptLabel CallStmt` | `OptLabel ReturnStmt` | `OptLabel StopStmt` 
         | `OptLabel CONTINUE`

**Exemplos de Regras de Instrução:**
* `AssignStmt` → `VarRef '=' Expr`
* `IfStmt` → `IF '(' Expr ')' THEN StmtList (ELSE StmtList)? ENDIF`
* `DoStmt` → `DO INT_LITERAL ID '=' Expr ',' Expr (',' Expr)? StmtList INT_LITERAL CONTINUE`

**Expressões:**
* `Expr` → `Expr BinOp Expr` | `UnaryOp Expr` | `'(' Expr ')'` 
         | `FunctionCall` | `VarRef` | `Literal`
* `BinOp` → `+` | `-` | `*` | `/` | `**` | `.EQ.` | `.LT.` | `.AND.` | ...
* `Literal` → `INT_LITERAL` | `REAL_LITERAL` | `STRING_LITERAL` | `.TRUE.` | `.FALSE.`

## 5. Análise Semântica e Gestão de Memória
A fase de análise semântica representa o "núcleo lógico" do compilador, sendo responsável por garantir que a Árvore Sintática Abstrata (AST) respeita as regras de contexto e de tipagem da linguagem. Nesta etapa, o sistema valida a coerência das operações e prepara a infraestrutura necessária para a correta atribuição de endereços de memória.

### 5.1. Tabela de Símbolos e Gestão de Âmbitos (Scopes)

Para gerir a visibilidade de variáveis e subprogramas, implementámos uma **Tabela de Símbolos baseada numa *stack* de dicionários**. Esta estrutura é vital para suportar a funcionalidade de subprogramas (`FUNCTION` e `SUBROUTINE`), permitindo o isolamento de contextos.

* **Âmbitos Aninhados**: Sempre que o analisador entra no corpo de uma nova unidade de programa, é efetuado um `push_scope()`, criando um novo nível de visibilidade local.

* **Resolução de Identificadores**: A procura de nomes (*lookup*) é realizada do topo para a base da *stack* (de "dentro para fora"). Isto assegura que uma variável local oculta uma variável global homónima, respeitando o princípio de **Lexical Scoping**.

* **Limpeza de Contexto**: Ao finalizar o processamento de uma unidade, o âmbito é removido através de `pop_scope()`, garantindo que as variáveis locais deixam de ser acessíveis, libertando logicamente os seus recursos.

**Esquema Visual da Tabela de Símbolos:**
A título de exemplo, durante a compilação de uma função `CONVRT` chamada pelo programa `CONVERSOR`, a nossa estrutura de memória assume a seguinte disposição:

```text
Stack Top -> [ Âmbito Local: FUNCTION CONVRT ]
             |-- N: INTEGER (Parâmetro, Offset: -2)
             |-- B: INTEGER (Parâmetro, Offset: -1)
             |-- CONVRT: INTEGER (Retorno, Offset: 0)
             |-- VAL: INTEGER (Local, Offset: 1)

Stack Base -> [ Âmbito Global: PROGRAM CONVERSOR ]
             |-- NUM: INTEGER (Global, Offset: 0)
             |-- BASE: INTEGER (Global, Offset: 1)
             |-- CONVRT: FUNCTION (Subprograma)
```
### 5.2. Gestão de Memória e Cálculo de Offsets

Dado que a Máquina Virtual EWVM assenta numa arquitetura baseada em *stack*, o compilador deve determinar antecipadamente a localização de cada dado. O nosso analisador resolve esta necessidade através do cálculo sistemático de deslocamentos de memória (offsets).

#### Diferenciação Global/Local
- As variáveis declaradas no programa principal são assinaladas como **globais** (`is_global=True`), o que ditará a utilização das instruções `PUSHG` ou `STOREG`.
- Inversamente, as variáveis internas a funções são **locais**, sendo acedidas através de `PUSHL` ou `STOREL`.

#### Alocação de Espaço
- O compilador reserva espaço contíguo para cada identificador.
- No caso de variáveis escalares, o incremento é unitário.
- Para arrays, o sistema calcula o produto das dimensões declaradas para reservar o bloco de memória adequado.

#### Convenção de Chamada
- Por norma de implementação, o valor de retorno de uma **FUNCTION** é reservado na primeira posição relativa do seu âmbito local (`offset 0`).
- Os parâmetros são mapeados com offsets negativos em relação à base da *stack* local.

### 5.3. Validação de Fluxo e Rótulos (Labels)

Uma característica distintiva do Fortran 77 é a utilização frequente de rótulos numéricos para controlo de fluxo. A análise semântica realiza uma varredura preventiva para assegurar a integridade destes saltos.

#### Integridade do `GOTO`
- Antes de autorizar a geração de código para um desvio, o sistema valida se o rótulo de destino (**target label**) foi efetivamente declarado no corpo da unidade.
- Caso contrário, a compilação é interrompida com um erro semântico impeditivo.

#### Fecho de Ciclos `DO`
- O sistema confirma se o rótulo que identifica o fim de um ciclo **DO** corresponde, de facto, a uma instrução **CONTINUE** válida,
evitar estruturas de iteração incompletas ou logicamente inválidas.

## 6. Otimização de Código (Valorização)
Para cumprir com distinção a etapa de valorização exigida, o projeto integra um módulo robusto de otimização intermédia (`optimizer.py`) que processa a AST antes da geração de código, garantindo que o *assembly* gerado para a EWVM é o mais eficiente possível.

### 6.1. Rastreador e Relatório de Otimizações
O compilador foi dotado de um sistema de métricas rigoroso. O otimizador instancia um dicionário interno (`self.stats`) com contadores dedicados para seis categorias de otimização: *Constant Folding*, *Constant Propagation*, *Algebraic Simplification*, *Strength Reduction*, *Dead Code Elimination* e *Logical Simplification*.
Sempre que o motor de travessia (Visitor) simplifica um nó, o contador associado é incrementado (`self.optimizations_applied += 1`). No final da compilação, o orquestrador no `main.py` lê este estado e imprime no terminal uma árvore detalhada das otimizações poupadas à execução na VM, fornecendo total transparência ao processo de compilação.

### 6.2. Memória e Propagação de Constantes (Constant Propagation)
Implementou-se um mecanismo de otimização local e global recorrendo ao dicionário `self.constants`. Durante a travessia de atribuições (`AssignStmt`), sempre que uma variável recebe um valor literal (Inteiro, Real, Lógico ou String), o otimizador memoriza essa associação. 
Quando o sistema processa nós de referência a variáveis (`VarRef`), interroga este dicionário através do método `_apply_constant_propagation`. Se a variável constar na memória, a referência à memória (que resultaria num `PUSHG` ou `PUSHL` na VM) é liminarmente substituída pelo nó de valor literal, encurtando o tempo de execução e abrindo portas a simplificações algébraicas em cadeia.

### 6.3. Redução de Força (Strength Reduction)
A redução de força substitui operações custosas por equivalentes mais baratas computacionalmente. Neste compilador, o método `_apply_strength_reduction` avalia elevações (`**`).
* Se o expoente for `0`, a árvore devolve diretamente o literal `1`.
* Se o expoente for `1`, a árvore devolve a própria base.
* Se o expoente for superior a 1, a operação é desdobrada em multiplicações sequenciais encadeadas, evitando sobrecarregar o gerador de código com a emissão de ciclos iterativos de assembly na máquina alvo.

### 6.4. Demonstração Prática da Otimização
Para ilustrar o impacto do nosso módulo de otimização, considere-se o seguinte excerto de código Fortran que sofre *Constant Folding* e *Constant Propagation*:

**Código Fonte Fortran:**
```fortran
X = 10
Y = X + (2 * 3)
```

Resultado da Otimização:
Neste caso, o motor de Constant Folding deteta a operação estática (2 * 3) e reduz o nó para o literal 6. De seguida, a Constant Propagation reconhece que X tem o valor fixo de 10, substituindo a referência à variável. A AST é simplificada para Y = 16, evitando que a máquina virtual execute instruções PUSHG, PUSHI, MUL e ADD em tempo de execução, gerando diretamente:
```text
PUSHI 10
STOREG 0    // X
PUSHI 16
STOREG 1    // Y
```
## 7.Geração de Código para a Máquina Virtual EWVM

O módulo de geração de código (`codegen.py`) constitui a etapa final do pipeline, sendo responsável por converter a representação intermédia (AST) em código objeto compatível com a Máquina Virtual EWVM. Esta fase baseia-se num modelo de tradução direta, onde cada nó da árvore é visitado para emitir as instruções assembly correspondentes.

### 7.1. Arquitetura Baseada em *Stack* e Avaliação de Expressões

Dado que a EWVM opera sobre uma *stack* de operandos, a geração de código para expressões utiliza uma travessia em pós-ordem (esquerda, direita, raiz).

#### Cálculo Aritmético e Lógico
- Para qualquer operação binária (ex: `A + B`), o gerador emite primeiro as instruções para colocar os operandos no topo da *stack* (`PUSHL` ou `PUSHG`) e, de seguida, emite a instrução da operação (ex: `ADD`, `SUB`, `MUL`, `DIV`).

#### Mapeamento de Operadores
- O compilador traduz operadores relacionais do Fortran (como `.EQ.`, `.LT.`, `.GE.`) para as instruções equivalentes da máquina virtual (`EQUAL`, `INF`, `SUPEQ`), permitindo a avaliação de condições booleanas diretamente na *stack*.

### 7.2. Estruturas de Controlo de Fluxo

A tradução de comandos de alto nível para uma linguagem de baixo nível exige a gestão de etiquetas de salto (`labels`) e desvios condicionais.

#### Seleção Condicional (`IF-THEN-ELSE`)
- A implementação utiliza etiquetas geradas dinamicamente. A condição é avaliada e, caso o resultado no topo da *stack* seja zero, é executada uma instrução `JZ` (Jump if Zero) para o bloco ELSE ou para o fim da estrutura.

#### Iteração (`Ciclos DO`)
- O ciclo `DO` é traduzido numa estrutura composta por uma etiqueta de início, uma verificação de limite (`INFEQ`), o corpo do ciclo, o incremento da variável de controlo e um salto incondicional (`JUMP`) de regresso ao início.

#### Desvios Incondicionais (`GOTO`)
- São mapeados diretamente para a instrução `JUMP`, utilizando o rótulo numérico fornecido pelo programador, devidamente normalizado pelo compilador.


### 7.3. Implementação de Subprogramas e Convenção de Chamada

O suporte a `FUNCTION` e `SUBROUTINE` exigiu a implementação de uma convenção de chamada rigorosa para garantir a integridade da *stack* durante a execução.

#### Invocação
- A chamada de um subprograma é realizada através da instrução `PUSHA` (para carregar o endereço da subrotina) seguida de `CALL`. Os argumentos são colocados na *stack* antes da chamada, sendo posteriormente acedidos através de offsets negativos no âmbito local do subprograma.

#### Retorno de Valores
- No caso das funções, o valor de retorno é armazenado numa posição específica da *stack* local e colocado no topo da *stack* imediatamente antes da execução da instrução `RETURN`, permitindo que o programa chamador utilize o resultado em expressões complexas.

### 7.4. Acesso à Memória e Funções Intrínsecas

O gerador distingue entre variáveis escalares e arrays. Para os arrays, o compilador emite instruções de cálculo do índice e utiliza `LOADN` ou `STOREN` para aceder às posições específicas da memória indexada.
Além disso, foram mapeadas diversas funções intrínsecas (como `MOD`, `SQRT`, `ABS`, `INT`, `MAX`, `MIN`) diretamente para instruções nativas da EWVM ou sequências otimizadas, garantindo o suporte às necessidades computacionais dos exemplos fornecidos no enunciado.

## 8. Dificuldades Encontradas e Soluções Adotadas

Durante o desenvolvimento deste compilador, a equipa deparou-se com desafios inerentes não só à natureza histórica da linguagem Fortran 77, mas também às limitações teóricas das ferramentas de geração de compiladores. As principais dificuldades e respetivas soluções foram:

### 8.1. Ambiguidade Sintática: Acesso a Arrays vs. Chamadas de Função
O maior desafio arquitetural residiu na ambiguidade sintática do Fortran no que concerne à distinção entre a invocação de subprogramas e o acesso a elementos de vetores (*arrays*). Sintaticamente, ambas as construções partilham a mesma assinatura exata: `Identificador(Argumentos/Índices)`. 

Como o analisador sintático (LALR) opera de forma independente do contexto, é teoricamente incapaz de desambiguar esta construção. A solução adotada consistiu em **adiar a decisão computacional**: o *parser* foi instruído a construir provisoriamente um nó do tipo `FunctionCall` por defeito. Posteriormente, durante a travessia semântica, o compilador interroga a Tabela de Símbolos; caso o identificador esteja registado como uma variável, o nó é dinamicamente reinterpretado como um acesso à memória, caso contrário, prossegue a validação como uma chamada de função.

### 8.2. Validação de Saltos e *Labels* Desconexos
O Fortran 77 permite o uso liberal de rótulos numéricos (*labels*) e instruções de desvio incondicional (`GOTO`). A dificuldade prende-se com o facto de um programador poder invocar um salto para uma linha que ainda não foi lida pelo *parser* ou que não existe de todo.
Para mitigar falhas de execução na máquina virtual (EWVM), implementámos um mecanismo de pré-processamento na fase semântica: a função `_collect_labels` efetua uma varredura exaustiva à árvore para recolher todos os rótulos instanciados. Só depois desta recolha é que os alvos dos comandos `GOTO` e dos ciclos `DO` são validados, garantindo a integridade total do grafo de fluxo de controlo.

### 8.3. Conflitos de Redução no Gerador de Gramática
Na fase inicial de construção da gramática no módulo `ply.yacc`, deparámo-nos com conflitos do tipo *shift/reduce* (típicos de ambiguidades clássicas como o *dangling-else* e a hierarquia de operadores aritméticos). A resolução não passou por complicar a gramática com regras redundantes, mas sim por uma afinação minuciosa da tabela estrutural de precedências (`precedence`), forçando a máquina de estados a dar prioridade à associação matemática correta, mantendo a árvore limpa e o gerador de tabelas otimizado.

## 9. Instruções de Utilização e Ambiente de Testes

O compilador foi desenvolvido para ser executado de forma multiplataforma, exigindo apenas o interpretador Python 3.10 (ou superior). Para garantir a integridade do sistema operativo e evitar conflitos de pacotes globais (em conformidade com a PEP 668), recomenda-se a configuração de um ambiente virtual isolado.

### 9.1. Configuração do Ambiente e Dependências
No terminal, a partir da diretoria raiz do projeto, devem ser executados os seguintes comandos para criar o ambiente virtual e instalar a biblioteca PLY:

```bash
# 1. Criar o ambiente virtual (venv)
python3 -m venv venv

# 2. Ativar o ambiente virtual (em macOS/Linux)
source venv/bin/activate

# 3. Instalar a dependência 
pip install ply
```

### 9.2. Compilação e Execução

Com o ambiente virtual ativado e as dependências instaladas, invoca-se o módulo principal:

```bash
python main.py <tests/ficheiro.f77>
```

### Ficheiros de teste

Todos os exemplos fornecidos no enunciado são suportados e compilam corretamente:

| Programa | Ficheiro | Funcionalidade testada |
|---------|----------|----------------------|
| Olá Mundo | `teste1.f77` | `PRINT`, strings |
| Fatorial | `teste2.f77` | `DO`, `READ`, variáveis inteiras |
| É primo? | `teste3.f77` | `IF-THEN-ELSE`, `GOTO`, `.AND.`, `MOD` |
| Soma de array | `teste4.f77` | Arrays, `DO`, `READ` com índices |
| Conversor de bases | `teste5.f77` | `FUNCTION`, chamada de função, `GOTO` |

**Resultado Esperado:** Se a compilação for bem-sucedida, o compilador irá gerar o código assembly (.vm), imprimi-lo no terminal e apresentar, no final, o resumo estruturado de todas as otimizações aplicadas à árvore sintática (ex: ├─ Constant Folding: 4). O ficheiro .vm encontra-se então pronto para ser executado na EWVM.


## 10. Conclusão

O desenvolvimento deste compilador cumpriu integralmente os requisitos propostos para a unidade curricular, concretizando com sucesso a tradução de uma linguagem histórica (Fortran 77) para instruções assembly da máquina virtual EWVM.

A adoção de uma arquitetura modular — separando rigorosamente a análise léxica, sintática, semântica, a fase de otimização e a geração de código — revelou-se crucial para o diagnóstico de erros e para a implementação fluida de mecanismos complexos. Destaca-se o sucesso na implementação das componentes de valorização, nomeadamente o suporte robusto a matrizes (*arrays*) e a subprogramas (`FUNCTION` e `SUBROUTINE`), que exigiram uma gestão avançada de memória e de âmbitos locais na Tabela de Símbolos.

A este sucesso junta-se a nova camada de valorização implementada: o módulo de otimização de código (`optimizer.py`). A capacidade de efetuar *Constant Folding*, Propagação de Constantes e Eliminação de Código Morto, aliada a um sistema transparente de métricas e relatórios, eleva o nível técnico do compilador, dotando-o de características próprias de ferramentas profissionais.

Adicionalmente, as opções de design arquitetural, como o suporte a free-form, a conversão de identificadores (*case-insensitivity*) e a resolução dinâmica de ambiguidades semânticas, dotaram a ferramenta de uma flexibilidade próxima dos compiladores reais.

Em suma, o projeto consolidou a aplicação prática da teoria das linguagens formais e autómatos, resultando numa "fábrica de software" robusta, capaz de compilar, otimizar e executar corretamente todos os programas de demonstração exigidos, desde o cálculo de fatoriais até à conversão de bases numéricas.
