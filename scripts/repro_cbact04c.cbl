*> Minimal reproduction of the main loop of CardDemo CBACT04C (lines 188-222 at commit 59cc6c2).
*> Same IF/ELSE structure, three in-memory records for two accounts (101, 101, 202).
*> Run: cobc -x -free scripts/repro_cbact04c.cbl -o /tmp/repro && /tmp/repro
IDENTIFICATION DIVISION.
PROGRAM-ID. REPRO04C.
DATA DIVISION.
WORKING-STORAGE SECTION.
01 END-OF-FILE      PIC X VALUE 'N'.
01 WS-FIRST-TIME    PIC X VALUE 'Y'.
01 WS-LAST-ACCT     PIC 9(3) VALUE 0.
01 WS-IDX           PIC 9 VALUE 0.
01 REC-ACCT         PIC 9(3).
01 ACCTS-TABLE      VALUE '101101202'.
   05 ACCT-ID       PIC 9(3) OCCURS 3.
PROCEDURE DIVISION.
    PERFORM UNTIL END-OF-FILE = 'Y'
        IF END-OF-FILE = 'N'
            PERFORM GET-NEXT
            IF END-OF-FILE = 'N'
                IF REC-ACCT NOT = WS-LAST-ACCT
                    IF WS-FIRST-TIME NOT = 'Y'
                        PERFORM UPDATE-ACCOUNT
                    ELSE
                        MOVE 'N' TO WS-FIRST-TIME
                    END-IF
                    MOVE REC-ACCT TO WS-LAST-ACCT
                END-IF
                DISPLAY 'interest transaction written for account ' REC-ACCT
            END-IF
        ELSE
            *> CBACT04C line 219-220: meant to update the last account
            PERFORM UPDATE-ACCOUNT
        END-IF
    END-PERFORM
    DISPLAY 'end of run'
    STOP RUN.
GET-NEXT.
    ADD 1 TO WS-IDX
    IF WS-IDX > 3
        MOVE 'Y' TO END-OF-FILE
    ELSE
        MOVE ACCT-ID(WS-IDX) TO REC-ACCT
    END-IF.
UPDATE-ACCOUNT.
    DISPLAY 'balance updated (interest added) for account ' WS-LAST-ACCT.
