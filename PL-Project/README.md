# PL-25-26-Grupo17
# Compilador Fortran 77 → EWVM

Projeto de Processamento de Linguagens 2026 — Universidade do Minho.

**Elementos:**
* Gonçalo Sá (A107376)
* José Rocha (A106887)
* Pedro Pereira (A107332)

---

## Estrutura do Projeto

```text
PL-25-26-Grupo17/
├── main.py                    ← entry point do compilador
├── requirements.txt           ← dependências Python
├── Relatorio-PL-25-26-G17.md ← Relatório detalhado do projeto
├── compiler/
│   ├── ast.py                 ← nós da AST (árvore sintática abstrata)
│   ├── lexer.py               ← análise léxica (ply.lex)
│   ├── parser.py              ← análise sintática (ply.yacc)
│   ├── semantic.py            ← análise semântica
│   ├── symboltable.py         ← tabela de símbolos
│   ├── optimizer.py           ← otimização de código (folding, propagação, etc.)
│   └── codegen.py             ← geração de código EWVM
└── tests/
    ├── teste1.f77             ← Exemplo 1: Olá Mundo
    ├── teste1.vm              ← Código EWVM gerado
    ├── teste2.f77             ← Exemplo 2: Fatorial
    ├── teste2.vm              ← Código EWVM gerado
    ├── teste3.f77             ← Exemplo 3: Verificação de primo
    ├── teste3.vm              ← Código EWVM gerado
    ├── teste4.f77             ← Exemplo 4: Soma de array
    ├── teste4.vm              ← Código EWVM gerado
    ├── teste5.f77             ← Exemplo 5: Conversão de bases (com FUNCTION)
    ├── teste5.vm              ← Código EWVM gerado
    ├── opt1_folding.f77       ← Teste: Constant Folding
    ├── opt2_propagation.f77   ← Teste: Constant Propagation
    ├── opt3_algebraic.f77     ← Teste: Algebraic Simplification
    ├── opt4_strength.f77      ← Teste: Strength Reduction + fallback dinâmico
    ├── opt5_deadcode.f77      ← Teste: Dead Code Elimination
    └── opt6_logical.f77       ← Teste: Logical Simplification
```

---

## Instalação e Execução

### 8.1. Configuração do Ambiente e Dependências
No terminal, a partir da diretoria raiz do projeto, devem ser executados os seguintes comandos para criar o ambiente virtual e instalar a biblioteca PLY:

```bash
# 1. Criar o ambiente virtual (venv)
python3 -m venv venv

# 2. Ativar o ambiente virtual (em macOS/Linux)
source venv/bin/activate

# 3. Instalar a dependência 
pip install ply
```

### 8.2. Compilação e Execução
Com o ambiente ativado, o processo de compilação é iniciado invocando o módulo principal e passando o caminho do ficheiro Fortran como argumento:

```bash
python main.py <tests/ficheiro.f77>
```

---
## Ficheiros de teste

### Exemplos do enunciado
Todos os exemplos fornecidos no enunciado são suportados e compilam corretamente:

| Programa | Ficheiro | Funcionalidade testada |
|---------|----------|----------------------|
| Olá Mundo | `teste1.f77` | `PRINT`, strings |
| Fatorial | `teste2.f77` | `DO`, `READ`, variáveis inteiras |
| É primo? | `teste3.f77` | `IF-THEN-ELSE`, `GOTO`, `.AND.`, `MOD` |
| Soma de array | `teste4.f77` | Arrays, `DO`, `READ` com índices |
| Conversor de bases | `teste5.f77` | `FUNCTION`, chamada de função, `GOTO` |

### Testes de otimização
Cada ficheiro valida uma otimização específica do compilador, com comentários que explicam o output esperado e o código `.vm` gerado:

| Otimização | Ficheiro | O que valida |
|---------|----------|----------------------|
| Constant Folding | `opt1.f77` | Expressões literais resolvidas em compile-time — sem `ADD`/`MUL` no `.vm` |
| Constant Propagation | `opt2.f77` | Variáveis substituídas por valores — sem `PUSHG` nas expressões |
| Algebraic Simplification | `opt3.f77` | `X+0→X`, `X*1→X`, `X*0→0` — operações inúteis eliminadas |
| Strength Reduction | `opt4.f77` | `X**N` literal → multiplicações; `X**N` dinâmico → ciclo no codegen |
| Dead Code Elimination | `opt5.f77` | Ramos `IF(.TRUE./.FALSE.)` removidos — strings `"ERRO"` ausentes no `.vm` |
| Logical Simplification | `opt6.f77` | Dupla negação, inversão relacional, `NOT` de literal |

---

## Documentação Técnica
Para informações detalhadas sobre a arquitetura do compilador, decisões de implementação (gramática e resolução de ambiguidades), gestão de memória e otimizações efetuadas, por favor consulte o ficheiro **[`Relatorio-PL-25-26-G17.md`](Relatorio-PL-25-26-G17.md)** incluído neste repositório.