"""
Symbol table for Fortran 77 compiler.
"""
from typing import Optional, List, Dict, Union
from .ast import FortranType, VarDecl, ProgramUnit

class SymbolTableError(Exception):
    pass

class Symbol:
    def __init__(self, name: str, sym_type: Union[FortranType, str], decl: Optional[Union[VarDecl, ProgramUnit]] = None) -> None:
        # Guarda o nome, o tipo (INTEGER, REAL, 'function', etc.) e o nó da AST
        self.name: str = name
        self.sym_type: Union[FortranType, str] = sym_type
        self.decl: Optional[Union[VarDecl, ProgramUnit]] = decl

class SymbolTable:
    def __init__(self) -> None:
        # Inicializa a pilha de escopos com o âmbito global vazio no fundo
        self.scopes: List[Dict[str, Symbol]] = [{}]

    def push_scope(self) -> None:
        # Adiciona um novo nível de visibilidade local (ex: ao entrar numa função)
        self.scopes.append({})

    def pop_scope(self) -> None:
        # Remove o nível local atual, mas protege o global (índice 0)
        if len(self.scopes) > 1:
            self.scopes.pop()

    def add_variable(self, decl: VarDecl, var_type: FortranType) -> Symbol:
        # Regista uma nova variável no escopo atual e previne duplicações
        name = decl.name.upper()
        if name in self.scopes[-1]:
            raise SymbolTableError(f"Variável '{name}' já declarada neste escopo.")
        sym = Symbol(name=name, sym_type=var_type, decl=decl)
        self.scopes[-1][name] = sym
        return sym

    def add_function(self, unit: ProgramUnit) -> Symbol:
        # Regista um subprograma diretamente no escopo global
        name = unit.name.upper()
        if name in self.scopes[0]:
            raise SymbolTableError(f"Subprograma '{name}' já definido.")
        sym = Symbol(name=name, sym_type=unit.kind, decl=unit)
        self.scopes[0][name] = sym
        return sym

    def lookup(self, name: str) -> Optional[Symbol]:
        # Procura um símbolo de dentro para fora (do escopo mais local para o global)
        upper = name.upper()
        for scope in reversed(self.scopes):
            if upper in scope:
                return scope[upper]
        return None

    def lookup_var(self, name: str) -> Optional[VarDecl]:
        # Atalho para procurar diretamente a declaração de uma variável
        sym = self.lookup(name)
        if sym and isinstance(sym.decl, VarDecl):
            return sym.decl
        return None

    def lookup_unit(self, name: str) -> Optional[ProgramUnit]:
        # Atalho para procurar diretamente a declaração de uma função/subrotina
        sym = self.lookup(name)
        if sym and isinstance(sym.decl, ProgramUnit):
            return sym.decl
        return None

    def get_type(self, name: str) -> Optional[FortranType]:
        # Devolve o tipo (INTEGER, REAL, etc.) de uma variável
        sym = self.lookup(name)
        if sym and isinstance(sym.sym_type, FortranType):
            return sym.sym_type
        return None

    def current_scope_vars(self) -> List[Symbol]:
        # Lista todas as variáveis ativas no nível de visibilidade atual
        return list(self.scopes[-1].values())