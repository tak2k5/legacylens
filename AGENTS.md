# Hướng dẫn cho trợ lý code (AGENTS.md)

LegacyLens đọc COBOL (AWS CardDemo), dựng đồ thị phụ thuộc, dùng agent LLM trích business rule có trích dẫn dòng.
Đọc README.md trước.

## Lệnh

- Cài: `make install`. Test: `make test` (offline, LLM giả lập). Lint: `make lint`.
- Dữ liệu: `make data` (ghim commit CardDemo trong `scripts/fetch_carddemo.sh`).
- Kiểm tra nhãn tay: `make check-gold`.

## Quy tắc

- Không đổi commit CardDemo đã ghim mà không cập nhật số dòng trong `gold/rules.jsonl`.
- Schema trong `src/legacylens/schema.py` là hợp đồng giữa agent, nhãn tay, chấm điểm và tài liệu; sửa thì sửa cả test.
- Test không được gọi mạng hay LLM thật; dùng `FakeClient` trong `tests/test_agent_eval.py`.
- Bảng Kết quả trong README chỉ điền số đo thật trên CardDemo; số từ LLM giả lập không được đưa vào.
- Không đưa API key, file `.env`, mã CardDemo hay mã nội bộ công ty vào repo.
