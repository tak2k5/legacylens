# Hướng dẫn làm LegacyLens từ đầu đến cuối

File riêng cho Kiet. Xóa trước khi để repo Public (bước 12).

Làm đúng thứ tự từ bước 0 đến bước 12. Mỗi bước có:

- **Ở đâu:** làm ở chỗ nào.
- **Làm:** khối lệnh. Dán cả khối vào terminal.
- **Đúng khi:** kết quả phải thấy. Chưa thấy thì đừng sang bước sau. Xem mục "Nếu lỗi" của bước đó hoặc Phụ lục A.
- **Ghi lại:** số cần chép vào README.
- **Đẩy:** lệnh lưu lên GitHub. Mỗi bước xong đẩy một lần, để mất Codespace cũng không mất việc.

Tổng thời gian khoảng 1,5 đến 2 ngày làm việc. Phần lâu nhất là bước 4 (duyệt nhãn) và bước 8 (cải thiện).
Chi phí 0 đồng.

| Bước | Việc | Thời gian |
| --- | --- | --- |
| 0 | Chuẩn bị tài khoản | 5 phút |
| 1 | Tạo repo, đưa code lên | 15 phút |
| 2 | Cài, tải dữ liệu, chạy test | 10 phút |
| 3 | Số liệu phân tích tĩnh | 5 phút |
| 4 | Duyệt 49 nhãn tay | 2-3 giờ |
| 5 | Chọn và cài mô hình LLM | 15-30 phút |
| 6 | Agent trích rule cho 5 chương trình | 30-60 phút |
| 7 | Chấm điểm | 30 phút |
| 8 | Cải thiện 1-2 lần | nửa ngày |
| 9 | Sinh tài liệu thiết kế vi/ja | 10 phút |
| 10 | Bài kiểm tra bấm giờ với người thật | 1-2 giờ |
| 11 | Kiểm tra lại lỗi CBACT04C | 15 phút |
| 12 | Hoàn tất: README, video, Public, CV | 1-2 giờ |

---

## Bước 0. Chuẩn bị

**Ở đâu:** trình duyệt.

**Làm:**

1. Đăng nhập GitHub (tài khoản dùng cho 2 repo kia).
2. Tải `legacylens.zip` về máy.
3. Chọn trước một trong ba cách chạy LLM ở bước 5 (A Gemini, B Groq, C Colab). Nếu chưa biết chọn gì, chọn A.

**Đúng khi:** có file zip trên máy và đã đăng nhập GitHub.

---

## Bước 1. Tạo repo và đưa code lên

**Ở đâu:** github.com, rồi Codespaces.

**Làm:**

1. Vào github.com/new. Đặt tên `legacylens`, chọn **Private**. **Không** tích "Add a README", không chọn
   .gitignore hay license, vì zip đã có sẵn. Bấm Create repository.
2. Trên trang repo trống, bấm **Code > Codespaces > Create codespace on main**. Chờ trình soạn thảo mở.
3. Kéo file `legacylens.zip` từ máy thả vào khung Explorer bên trái của Codespace.
4. Dán vào terminal (Ctrl+` để mở):

```bash
unzip -q legacylens.zip -d /tmp/ll && cp -a /tmp/ll/legacylens/. . && rm -rf /tmp/ll legacylens.zip
sed -i "s/<ten-github>/$GITHUB_USER/" README.md
ls
```

**Đúng khi:** `ls` in ra `AGENTS.md  HUONG_DAN.md  LICENSE  Makefile  README.md  app.py  docs  gold ...`.

**Đẩy:**

```bash
git add -A
git status --short | grep -E '(^|/)(\.env|data/)' && echo "DỪNG: có file không được đẩy" || echo "sạch"
git commit -qm "LegacyLens: đọc COBOL CardDemo, đồ thị phụ thuộc, agent trích business rule có trích dẫn"
git branch -M main && git push -u origin main
```

Dòng thứ hai phải in `sạch`.

---

## Bước 2. Cài thư viện, tải CardDemo, chạy test

**Ở đâu:** terminal Codespace.

**Làm:**

```bash
make install
make data
make test
make lint
```

**Đúng khi:**

- `make data` in `CardDemo @ 59cc6c2... -> data/carddemo`.
- `make test` in `27 passed`.
- `make lint` in `All checks passed!` và `files already formatted`.

**Nếu lỗi:** `make: python: No such file` thì chạy `make install PY=python3` và thêm `PY=python3` vào mọi lệnh
make. Repo chỉ dùng CPU, chạy tốt trên máy 2 nhân 8 GB.

Ghi chú: repo có `.devcontainer`. Từ lần tạo Codespace sau, bước cài và `make data` tự chạy. Lần này bạn đã tạo
Codespace trước khi có file đó nên phải chạy tay, không cần Rebuild.

**Đẩy:** không có gì mới. Sau khi đẩy ở bước 1, mở tab Actions trên GitHub: lần chạy `ci` phải có dấu xanh.

---

## Bước 3. Số liệu phân tích tĩnh

**Ở đâu:** terminal.

**Làm:**

```bash
make stats graph check-gold
```

**Đúng khi:**

- `stats` in `"programs": 44`, `"copybooks": 62`, `"jcl_steps": 119`, `"loc": 22904`, `"paragraphs": 870`,
  `"graph_nodes": 225`, `"graph_edges": 710`.
- Có file `reports/graph.json` và `reports/graph.mmd`.
- Dòng cuối là `49/49 gold rules pass the citation check`.

**Ghi lại:** các số này đã có sẵn trong bảng đầu của mục Kết quả trong README. Chỉ cần so lại cho khớp.

**Đẩy:**

```bash
git add reports && git commit -qm "Đồ thị phụ thuộc CardDemo" && git push
```

---

## Bước 4. Duyệt 49 nhãn tay (phần quan trọng nhất)

Nhãn trong `gold/rules.jsonl` do trợ lý soạn. Chúng đã qua kiểm tra trích dẫn tự động, nhưng phải do bạn đọc và
xác nhận thì mới được gọi là nhãn tay. Đây cũng là cách học đủ COBOL để trả lời phỏng vấn. Mở song song tài liệu
"COBOL tối thiểu cho phỏng vấn LegacyLens".

**Ở đâu:** Codespace, terminal và trình soạn thảo.

**Làm:** đi theo thứ tự dưới đây, từ dễ đến khó.

| Thứ tự | Chương trình | Làm gì | Số nhãn |
| --- | --- | --- | --- |
| 1 | COSGN00C | Đăng nhập | 9 |
| 2 | COBIL00C | Thanh toán hóa đơn | 8 |
| 3 | CBTRN02C | Ghi sổ giao dịch hằng ngày | 6 |
| 4 | CBACT04C | Tính lãi hằng tháng | 8 |
| 5 | COTRN02C | Thêm giao dịch | 18 |

Với mỗi chương trình:

```bash
make review PROG=COSGN00C
```

Lệnh in ra `mở out/review/COSGN00C.txt`. Ctrl+click vào đường dẫn để mở. File liệt kê từng nhãn, ngay dưới là
các dòng code nó trích. Muốn xem rộng hơn, bấm Ctrl+P, gõ `COSGN00C.cbl:118` để nhảy tới dòng 118.

Với mỗi nhãn, hỏi 3 câu:

1. `summary` có nói đúng điều code làm không? (đọc từng `IF`, `MOVE`, `PERFORM` trong vùng trích)
2. `condition` và `outcome` có đúng mã lỗi, thông báo, giá trị như trong code không?
3. Vùng trích có gọn không? Phải gồm dòng điều kiện và dòng kết quả, không quá 30 dòng.

Sau mỗi chương trình, hỏi thêm: còn quy tắc nghiệp vụ nào trong chương trình mà danh sách bỏ sót không?

- Sai thì sửa ngay trong `gold/rules.jsonl`. Mỗi nhãn là một dòng JSON, giữ nguyên định dạng một dòng.
- Thiếu thì chép một dòng có sẵn, đổi `id` (ví dụ `COSGN00C-G10`), rồi sửa nội dung và số dòng.
- Ghi vào một file nháp những gì bạn đã sửa. Đó là chuyện để kể khi phỏng vấn.

**Đúng khi:** chạy `make check-gold` sau mỗi chương trình, dòng cuối vẫn là `N/N gold rules pass`.

**Nếu lỗi:** `cites no evidence` nghĩa là vùng trích không chứa tên biến hay thông báo nào mà nhãn nhắc tới. Sửa
số dòng hoặc thêm tên biến đúng vào `fields`.

**Ghi lại:** số nhãn cuối cùng. Nếu khác 49, sửa con số trong README (tìm `49`).

**Đẩy:** sau mỗi chương trình:

```bash
git add gold && git commit -qm "Duyệt nhãn COSGN00C" && git push
```

---

## Bước 5. Chọn và cài mô hình LLM

Chọn một trong ba cách. Cả ba đều miễn phí và gọi qua cùng một kiểu API, nên code không phải sửa.

| | A. Gemini (khuyên dùng) | B. Groq | C. Ollama trên Colab T4 |
| --- | --- | --- | --- |
| Lấy khóa | aistudio.google.com/apikey | console.groq.com/keys (khóa đang dùng ở repo kia) | Không cần khóa |
| Ưu điểm | Hạn mức token mỗi phút rộng, gọi tool tốt | Rất nhanh, đã có khóa | Dùng GPU Colab, không giới hạn |
| Rủi ro | Hạn mức đổi theo thời gian | Gói miễn phí giới hạn token mỗi phút thấp, agent đọc nhiều code dễ gặp lỗi 413 hoặc 429 | Mô hình 7B yếu hơn, phải giữ tab Colab mở |

Hạn mức gói miễn phí thay đổi thường xuyên. Xem trang Rate limits của nhà cung cấp trước khi chạy.

**Ở đâu:** trình duyệt (lấy khóa), rồi Codespace.

**Làm:**

1. Tạo file `.env` và mở nó:

```bash
cp .env.example .env && code .env
```

2. Trong `.env`, bỏ dấu `#` ở **một** khối (A, B hoặc C) và điền khóa sau `LLM_API_KEY=`.
   - Với C: mở `notebooks/colab_llm.ipynb` trên Colab (File > Upload notebook), chọn Runtime > T4 GPU,
     Run all. Ô cuối in ra `LLM_BASE_URL=https://....trycloudflare.com/v1`. Chép vào `.env`.
3. Kiểm tra tên mô hình có tồn tại và khóa dùng được:

```bash
set -a; . ./.env; set +a
curl -s "${LLM_BASE_URL%/}/models" -H "Authorization: Bearer $LLM_API_KEY" | grep -o '"id": *"[^"]*"' | head -20
git check-ignore .env && echo ".env sẽ không bị đẩy"
```

4. Hỏi thử một câu:

```bash
make ask Q="Which program checks the user id and password at sign-on, and what happens when the password is wrong?"
```

**Đúng khi:**

- Danh sách mô hình có tên bạn ghi ở `LLM_MODEL`. Nếu không có, chọn một tên trong danh sách rồi sửa `.env`
  (Gemini ghi tên dạng `models/gemini-...`, bỏ phần `models/` khi điền).
- `git check-ignore` in `.env sẽ không bị đẩy`.
- `make ask` in một câu trả lời, các dòng `[COSGN00C:...] ok`, và dòng cuối có số token.

**Nếu lỗi:** xem Phụ lục A.

Không muốn dùng file `.env`: vào github.com/settings/codespaces > New secret, tạo `LLM_BASE_URL`, `LLM_API_KEY`,
`LLM_MODEL`, cho phép repo `legacylens`, rồi khởi động lại Codespace. Lệnh make tự dùng biến này khi không có `.env`.

**Ghi lại:** tên mô hình. Bảng Kết quả cần nó.

**Đẩy:** không đẩy gì. `.env` không bao giờ lên GitHub.

---

## Bước 6. Agent trích rule cho 5 chương trình

**Ở đâu:** terminal. Chạy từng chương trình một, để lỗi giới hạn tốc độ chỉ làm hỏng một chương trình.

**Làm:**

```bash
make extract PROGS=COSGN00C
```

Xem kết quả trước khi chạy tiếp:

```bash
cat out/rules/COSGN00C.json | head -40
tail -1 reports/runs.jsonl
```

Rồi chạy 4 chương trình còn lại:

```bash
make extract PROGS="COBIL00C CBTRN02C CBACT04C COTRN02C"
```

**Đúng khi:** mỗi chương trình in một dòng dạng
`COSGN00C: 8 rules, 8 pass the citation check, 11 tool calls (0 repeats blocked), 41230+2210 tokens, 38.5s`.

**Nếu lỗi:**

- Một chương trình in `FAILED` thì các chương trình khác vẫn được lưu. Cuối lệnh có dòng gợi ý chạy lại đúng
  chương trình hỏng.
- `429` hoặc `rate limit`: thêm `LLM_PAUSE=6` vào `.env` (nghỉ 6 giây giữa hai lần gọi), chạy lại.
- `413`, `Request too large` hoặc `context length`: mô hình hoặc gói miễn phí không đủ cửa sổ. Đổi sang cách A
  hoặc C, hoặc giảm số bước: `make extract PROGS=COTRN02C ARGS="--max-steps 10"`.
- `did not return valid JSON`: mô hình yếu không trả JSON đúng. Chạy lại một lần. Nếu vẫn lỗi, đổi mô hình.

**Ghi lại:** token và giây trung bình mỗi chương trình. Tính nhanh:

```bash
python3 -c "
import json; rows=[json.loads(l) for l in open('reports/runs.jsonl')][-5:]
print('model', rows[-1]['model'])
print('tokens/program', round(sum(r['prompt_tokens']+r['completion_tokens'] for r in rows)/len(rows)))
print('seconds/program', round(sum(r['seconds'] for r in rows)/len(rows),1))"
```

**Đẩy:** `out/` không được đẩy (là đầu ra tạm). Số liệu sẽ đẩy ở bước 7.

---

## Bước 7. Chấm điểm

**Ở đâu:** terminal.

**Làm:**

```bash
make eval
make eval-qa
```

`eval-qa` hỏi agent 20 câu, mất 10-30 phút. Gặp `429` thì đặt `LLM_PAUSE` như bước 6.

**Đúng khi:** có `reports/eval.md` và `reports/eval_qa.md`, mỗi file có bảng số.

**Ghi lại:** mở hai file, chép vào bảng thứ hai trong mục Kết quả của README:

| Ô trong README | Lấy từ |
| --- | --- |
| Precision / Recall / F1 | các dòng `Precision`, `Recall`, `F1` trong `reports/eval.md` |
| Trích dẫn qua kiểm tra | dòng `Citations that pass the source check` trong `reports/eval.md` |
| Token và thời gian | số tính ở bước 6, kèm tên mô hình |
| Agent trả lời đúng 20 câu | `Correct` và `Answers citing the expected lines` trong `reports/eval_qa.md` |

Số nào ra thấp cũng ghi đúng như vậy. Một F1 0,45 có giải thích còn tốt hơn một con số đẹp không chứng minh được.

**Đẩy:**

```bash
cp reports/eval.md reports/eval_lan1.md && cp reports/eval_qa.md reports/eval_qa_lan1.md
git add reports README.md && git commit -qm "Kết quả lần 1: trích rule và hỏi đáp onboarding" && git push
```

---

## Bước 8. Cải thiện 1-2 lần

Đây là phần để kể khi phỏng vấn: thấy lỗi gì, đổi gì, số thay đổi ra sao.

**Ở đâu:** `reports/eval.md`, `src/legacylens/agent.py`, terminal.

**Làm:**

1. Đọc dòng `Missed gold rules` (nhãn tay mà agent bỏ sót) và `Predicted rules with no gold match` (rule agent
   thêm mà nhãn không có) ở cuối `reports/eval.md`. Mở `gold/rules.jsonl` và `out/rules/<chương trình>.json` để so. Tìm một kiểu lỗi lặp lại. Ví dụ: hay trích cả đoạn dài, bỏ qua kiểm tra trong
   `EVALUATE`, gộp hai rule làm một.
2. Sửa **một** chỗ. Ví dụ:
   - Thêm một câu vào `SYSTEM_RULES` trong `src/legacylens/agent.py` ("Each WHEN branch that sets an error
     message is a separate rule.").
   - Tăng số bước agent được đi từ 16 lên 24: thêm `ARGS="--max-steps 24"` vào lệnh extract ở dưới.
   - Đổi mô hình trong `.env`.
3. Chạy lại:

```bash
make test
make extract PROGS="COSGN00C COBIL00C CBTRN02C CBACT04C COTRN02C" && make eval
```

4. Thêm vào README, ngay dưới bảng Kết quả, một bảng nhỏ:

```markdown
| Lần | Thay đổi | P / R / F1 | Token mỗi chương trình |
| --- | --- | --- | --- |
| 1 | Bản đầu | ... | ... |
| 2 | Tách mỗi nhánh WHEN thành một rule | ... | ... |
```

**Đúng khi:** `make test` vẫn `27 passed`, và bảng có ít nhất 2 dòng với số thật.

**Ghi lại:** kể cả khi số giảm. "Thử X, F1 giảm vì Y, nên quay lại" là câu trả lời phỏng vấn tốt.

**Đẩy:**

```bash
cp reports/eval.md reports/eval_lan2.md
git add -A
git status --short | grep -E '(^|/)(\.env|data/)' && echo "DỪNG: có file không được đẩy" || echo "sạch"
git commit -qm "Lần 2: <ghi thay đổi>" && git push
```

---

## Bước 9. Tài liệu thiết kế tiếng Việt và tiếng Nhật

**Ở đâu:** terminal.

**Làm:**

```bash
make doc PROGS="COSGN00C COBIL00C CBTRN02C CBACT04C COTRN02C"
```

Mở `docs/generated/CBACT04C.vi.md`, bấm Ctrl+Shift+V để xem bản hiển thị (có sơ đồ Mermaid).

**Đúng khi:** mỗi chương trình có hai file `.vi.md` và `.ja.md`. Bảng rule có cột trích dẫn, rule trượt kiểm tra
được đánh dấu.

**Đẩy:**

```bash
git add docs/generated && git commit -qm "Tài liệu thiết kế vi/ja cho 5 chương trình" && git push
```

---

## Bước 10. Bài kiểm tra bấm giờ với người thật

Sau bước 4 bạn đã thuộc code, nên nếu bạn tự làm bài thì kết quả bị lệch. Nên nhờ 1-2 người bạn biết lập trình
nhưng chưa đọc CardDemo.

**Ở đâu:** Codespace (cho người làm bài dùng chung qua chia sẻ màn hình), phiếu `onboarding/BAI_KIEM_TRA.md`.

**Làm:**

1. Mở giao diện:

```bash
make ui
```

   Codespaces hiện thông báo cổng 8501, bấm **Open in Browser**.
2. Người làm bài trả lời Q01-Q10 chỉ bằng đọc code (được dùng tìm kiếm của trình soạn thảo), ghi giờ bắt đầu và xong.
3. Trả lời Q11-Q20 bằng giao diện LegacyLens, ghi giờ.
4. Nếu có người thứ hai, đổi ngược: Q01-Q10 dùng giao diện, Q11-Q20 đọc code. Như vậy độ khó câu hỏi không làm lệch
   kết quả.
5. Chấm theo `onboarding/questions.jsonl` (từ khóa và dòng mong đợi).

**Ghi lại:** điền dòng cuối của bảng Kết quả: thời gian trung bình mỗi câu và số câu đúng, cho cả hai cách. Ghi
rõ số người làm (ví dụ "2 người, 10 câu mỗi cách"). Mẫu nhỏ thì nói là mẫu nhỏ.

**Đẩy:**

```bash
git add onboarding README.md && git commit -qm "Kết quả bài kiểm tra onboarding bấm giờ" && git push
```

---

## Bước 11. Kiểm tra lại lỗi CBACT04C

README có mục "Một lỗi gặp khi gán nhãn". Trợ lý đã chạy thử bản tái hiện và tìm thấy lỗi đã được báo ở issue #64
của CardDemo. Bạn cần tự hiểu và tự chạy để kể được.

**Ở đâu:** Codespace.

**Làm:**

```bash
sudo apt-get update -qq && sudo apt-get install -y -qq gnucobol
cobc -x -free scripts/repro_cbact04c.cbl -o /tmp/repro && /tmp/repro
```

Rồi mở `data/carddemo/app/cbl/CBACT04C.cbl` dòng 188-222 (Ctrl+P, gõ `CBACT04C.cbl:188`), so với
`scripts/repro_cbact04c.cbl`.

**Đúng khi:** chương trình in `balance updated ... for account 101` nhưng không có dòng nào cho account 202. Bạn
tự giải thích được bằng lời vì sao nhánh `ELSE` ở dòng 219 không bao giờ chạy.

Khi kể, nói đúng: "Tôi gặp lỗi này khi duyệt nhãn, viết bản tái hiện bằng GnuCOBOL, rồi thấy nó đã được báo ở
issue #64." Đừng nói là bạn phát hiện đầu tiên.

**Đẩy:** không có gì mới.

---

## Bước 12. Hoàn tất

**Ở đâu:** Codespace, GitHub, CV.

**Làm:**

1. Kiểm tra README không còn ô `[X]`:

```bash
grep -n "\[X\]" README.md || echo "đã điền hết"
```

2. Quay video 2 phút (OBS hoặc công cụ ghi màn hình có sẵn): `make stats`, mở `reports/graph.mmd`, `make ui` hỏi
   một câu và mở trích dẫn, mở `docs/generated/CBACT04C.ja.md`, mở `reports/eval.md`. Tải lên YouTube ở chế độ
   Unlisted, dán link vào đầu README.
3. Xóa file riêng và đẩy:

```bash
git rm -q HUONG_DAN.md
git commit -qm "Bỏ ghi chú riêng" && git push
```

4. Kiểm tra lần cuối là không có khóa trong lịch sử git:

```bash
git log -p | grep -nE "gsk_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{30,}|API_KEY=[A-Za-z0-9_-]{16,}" && echo "DỪNG: có khóa trong lịch sử" || echo "sạch"
```

5. Trên GitHub: Settings > General > Danger Zone > Change visibility > **Public**.
6. Thêm dự án vào CV theo mẫu câu trong tài liệu "Dự án giải quyết vấn đề thật của FPT Software", thay số bằng số
   của bạn. Nói đúng về nhãn: "49 nhãn tôi duyệt từng dòng với mã nguồn". Nếu được hỏi, nói rõ bản nháp đầu có trợ
   giúp của AI.

**Đúng khi:** repo Public, CI xanh, README không còn `[X]`, lệnh ở mục 4 in `sạch`.

---

## Phụ lục A. Lỗi thường gặp

| Thấy | Nghĩa là | Làm |
| --- | --- | --- |
| `error: No LLM endpoint configured` | Chưa có `.env` hay secret | Bước 5 |
| `401` hoặc `invalid api key` | Khóa sai hoặc thiếu | Sửa `LLM_API_KEY`, không để dấu cách hay dấu nháy |
| `404` hoặc `model not found` | Sai tên mô hình | Chạy lệnh `curl .../models` ở bước 5, chọn tên có trong danh sách |
| `429`, `rate limit` | Quá số lần gọi mỗi phút | `LLM_PAUSE=6` trong `.env`, chạy lại chương trình hỏng |
| `413`, `Request too large` | Quá token mỗi phút hoặc quá cửa sổ ngữ cảnh | Đổi sang cách A hoặc C |
| `did not return valid JSON` | Mô hình trả sai định dạng | Chạy lại, hoặc đổi mô hình mạnh hơn |
| Colab: `Connection refused` hoặc `530` | Colab đã ngắt, URL đường hầm chết | Chạy lại notebook, cập nhật `LLM_BASE_URL` |
| `data/carddemo/app not found` | Chưa tải dữ liệu | `make data` |
| CI đỏ ở bước lint | Code chưa format | `ruff format . && make lint`, rồi đẩy lại |

## Phụ lục B. Repo so với các ràng buộc bạn đã nêu

| Ràng buộc | Repo |
| --- | --- |
| Không cài gì trên máy, làm trong Codespaces | Có. Mọi bước chạy trong Codespace; có `.devcontainer` |
| Đủ chạy trên Codespaces 2 nhân | Có. Chỉ dùng CPU, không Docker; CardDemo 22.904 dòng, dựng đồ thị dưới 1 giây |
| GPU chỉ dùng trên Colab | Có. Repo không cần GPU; cách C chạy mô hình trên Colab T4 |
| 0 đồng | Có. Gemini/Groq gói miễn phí hoặc Colab miễn phí; CI dùng GitHub Actions miễn phí |
| Chỉ điền số tự đo | Có. Bảng Kết quả để `[X]` cho tới khi bạn chạy; test dùng LLM giả lập không sinh số |
| Không đẩy khóa, `.env`, dữ liệu lên GitHub | Có. `.env`, `data/`, `out/` nằm trong `.gitignore`; bước 1 và 12 kiểm tra lại |
| Zip chỉ chứa code, không có lịch sử git | Có |
| Dùng lại khóa Groq của repo kia | Có. Đặt `LLM_API_KEY` bằng khóa đó (cách B); repo cũng nhận `GROQ_API_KEY` |
