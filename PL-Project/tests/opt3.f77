! ============================================================
! TESTE: Algebraic Simplification
! Operacoes matematicamente inuteis devem desaparecer do .vm:
!   A + 0  ->  A    (sem ADD no codigo gerado)
!   A * 1  ->  A    (sem MUL no codigo gerado)
!   A * 0  ->  0    (sem PUSHG A no codigo gerado)
!
! Usa READ para que A nao seja constante e o otimizador
! nao possa aplicar Constant Folding — so Algebraic.
!
! Introduza o valor: 7
! Output esperado:
!   A + 0 = 7
!   A * 1 = 7
!   A * 0 = 0
! ============================================================
PROGRAM OPT3ALGEBRAIC
  INTEGER A, B, C, D

  PRINT *, 'Introduza um numero:'
  READ *, A

  B = A + 0
  C = A * 1
  D = A * 0

  PRINT *, 'A + 0 = ', B
  PRINT *, 'A * 1 = ', C
  PRINT *, 'A * 0 = ', D
END
