"""
Parser para Fortran 77 (Free-form) usando a biblioteca PLY.
"""
import ply.yacc
from typing import Optional
from .lexer import tokens, create_lexer
from .ast import *

# ---------------------------------------------------------------------------
# Precedência de Operadores
# ---------------------------------------------------------------------------
# Define a ordem de resolução das contas (do menos prioritário para o mais prioritário)
precedence = (
    ('left',  'OR'),
    ('left',  'AND'),
    ('right', 'NOT'),
    ('left',  'EQ', 'NE', 'LT', 'LE', 'GT', 'GE'),
    ('left',  'PLUS', 'MINUS'),
    ('left',  'STAR', 'SLASH'),
    ('right', 'UMINUS'),
    ('right', 'POWER'),
)

# ---------------------------------------------------------------------------
# Regras de Quebra de Linha
# ---------------------------------------------------------------------------
def p_nls(p):
    """nls : NL
           | nls NL"""
    # Absorve múltiplas quebras de linha seguidas
    p[0] = None

# ---------------------------------------------------------------------------
# Estrutura do Programa
# ---------------------------------------------------------------------------
def p_program(p):
    """program : unit_list
               | nls unit_list"""
    units = p[1] if len(p) == 2 else p[2]
    main = next((u for u in units if u.kind == 'program'), units[0])
    p[0] = Program(name=main.name, units=units)

def p_unit_list_one(p):
    """unit_list : unit"""
    p[0] = [p[1]]

def p_unit_list_many(p):
    """unit_list : unit_list unit"""
    p[0] = p[1] + [p[2]]

# ---------------------------------------------------------------------------
# Unidades de Código (Program, Subroutine, Function)
# ---------------------------------------------------------------------------
def p_unit_program(p):
    """unit : PROGRAM ID nls decl_list stmt_list END nls
            | PROGRAM ID nls decl_list stmt_list END"""
    # Bloco principal do programa
    p[0] = ProgramUnit(kind='program', name=p[2], params=[],
                       return_type=None, declarations=p[4], body=p[5])

def p_unit_subroutine(p):
    """unit : SUBROUTINE ID LPAREN param_list RPAREN nls decl_list stmt_list END nls
            | SUBROUTINE ID LPAREN param_list RPAREN nls decl_list stmt_list END"""
    # Subrotina (não devolve valor)
    p[0] = ProgramUnit(kind='subroutine', name=p[2], params=p[4],
                       return_type=None, declarations=p[7], body=p[8])

def p_unit_function(p):
    """unit : type_spec FUNCTION ID LPAREN param_list RPAREN nls decl_list stmt_list END nls
            | type_spec FUNCTION ID LPAREN param_list RPAREN nls decl_list stmt_list END"""
    # Função (devolve um valor do tipo type_spec)
    p[0] = ProgramUnit(kind='function', name=p[3], params=p[5],
                       return_type=p[1], declarations=p[8], body=p[9])

# ---------------------------------------------------------------------------
# Parâmetros e Declarações
# ---------------------------------------------------------------------------
def p_param_list_empty(p):
    """param_list :"""
    p[0] = []

def p_param_list_one(p):
    """param_list : ID"""
    p[0] = [p[1]]

def p_param_list_many(p):
    """param_list : param_list COMMA ID"""
    p[0] = p[1] + [p[3]]

def p_decl_list_empty(p):
    """decl_list :"""
    p[0] = []

def p_decl_list_many(p):
    """decl_list : decl_list decl"""
    p[0] = p[1] + [p[2]]

def p_decl(p):
    """decl : type_spec vardecl_list nls"""
    # Junta o tipo de dados à lista de variáveis declaradas
    p[0] = Declaration(var_type=p[1], variables=p[2])

def p_type_spec(p):
    """type_spec : INTEGER
                 | REAL
                 | LOGICAL
                 | CHARACTER"""
    # Mapeia as palavras-chave do Fortran para os nossos tipos internos (Enums)
    mapping = {
        'INTEGER':   FortranType.INTEGER,
        'REAL':      FortranType.REAL,
        'LOGICAL':   FortranType.LOGICAL,
        'CHARACTER': FortranType.CHARACTER,
    }
    p[0] = mapping[p[1]]

def p_vardecl_list_one(p):
    """vardecl_list : vardecl"""
    p[0] = [p[1]]

def p_vardecl_list_many(p):
    """vardecl_list : vardecl_list COMMA vardecl"""
    p[0] = p[1] + [p[3]]

def p_vardecl_scalar(p):
    """vardecl : ID"""
    p[0] = VarDecl(name=p[1], dimensions=[])

def p_vardecl_array(p):
    """vardecl : ID LPAREN dim_list RPAREN"""
    # Deteta a declaração de vetores/matrizes (ex: LISTA(10))
    p[0] = VarDecl(name=p[1], dimensions=p[3])

def p_dim_list_one(p):
    """dim_list : INT_LITERAL"""
    p[0] = [p[1]]

def p_dim_list_many(p):
    """dim_list : dim_list COMMA INT_LITERAL"""
    p[0] = p[1] + [p[3]]

# ---------------------------------------------------------------------------
# Instruções (Statements)
# ---------------------------------------------------------------------------
def p_stmt_list_empty(p):
    """stmt_list :"""
    p[0] = []

def p_stmt_list_many(p):
    """stmt_list : stmt_list stmt"""
    # Ignora quebras de linha soltas (que devolvem None)
    p[0] = p[1] + ([p[2]] if p[2] is not None else [])

def p_stmt_blank(p):
    """stmt : nls"""
    p[0] = None

def p_stmt_assign(p):
    """stmt : opt_label ID EQUALS expr nls"""
    # Atribuição escalar (ex: X = 10)
    p[0] = AssignStmt(label=p[1], target=VarRef(name=p[2]), value=p[4])

def p_stmt_assign_array(p):
    """stmt : opt_label ID LPAREN expr_list RPAREN EQUALS expr nls"""
    # Atribuição num índice do array (ex: LISTA(1) = 10)
    p[0] = AssignStmt(label=p[1], target=VarRef(name=p[2], indices=p[4]), value=p[7])

def p_stmt_print(p):
    """stmt : opt_label PRINT STAR COMMA expr_list nls"""
    p[0] = PrintStmt(label=p[1], items=p[5])

def p_stmt_print_empty(p):
    """stmt : opt_label PRINT STAR nls"""
    p[0] = PrintStmt(label=p[1], items=[])

def p_stmt_read(p):
    """stmt : opt_label READ STAR COMMA expr_list nls"""
    # Trata leituras do teclado, convertendo FunctionCalls fantasma em acessos a Arrays
    targets = []
    for e in p[5]:
        if isinstance(e, VarRef):
            targets.append(e)
        elif isinstance(e, FunctionCall):
            targets.append(VarRef(name=e.name, indices=e.args))
    p[0] = ReadStmt(label=p[1], targets=targets)
    
def p_stmt_if(p):
    """stmt : opt_label IF LPAREN expr RPAREN THEN nls stmt_list ENDIF nls"""
    # Bloco IF simples
    p[0] = IfStmt(label=p[1], condition=p[4], then_body=p[8], else_body=[])

def p_stmt_if_else(p):
    """stmt : opt_label IF LPAREN expr RPAREN THEN nls stmt_list ELSE nls stmt_list ENDIF nls"""
    # Bloco IF com ELSE
    p[0] = IfStmt(label=p[1], condition=p[4], then_body=p[8], else_body=p[11])

def p_stmt_if_goto(p):
    """stmt : opt_label IF LPAREN expr RPAREN GOTO INT_LITERAL nls"""
    # IF lógico do Fortran antigo (se verdadeiro, salta para a label)
    p[0] = IfStmt(label=p[1], condition=p[4], then_body=[GotoStmt(label=None, target=p[7])], else_body=[])

def p_stmt_do(p):
    """stmt : opt_label DO INT_LITERAL ID EQUALS expr COMMA expr nls do_body"""
    # Ciclo DO sem step (incremento default)
    end_lbl, body = p[10]
    if p[3] != end_lbl:
        print(f"[Aviso Parser] A label do DO ({p[3]}) não bate certo com o CONTINUE ({end_lbl})")
    p[0] = DoStmt(label=p[1], end_label=p[3], var=p[4], start=p[6], stop=p[8], step=None, body=body)

def p_stmt_do_step(p):
    """stmt : opt_label DO INT_LITERAL ID EQUALS expr COMMA expr COMMA expr nls do_body"""
    # Ciclo DO com step definido
    end_lbl, body = p[12]
    if p[3] != end_lbl:
        print(f"[Aviso Parser] A label do DO ({p[3]}) não bate certo com o CONTINUE ({end_lbl})")
    p[0] = DoStmt(label=p[1], end_label=p[3], var=p[4], start=p[6], stop=p[8], step=p[10], body=body)

def p_do_body(p):
    """do_body : stmt_list INT_LITERAL CONTINUE nls"""
    # Agrupa o corpo do ciclo DO com a sua label final (CONTINUE)
    p[0] = (p[2], p[1])

def p_stmt_goto(p):
    """stmt : opt_label GOTO INT_LITERAL nls"""
    p[0] = GotoStmt(label=p[1], target=p[3])

def p_stmt_continue(p):
    """stmt : opt_label CONTINUE nls"""
    p[0] = ContinueStmt(label=p[1])

def p_stmt_return(p):
    """stmt : opt_label RETURN nls"""
    p[0] = ReturnStmt(label=p[1])

def p_stmt_stop(p):
    """stmt : opt_label STOP nls"""
    p[0] = StopStmt(label=p[1])

def p_stmt_call_args(p):
    """stmt : opt_label CALL ID LPAREN expr_list RPAREN nls"""
    p[0] = CallStmt(label=p[1], name=p[3], args=p[5])

def p_stmt_call_noargs(p):
    """stmt : opt_label CALL ID nls"""
    p[0] = CallStmt(label=p[1], name=p[3], args=[])

def p_opt_label_none(p):
    """opt_label :"""
    p[0] = None

def p_opt_label_int(p):
    """opt_label : INT_LITERAL"""
    p[0] = p[1]

# ---------------------------------------------------------------------------
# Expressões (Matemática e Lógica)
# ---------------------------------------------------------------------------
def p_expr_list_one(p):
    """expr_list : expr"""
    p[0] = [p[1]]

def p_expr_list_many(p):
    """expr_list : expr_list COMMA expr"""
    p[0] = p[1] + [p[3]]

def p_expr_binop(p):
    """expr : expr PLUS  expr
            | expr MINUS expr
            | expr STAR  expr
            | expr SLASH expr
            | expr POWER expr
            | expr EQ    expr
            | expr NE    expr
            | expr LT    expr
            | expr LE    expr
            | expr GT    expr
            | expr GE    expr
            | expr AND   expr
            | expr OR    expr"""
    p[0] = BinaryExpr(op=p[2], left=p[1], right=p[3])

def p_expr_uminus(p):
    """expr : MINUS expr %prec UMINUS"""
    p[0] = UnaryExpr(op='-', operand=p[2])

def p_expr_not(p):
    """expr : NOT expr"""
    p[0] = UnaryExpr(op='.NOT.', operand=p[2])

def p_expr_paren(p):
    """expr : LPAREN expr RPAREN"""
    p[0] = p[2]

def p_expr_int(p):
    """expr : INT_LITERAL"""
    p[0] = IntLiteral(value=p[1])

def p_expr_real(p):
    """expr : REAL_LITERAL"""
    p[0] = RealLiteral(value=p[1])

def p_expr_true(p):
    """expr : TRUE"""
    p[0] = LogicalLiteral(value=True)

def p_expr_false(p):
    """expr : FALSE"""
    p[0] = LogicalLiteral(value=False)

def p_expr_string(p):
    """expr : STRING_LITERAL"""
    p[0] = StringLiteral(value=p[1])

def p_expr_funcall(p):
    """expr : ID LPAREN expr_list RPAREN"""
    p[0] = FunctionCall(name=p[1], args=p[3])

def p_expr_var(p):
    """expr : ID"""
    p[0] = VarRef(name=p[1])

# ---------------------------------------------------------------------------
# Tratamento de Erros
# ---------------------------------------------------------------------------
def p_error(p):
    # Apanha erros de sintaxe (tokens em locais inesperados)
    if p:
        print(f"[Erro de Sintaxe] Encontrado '{p.value}' em local inválido (linha {p.lineno})")
    else:
        print("[Erro de Sintaxe] Fim de ficheiro inesperado (EOF)")

# ---------------------------------------------------------------------------
# Inicialização do Parser
# ---------------------------------------------------------------------------
parser = ply.yacc.yacc(start='program')

def parse(source: str) -> Optional[Program]:
    # Cria o lexer e arranca a conversão do código fonte para a AST
    lx = create_lexer()
    return parser.parse(source, lexer=lx)