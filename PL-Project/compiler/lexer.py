"""
Analisador Lexical (Lexer) para Fortran 77 (Formato Livre).
Usa a biblioteca PLY para ler o ficheiro e parti-lo numa lista de tokens.
"""
import re
import ply.lex
from ply.lex import LexToken

# ---------------------------------------------------------------------------
# Palavras Reservadas do Fortran
# ---------------------------------------------------------------------------
reserved = {
    'PROGRAM'    : 'PROGRAM',
    'END'        : 'END',
    'INTEGER'    : 'INTEGER',
    'REAL'       : 'REAL',
    'LOGICAL'    : 'LOGICAL',
    'CHARACTER'  : 'CHARACTER',
    'IF'         : 'IF',
    'THEN'       : 'THEN',
    'ELSE'       : 'ELSE',
    'ENDIF'      : 'ENDIF',
    'DO'         : 'DO',
    'CONTINUE'   : 'CONTINUE',
    'GOTO'       : 'GOTO',
    'PRINT'      : 'PRINT',
    'READ'       : 'READ',
    'RETURN'     : 'RETURN',
    'STOP'       : 'STOP',
    'CALL'       : 'CALL',
    'SUBROUTINE' : 'SUBROUTINE',
    'FUNCTION'   : 'FUNCTION',
}

# ---------------------------------------------------------------------------
# Lista Completa de Tokens
# ---------------------------------------------------------------------------
tokens = list(reserved.values()) + [
    # Literais (Valores)
    'INT_LITERAL', 'REAL_LITERAL', 'TRUE', 'FALSE', 'STRING_LITERAL',
    # Identificadores (Nomes de variáveis e funções)
    'ID',
    # Operadores Relacionais e Lógicos
    'EQ', 'NE', 'LT', 'LE', 'GT', 'GE', 'AND', 'OR', 'NOT',
    # Matemática
    'POWER',
    # Pontuação e Símbolos
    'COMMA', 'LPAREN', 'RPAREN', 'EQUALS', 'STAR', 'SLASH', 'PLUS', 'MINUS',
    # Fim de linha (crucial para o nosso Parser)
    'NL',
]

# ---------------------------------------------------------------------------
# Tokens Simples (Mapeamento Direto)
# ---------------------------------------------------------------------------
t_POWER  = r'\*\*'
t_STAR   = r'\*'
t_SLASH  = r'/'
t_PLUS   = r'\+'
t_MINUS  = r'-'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_COMMA  = r','
t_EQUALS = r'='

# Ignora espaços em branco e tabs
t_ignore = ' \t\r'

# ---------------------------------------------------------------------------
# Operadores Lógicos e Relacionais (.EQ., .AND., etc.)
# ---------------------------------------------------------------------------
def t_EQ(t: LexToken) -> LexToken:
    r'\.EQ\.'
    return t

def t_NE(t: LexToken) -> LexToken:
    r'\.NE\.'
    return t

def t_LE(t: LexToken) -> LexToken:
    r'\.LE\.'
    return t

def t_LT(t: LexToken) -> LexToken:
    r'\.LT\.'
    return t

def t_GE(t: LexToken) -> LexToken:
    r'\.GE\.'
    return t

def t_GT(t: LexToken) -> LexToken:
    r'\.GT\.'
    return t

def t_AND(t: LexToken) -> LexToken:
    r'\.AND\.'
    return t

def t_OR(t: LexToken) -> LexToken:
    r'\.OR\.'
    return t

def t_NOT(t: LexToken) -> LexToken:
    r'\.NOT\.'
    return t

def t_TRUE(t: LexToken) -> LexToken:
    r'\.TRUE\.'
    t.value = True
    return t

def t_FALSE(t: LexToken) -> LexToken:
    r'\.FALSE\.'
    t.value = False
    return t

# ---------------------------------------------------------------------------
# Identificadores e Literais
# ---------------------------------------------------------------------------
def t_ID(t: LexToken) -> LexToken:
    r'[A-Za-z][A-Za-z0-9_]*'
    # Verifica se a palavra é uma keyword (ex: IF). Se não for, assume que é uma variável (ID).
    t.type = reserved.get(t.value.upper(), 'ID')
    t.value = t.value.upper()
    return t

def t_REAL_LITERAL(t: LexToken) -> LexToken:
    r'[0-9]+\.[0-9]*([eE][+-]?[0-9]+)?|[0-9]+[eE][+-]?[0-9]+'
    # Tem de vir definido antes do INT_LITERAL no código para o PLY apanhar os decimais primeiro
    t.value = float(t.value)
    return t

def t_STRING_LITERAL(t: LexToken) -> LexToken:
    r"'([^']|'')*'"
    # Remove as aspas simples exteriores e converte duas aspas juntas ('') numa aspa de texto
    t.value = t.value[1:-1].replace("''", "'")
    return t

def t_INT_LITERAL(t: LexToken) -> LexToken:
    r'[0-9]+'
    t.value = int(t.value)
    return t

# ---------------------------------------------------------------------------
# Comentários e Quebras de Linha
# ---------------------------------------------------------------------------
def t_COMMENT(t: LexToken) -> None:
    r'!.*'
    # Apanha tudo desde o '!' até ao fim da linha e descarta (não gera token)
    pass

def t_NL(t: LexToken) -> LexToken:
    r'\n+'
    # Vai contando as quebras de linha para podermos dizer a linha certa nos avisos de erro
    t.lexer.lineno += len(t.value)
    return t

# ---------------------------------------------------------------------------
# Tratamento de Erros
# ---------------------------------------------------------------------------
def t_error(t: LexToken) -> None:
    print(f"[Lexer] Caráter ilegal '{t.value[0]}' na linha {t.lexer.lineno}")
    # Ignora o caráter estranho e continua para não rebentar o compilador
    t.lexer.skip(1)

# ---------------------------------------------------------------------------
# Inicialização
# ---------------------------------------------------------------------------
# Fortran é case-insensitive, logo ligamos a flag do regex para ignorar maiúsculas/minúsculas
lexer = ply.lex.lex(reflags=re.IGNORECASE)

def create_lexer() -> ply.lex.Lexer:
    # Função que exporta o lexer fresquinho para ser usado pelo nosso parser
    return ply.lex.lex(reflags=re.IGNORECASE)