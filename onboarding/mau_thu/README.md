# File mẫu để thử lệnh chấm

Ba file trong thư mục này do AI viết để thử `make grade`. Đây **không phải** câu trả lời của người thật. Mỗi file có
dòng `MẪU THỬ` ở đầu, nên lệnh chấm ghi rõ "không phải dữ liệu thật" và khối chấm ở bước 10 không ghi chúng vào
`onboarding/ket_qua_bam_gio.csv`. Không dùng số chấm từ các file này ở README hay CV.

- `sv_a_doc_code.txt`: người mới, chỉ đọc code, Q01-Q10. Nhiều câu đoán hoặc thiếu ý.
- `sv_b_legacylens.txt`: người mới, dùng LegacyLens, Q11-Q20. Phần lớn đúng, vài câu thiếu ý.
- `sv_c_tieng_viet.txt`: trả lời bằng tiếng Việt, Q01-Q10. Đúng ý nhưng ít từ khóa tiếng Anh, để thấy mô hình chấm theo
  nghĩa còn từ khóa thì không.
