! ============================================================
! TESTE: Constant Propagation
! Quando uma variavel recebe um literal, todas as referencias
! seguintes a essa variavel devem ser substituidas pelo valor.
! Encadeia com Constant Folding: Y = X + 5 vira 10 + 5 vira 15.
!
! No codigo .vm NAO devem aparecer PUSHG para X, Y, Z
! nas expressoes — so PUSHI com os valores calculados.
!
! Output esperado:
!   X = 10
!   Y = 15
!   Z = 30
!   W = 10
! ============================================================
PROGRAM OPT2PROPAGATION
  INTEGER X, Y, Z, W

  X = 10
  Y = X + 5
  Z = Y * 2
  W = Z - X - 10

  PRINT *, 'X = ', X
  PRINT *, 'Y = ', Y
  PRINT *, 'Z = ', Z
  PRINT *, 'W = ', W
END
