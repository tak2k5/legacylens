# Bài kiểm tra onboarding với người thật

Người làm bài làm trên mục **📝 Bài kiểm tra** của giao diện (`make ui`). Mỗi người nhận một đề 20 câu rút ngẫu nhiên
từ `ngan_hang.jsonl`: 240 câu về 24 chương trình CardDemo, 10 câu mỗi chương trình. Mỗi câu trong đề thuộc một chương
trình khác nhau, và mỗi đề có nhiều nhất một câu hỏi mã giao dịch CICS. Đề cố định theo số thứ tự của người làm bài, nên
tải lại trang vẫn ra đúng đề đó. File câu trả lời ghi dòng `Đề: Q01=COSGN00C-03 ...`, nên lúc chấm luôn biết câu nào là
câu nào trong ngân hàng.

- Phần 1 (Q01-Q10 hoặc Q11-Q20): chỉ đọc code. Dưới mỗi câu có tên chương trình, ghi chú đầu file và toàn bộ mã nguồn.
- Phần 2: dùng LegacyLens (Hỏi đáp, Tài liệu, Bản đồ).
- Người số lẻ đọc code ở Q01-Q10, người số chẵn đọc code ở Q11-Q20.

Làm ngoài giao diện: `make paper N=3` ghi đề của người số 3 (`onboarding/tra_loi/de_nguoi3.md`) và hai file trả lời
`nguoi3_phan1.txt`, `nguoi3_phan2.txt` có sẵn dòng `Đề:`. Người làm bài điền sau mỗi `Qnn:` rồi gửi lại.

Mỗi câu trong ngân hàng có nhóm từ khóa của đáp án và vùng dòng trong mã nguồn. Các câu do AI soạn nháp từ mã nguồn;
test `test_question_bank_answers_are_in_the_cited_lines` kiểm tra mọi nhóm từ khóa đều có trong vùng dòng được trích.

`questions.jsonl` là 20 câu cố định dùng cho `make eval-qa` (agent tự trả lời) và cho các file mẫu trong `mau_thu/`.
