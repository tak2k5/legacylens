# Câu hỏi mẫu cho từng chương trình

Dùng để hỏi thử ở mục Ask hoặc khi quay video. Các câu này **không** trùng với 20 câu chấm điểm ở
`onboarding/questions.jsonl`. Đừng dùng 20 câu đó để hỏi thử trước mặt người làm bài kiểm tra.

Hỏi bằng tiếng Anh cho kết quả ổn định nhất (mô hình trả lời bằng tiếng Anh). Câu trả lời chưa được chấm, nên luôn
mở trích dẫn `ok` để xem code. Ba loại câu hỏi hợp với cách LegacyLens tìm code nhất:

- **Làm gì:** "What does X do for the business?"
- **Dữ liệu:** "Which files does X read and write?" hoặc "Which copybooks does X use?"
- **Liên kết:** "Which programs call X?" hoặc "Which programs can X transfer control to?"

## 5 chương trình đã gán nhãn (câu hỏi chi tiết hơn)

### COSGN00C: màn hình đăng nhập

- What happens when the user presses PF3 on the sign-on screen?
- What does COSGN00C do when reading the user security file fails for a reason other than "not found"?
- Which file does COSGN00C read to check the password?

### COBIL00C: thanh toán hóa đơn

- What does the bill payment screen do when the user answers N to the confirmation?
- How does COBIL00C update the account balance after the payment is written?
- How is the transaction ID of a bill payment generated?
- What happens when COBIL00C is started without a COMMAREA?

### CBTRN02C: ghi sổ giao dịch hằng ngày

- How does CBTRN02C update the cycle credit and cycle debit when it posts a transaction?
- Which file does CBTRN02C read the daily transactions from?
- Does CBTRN02C check the credit limit before or after the expiration date?

### CBACT04C: tính lãi hằng tháng

- How is the transaction ID of an interest charge built in CBACT04C?
- For which transaction categories does CBACT04C skip the interest calculation?
- How does CBACT04C know that it has moved on to a new account?

### COTRN02C: thêm giao dịch

- What does PF5 do on the add transaction screen?
- Which merchant fields are mandatory when adding a transaction?
- What happens when the user types a card number instead of an account ID?
- What does COTRN02C do when the new transaction ID already exists?

## Các chương trình còn lại

### Batch

| Chương trình | Câu hỏi |
| --- | --- |
| CBACT01C | What does CBACT01C do with the account file, and which output files does it write? |
| CBACT02C | Which file does CBACT02C read and what does it print? |
| CBACT03C | What does the card cross-reference file printed by CBACT03C contain? |
| CBCUS01C | Which file does CBCUS01C read and what does it print? |
| CBEXPORT | Which CardDemo files does CBEXPORT read to build the export file? |
| CBIMPORT | Into which target files does CBIMPORT split the export file? |
| CBPAUP0C | When is a pending authorization message considered expired by CBPAUP0C? |
| CBSTM03A | Which data does CBSTM03A use to print account statements? |
| CBSTM03B | Which program calls CBSTM03B, and what file operations does it perform? |
| CBTRN01C | How is CBTRN01C different from CBTRN02C? |
| CBTRN03C | Which files does CBTRN03C read to print the transaction detail report? |
| COBSWAIT | What parameter does COBSWAIT take and what is its unit? |
| COBTUPDT | Which table or file does COBTUPDT update, and what input does it take? |
| CSUTLDTC | Which programs call CSUTLDTC and what do they pass to it? |
| DBUNLDGS | What does DBUNLDGS unload and where does it write it? |
| PAUDBLOD | What does PAUDBLOD load and from which file? |
| PAUDBUNL | What does PAUDBUNL unload and to which file? |

### Online (màn hình)

| Chương trình | Câu hỏi |
| --- | --- |
| COACCT01 | What does COACCT01 do and which programs call it? |
| COACTUPC | Which account fields can a user change in COACTUPC, and how are they validated? |
| COACTVWC | Which files does COACTVWC read to show an account? |
| COADM01C | Which options does the admin menu COADM01C offer? |
| COCRDLIC | How does COCRDLIC decide which credit cards to list? |
| COCRDSLC | Which file does COCRDSLC read to show the details of a card? |
| COCRDUPC | Which card fields can be updated in COCRDUPC? |
| CODATE01 | What does CODATE01 do and which programs use it? |
| COMEN01C | Which options does the main menu COMEN01C offer to a regular user? |
| COPAUA0C | On what conditions does COPAUA0C approve or decline a card authorization? |
| COPAUS0C | What information does the authorization summary screen COPAUS0C show? |
| COPAUS1C | Which program does COPAUS1C transfer control to, and when? |
| COPAUS2C | How does COPAUS2C mark an authorization message as fraud? |
| CORPT00C | How does CORPT00C submit the report batch job from the online screen? |
| COTRN00C | How does COTRN00C page through the transaction list? |
| COTRN01C | Which file does COTRN01C read to show one transaction? |
| COTRTLIC | Which Db2 operations does COTRTLIC perform on transaction types? |
| COTRTUPC | How does COTRTUPC validate a transaction type before updating it? |
| COUSR00C | Which file does COUSR00C list users from? |
| COUSR01C | Which fields are required when adding a user in COUSR01C? |
| COUSR02C | Which user fields can be changed in COUSR02C? |
| COUSR03C | What does COUSR03C check before deleting a user? |
