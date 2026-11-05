# Tài liệu thiết kế: COTRN02C

_Sinh tự động bởi LegacyLens. Phần cấu trúc lấy từ phân tích tĩnh; mục đích và quy tắc do LLM viết, mỗi quy tắc đã được đối chiếu với mã nguồn._

## Tổng quan

| Loại | Online (CICS) |
| --- | --- |
| Số dòng code | 614 |
| Mã nguồn | [cbl/COTRN02C.cbl](../../data/carddemo/app/cbl/COTRN02C.cbl) |

## Dữ liệu vào ra

| File / dataset | Chế độ | Dòng |
| --- | --- | --- |
| CXACAIX | đọc | [578](../../data/carddemo/app/cbl/COTRN02C.cbl#L578) |
| CCXREF | đọc | [611](../../data/carddemo/app/cbl/COTRN02C.cbl#L611) |
| TRANSACT | đọc | [644](../../data/carddemo/app/cbl/COTRN02C.cbl#L644) |
| TRANSACT | ghi | [713](../../data/carddemo/app/cbl/COTRN02C.cbl#L713) |

## Chuyển sang chương trình khác

| Chương trình | Cách gọi | Dòng |
| --- | --- | --- |
| COMEN01C | XCTL | [508](../../data/carddemo/app/cbl/COTRN02C.cbl#L508) |
| COSGN00C | XCTL | [508](../../data/carddemo/app/cbl/COTRN02C.cbl#L508) |
| CSUTLDTC | CALL | [393](../../data/carddemo/app/cbl/COTRN02C.cbl#L393) |
| CSUTLDTC | CALL | [413](../../data/carddemo/app/cbl/COTRN02C.cbl#L413) |

## Copybook dùng

`COCOM01Y`, `COTRN02`, `COTTL01Y`, `CSDAT01Y`, `CSMSG01Y`, `CVTRA05Y`, `CVACT01Y`, `CVACT03Y`, `DFHAID`, `DFHBMSCA`

## Luồng xử lý (PERFORM)

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

## Quy tắc nghiệp vụ

Chưa trích xuất. Chạy `legacylens extract` trước.
