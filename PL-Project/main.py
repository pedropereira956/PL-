"""
Ponto de Entrada (Main Entry Point) do Compilador Fortran 77.
"""
import sys
import os

# Adiciona o diretório atual ao path para encontrar o pacote 'compiler'
sys.path.insert(0, os.path.dirname(__file__))

from compiler.lexer     import create_lexer
from compiler.parser    import parse
from compiler.semantic  import analyse
from compiler.optimizer import ASTOptimizer
from compiler.codegen   import generate

def compile_file(path: str) -> int:
    # Lê o ficheiro e orquestra o pipeline: Parser -> Semantic -> Optimizer -> Codegen
    try:
        with open(path, 'r', encoding='utf-8') as f:
            source = f.read()
    except FileNotFoundError:
        print(f"[Erro Fatal] Ficheiro '{path}' não encontrado.")
        return 1

    print(f"=== A compilar: {path} ===\n")

    # 1. Análise Sintática (Gera a Árvore Sintática - AST)
    ast = parse(source)
    if ast is None:
        print("[Erro] Falha na análise sintática.")
        return 1

    # 2. Análise Semântica (Valida a lógica, regras de Fortran e Tabela de Símbolos)
    ok = analyse(ast)
    if not ok:
        print("[Erro] Falha na análise semântica.")
        return 1

    # 3. Otimização da AST (Remove operações inúteis e código morto)
    optimizer = ASTOptimizer()
    ast = optimizer.optimize(ast)

    # 4. Geração de Código (Traduz a AST validada para Assembly da EWVM)
    ewvm_code = generate(ast)

    # Grava o resultado final num ficheiro com a extensão .vm
    out_path = os.path.splitext(path)[0] + '.vm'
    with open(out_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(ewvm_code)

    # Imprime o código gerado no terminal para facilitar o debug
    print("\n--- Código Máquina Gerado ---")
    print(ewvm_code)
    print("-----------------------------\n")
    print(f"=== Output gravado em: {out_path} ===\n")


    if optimizer.optimizations_applied > 0:
        print("[Otimizador] Otimizações aplicadas:")
        for nome, count in optimizer.stats.items():
            if count > 0:
                print(f"  ├─ {nome:<26} {count}")
        print(f"  └─ {'Total':<26} {optimizer.optimizations_applied}\n")
    else:
        print("[Otimizador] O código já se encontrava otimizado.\n")
    
    return 0

if __name__ == '__main__':
    # Garante que o utilizador passou o ficheiro .f77 ao correr o script
    if len(sys.argv) < 2:
        print("Uso: python main.py <ficheiro.f77>")
        sys.exit(1)
        
    sys.exit(compile_file(sys.argv[1]))