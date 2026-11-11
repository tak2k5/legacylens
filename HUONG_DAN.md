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
| 5 | Chạy mô hình open-weight trên Colab T4 | 15-20 phút |
| 6 | Agent trích rule cho 5 chương trình | 30-90 phút |
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
3. Đăng nhập tài khoản Google, để dùng Colab ở bước 5.

**Đúng khi:** có file zip trên máy, đã đăng nhập GitHub và Google.

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
- `make test` in `31 passed`.
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

## Bước 5. Chạy mô hình open-weight trên Colab T4

Dùng mô hình open-weight **Qwen2.5 7B Instruct** (giấy phép Apache-2.0), chạy bằng **Ollama** trên GPU T4 miễn phí
của Colab. Codespace gọi sang Colab qua một đường hầm Cloudflare. Bạn không cần khóa API và không phụ thuộc gói
miễn phí của hãng nào.

```text
Codespace (make ask / extract)  --internet-->  đường hầm Cloudflare  -->  Colab T4: Ollama + Qwen2.5 7B
```

Cần hai tab trình duyệt mở cùng lúc: tab **Colab** (máy chủ mô hình) và tab **Codespace** (chạy LegacyLens).

Mất khoảng 15-20 phút cho lần đầu. Những lần sau chỉ cần làm lại 5.3, 5.4 và 5.6 (khoảng 8 phút).

### 5.1. Lấy file notebook về máy

**Ở đâu:** Codespace.

**Làm:** trong khung Explorer bên trái, mở thư mục `notebooks`, bấm chuột phải vào `colab_llm.ipynb` > **Download**.

**Đúng khi:** máy bạn có file `colab_llm.ipynb` (thường trong thư mục Downloads).

### 5.2. Mở notebook trên Colab

**Ở đâu:** tab mới, colab.research.google.com. Đăng nhập tài khoản Google.

**Làm:** hộp thoại "Open notebook" hiện ra (nếu không, chọn **File > Upload notebook**). Chọn thẻ **Upload**, kéo
file `colab_llm.ipynb` vào.

**Đúng khi:** notebook mở ra, tiêu đề đầu trang là "LLM open-weight trên Colab T4 cho LegacyLens".

### 5.3. Bật GPU T4

**Ở đâu:** Colab.

**Làm:** menu **Runtime > Change runtime type**. Ở "Hardware accelerator" chọn **T4 GPU**, bấm **Save**.

**Đúng khi:** góc trên bên phải có chữ **T4** sau khi kết nối.

**Nếu lỗi:** "Cannot connect to GPU backend" nghĩa là Colab đang hết GPU miễn phí hoặc bạn đã dùng hết hạn mức
trong ngày. Chờ vài giờ rồi thử lại. Trong lúc chờ, bạn vẫn làm được bước 4.

### 5.4. Chạy cả notebook

**Ở đâu:** Colab.

**Làm:** menu **Runtime > Run all**. Nếu Colab hỏi "Warning: This notebook was not authored by Google", bấm
**Run anyway**. Chờ khoảng 5-8 phút. Không cần sửa ô nào.

**Đúng khi:** đọc kết quả dưới từng ô theo thứ tự:

| Ô | Phải thấy |
| --- | --- |
| 2. Kiểm tra GPU | `Tesla T4, 15360 MiB` |
| 3. Cài Ollama | dòng cuối `ollama version is ...` |
| 4. Khởi động | `Ollama đang chạy: {"version": ...}` |
| 5. Tải mô hình | dòng cuối `success` |
| 6. Thử gọi tool | `Gọi tool OK (...s): {'name': 'read_lines', ...}` |
| 7. Đường hầm | 4 dòng bắt đầu bằng `LLM_` |

**Nếu lỗi:**

- Ô 2 in `KHÔNG CÓ GPU`: làm lại 5.3, rồi Run all lại.
- Ô 6 in `Mô hình không gọi tool`: chạy lại riêng ô 6 (bấm nút ▶ bên trái ô). Nếu vẫn vậy, xem 5.9.
- Ô 7 in `Chưa có URL`: chạy lại riêng ô 7.

### 5.5. Tạo file `.env` trong Codespace

**Ở đâu:** tab Codespace, terminal.

**Làm:**

```bash
cp .env.example .env && code .env
```

File `.env` mở ra trong trình soạn thảo. Xóa hết nội dung, rồi dán 4 dòng `LLM_` mà ô 7 của Colab in ra. File chỉ
còn 4 dòng dạng:

```text
LLM_BASE_URL=https://abc-def-ghi.trycloudflare.com/v1
LLM_MODEL=qwen2.5:7b-instruct
LLM_API_KEY=ollama
LLM_CONTEXT=32768
```

Bấm Ctrl+S để lưu.

**Đúng khi:** đã lưu file, tên tab không còn dấu chấm tròn.

### 5.6. Kiểm tra Codespace gọi được sang Colab

**Ở đâu:** terminal Codespace.

**Làm:**

```bash
set -a; . ./.env; set +a
curl -s "$LLM_BASE_URL/models"; echo
git check-ignore .env && echo ".env sẽ không bị đẩy"
```

**Đúng khi:**

- Dòng đầu là JSON có `"id":"qwen2.5:7b-instruct"`.
- Dòng cuối là `.env sẽ không bị đẩy`.

**Nếu lỗi:** lỗi `530`, `1033`, hoặc không in gì nghĩa là đường hầm đã tắt. Xem tab Colab còn chạy không (góc phải
còn chữ T4 và có dấu ✓ xanh). Nếu Colab đã ngắt, làm lại từ 5.3, rồi dán URL mới vào `.env` (5.5).

### 5.7. Hỏi thử một câu

**Ở đâu:** terminal Codespace.

**Làm:**

```bash
make ask Q="Which program checks the user id and password at sign-on, and what happens when the password is wrong?"
```

Chờ 1-3 phút. Mô hình chạy trên T4 chậm hơn API trả phí, đây là bình thường.

**Đúng khi:** in ra một đoạn trả lời, vài dòng `[COSGN00C:...] ok`, và dòng cuối dạng
`(5 tool calls, 18000+300 tokens, 70.2s)`.

**Nếu lỗi:**

- `WARNING: a request used ... context tokens`: cuộc hội thoại gần chạm giới hạn 32k token, mô hình có thể quên
  phần đầu. Với một câu hỏi thì bỏ qua được. Nếu lỗi này hiện khi chạy `make extract`, giảm số bước bằng
  `ARGS="--max-steps 10"` (xem bước 6).
- `did not return valid JSON`: chạy lại lệnh. Mô hình 7B đôi khi trả sai định dạng.
- Các lỗi khác: xem Phụ lục A.

### 5.8. Mỗi lần quay lại làm tiếp

Colab miễn phí tự ngắt khi để yên khoảng 90 phút, và mỗi phiên dài tối đa khoảng 12 giờ. Mỗi lần ngắt thì URL đổi.
Khi quay lại:

1. Colab: **Runtime > Run all** (5.4). Lần này nhanh hơn nếu runtime chưa bị xóa.
2. Chép 4 dòng `LLM_` mới vào `.env` (5.5).
3. Chạy lại 5.6 để kiểm tra.

Trong lúc chạy `make extract` hay `make eval-qa`, thỉnh thoảng bấm vào tab Colab để nó không bị coi là để yên.

### 5.9. Khi Qwen 7B không đủ tốt

Có hai cách, theo thứ tự nên thử:

1. **Mô hình open-weight lớn hơn trên Colab.** Trong ô 1 của notebook, bỏ dấu `#` ở hai dòng `qwen2.5:14b-instruct`
   và `CONTEXT = 16384`, thêm `#` vào hai dòng 7B, rồi Run all lại. Sửa `.env` theo 4 dòng mới. Mô hình 14B chính
   xác hơn nhưng chậm hơn khoảng 2 lần, và cửa sổ chỉ 16k nên chạy extract với `ARGS="--max-steps 10"`. So sánh 7B
   với 14B cũng là một lần thử tốt cho bước 8.
2. **Dự phòng qua API.** Nếu Colab không có GPU nhiều ngày liền, dùng khối B (Gemini) hoặc C (Groq) trong
   `.env.example`. Groq cũng phục vụ mô hình open-weight như `llama-3.3-70b-versatile`, nhưng gói miễn phí giới hạn
   token mỗi phút thấp. Khi dùng dự phòng, ghi rõ tên mô hình trong README.

**Ghi lại:** tên mô hình (ví dụ `Qwen2.5 7B Instruct, Ollama, Colab T4`). Bảng Kết quả cần nó.

**Đẩy:** không đẩy gì. `.env` không bao giờ lên GitHub.

---

## Bước 6. Agent trích rule cho 5 chương trình

**Ở đâu:** terminal Codespace, tab Colab vẫn mở. Chạy từng chương trình một, để một lỗi chỉ làm hỏng một chương
trình. Trên T4, mỗi chương trình mất vài phút.

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

Số `tool calls` phải lớn hơn 0. Nếu bằng 0, mô hình đã trả lời chỉ từ dàn ý mà không đọc code, nên kết quả không
dùng được. Agent tự nhắc mô hình đọc code tối đa 2 lần; nếu vẫn 0, chạy lại chương trình đó hoặc xem 5.9.

**Nếu lỗi:**

- Một chương trình in `FAILED` thì các chương trình khác vẫn được lưu. Cuối lệnh có dòng gợi ý chạy lại đúng
  chương trình hỏng.
- `WARNING: a request used ... context tokens`: chương trình dài làm hội thoại chạm giới hạn cửa sổ, kết quả
  chương trình đó không đáng tin. Chạy lại với ít bước hơn:
  `make extract PROGS=COTRN02C ARGS="--max-steps 10"`.
- `Connection error`, `530` hoặc `1033`: Colab đã ngắt. Làm theo 5.8, rồi chạy lại chương trình hỏng.
- `did not return valid JSON`: mô hình 7B trả sai định dạng. Chạy lại một lần. Nếu vẫn lỗi, xem 5.9.
- Chỉ khi dùng API dự phòng: `429` hoặc `rate limit` thì thêm `LLM_PAUSE=6` vào `.env`; `413` hoặc
  `Request too large` thì gói miễn phí không đủ, quay lại Colab.

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

`eval-qa` hỏi agent 20 câu. Trên T4 mất khoảng 30-60 phút, giữ tab Colab mở. Nếu Colab ngắt giữa chừng, các
câu sau bị chấm sai: làm theo 5.8 rồi chạy lại `make eval-qa`.

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
   - Đổi sang mô hình open-weight lớn hơn: Qwen2.5 14B (xem 5.9).
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
| 3 | Qwen2.5 7B -> 14B | ... | ... |
```

**Đúng khi:** `make test` vẫn `31 passed`, và bảng có ít nhất 2 dòng với số thật.

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
| `error: No LLM endpoint configured` | Chưa có `.env` hay secret | Bước 5.5 |
| `Connection error`, `530`, `1033`, `Connection refused` | Colab đã ngắt, URL đường hầm không còn | Bước 5.8 |
| `Name or service not known` | `LLM_BASE_URL` sai chính tả hoặc là URL của phiên Colab cũ | Chép lại 4 dòng từ ô 7 của notebook (5.5) |
| `Error code: 524` | Cloudflare cắt yêu cầu im lặng quá 100 giây | Bản mới tự bật streaming cho URL trycloudflare; cập nhật repo rồi chạy lại |
| `0 tool calls` trong kết quả extract | Mô hình không đọc code | Chạy lại; vẫn vậy thì dùng 14B (5.9) |
| `404` hoặc `model not found` | `LLM_MODEL` khác tên mô hình đã tải | Chạy 5.6, chép đúng tên trong JSON vào `.env` |
| `WARNING: a request used ... context tokens` | Hội thoại chạm giới hạn cửa sổ | `ARGS="--max-steps 10"`, hoặc 7B với `CONTEXT = 32768` |
| `did not return valid JSON` | Mô hình trả sai định dạng | Chạy lại; vẫn lỗi thì xem 5.9 |
| Lệnh chạy rất lâu, không in gì | Mô hình đang chạy trên T4, hoặc Colab treo | Chờ 5 phút; xem ô 8 của notebook |
| Colab: `Cannot connect to GPU backend` | Hết GPU miễn phí | Chờ vài giờ, làm bước 4 trong lúc chờ |
| Chỉ khi dùng API dự phòng: `401` | Khóa sai | Sửa `LLM_API_KEY`, không để dấu cách hay dấu nháy |
| Chỉ khi dùng API dự phòng: `429`, `413` | Vượt hạn mức gói miễn phí | `LLM_PAUSE=6` trong `.env`; `413` thì quay lại Colab |
| `data/carddemo/app not found` | Chưa tải dữ liệu | `make data` |
| CI đỏ ở bước lint | Code chưa format | `ruff format . && make lint`, rồi đẩy lại |

## Phụ lục B. Repo so với các ràng buộc bạn đã nêu

| Ràng buộc | Repo |
| --- | --- |
| Không cài gì trên máy, làm trong Codespaces | Có. Mọi bước chạy trong Codespace; có `.devcontainer` |
| Đủ chạy trên Codespaces 2 nhân | Có. Chỉ dùng CPU, không Docker; CardDemo 22.904 dòng, dựng đồ thị dưới 1 giây |
| GPU chỉ dùng trên Colab | Có. Repo không cần GPU; mô hình chạy trên Colab T4 (bước 5) |
| 0 đồng | Có. Colab T4 miễn phí cho mô hình; CI dùng GitHub Actions miễn phí |
| Ưu tiên LLM open-weight | Có. Mặc định là Qwen2.5 7B Instruct (Apache-2.0) qua Ollama trên Colab; API chỉ là dự phòng |
| Chỉ điền số tự đo | Có. Bảng Kết quả để `[X]` cho tới khi bạn chạy; test dùng LLM giả lập không sinh số |
| Không đẩy khóa, `.env`, dữ liệu lên GitHub | Có. `.env`, `data/`, `out/` nằm trong `.gitignore`; bước 1 và 12 kiểm tra lại |
| Zip chỉ chứa code, không có lịch sử git | Có |
| Dùng lại khóa Groq của repo kia | Có, làm dự phòng. Khối C trong `.env.example`; repo cũng nhận `GROQ_API_KEY` |
