! ============================================================
! TESTE: Logical Simplification
! Tres casos:
!   1. Dupla negacao:  .NOT. (.NOT. X) -> X
!   2. Inversao relacional: .NOT. (A .LT. B) -> A .GE. B
!   3. NOT de literal: .NOT. .FALSE. -> .TRUE.
!
! Introduza X = 3, Y = 5
! Output esperado:
!   NOT NOT X>0 com X=3: 1   (verdadeiro)
!   NOT (3 < 5): 0            (falso, 3 e menor que 5)
!   NOT FALSE = 1             (verdadeiro)
! ============================================================
PROGRAM OPT6LOGICAL
  INTEGER X, Y
  LOGICAL A, B, C

  PRINT *, 'Introduza X:'
  READ *, X
  PRINT *, 'Introduza Y:'
  READ *, Y

  ! Caso 1: Dupla negacao — .NOT.(.NOT.(X .GT. 0)) -> X .GT. 0
  A = .NOT. (.NOT. (X .GT. 0))
  PRINT *, 'NOT NOT (X>0) com X=', X, ': ', A

  ! Caso 2: Inversao — .NOT.(X .LT. Y) -> X .GE. Y
  B = .NOT. (X .LT. Y)
  PRINT *, 'NOT (X<Y) com X=', X, ' Y=', Y, ': ', B

  ! Caso 3: NOT de literal — .NOT. .FALSE. -> .TRUE.
  C = .NOT. .FALSE.
  PRINT *, 'NOT FALSE = ', C
END
