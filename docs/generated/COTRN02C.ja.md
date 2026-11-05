# 設計書: COTRN02C

_LegacyLens により自動生成。構造は静的解析、目的と業務ルールは LLM が作成し、各ルールはソースと照合済み。_

## 概要

| 種別 | オンライン (CICS) |
| --- | --- |
| コード行数 | 614 |
| ソース | [cbl/COTRN02C.cbl](../../data/carddemo/app/cbl/COTRN02C.cbl) |

## 入出力

| ファイル / データセット | モード | 行 |
| --- | --- | --- |
| CXACAIX | 読込 | [578](../../data/carddemo/app/cbl/COTRN02C.cbl#L578) |
| CCXREF | 読込 | [611](../../data/carddemo/app/cbl/COTRN02C.cbl#L611) |
| TRANSACT | 読込 | [644](../../data/carddemo/app/cbl/COTRN02C.cbl#L644) |
| TRANSACT | 書込 | [713](../../data/carddemo/app/cbl/COTRN02C.cbl#L713) |

## 他プログラムへの遷移

| プログラム | 方式 | 行 |
| --- | --- | --- |
| COMEN01C | XCTL | [508](../../data/carddemo/app/cbl/COTRN02C.cbl#L508) |
| COSGN00C | XCTL | [508](../../data/carddemo/app/cbl/COTRN02C.cbl#L508) |
| CSUTLDTC | CALL | [393](../../data/carddemo/app/cbl/COTRN02C.cbl#L393) |
| CSUTLDTC | CALL | [413](../../data/carddemo/app/cbl/COTRN02C.cbl#L413) |

## コピー句

`COCOM01Y`, `COTRN02`, `COTTL01Y`, `CSDAT01Y`, `CSMSG01Y`, `CVTRA05Y`, `CVACT01Y`, `CVACT03Y`, `DFHAID`, `DFHBMSCA`

## 処理フロー (PERFORM)

```mermaid
flowchart TD
    p0["ADD-TRANSACTION"] --> p3["ENDBR-TRANSACT-FILE"]
    p0["ADD-TRANSACTION"] --> p10["READPREV-TRANSACT-FILE"]
    p0["ADD-TRANSACTION"] --> p14["STARTBR-TRANSACT-FILE"]
    p0["ADD-TRANSACTION"] --> p17["WRITE-TRANSACT-FILE"]
    p1["CLEAR-CURRENT-SCREEN"] --> p4["INITIALIZE-ALL-FIELDS"]
    p1["CLEAR-CURRENT-SCREEN"] --> p13["SEND-TRNADD-SCREEN"]
    p2["COPY-LAST-TRAN-DATA"] --> p3["ENDBR-TRANSACT-FILE"]
    p2["COPY-LAST-TRAN-DATA"] --> p7["PROCESS-ENTER-KEY"]
    p2["COPY-LAST-TRAN-DATA"] --> p10["READPREV-TRANSACT-FILE"]
    p2["COPY-LAST-TRAN-DATA"] --> p14["STARTBR-TRANSACT-FILE"]
    p2["COPY-LAST-TRAN-DATA"] --> p16["VALIDATE-INPUT-KEY-FIELDS"]
    p5["MAIN-PARA"] --> p1["CLEAR-CURRENT-SCREEN"]
    p5["MAIN-PARA"] --> p2["COPY-LAST-TRAN-DATA"]
    p5["MAIN-PARA"] --> p7["PROCESS-ENTER-KEY"]
    p5["MAIN-PARA"] --> p11["RECEIVE-TRNADD-SCREEN"]
    p5["MAIN-PARA"] --> p12["RETURN-TO-PREV-SCREEN"]
    p5["MAIN-PARA"] --> p13["SEND-TRNADD-SCREEN"]
    p7["PROCESS-ENTER-KEY"] --> p0["ADD-TRANSACTION"]
    p7["PROCESS-ENTER-KEY"] --> p13["SEND-TRNADD-SCREEN"]
    p7["PROCESS-ENTER-KEY"] --> p15["VALIDATE-INPUT-DATA-FIELDS"]
    p7["PROCESS-ENTER-KEY"] --> p16["VALIDATE-INPUT-KEY-FIELDS"]
    p8["READ-CCXREF-FILE"] --> p13["SEND-TRNADD-SCREEN"]
    p9["READ-CXACAIX-FILE"] --> p13["SEND-TRNADD-SCREEN"]
    p10["READPREV-TRANSACT-FILE"] --> p13["SEND-TRNADD-SCREEN"]
    p13["SEND-TRNADD-SCREEN"] --> p6["POPULATE-HEADER-INFO"]
    p14["STARTBR-TRANSACT-FILE"] --> p13["SEND-TRNADD-SCREEN"]
    p15["VALIDATE-INPUT-DATA-FIELDS"] --> p13["SEND-TRNADD-SCREEN"]
    p16["VALIDATE-INPUT-KEY-FIELDS"] --> p8["READ-CCXREF-FILE"]
    p16["VALIDATE-INPUT-KEY-FIELDS"] --> p9["READ-CXACAIX-FILE"]
    p16["VALIDATE-INPUT-KEY-FIELDS"] --> p13["SEND-TRNADD-SCREEN"]
    p17["WRITE-TRANSACT-FILE"] --> p4["INITIALIZE-ALL-FIELDS"]
    p17["WRITE-TRANSACT-FILE"] --> p13["SEND-TRNADD-SCREEN"]
```

## 業務ルール

未抽出です。先に `legacylens extract` を実行してください。
