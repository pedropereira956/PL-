! ============================================================
! TESTE: Strength Reduction + AST Lowering + Fallback Dinamico
!
! CAMINHO 1 — Optimizer (Middle-end):
!   Expoentes literais sao resolvidos por AST Lowering antes
!   de chegarem ao Gerador de Codigo.
!   X**2 -> X*X, X**3 -> X*X*X, X**0 -> 1, X**1 -> X
!   3**3 -> 27 (encadeia com Constant Folding)
!   No .vm: apenas PUSHG e MUL, sem ciclos POWSTART/POWEND
!
! CAMINHO 2 — Codegen (Back-end):
!   Expoentes dinamicos (X**N com N variavel) nao podem ser
!   resolvidos em compile-time. O codegen gera um ciclo de
!   multiplicacao em assembly (POWSTART/POWEND).
!   No .vm: ciclo com DUP, SUP, JZ, SWAP, MUL, SUB, JUMP
!
! Introduza base: 2, expoente: 4
! Output esperado:
!   2 ao quadrado = 4        (optimizer: X*X)
!   2 ao cubo = 8            (optimizer: X*X*X)
!   2 a quarta = 16          (optimizer: X*X*X*X)
!   3 ao cubo = 27           (optimizer: folding direto)
!   2 a zero = 1             (optimizer: identidade)
!   2 a um = 2               (optimizer: identidade)
!   2 ** 4 (dinamico) = 16   (codegen: ciclo POWSTART/POWEND)
! ============================================================
PROGRAM OPT4STRENGTH
  INTEGER X, N, Y, Z, W, R

  PRINT *, 'Introduza a base:'
  READ *, X

  ! --- CAMINHO 1: Expoentes literais (resolvidos pelo Optimizer) ---

  ! X**2 -> X*X no .vm (dois PUSHG + um MUL)
  Y = X ** 2
  PRINT *, X, ' ao quadrado = ', Y

  ! X**3 -> X*X*X no .vm (tres PUSHG + dois MUL)
  Z = X ** 3
  PRINT *, X, ' ao cubo = ', Z

  ! X**4 -> X*X*X*X no .vm (quatro PUSHG + tres MUL)
  W = X ** 4
  PRINT *, X, ' a quarta = ', W

  ! 3**3 -> PUSHI 27 no .vm (Strength Reduction + Constant Folding)
  PRINT *, '3 ao cubo = ', 3 ** 3

  ! X**0 -> PUSHI 1 no .vm (identidade)
  PRINT *, X, ' a zero = ', X ** 0

  ! X**1 -> PUSHG X no .vm (identidade)
  PRINT *, X, ' a um = ', X ** 1

  ! --- CAMINHO 2: Expoente dinamico (resolvido pelo Codegen) ---

  ! X**N com N lido em runtime — optimizer nao consegue agir
  ! No .vm: ciclo LPOWSTART/LPOWEND com DUP/SUP/JZ/SWAP/MUL
  PRINT *, 'Introduza o expoente:'
  READ *, N
  R = X ** N
  PRINT *, X, ' ** ', N, ' (dinamico) = ', R

END
