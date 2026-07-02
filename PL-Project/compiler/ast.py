"""
Definição da Árvore Sintática Abstrata (AST) para Fortran 77.
As dataclasses representam os nós da árvore gerada pelo Parser.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Literal

# ---------------------------------------------------------------------------
# Tipos de Dados
# ---------------------------------------------------------------------------
class FortranType(IntEnum):
    # Enumeração dos tipos de dados suportados pelo compilador
    INTEGER  = 0
    REAL     = 1
    LOGICAL  = 2
    CHARACTER = 3

# ---------------------------------------------------------------------------
# Estrutura Global do Programa
# ---------------------------------------------------------------------------
@dataclass
class Program:
    # Nó raiz da árvore: contém o programa principal e todas as funções/subrotinas
    name: str
    units: list[ProgramUnit]

@dataclass
class ProgramUnit:
    # Representa um bloco de código autónomo (PROGRAM, FUNCTION ou SUBROUTINE)
    kind: Literal['program', 'function', 'subroutine']
    name: str
    params: list[str]                        # Argumentos recebidos (vazio se for PROGRAM)
    return_type: FortranType | None          # Apenas aplicável a FUNCTION
    declarations: list[Declaration]          # Variáveis declaradas no topo do bloco
    body: list[Statement]                    # Corpo de instruções a executar

# ---------------------------------------------------------------------------
# Declarações e Variáveis
# ---------------------------------------------------------------------------
@dataclass
class Declaration:
    # Agrupa várias variáveis declaradas na mesma linha com o mesmo tipo
    var_type: FortranType
    variables: list[VarDecl]

@dataclass
class VarDecl:
    # Detalhes de uma variável específica na memória
    name: str
    dimensions: list[int] = field(default_factory=list)  # Lista vazia = escalar, com valores = array
    scope_offset: int = -1                               # Posição na Stack (calculada no Semantic)
    is_global: bool = True                               # True se pertencer ao MAIN, False se local

# ---------------------------------------------------------------------------
# Expressões (Contas, Valores e Comparações)
# ---------------------------------------------------------------------------
BinaryOp = Literal['+', '-', '*', '/', '**',
                   '.EQ.', '.NE.', '.LT.', '.LE.', '.GT.', '.GE.',
                   '.AND.', '.OR.']
UnaryOp  = Literal['+', '-', '.NOT.']

@dataclass
class IntLiteral:
    value: int

@dataclass
class RealLiteral:
    value: float

@dataclass
class LogicalLiteral:
    value: bool   # Representa .TRUE. ou .FALSE.

@dataclass
class StringLiteral:
    value: str

@dataclass
class VarRef:
    # Referência a uma variável ou a uma posição de um array (ex: LISTA(I))
    name: str
    indices: list[Expression] = field(default_factory=list)
    decl: VarDecl | None = None  # Ligação à declaração original (preenchida pelo Semantic)

@dataclass
class BinaryExpr:
    # Operação entre duas expressões (ex: A + B, X .LT. 10)
    op: BinaryOp
    left: Expression
    right: Expression

@dataclass
class UnaryExpr:
    # Operação aplicada a uma única expressão (ex: -A, .NOT. B)
    op: UnaryOp
    operand: Expression

@dataclass
class FunctionCall:
    # Chamada a uma função que devolve um valor no meio de uma conta
    name: str
    args: list[Expression]

# Agrupamento de tudo o que pode ser avaliado para gerar um valor
Expression = IntLiteral | RealLiteral | LogicalLiteral | StringLiteral | \
             VarRef | BinaryExpr | UnaryExpr | FunctionCall

# ---------------------------------------------------------------------------
# Instruções (Statements)
# ---------------------------------------------------------------------------
@dataclass
class AssignStmt:
    # Atribuição de valores (ex: X = 10)
    label: int | None
    target: VarRef
    value: Expression

@dataclass
class PrintStmt:
    # Escrita no ecrã (ex: PRINT *, "Ola", X)
    label: int | None
    items: list[Expression]

@dataclass
class ReadStmt:
    # Leitura do teclado (ex: READ *, X, Y)
    label: int | None
    targets: list[VarRef]

@dataclass
class IfStmt:
    # Estrutura condicional (IF condição THEN ... ELSE ... ENDIF)
    label: int | None
    condition: Expression
    then_body: list[Statement]
    else_body: list[Statement]

@dataclass
class DoStmt:
    # Ciclo de repetição Fortran (DO 10 I = 1, 10, 2)
    label: int | None
    end_label: int          # A label numérica do CONTINUE que fecha o ciclo
    var: str
    start: Expression
    stop: Expression
    step: Expression | None
    body: list[Statement]

@dataclass
class GotoStmt:
    # Salto incondicional de fluxo
    label: int | None
    target: int

@dataclass
class ContinueStmt:
    # Âncora vazia, normalmente usada para fechar ciclos DO
    label: int | None

@dataclass
class ReturnStmt:
    # Devolve o controlo a quem chamou a Função/Subrotina
    label: int | None

@dataclass
class StopStmt:
    # Termina a execução do programa imediatamente
    label: int | None

@dataclass
class CallStmt:
    # Invoca uma Subrotina que não devolve valor (ex: CALL INIT())
    label: int | None
    name: str
    args: list[Expression]

# Agrupamento de todas as instruções executáveis do nosso Fortran
Statement = AssignStmt | PrintStmt | ReadStmt | IfStmt | DoStmt | \
            GotoStmt | ContinueStmt | ReturnStmt | StopStmt | CallStmt