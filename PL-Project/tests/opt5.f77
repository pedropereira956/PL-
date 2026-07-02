! ============================================================
! TESTE: Dead Code Elimination
! Blocos IF com condicao literal sao eliminados em compilacao.
! No codigo .vm:
!   - O bloco ELSE do primeiro IF nao deve aparecer
!   - O bloco THEN do segundo IF nao deve aparecer
!   - O codigo gerado deve ser uma sequencia linear de PRINT
!
! Output esperado:
!   Linha 1: ramo TRUE executa
!   Linha 2: ramo ELSE executa
!   Fim do programa
! ============================================================
PROGRAM OPT5DEADCODE
  INTEGER X

  ! IF com .TRUE.: ramo ELSE e eliminado completamente
  IF (.TRUE.) THEN
    PRINT *, 'Linha 1: ramo TRUE executa'
  ELSE
    PRINT *, 'ERRO - este ramo nao devia existir no .vm'
  ENDIF

  ! IF com .FALSE.: ramo THEN e eliminado completamente
  IF (.FALSE.) THEN
    PRINT *, 'ERRO - este ramo nao devia existir no .vm'
  ELSE
    PRINT *, 'Linha 2: ramo ELSE executa'
  ENDIF

  PRINT *, 'Fim do programa'
END
