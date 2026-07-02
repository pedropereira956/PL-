"""
Otimizador da Árvore Sintática (AST) para o compilador Fortran 77.
Implementa uma arquitetura modular de Passagem Única (Single-Pass).
"""
from typing import Any, List, Optional, Union, Dict
from compiler.ast import (
    Program, ProgramUnit, VarDecl, IntLiteral, RealLiteral, 
    LogicalLiteral, StringLiteral, VarRef, BinaryExpr, UnaryExpr, 
    FunctionCall, AssignStmt, PrintStmt, ReadStmt, IfStmt, 
    DoStmt, GotoStmt, ContinueStmt, ReturnStmt, StopStmt, CallStmt,
    Expression
)

class ASTOptimizer:
    def __init__(self) -> None:
        self.optimizations_applied: int = 0
        # Memória para a Propagação de Constantes (mapeia nome da variável -> valor literal)
        self.constants: Dict[str, Expression] = {}
        # Contadores por tipo de otimização
        self.stats: Dict[str, int] = {
            'Constant Folding':         0,
            'Constant Propagation':     0,
            'Algebraic Simplification': 0,
            'Strength Reduction':       0,
            'Dead Code Elimination':    0,
            'Logical Simplification':   0,
        }

    def optimize(self, node: Program) -> Program:
        """Ponto de entrada principal do otimizador."""
        return self._visit(node)

    # ==========================================
    # Motor de Travessia (Visitor Pattern)
    # ==========================================
    def _visit(self, node: Any) -> Any:
        if node is None:
            return None

        # Achata listas aninhadas (comum após Dead Code Elimination)
        if isinstance(node, list):
            optimized_list = []
            for child in node:
                opt_child = self._visit(child)
                if isinstance(opt_child, list):
                    optimized_list.extend(opt_child)
                elif opt_child is not None:
                    optimized_list.append(opt_child)
            return optimized_list

        method_name = f'_visit_{type(node).__name__}'
        visitor = getattr(self, method_name, self._generic_visit)
        return visitor(node)

    def _generic_visit(self, node: Any) -> Any:
        return node

    # ==========================================
    # Varredura de Blocos e Gestão de Estado
    # ==========================================
    def _visit_Program(self, node: Program) -> Program:
        node.units = self._visit(node.units)
        return node

    def _visit_ProgramUnit(self, node: ProgramUnit) -> ProgramUnit:
        self.constants.clear() # Reset às constantes por segurança
        node.body = self._visit(node.body)
        return node

    def _visit_AssignStmt(self, node: AssignStmt) -> AssignStmt:
        if node.label is not None: self.constants.clear()

        node.target = self._visit(node.target)
        node.value = self._visit(node.value)

        # Atualiza a memória de constantes
        if isinstance(node.target, VarRef) and len(node.target.indices) == 0:
            if isinstance(node.value, (IntLiteral, RealLiteral, LogicalLiteral, StringLiteral)):
                self.constants[node.target.name] = node.value
            else:
                self.constants.pop(node.target.name, None)

        return node

    def _visit_PrintStmt(self, node: PrintStmt) -> PrintStmt:
        if node.label is not None: self.constants.clear()
        node.items = self._visit(node.items)
        return node

    def _visit_ReadStmt(self, node: ReadStmt) -> ReadStmt:
        if node.label is not None: self.constants.clear()
        node.targets = self._visit(node.targets)
        for t in node.targets:
            if isinstance(t, VarRef) and len(t.indices) == 0:
                self.constants.pop(t.name, None)
        return node

    def _visit_DoStmt(self, node: DoStmt) -> DoStmt:
        if node.label is not None: self.constants.clear()
        node.start = self._visit(node.start)
        node.stop = self._visit(node.stop)
        node.step = self._visit(node.step) if node.step else None
        
        self.constants.clear()
        node.body = self._visit(node.body)
        self.constants.clear()
        return node

    def _visit_CallStmt(self, node: CallStmt) -> CallStmt:
        if node.label is not None: self.constants.clear()
        node.args = self._visit(node.args)
        self.constants.clear()
        return node
        
    def _visit_GotoStmt(self, node: GotoStmt) -> GotoStmt:
        self.constants.clear()
        return node

    def _visit_FunctionCall(self, node: FunctionCall) -> FunctionCall:
        node.args = self._visit(node.args)
        return node

    # ==========================================
    # Aplicação Modular de Otimizações
    # ==========================================
    def _visit_VarRef(self, node: VarRef) -> Union[VarRef, Expression]:
        node.indices = self._visit(node.indices)
        return self._apply_constant_propagation(node)

    def _visit_BinaryExpr(self, node: BinaryExpr) -> Expression:
        # 1. Avalia os filhos (Bottom-Up)
        node.left = self._visit(node.left)
        node.right = self._visit(node.right)

        # 2. Passa o nó pela "linha de montagem" de otimizações
        node = self._apply_strength_reduction(node)
        node = self._apply_constant_folding(node)
        node = self._apply_algebraic_simplification(node)
        return node

    def _visit_UnaryExpr(self, node: UnaryExpr) -> Expression:
        node.operand = self._visit(node.operand)
        return self._apply_logical_simplification(node)

    def _visit_IfStmt(self, node: IfStmt) -> Union[IfStmt, List[Any]]:
        if node.label is not None: self.constants.clear()
        node.condition = self._visit(node.condition)

        # Aplica a Eliminação de Código Morto. Se retornar uma lista ou outro nó, o IF morreu.
        optimized_node = self._apply_dead_code_elimination(node)
        if not isinstance(optimized_node, IfStmt):
            return optimized_node

        # Se o IF sobreviveu (condição dinâmica), visita os ramos de forma segura
        self.constants.clear()
        node.then_body = self._visit(node.then_body)
        self.constants.clear()
        node.else_body = self._visit(node.else_body)
        self.constants.clear()

        return node

    # ==========================================
    # Módulos de Otimização (Puros e Isolados)
    # ==========================================
    
    def _apply_constant_propagation(self, node: VarRef) -> Union[VarRef, Expression]:
        """Substitui variáveis por valores fixos previamente memorizados."""
        if len(node.indices) == 0 and node.name in self.constants:
            self.optimizations_applied += 1
            self.stats['Constant Propagation'] += 1
            return self.constants[node.name]
        return node

    def _apply_strength_reduction(self, node: Expression) -> Expression:
        if isinstance(node, BinaryExpr) and node.op == '**':
            if isinstance(node.right, IntLiteral) and node.right.value == 0:
                self.optimizations_applied += 1
                self.stats['Strength Reduction'] += 1
                return IntLiteral(1)
            if isinstance(node.right, IntLiteral) and node.right.value == 1:
                self.optimizations_applied += 1
                self.stats['Strength Reduction'] += 1
                return node.left
            if isinstance(node.right, IntLiteral) and node.right.value > 1:
                self.optimizations_applied += 1
                self.stats['Strength Reduction'] += 1
                n = node.right.value
                result = node.left
                for _ in range(n - 1):
                    result = BinaryExpr(op='*', left=result, right=node.left)
                return self._visit(result)
        return node

    def _apply_constant_folding(self, node: Expression) -> Expression:
        """Resolve contas estáticas em tempo de compilação."""
        if isinstance(node, BinaryExpr):
            if isinstance(node.left, IntLiteral) and isinstance(node.right, IntLiteral):
                l, r = node.left.value, node.right.value
                
                # Matemática
                if node.op == '+': self.optimizations_applied += 1; self.stats['Constant Folding'] += 1; return IntLiteral(l + r)
                if node.op == '-': self.optimizations_applied += 1; self.stats['Constant Folding'] += 1; return IntLiteral(l - r)
                if node.op == '*': self.optimizations_applied += 1; self.stats['Constant Folding'] += 1; return IntLiteral(l * r)
                if node.op == '/' and r != 0: self.optimizations_applied += 1; self.stats['Constant Folding'] += 1; return IntLiteral(l // r)
                
                # Relacionais 
                if node.op == '.EQ.': self.optimizations_applied += 1; self.stats['Constant Folding'] += 1; return LogicalLiteral(l == r)
                if node.op == '.NE.': self.optimizations_applied += 1; self.stats['Constant Folding'] += 1; return LogicalLiteral(l != r)
                if node.op == '.LT.': self.optimizations_applied += 1; self.stats['Constant Folding'] += 1; return LogicalLiteral(l < r)
                if node.op == '.LE.': self.optimizations_applied += 1; self.stats['Constant Folding'] += 1; return LogicalLiteral(l <= r)
                if node.op == '.GT.': self.optimizations_applied += 1; self.stats['Constant Folding'] += 1; return LogicalLiteral(l > r)
                if node.op == '.GE.': self.optimizations_applied += 1; self.stats['Constant Folding'] += 1; return LogicalLiteral(l >= r)
                
        return node

    def _apply_algebraic_simplification(self, node: Expression) -> Expression:
        """Remove operações matematicamente inúteis (+0, *1, *0)."""
        if isinstance(node, BinaryExpr):
            if node.op == '+' and isinstance(node.right, IntLiteral) and node.right.value == 0:
                self.optimizations_applied += 1
                self.stats['Algebraic Simplification'] += 1
                return node.left
            if node.op == '*' and isinstance(node.right, IntLiteral) and node.right.value == 1:
                self.optimizations_applied += 1
                self.stats['Algebraic Simplification'] += 1
                return node.left
            if node.op == '*' and isinstance(node.right, IntLiteral) and node.right.value == 0:
                self.optimizations_applied += 1
                self.stats['Algebraic Simplification'] += 1
                return IntLiteral(0)
        return node

    def _apply_logical_simplification(self, node: UnaryExpr) -> Expression:
        """Limpa duplas negações, inverte comparações lógicas e resolve literais."""
        if node.op == '.NOT.':
            
            # Constant Folding Lógico: .NOT. (Verdadeiro) -> Falso
            if isinstance(node.operand, LogicalLiteral):
                self.optimizations_applied += 1
                self.stats['Logical Simplification'] += 1
                return LogicalLiteral(not node.operand.value)
            
            # Dupla Negação: .NOT. (.NOT. X) -> X
            if isinstance(node.operand, UnaryExpr) and node.operand.op == '.NOT.':
                self.optimizations_applied += 1
                self.stats['Logical Simplification'] += 1
                return node.operand.operand
            
            # Inversão: .NOT. (A < B) -> A >= B
            if isinstance(node.operand, BinaryExpr):
                inverse_ops = {
                    '.LT.': '.GE.', '.LE.': '.GT.', '.GT.': '.LE.',
                    '.GE.': '.LT.', '.EQ.': '.NE.', '.NE.': '.EQ.'
                }
                if node.operand.op in inverse_ops:
                    self.optimizations_applied += 1
                    self.stats['Logical Simplification'] += 1
                    return BinaryExpr(inverse_ops[node.operand.op], node.operand.left, node.operand.right)
        return node

    def _apply_dead_code_elimination(self, node: IfStmt) -> Union[IfStmt, List[Any]]:
        """Remove ramos de código que nunca vão ser executados."""
        if isinstance(node.condition, LogicalLiteral):
            self.optimizations_applied += 1
            self.stats['Dead Code Elimination'] += 1
            
            surviving_body = node.then_body if node.condition.value else node.else_body
            surviving_body = self._visit(surviving_body) # Otimiza o bloco sobrevivente
            
            # Se o IF original tinha Label (GOTO target), preserva-a através de um CONTINUE
            if node.label is not None:
                return [ContinueStmt(label=node.label)] + surviving_body
            return surviving_body
        return node