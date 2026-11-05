# Tài liệu thiết kế: COBIL00C

_Sinh tự động bởi LegacyLens. Phần cấu trúc lấy từ phân tích tĩnh; mục đích và quy tắc do LLM viết, mỗi quy tắc đã được đối chiếu với mã nguồn._

## Tổng quan

| Loại | Online (CICS) |
| --- | --- |
| Số dòng code | 420 |
| Mã nguồn | [cbl/COBIL00C.cbl](../../data/carddemo/app/cbl/COBIL00C.cbl) |

## Dữ liệu vào ra

| File / dataset | Chế độ | Dòng |
| --- | --- | --- |
| ACCTDAT | đọc | [345](../../data/carddemo/app/cbl/COBIL00C.cbl#L345) |
| ACCTDAT | ghi | [379](../../data/carddemo/app/cbl/COBIL00C.cbl#L379) |
| CXACAIX | đọc | [410](../../data/carddemo/app/cbl/COBIL00C.cbl#L410) |
| TRANSACT | đọc | [443](../../data/carddemo/app/cbl/COBIL00C.cbl#L443) |
| TRANSACT | ghi | [512](../../data/carddemo/app/cbl/COBIL00C.cbl#L512) |

## Chuyển sang chương trình khác

| Chương trình | Cách gọi | Dòng |
| --- | --- | --- |
| COMEN01C | XCTL | [281](../../data/carddemo/app/cbl/COBIL00C.cbl#L281) |
| COSGN00C | XCTL | [281](../../data/carddemo/app/cbl/COBIL00C.cbl#L281) |

## Copybook dùng

`COCOM01Y`, `COBIL00`, `COTTL01Y`, `CSDAT01Y`, `CSMSG01Y`, `CVACT01Y`, `CVACT03Y`, `CVTRA05Y`, `DFHAID`, `DFHBMSCA`

## Luồng xử lý (PERFORM)

```mermaid
flowchart TD
    p0["CLEAR-CURRENT-SCREEN"] --> p3["INITIALIZE-ALL-FIELDS"]
    p0["CLEAR-CURRENT-SCREEN"] --> p12["SEND-BILLPAY-SCREEN"]
    p4["MAIN-PARA"] --> p0["CLEAR-CURRENT-SCREEN"]
    p4["MAIN-PARA"] --> p6["PROCESS-ENTER-KEY"]
    p4["MAIN-PARA"] --> p10["RECEIVE-BILLPAY-SCREEN"]
    p4["MAIN-PARA"] --> p11["RETURN-TO-PREV-SCREEN"]
    p4["MAIN-PARA"] --> p12["SEND-BILLPAY-SCREEN"]
    p6["PROCESS-ENTER-KEY"] --> p0["CLEAR-CURRENT-SCREEN"]
    p6["PROCESS-ENTER-KEY"] --> p1["ENDBR-TRANSACT-FILE"]
    p6["PROCESS-ENTER-KEY"] --> p2["GET-CURRENT-TIMESTAMP"]
    p6["PROCESS-ENTER-KEY"] --> p7["READ-ACCTDAT-FILE"]
    p6["PROCESS-ENTER-KEY"] --> p8["READ-CXACAIX-FILE"]
    p6["PROCESS-ENTER-KEY"] --> p9["READPREV-TRANSACT-FILE"]
    p6["PROCESS-ENTER-KEY"] --> p12["SEND-BILLPAY-SCREEN"]
    p6["PROCESS-ENTER-KEY"] --> p13["STARTBR-TRANSACT-FILE"]
    p6["PROCESS-ENTER-KEY"] --> p14["UPDATE-ACCTDAT-FILE"]
    p6["PROCESS-ENTER-KEY"] --> p15["WRITE-TRANSACT-FILE"]
    p7["READ-ACCTDAT-FILE"] --> p12["SEND-BILLPAY-SCREEN"]
    p8["READ-CXACAIX-FILE"] --> p12["SEND-BILLPAY-SCREEN"]
    p9["READPREV-TRANSACT-FILE"] --> p12["SEND-BILLPAY-SCREEN"]
    p12["SEND-BILLPAY-SCREEN"] --> p5["POPULATE-HEADER-INFO"]
    p13["STARTBR-TRANSACT-FILE"] --> p12["SEND-BILLPAY-SCREEN"]
    p14["UPDATE-ACCTDAT-FILE"] --> p12["SEND-BILLPAY-SCREEN"]
    p15["WRITE-TRANSACT-FILE"] --> p3["INITIALIZE-ALL-FIELDS"]
    p15["WRITE-TRANSACT-FILE"] --> p12["SEND-BILLPAY-SCREEN"]
```

## Quy tắc nghiệp vụ

Chưa trích xuất. Chạy `legacylens extract` trước.
