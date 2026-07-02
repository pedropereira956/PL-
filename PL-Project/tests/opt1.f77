! ============================================================
! TESTE: Constant Folding
! Operacoes entre literais devem ser resolvidas em tempo
! de compilacao. O codigo .vm NAO deve conter ADD/SUB/MUL/DIV
! entre estes valores — apenas PUSHI com o resultado final.
!
! Output esperado:
!   A = 5
!   B = 40
!   C = 12
!   D = 5
!   E = 1
! ============================================================
PROGRAM OPT1FOLDING
  INTEGER A, B, C, D, E

  A = 2 + 3
  B = 10 * 4
  C = 20 - 8
  D = 15 / 3
  E = 7 - 3 * 2

  PRINT *, 'A = ', A
  PRINT *, 'B = ', B
  PRINT *, 'C = ', C
  PRINT *, 'D = ', D
  PRINT *, 'E = ', E
END
