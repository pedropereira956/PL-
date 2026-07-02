"""
Gerador de Código (Code Generator) para a Máquina Virtual EWVM.
Traduz a Árvore Sintática (AST) para instruções Assembly.
"""
from typing import List, Optional
from .ast import *
from .symboltable import SymbolTable, SymbolTableError

class CodeGenError(Exception):
    pass

class CodeGenerator:
    def __init__(self) -> None:
        self.code: List[str] = []
        self._label_counter: int = 0
        self._unit_name: Optional[str] = None
        self._sym: Optional[SymbolTable] = None
        self._current_unit: Optional[ProgramUnit] = None

    def generate(self, program: Program) -> str:
        # Ponto de entrada: inicializa a tabela e regista as funções antes de compilar
        self._sym = SymbolTable()
        
        for unit in program.units:
            if unit.kind != 'program':
                self._sym.add_function(unit)
                
        # Garante que o bloco MAIN (program) é compilado antes das subrotinas
        main = next((u for u in program.units if u.kind == 'program'), None)
        subs = [u for u in program.units if u.kind != 'program']
        
        if main:
            self._gen_unit(main)
        for sub in subs:
            self._gen_unit(sub)
            
        return '\n'.join(self.code)

    def _gen_unit(self, unit: ProgramUnit) -> None:
        # Prepara a memória e o escopo para um bloco (Main, Function ou Subroutine)
        self._unit_name = unit.name.upper()
        self._current_unit = unit
        self._sym.push_scope()

        if unit.kind == 'program':
            self._emit('START')
        else:
            self._label(f'F{self._unit_name}')

        offset = 0

        # Se for uma FUNCTION, aloca espaço no índice 0 para a variável de retorno
        if unit.return_type is not None:
            ret_decl = VarDecl(name=unit.name.upper(), dimensions=[], is_global=False, scope_offset=offset)
            self._sym.add_variable(ret_decl, unit.return_type)
            self._push_default(unit.return_type)
            offset += 1

        # Mapeia os parâmetros da função para offsets negativos (argumentos passados na Stack)
        param_offset = -(len(unit.params))
        for pname in unit.params:
            pd = VarDecl(name=pname.upper(), dimensions=[], is_global=False, scope_offset=param_offset)
            try:
                self._sym.add_variable(pd, FortranType.INTEGER)
            except SymbolTableError:
                pass
            param_offset += 1

        # Alocação de variáveis locais e Arrays
        for decl in unit.declarations:
            for vd in decl.variables:
                vd.is_global = (unit.kind == 'program')
                
                # Previne sombreamento de funções globais
                if self._sym.lookup_unit(vd.name) is not None:
                    continue
                    
                existing = self._sym.lookup_var(vd.name)
                if existing is not None:
                    sym = self._sym.lookup(vd.name)
                    if sym:
                        sym.sym_type = decl.var_type
                        vd.scope_offset = existing.scope_offset
                    continue
                    
                vd.scope_offset = offset
                
                # Calcula tamanho para alocação (Arrays multiplicam dimensões)
                size = 1
                for d in vd.dimensions:
                    size *= d
                    
                try:
                    self._sym.add_variable(vd, decl.var_type)
                except SymbolTableError:
                    pass
                    
                # Injeta instruções na VM para reservar memória
                if len(vd.dimensions) == 0:
                    self._push_default(decl.var_type)
                    offset += 1
                else:
                    self._emit(f'ALLOC {size}')
                    offset += 1

        # Traduz o corpo do programa
        for stmt in unit.body:
            self._gen_stmt(stmt)

        # Finaliza a unidade
        if unit.kind == 'program':
            self._emit('STOP')
        else:
            if not self._last_is_jump(unit.body):   # ← só emite se necessário
                if unit.return_type is not None:
                    self._emit('PUSHL 0')
                self._emit('RETURN')

        self._sym.pop_scope()

    def _last_is_jump(self, stmts: list) -> bool:
        """Verifica se o último statement já transfere o fluxo."""
        if not stmts:
            return False
        last = stmts[-1]
        return isinstance(last, (GotoStmt, ReturnStmt, StopStmt))

    def _gen_stmt(self, stmt: Statement) -> None:
        # Despachante que traduz cada instrução Fortran para Assembly EWVM
        lbl = getattr(stmt, 'label', None)
        if lbl is not None:
            self._label(self._stmt_label(lbl))

        if isinstance(stmt, AssignStmt):
            self._gen_expr(stmt.value)
            self._store_varref(stmt.target)

        elif isinstance(stmt, PrintStmt):
            for item in stmt.items:
                self._gen_expr(item)
                self._emit_write(item)
            self._emit('WRITELN')

        elif isinstance(stmt, ReadStmt):
            for target in stmt.targets:
                decl = self._sym.lookup_var(target.name)
                sym  = self._sym.lookup(target.name)
                
                # Leitura direta para dentro de um Array (requer cálculo de endereço STOREN)
                if len(target.indices) > 0 and decl is not None:
                    instr = 'PUSHL' if not decl.is_global else 'PUSHG'
                    self._emit(f'{instr} {decl.scope_offset}')
                    self._gen_expr(target.indices[0])
                    self._emit('PUSHI 1')
                    self._emit('SUB')
                    
                    if sym and sym.sym_type == FortranType.REAL:
                        self._emit('READ\nATOF')
                    else:
                        self._emit('READ\nATOI')
                    self._emit('STOREN')
                else:
                    # Leitura para variável escalar simples
                    if sym and sym.sym_type == FortranType.REAL:
                        self._emit('READ\nATOF')
                    else:
                        self._emit('READ\nATOI')
                    self._store_varref(target)

        elif isinstance(stmt, IfStmt):
            else_lbl = self._new_label('ELSE')
            end_lbl  = self._new_label('ENDIF')
            
            self._gen_expr(stmt.condition)
            self._emit(f'JZ {else_lbl}')
            
            for s in stmt.then_body:
                self._gen_stmt(s)
            if not self._last_is_jump(stmt.then_body):  # ← só emite se necessário
                self._emit(f'JUMP {end_lbl}')
            
            self._label(else_lbl)
            for s in stmt.else_body:
                self._gen_stmt(s)
            self._label(end_lbl)

        elif isinstance(stmt, DoStmt):
            start_lbl = self._new_label('DOSTART')
            end_lbl   = self._new_label('DOEND')
            
            # Inicializa a variável do ciclo
            self._gen_expr(stmt.start)
            self._store_name(stmt.var)
            
            self._label(start_lbl)
            
            # Condição de paragem
            self._load_name(stmt.var)
            self._gen_expr(stmt.stop)
            self._emit('INFEQ')
            self._emit(f'JZ {end_lbl}')
            
            for s in stmt.body:
                self._gen_stmt(s)
                
            # Incremento (Step)
            self._load_name(stmt.var)
            if stmt.step:
                self._gen_expr(stmt.step)
            else:
                self._emit('PUSHI 1')
            self._emit('ADD')
            self._store_name(stmt.var)
            
            self._emit(f'JUMP {start_lbl}')
            self._label(end_lbl)

        elif isinstance(stmt, GotoStmt):
            self._emit(f'JUMP {self._stmt_label(stmt.target)}')

        elif isinstance(stmt, ContinueStmt):
            pass # Apenas ancora labels, não gera código na EWVM

        elif isinstance(stmt, ReturnStmt):
            if self._current_unit and self._current_unit.return_type is not None:
                self._emit('PUSHL 0')
            self._emit('RETURN')

        elif isinstance(stmt, StopStmt):
            self._emit('STOP')

        elif isinstance(stmt, CallStmt):
            for arg in stmt.args:
                self._gen_expr(arg)
            self._emit(f'PUSHA F{stmt.name.upper()}')
            self._emit('CALL')
            # Limpa argumentos da stack após a chamada (C-style / stdcall adjustment)
            if stmt.args:
                self._emit(f'POP {len(stmt.args)}')

    def _gen_expr(self, expr: Expression) -> None:
        # Coloca valores literais, variáveis ou resultados de contas na Stack
        if isinstance(expr, IntLiteral):
            self._emit(f'PUSHI {expr.value}')
        elif isinstance(expr, RealLiteral):
            self._emit(f'PUSHF {expr.value:.10f}')
        elif isinstance(expr, LogicalLiteral):
            self._emit(f'PUSHI {1 if expr.value else 0}')
        elif isinstance(expr, StringLiteral):
            escaped = expr.value.replace('"', '')
            self._emit(f'PUSHS "{escaped}"')
        elif isinstance(expr, VarRef):
            self._load_varref(expr)
        elif isinstance(expr, BinaryExpr):
            if expr.op == '**':
                self._gen_power(expr.left, expr.right)
            else:
                self._gen_expr(expr.left)
                self._gen_expr(expr.right)
                self._emit(self._binop_instr(expr.op))
        elif isinstance(expr, UnaryExpr):
            self._gen_expr(expr.operand)
            if expr.op == '-':
                self._emit('PUSHI -1\nMUL')
            elif expr.op == '.NOT.':
                self._emit('NOT')
        elif isinstance(expr, FunctionCall):
            self._gen_funcall(expr)

    def _gen_funcall(self, call: FunctionCall) -> None:
        name = call.name.upper()
        decl = self._sym.lookup_var(name)
        unit = self._sym.lookup_unit(name)
        
        # Resolve ambiguidade: é um Array ou uma Função?
        if decl is not None and unit is None:
            self._load_varref(VarRef(name=call.name, indices=call.args))
            return
            
        # Funções Embutidas (Built-ins)
        if name == 'MOD':
            self._gen_expr(call.args[0])
            self._gen_expr(call.args[1])
            self._emit('MOD')
        elif name == 'ABS':
            self._gen_expr(call.args[0])
            self._emit('ABS')
        elif name == 'SQRT':
            self._gen_expr(call.args[0])
            self._emit('SQRT')
        elif name == 'INT':
            self._gen_expr(call.args[0])
            self._emit('FTOI')
        elif name in ('MAX', 'MIN'):
            self._gen_expr(call.args[0])
            for arg in call.args[1:]:
                self._gen_expr(arg)
                self._emit('MAX' if name == 'MAX' else 'MIN')
        else:
            # Chamada a função de utilizador
            for arg in call.args:
                self._gen_expr(arg)
            self._emit(f'PUSHA F{name}')
            self._emit('CALL')

    def _load_varref(self, ref: VarRef) -> None:
        # Lê da memória (Local ou Global) para o topo da Stack
        decl = self._sym.lookup_var(ref.name)
        if decl is None:
            print(f"[CodeGen] Aviso: variável não declarada '{ref.name}', a assumir 0")
            self._emit('PUSHI 0')
            return
            
        instr = 'PUSHL' if not decl.is_global else 'PUSHG'
        if len(ref.indices) == 0:
            self._emit(f'{instr} {decl.scope_offset}')
        else:
            # Aritmética de ponteiros para Arrays (1-based index)
            self._emit(f'{instr} {decl.scope_offset}')
            self._gen_expr(ref.indices[0])
            self._emit('PUSHI 1\nSUB\nLOADN')

    def _store_varref(self, ref: VarRef) -> None:
        # Guarda o topo da Stack na memória (Local ou Global)
        decl = self._sym.lookup_var(ref.name)
        if decl is None:
            print(f"[CodeGen] Aviso: variável não declarada '{ref.name}'")
            return
            
        instr = 'PUSHL' if not decl.is_global else 'PUSHG'
        if len(ref.indices) == 0:
            store_instr = 'STOREL' if not decl.is_global else 'STOREG'
            self._emit(f'{store_instr} {decl.scope_offset}')
        else:
            # Guardar num índice do Array (STOREN)
            self._emit(f'{instr} {decl.scope_offset}')
            self._gen_expr(ref.indices[0])
            self._emit('PUSHI 1\nSUB\nROT\nSTOREN')

    def _load_name(self, name: str) -> None:
        # Atalho de leitura por nome
        decl = self._sym.lookup_var(name)
        if decl:
            instr = 'PUSHL' if not decl.is_global else 'PUSHG'
            self._emit(f'{instr} {decl.scope_offset}')
        else:
            self._emit('PUSHI 0')

    def _store_name(self, name: str) -> None:
        # Atalho de escrita por nome
        decl = self._sym.lookup_var(name)
        if decl:
            instr = 'STOREL' if not decl.is_global else 'STOREG'
            self._emit(f'{instr} {decl.scope_offset}')

    def _emit_write(self, expr: Expression) -> None:
        # Deteta o tipo de dado na Stack para invocar a instrução certa na Máquina Virtual
        if isinstance(expr, StringLiteral):
            self._emit('WRITES')
        elif isinstance(expr, RealLiteral):
            self._emit('WRITEF')
        elif isinstance(expr, IntLiteral) or isinstance(expr, LogicalLiteral):
            self._emit('WRITEI')
        elif isinstance(expr, VarRef):
            var_type = self._sym.get_type(expr.name)
            if var_type == FortranType.REAL:
                self._emit('WRITEF')
            elif var_type == FortranType.CHARACTER:
                self._emit('WRITES')
            else:
                self._emit('WRITEI')
        else:
            self._emit('WRITEI')

    def _binop_instr(self, op: str) -> str:
        # Mapeia operadores da AST para mnemónicas da EWVM
        return {
            '+':     'ADD',
            '-':     'SUB',
            '*':     'MUL',
            '/':     'DIV',
            '.EQ.':  'EQUAL',
            '.NE.':  'EQUAL\nNOT',
            '.LT.':  'INF',
            '.LE.':  'INFEQ',
            '.GT.':  'SUP',
            '.GE.':  'SUPEQ',
            '.AND.': 'AND',
            '.OR.':  'OR',
        }.get(op, f'// unknown op {op}')
    
    def _gen_power(self, base: Expression, exp: Expression) -> None:
        # Fallback para expoentes dinâmicos (X**Y onde Y é variável).
        # Expoentes literais são resolvidos pelo optimizer via AST Lowering.
        # Gera um ciclo de multiplicação em assembly:
        #   result = 1
        #   while counter > 0: result *= base; counter -= 1
        start_lbl = self._new_label('POWSTART')
        end_lbl   = self._new_label('POWEND')

        self._emit('PUSHI 1')      # result = 1        stack: [result]
        self._gen_expr(exp)        # counter = exp     stack: [result, counter]

        self._label(start_lbl)
        self._emit('DUP 1')        # stack: [result, counter, counter]
        self._emit('PUSHI 0')
        self._emit('SUP')          # counter > 0?
        self._emit(f'JZ {end_lbl}')

        self._emit('SWAP')         # stack: [counter, result]
        self._gen_expr(base)       # stack: [counter, result, base]
        self._emit('MUL')          # stack: [counter, result*base]
        self._emit('SWAP')         # stack: [result*base, counter]
        self._emit('PUSHI 1')
        self._emit('SUB')          # stack: [result*base, counter-1]
        self._emit(f'JUMP {start_lbl}')

        self._label(end_lbl)
        self._emit('POP 1')        # remove counter=0, fica só [result]

    def _new_label(self, prefix: str) -> str:
        # Gera labels únicas para IFs e ciclos DO
        self._label_counter += 1
        return f'L{prefix}{self._label_counter}'

    def _stmt_label(self, n: int) -> str:
        # Gera labels amarradas aos números das linhas (GOTOs)
        unit = self._unit_name or 'MAIN'
        return f'LBL{unit}{n}'

    def _label(self, name: str) -> None:
        clean = name.replace(' ', '').replace('\r', '')
        if not clean.endswith(':'):
            clean += ':'
        self.code.append(clean)

    def _push_default(self, t: FortranType) -> None:
        # Valores de inicialização padrão (Default values)
        if t == FortranType.REAL:
            self._emit('PUSHF 0.0000000000')
        elif t == FortranType.CHARACTER:
            self._emit('PUSHS ""')
        else:
            self._emit('PUSHI 0')

    def _emit(self, instr: str) -> None:
        for line in instr.replace('\r', '').split('\n'):
            line = line.strip()
            if line:
                self.code.append(f' {line}')


def generate(program: Program) -> str:
    # Função de atalho exposta para o main.py
    return CodeGenerator().generate(program)