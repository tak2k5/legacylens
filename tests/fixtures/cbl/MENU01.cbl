       IDENTIFICATION DIVISION.
       PROGRAM-ID. MENU01.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-TO-PGM            PIC X(8).
       01 WS-FILE              PIC X(8) VALUE 'PAYDAT'.
       PROCEDURE DIVISION.
       MAIN-PARA.
           EXEC CICS READ
                FILE(WS-FILE)
                INTO(PAY-REC)
           END-EXEC
           IF PAY-AMT > 0
               MOVE 'PAYCHK' TO WS-TO-PGM
           ELSE
               MOVE 'SIGNON' TO WS-TO-PGM
           END-IF
           EXEC CICS XCTL PROGRAM(WS-TO-PGM)
           END-EXEC.
