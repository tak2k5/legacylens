# Hướng dẫn làm LegacyLens: phần còn lại

File riêng cho Kiet. Xóa trước khi để repo Public (bước 12).

## Bạn đang ở đây

| Bước | Việc | Trạng thái |
| --- | --- | --- |
| 0-3 | Repo, cài đặt, dữ liệu, số liệu tĩnh | Xong |
| 4, 4.9 | Duyệt và chốt nhãn tay | Xong |
| 5 | Cập nhật repo, chạy mô hình open-weight trên Colab T4 | **Làm tiếp từ 5.0** (30 phút) |
| 6 | Agent trích rule cho 5 chương trình | 30-90 phút |
| 7 | Chấm điểm | 30-60 phút |
| 8 | Cải thiện 1-2 lần | nửa ngày |
| 9 | Sinh tài liệu thiết kế vi/ja | 10 phút |
| 10 | Bài kiểm tra bấm giờ với người thật | 1-2 giờ |
| 11 | Kiểm tra lại lỗi CBACT04C | 15 phút |
| 12 | Hoàn tất: README, video, Public, CV | 1-2 giờ |

Làm đúng thứ tự từ trên xuống dưới, bắt đầu ở bước 5.0. Các mục ghi **"Chỉ khi cần"** thì bỏ qua nếu không gặp tình
huống đó. Các bước đã làm (0-4.9 và phần cập nhật repo) nằm ở Phụ lục C để tra lại.

Mỗi bước có:

- **Ở đâu:** làm ở chỗ nào.
- **Làm:** khối lệnh. Dán cả khối vào terminal.
- **Đúng khi:** kết quả phải thấy. Chưa thấy thì đừng sang bước sau. Xem mục "Nếu lỗi" của bước đó hoặc Phụ lục A.
- **Ghi lại:** số cần chép vào README.
- **Đẩy:** lệnh lưu lên GitHub. Mỗi bước xong đẩy một lần, để mất Codespace cũng không mất việc.

---

## Bước 5. Chạy mô hình open-weight trên Colab T4

Dùng mô hình open-weight **Qwen2.5 7B Instruct** (giấy phép Apache-2.0), chạy bằng **Ollama** trên GPU T4 miễn phí
của Colab. Codespace gọi sang Colab qua một đường hầm Cloudflare. Bạn không cần khóa API và không phụ thuộc gói
miễn phí của hãng nào.

```text
Codespace (make ask / extract)  --internet-->  đường hầm Cloudflare  -->  Colab T4: Ollama + Qwen2.5 7B
```

Cần hai tab trình duyệt mở cùng lúc: tab **Colab** (máy chủ mô hình) và tab **Codespace** (chạy LegacyLens).

Mất khoảng 30 phút cho lần đầu, kể cả 5.0. Những lần sau chỉ cần làm 5.8 (khoảng 8 phút).

### 5.0. Cập nhật repo lên bản mới nhất

Bản zip mới có thêm lệnh `make readme` (tự chép số vào README) và cách thử prompt không cần sửa code, dùng ở bước 7
và 8. Nhãn bạn đã duyệt được giữ nguyên.

**Làm:** tải `legacylens.zip` mới nhất về máy, kéo thả vào thư mục gốc của repo trong Codespace (ngang hàng
`Makefile`). Rồi dán:

```bash
cd /workspaces/legacylens
git add -A && git commit -qm "Lưu trước khi cập nhật" ; git push
rm -rf /tmp/gold_cua_toi && cp -a gold /tmp/gold_cua_toi
cp README.md /tmp/README_cua_toi.md
rm -rf /tmp/ll && unzip -q legacylens.zip -d /tmp/ll && rm legacylens.zip
git ls-files -z | xargs -0 rm -f
cp -a /tmp/ll/legacylens/. .
cp -a /tmp/gold_cua_toi/. gold/
cp /tmp/README_cua_toi.md README.md
sed -i 's/# 3[0-9] test offline/# 34 test offline/' README.md
rm -rf /tmp/ll
make install > /dev/null && make test && make check-gold | tail -1
make help | grep -E "readme|gold-ok"
git add -A && git commit -qm "Cập nhật bản mới: make readme, thử prompt" && git push
```

README của bạn (đã sửa số nhãn ở 4.9) cũng được giữ nguyên.

**Đúng khi:**

- `make test` in `34 passed`.
- `check-gold` in `N/N gold rules pass` với N là số nhãn của bạn.
- Có hai dòng `readme` và `gold-ok`.
- `git push` kết thúc bằng `main -> main`.

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
trong ngày. Chờ vài giờ rồi thử lại. Trong lúc chờ, bạn có thể làm trước bước 11 (không cần Colab).

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

### 5.8. Chỉ khi cần: Colab đã ngắt, hoặc bạn quay lại sau khi nghỉ

Colab miễn phí tự ngắt khi để yên khoảng 90 phút, và mỗi phiên dài tối đa khoảng 12 giờ. Mỗi lần ngắt thì URL đổi.
Khi quay lại:

1. Colab: **Runtime > Run all** (5.4). Lần này nhanh hơn nếu runtime chưa bị xóa.
2. Chép 4 dòng `LLM_` mới vào `.env` (5.5).
3. Chạy lại 5.6 để kiểm tra.

Trong lúc chạy `make extract` hay `make eval-qa`, thỉnh thoảng bấm vào tab Colab để nó không bị coi là để yên.

### 5.9. Chỉ khi cần: Qwen 7B không đủ tốt

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

**Ở đâu:** terminal Codespace. Tab Colab phải đang chạy (bước 5). Trên T4, mỗi chương trình mất vài phút.

### 6.1. Chạy chương trình đầu tiên

```bash
cd /workspaces/legacylens
make extract PROGS=COSGN00C
```

**Đúng khi:** in một dòng dạng
`COSGN00C: 8 rules, 8 pass the citation check, 11 tool calls (0 repeats blocked), 41230+2210 tokens, 38.5s`,
với `tool calls` **lớn hơn 0**. Bằng 0 nghĩa là mô hình không đọc code: dán lại khối trên một lần. Vẫn 0 thì làm 5.9.

### 6.2. Chạy 4 chương trình còn lại

```bash
make extract PROGS="COBIL00C CBTRN02C CBACT04C COTRN02C"
```

**Đúng khi:** 4 dòng giống 6.1, không dòng nào có `FAILED`.

### 6.3. Chỉ khi cần: có chương trình bị lỗi

Cuối lệnh có dòng `failed: ... make extract PROGS="..."`. Xử lý theo lỗi in ra, rồi dán đúng lệnh đó:

- `Connection error`, `530`, `1033`, `524`: Colab đã ngắt. Làm 5.8 rồi chạy lại.
- `did not return valid JSON`: chạy lại một lần. Vẫn lỗi thì làm 5.9.
- `WARNING: a request used ... context tokens`: chạy lại với ít bước hơn, ví dụ
  `make extract PROGS=COTRN02C ARGS="--max-steps 10"`.

### 6.4. Kiểm tra cả 5 chương trình

```bash
python3 - <<'PY'
import json
rows = {}
for line in open("reports/runs.jsonl"):
    r = json.loads(line); rows[r["program"]] = r
for p in ["COSGN00C", "COBIL00C", "CBTRN02C", "CBACT04C", "COTRN02C"]:
    r = rows.get(p)
    print(f"{p}: " + ("CHƯA CHẠY" if not r else f"{r['rules']} rules, {r['citations_ok']} trích đúng, {r['tool_calls']} tool calls"
          + ("  <- chạy lại (0 tool calls)" if r["tool_calls"] == 0 else "")))
PY
```

**Đúng khi:** đủ 5 dòng, không dòng nào có `CHƯA CHẠY` hay `chạy lại`.

**Đẩy:** chưa đẩy. Số liệu đẩy ở bước 7.

---

## Bước 7. Chấm điểm và ghi số vào README

**Ở đâu:** terminal Codespace. Tab Colab vẫn mở (7.2 cần mô hình).

### 7.1. Chấm phần trích rule (vài giây, không cần mô hình)

```bash
make eval > /dev/null && cat reports/eval.md
```

**Đúng khi:** in một bảng có các dòng `Precision`, `Recall`, `F1`.

### 7.2. Chấm phần hỏi đáp onboarding (30-60 phút)

```bash
make eval-qa > /dev/null && cat reports/eval_qa.md | head -12
```

Trong lúc chờ, thỉnh thoảng bấm vào tab Colab. Nếu Colab ngắt giữa chừng, làm 5.8 rồi dán lại khối này.

**Đúng khi:** in bảng có dòng `Correct (keywords + citation)`.

### 7.3. Ghi số vào README

```bash
make readme
make readme NOTE="Bản đầu: Qwen2.5 7B, prompt gốc"
sed -n '/Trích business rule/,/## Cách chấm/p' README.md
```

Lệnh đầu chép số vào bảng Kết quả. Lệnh thứ hai thêm dòng 1 vào bảng "Các lần thử". Không cần sửa README bằng tay.

**Đúng khi:** bảng không còn `[X]` ở các dòng Precision, Trích dẫn, Token, Agent trả lời đúng. Còn `[X]` ở dòng
"Người trả lời 20 câu" là đúng, dòng đó điền ở bước 10. Số thấp cũng giữ nguyên: một F1 thấp có giải thích vẫn tốt
hơn một con số đẹp không chứng minh được.

### 7.4. Lưu và đẩy

```bash
cp reports/eval.md reports/eval_lan1.md && cp reports/eval_qa.md reports/eval_qa_lan1.md
git add reports README.md && git commit -qm "Kết quả lần 1: trích rule và hỏi đáp onboarding" && git push
```

---

## Bước 8. Cải thiện 1-2 lần

Đây là phần để kể khi phỏng vấn: thấy lỗi gì, đổi gì, số thay đổi ra sao. Bạn làm 2 lần thử: lần 2 đổi prompt, lần 3
đổi sang mô hình lớn hơn. Mỗi lần đều ghi vào bảng "Các lần thử", kể cả khi số giảm.

### 8.1. Xem agent sai ở đâu

```bash
python3 - <<'PY'
import json
ev = json.load(open("reports/eval.json"))
gold = {json.loads(l)["id"]: json.loads(l) for l in open("gold/rules.jsonl")}
print("Nhãn tay agent bỏ sót:")
for i in ev.get("missed", []):
    g = gold.get(i, {})
    print(f"  {i} [{g.get('kind')}] {g.get('summary')}")
print(f"\nRule agent thêm mà nhãn tay không có: {len(ev.get('extra', []))}")
PY
```

Đọc danh sách bỏ sót và tìm một kiểu lặp lại. Với mô hình nhỏ, kiểu hay gặp nhất là gộp nhiều nhánh `WHEN` của một
`EVALUATE` thành một rule, nên bỏ sót các nhãn validation. Ghi kiểu lỗi bạn thấy vào file nháp.

### 8.2. Lần 2: thêm một luật vào prompt (30-60 phút)

```bash
export LLM_EXTRA_RULES="Each IF or WHEN branch that sets its own error message, code or target program is a separate rule."
make extract PROGS="COSGN00C COBIL00C CBTRN02C CBACT04C COTRN02C"
make eval > /dev/null && grep -E "Precision|Recall|F1" reports/eval.md
make readme NOTE="Lần 2: mỗi nhánh IF/WHEN có thông báo riêng là một rule"
cp reports/eval.md reports/eval_lan2.md
unset LLM_EXTRA_RULES
```

`LLM_EXTRA_RULES` thêm một câu vào cuối phần luật của prompt (xem `extract_rules` trong `src/legacylens/agent.py`),
nên không phải sửa code. Muốn thử câu khác, đổi nội dung trong dấu nháy.

**Đúng khi:** in 3 dòng Precision, Recall, F1 mới, và `updated: Lần thử 2`.

### 8.3. Lần 3: mô hình open-weight lớn hơn, Qwen2.5 14B (khoảng 1 giờ)

1. Tab Colab: trong ô 1 của notebook, thêm `#` vào đầu hai dòng `MODEL = "qwen2.5:7b-instruct"` và `CONTEXT = 32768`,
   bỏ `#` ở hai dòng `qwen2.5:14b-instruct` và `CONTEXT = 16384`. Chọn **Runtime > Run all**.
2. Ô 7 in 4 dòng `LLM_` mới. Trong Codespace, `code .env`, thay 4 dòng cũ bằng 4 dòng mới, Ctrl+S.
3. Dán:

```bash
make extract PROGS="COSGN00C COBIL00C CBTRN02C CBACT04C COTRN02C" ARGS="--max-steps 10"
make eval > /dev/null && grep -E "Precision|Recall|F1" reports/eval.md
make readme NOTE="Lần 3: Qwen2.5 14B, tối đa 10 bước"
cp reports/eval.md reports/eval_lan3.md
```

Nếu muốn dùng prompt của lần 2 cho lần này, dán dòng `export LLM_EXTRA_RULES=...` của 8.2 trước khối trên, và ghi
rõ trong NOTE.

**Đúng khi:** `updated: Lần thử 3`.

### 8.4. Chọn kết quả cho bảng chính

```bash
sed -n '/### Các lần thử/,/## Cách chấm/p' README.md
```

- Nếu **lần 3** có F1 cao nhất và bạn muốn bảng chính dùng nó: dán `make readme`. Số hỏi đáp onboarding vẫn là của
  lần 1 và ghi rõ tên mô hình của lần đó, nên không lẫn.
- Nếu không: không làm gì, bảng chính giữ số lần 1.

### 8.5. Lưu và đẩy

```bash
git add -A
git status --short | grep -E '(^|/)(\.env|data/)' && echo "DỪNG: có file không được đẩy" || echo "sạch"
git commit -qm "Cải thiện: thử prompt và mô hình 14B" && git push
```

**Đúng khi:** dòng thứ hai in `sạch`, `git push` kết thúc bằng `main -> main`.

**Ghi lại:** vào file nháp, mỗi lần thử 2 câu: đổi gì, số thay đổi ra sao và vì sao bạn nghĩ vậy.

---

## Bước 9. Tài liệu thiết kế tiếng Việt và tiếng Nhật

Tài liệu dùng các rule agent trích ở lần chạy gần nhất (thư mục `out/rules`). Không cần mô hình.

```bash
make doc PROGS="COSGN00C COBIL00C CBTRN02C CBACT04C COTRN02C"
ls docs/generated
code docs/generated/CBACT04C.vi.md
```

Trong tab vừa mở, bấm Ctrl+Shift+V để xem bản hiển thị, có sơ đồ Mermaid.

**Đúng khi:** `ls` in 10 file, mỗi chương trình một `.vi.md` và một `.ja.md`. Bảng rule có cột trích dẫn.

**Đẩy:**

```bash
git add docs/generated && git commit -qm "Tài liệu thiết kế vi/ja cho 5 chương trình" && git push
```

---

## Bước 10. Bài kiểm tra bấm giờ với người thật

Bạn đã thuộc code sau bước 4, nên bạn tự làm bài thì kết quả bị lệch. Nhờ 1-2 người biết lập trình nhưng chưa đọc
CardDemo. Bạn điều khiển Codespace và chia sẻ màn hình (Google Meet, Zalo, ...); người làm bài đọc và nói câu trả lời.

### 10.1. Mở giao diện

```bash
make ui
```

Codespaces hiện thông báo cổng 8501, bấm **Open in Browser**. Để tab Colab chạy.

### 10.2. Phần A: chỉ đọc code (câu Q01-Q10 trong `onboarding/BAI_KIEM_TRA.md`)

Mở terminal thứ hai (dấu `+` ở khung terminal). Trước câu đầu tiên:

```bash
T0=$(date +%s)
```

Người làm bài dùng Explorer và Ctrl+Shift+F (tìm trong toàn bộ file) để trả lời Q01-Q10. Bạn ghi câu trả lời vào
phiếu. Xong câu cuối:

```bash
echo "Phần A: $(( ($(date +%s) - T0) / 60 )) phút"
```

### 10.3. Phần B: dùng LegacyLens (câu Q11-Q20)

```bash
T0=$(date +%s)
```

Người làm bài gõ câu hỏi vào tab giao diện (mục Ask), đọc câu trả lời và trích dẫn, rồi nói đáp án của họ. Xong:

```bash
echo "Phần B: $(( ($(date +%s) - T0) / 60 )) phút"
```

### 10.4. Chấm và ghi vào README

Chấm từng câu bằng đáp án trong `onboarding/questions.jsonl` (từ khóa phải có) và `GIAI_THICH_NHAN.md` trong thư mục dự án. Rồi dán,
thay các số bằng số của bạn: phút **mỗi câu** = tổng phút chia 10.

```bash
make readme READ_MIN=4.5 TOOL_MIN=1.5 READ_OK=6/10 TOOL_OK=9/10 PEOPLE="1 người, 10 câu mỗi cách"
git add README.md onboarding && git commit -qm "Kết quả bài kiểm tra onboarding bấm giờ" && git push
```

Có người thứ hai: cho họ làm ngược lại (Q01-Q10 bằng LegacyLens, Q11-Q20 đọc code), lấy trung bình của hai người và
ghi `PEOPLE="2 người, 10 câu mỗi cách"`. Mẫu nhỏ thì nói là mẫu nhỏ.

**Đúng khi:** `make readme` in `updated: Bài kiểm tra với người thật` và `0 [X] left in README`.

---

## Bước 11. Kiểm tra lại lỗi CBACT04C (không cần Colab)

README có mục "Một lỗi gặp khi gán nhãn". Lỗi đã được báo ở issue #64 của CardDemo. Bạn tự chạy để kể được.

```bash
sudo apt-get update -qq && sudo apt-get install -y -qq gnucobol > /dev/null
cobc -x -free scripts/repro_cbact04c.cbl -o /tmp/repro && /tmp/repro
code data/carddemo/app/cbl/CBACT04C.cbl scripts/repro_cbact04c.cbl
```

Trong tab `CBACT04C.cbl`, bấm Ctrl+G, gõ `188`, Enter. Đọc dòng 188-222, so với `repro_cbact04c.cbl`.

**Đúng khi:** chương trình in `balance updated ... for account 101` và không có dòng nào cho account 202. Bạn tự
giải thích được bằng lời: vòng `PERFORM UNTIL END-OF-FILE = 'Y'` kiểm tra trước mỗi lượt, nên mỗi lượt bắt đầu với
`END-OF-FILE = 'N'`, và nhánh `ELSE` ở dòng 219 không bao giờ chạy.

Khi kể, nói đúng: "Tôi gặp lỗi này khi duyệt nhãn, viết bản tái hiện bằng GnuCOBOL, rồi thấy nó đã được báo ở
issue #64." Đừng nói là bạn phát hiện đầu tiên.

**Đẩy:** không có gì mới.

---

## Bước 12. Hoàn tất

### 12.1. Kiểm tra lần cuối

```bash
cd /workspaces/legacylens
grep -c "\[X\]" README.md
make test lint check-gold 2>&1 | grep -E "passed|failed|All checks|gold rules"
```

**Đúng khi:** dòng đầu là `0`, sau đó có `34 passed`, `All checks passed!`, `N/N gold rules pass`.

### 12.2. Quay video demo 2 phút

Quay màn hình (Xbox Game Bar trên Windows: Win+Alt+R; macOS: Cmd+Shift+5) theo thứ tự:

1. Terminal: `make stats` (số chương trình, dòng code).
2. Mở `reports/graph.mmd` (đồ thị phụ thuộc).
3. `make ui`, hỏi một câu, mở một trích dẫn.
4. Mở `docs/generated/CBACT04C.ja.md` (tài liệu tiếng Nhật).
5. Mở `README.md`, kéo tới bảng Kết quả và bảng Các lần thử.

Tải lên YouTube, chế độ **Unlisted**, rồi dán (thay link):

```bash
make readme VIDEO=https://youtu.be/LINK_CUA_BAN
git add README.md && git commit -qm "Thêm video demo" && git push
```

### 12.3. Xóa file riêng, kiểm tra không lộ khóa

```bash
git rm -q HUONG_DAN.md
git commit -qm "Bỏ ghi chú riêng" && git push
git log -p | grep -nE "gsk_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{30,}|API_KEY=[A-Za-z0-9_-]{16,}" && echo "DỪNG: có khóa trong lịch sử" || echo "sạch"
git ls-files | grep -E "^\.env$|^data/" && echo "DỪNG: có file không được đẩy" || echo "sạch"
```

**Đúng khi:** hai dòng cuối đều in `sạch`. Bản hướng dẫn này vẫn còn trong thư mục dự án, bạn không mất nó.

### 12.4. Để repo Public

Trên github.com/tak2k5/legacylens: **Settings > General**, kéo xuống **Danger Zone > Change visibility > Public**.
Rồi mở tab **Actions**: lần chạy `ci` mới nhất phải có dấu xanh.

### 12.5. Thêm vào CV

Mở tài liệu "Dự án giải quyết vấn đề thật của FPT Software", lấy mẫu câu và thay bằng số trong README:

```bash
sed -n '/Trích business rule/,/## Cách chấm/p' README.md
```

Nói đúng về nhãn: "N nhãn do AI soạn nháp, tôi đối chiếu từng nhãn với mã nguồn, sửa và thêm 3 nhãn". Nếu được hỏi,
nói rõ bản nháp đầu có trợ giúp của AI. Mang theo file nháp ghi các lần thử ở bước 8 để ôn trước phỏng vấn.

**Đúng khi:** repo Public, CI xanh, README không còn `[X]`, CV có link repo và link video.

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
| Colab: `Cannot connect to GPU backend` | Hết GPU miễn phí | Chờ vài giờ; trong lúc chờ làm trước bước 11 |
| Chỉ khi dùng API dự phòng: `401` | Khóa sai | Sửa `LLM_API_KEY`, không để dấu cách hay dấu nháy |
| Chỉ khi dùng API dự phòng: `429`, `413` | Vượt hạn mức gói miễn phí | `LLM_PAUSE=6` trong `.env`; `413` thì quay lại Colab |
| `configured for Git LFS but 'git-lfs' was not found` rồi `failed to push` | Codespace có hook Git LFS thừa | `grep -l "git-lfs\|git lfs" .git/hooks/* \| xargs -r rm -v` rồi `git push` (repo không dùng LFS) |
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

## Phụ lục C. Các bước đã làm (để tra lại)

Phần dưới là các bước 0-4 và mục cập nhật repo bạn đã làm. Không cần làm lại.

### Đã có repo từ bản zip cũ? Cập nhật lên bản mới, giữ nhãn đã duyệt

Làm mục này **thay cho bước 0 và bước 1** nếu repo `legacylens` đã có trên GitHub. Mục này thay toàn bộ code bằng bản
zip mới nhất nhưng giữ lại 4 thứ: nhãn bạn đã duyệt (`gold/rules.jsonl`), lịch sử git, file `.env` và dữ liệu
CardDemo đã tải. Kết quả `make extract` cũ bị xóa, vì đó là số của bản lỗi và không được dùng.

Mất khoảng 15 phút.

#### U1. Lưu hết việc đang làm

**Ở đâu:** terminal Codespace của repo `legacylens`.

**Làm:**

```bash
cd /workspaces/legacylens
git add -A && git commit -qm "Lưu trước khi cập nhật bản mới" ; git push
git status --short
```

**Đúng khi:** `git status --short` không in gì. Nếu dòng commit báo `nothing to commit` thì cũng không sao.

#### U2. Tải zip mới vào Codespace

**Làm:** tải `legacylens.zip` mới nhất về máy, kéo thả vào khung Explorer, thả ở **thư mục gốc** (ngang hàng với
`Makefile`).

**Đúng khi:** `ls legacylens.zip` in ra `legacylens.zip`.

#### U3. Thay code, giữ nhãn

**Làm:** dán cả khối:

```bash
cd /workspaces/legacylens
rm -rf /tmp/gold_cua_toi && cp -a gold /tmp/gold_cua_toi
rm -rf /tmp/ll && unzip -q legacylens.zip -d /tmp/ll && rm legacylens.zip
git ls-files -z | xargs -0 rm -f
cp -a /tmp/ll/legacylens/. .
cp -a /tmp/gold_cua_toi/. gold/
sed -i "s/<ten-github>/$GITHUB_USER/" README.md
rm -rf out reports/runs.jsonl /tmp/ll
git add -A && git status --short
```

Dòng `git ls-files ... rm` xóa các file git đang theo dõi, để file đã bỏ ở bản mới (ví dụ `LAM_TIEP.md`) không còn
sót lại. Nó không đụng tới `.env`, `data/` và file nháp chưa commit.

**Đúng khi:**

- Danh sách cuối **không** có dòng nào chứa `gold/rules.jsonl` (nhãn của bạn giữ nguyên).
- Có các dòng `M` hoặc `A` cho `src/legacylens/agent.py`, `notebooks/colab_llm.ipynb`, `HUONG_DAN.md`, ...
- Không có dòng nào chứa `.env` hay `data/`.

**Nếu lỗi:** thấy `gold/rules.jsonl` trong danh sách thì chạy `cp -a /tmp/gold_cua_toi/. gold/` rồi
`git status --short` lại.

#### U4. Kiểm tra bản mới

**Làm:**

```bash
make install
make test
make lint
make check-gold
```

**Đúng khi:** `make test` in `32 passed`, `make lint` sạch, dòng cuối `check-gold` là `N/N gold rules pass` với N
là số nhãn sau khi bạn duyệt.

#### U5. Đẩy lên GitHub

```bash
git commit -qm "Cập nhật bản mới: streaming qua Colab, nhắc mô hình đọc code" && git push
```

**Đúng khi:** tab Actions trên GitHub có lần chạy `ci` mới, dấu xanh.

#### U6. Làm tiếp

Kiểm tra repo đã có lệnh duyệt nhãn mới:

```bash
make help | grep gold
```

Phải thấy các dòng `gold-ok`, `gold-set`, `gold-lines`, `gold-fix`, `gold-add`. Không thấy thì zip là bản cũ: tải lại
rồi làm lại U3.

Bước 2 và 3 đã xong nên bỏ qua. Sau đó:

- **Chưa đánh dấu nhãn bằng `make gold-ok`** (chưa có `gold/REVIEWED.txt`, hoặc file chưa đủ số nhãn): làm **bước 4**
  từ 4.1, rồi sang bước 5.
- **Đã duyệt đủ** (4.8 in hai số bằng nhau): sang thẳng **5.1**.

Ở bước 5, làm lại từ 5.1 kể cả khi đã có `.env`, vì notebook Colab có bản mới và URL đường hầm cũ đã hết hạn. Đến
5.5, thay 4 dòng `LLM_` trong `.env` bằng 4 dòng mới.

---

### Bước 0. Chuẩn bị

**Ở đâu:** trình duyệt.

**Làm:**

1. Đăng nhập GitHub (tài khoản dùng cho 2 repo kia).
2. Tải `legacylens.zip` về máy.
3. Đăng nhập tài khoản Google, để dùng Colab ở bước 5.

**Đúng khi:** có file zip trên máy, đã đăng nhập GitHub và Google.

---

### Bước 1. Tạo repo và đưa code lên

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

### Bước 2. Cài thư viện, tải CardDemo, chạy test

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
- `make test` in `32 passed`.
- `make lint` in `All checks passed!` và `files already formatted`.

**Nếu lỗi:** `make: python: No such file` thì chạy `make install PY=python3` và thêm `PY=python3` vào mọi lệnh
make. Repo chỉ dùng CPU, chạy tốt trên máy 2 nhân 8 GB.

Ghi chú: repo có `.devcontainer`. Từ lần tạo Codespace sau, bước cài và `make data` tự chạy. Lần này bạn đã tạo
Codespace trước khi có file đó nên phải chạy tay, không cần Rebuild.

**Đẩy:** không có gì mới. Sau khi đẩy ở bước 1, mở tab Actions trên GitHub: lần chạy `ci` phải có dấu xanh.

---

### Bước 3. Số liệu phân tích tĩnh

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

### Bước 4. Duyệt 49 nhãn tay (phần quan trọng nhất)

Nhãn trong `gold/rules.jsonl` do trợ lý soạn. Chúng đã qua kiểm tra trích dẫn tự động, nhưng phải do bạn đọc và
xác nhận thì mới được gọi là nhãn tay. Đây cũng là cách học đủ COBOL để trả lời phỏng vấn. Mở song song tài liệu
"COBOL tối thiểu cho phỏng vấn LegacyLens".

Làm đúng thứ tự từ 4.1 đến 4.8, từ trên xuống dưới. Bạn **không sửa JSON bằng tay**: mỗi việc là một lệnh dán sẵn,
và lệnh chỉ lưu khi nhãn vẫn qua kiểm tra trích dẫn, nên không làm hỏng file được. Nhãn đã duyệt được ghi vào
`gold/REVIEWED.txt`, làm bằng chứng bạn đã đọc từng nhãn.

**Ở đâu:** Codespace, terminal và trình soạn thảo.

#### 4.1. Kiểm tra trước khi bắt đầu

```bash
cd /workspaces/legacylens
make check-gold | tail -1
echo "Đã duyệt: $(cat gold/REVIEWED.txt 2>/dev/null | wc -l) nhãn"
```

**Đúng khi:** dòng đầu là `49/49 gold rules pass the citation check`. Dòng sau cho biết đã duyệt bao nhiêu (lần đầu là 0).

#### 4.2. Học cách duyệt một nhãn (đọc một lần, không chạy lệnh)

Mỗi nhãn trong file duyệt trông như sau:

```text
=== COSGN00C-G1 [routing] MAIN-PARA
Pressing PF3 on the sign-on screen ends the session with a thank-you message.
  condition: EIBAID = DFHPF3
  outcome:   CCDA-MSG-THANK-YOU sent as plain text
  fields:    EIBAID, CCDA-MSG-THANK-YOU
   88:                    WHEN DFHPF3
   89:                        MOVE CCDA-MSG-THANK-YOU        TO WS-MESSAGE
   90:                        PERFORM SEND-PLAIN-TEXT
  [not reviewed yet]  correct:  make gold-ok ID=COSGN00C-G1
             fix text: make gold-set ID=COSGN00C-G1 F=summary V="..."
             fix lines: make gold-lines ID=COSGN00C-G1 L=START-END
```

Với mỗi nhãn, làm 3 việc theo thứ tự:

1. **Đọc** các dòng code có số ở đầu, rồi so với 3 dòng chữ phía trên:
   - Câu đầu tiên (summary) có nói đúng điều code làm không? Đọc từng `IF`, `WHEN`, `MOVE`, `PERFORM`.
   - `condition` và `outcome` có đúng mã lỗi, thông báo, giá trị trong code không?
   - Các dòng trích có đủ dòng điều kiện lẫn dòng kết quả không?
   
   Cần xem code rộng hơn: bấm Ctrl+P, gõ `COSGN00C.cbl:85`, Enter để nhảy tới dòng 85.
2. **Sửa** nếu sai (bỏ qua nếu đúng): chép lệnh ở hàng phù hợp, thay phần in hoa, dán vào terminal.

   | Bạn thấy | Lệnh |
   | --- | --- |
   | Câu summary sai hoặc khó hiểu | `make gold-set ID=COSGN00C-G1 F=summary V="CÂU MỚI"` |
   | condition sai | `make gold-set ID=COSGN00C-G1 F=condition V="ĐIỀU KIỆN MỚI"` |
   | outcome sai | `make gold-set ID=COSGN00C-G1 F=outcome V="KẾT QUẢ MỚI"` |
   | Thiếu hoặc thừa tên biến | `make gold-set ID=COSGN00C-G1 F=fields V="EIBAID, CCDA-MSG-THANK-YOU"` |
   | Trích sai dòng | `make gold-lines ID=COSGN00C-G1 L=88-90` |
   | Sai cả dòng trích lẫn tên biến | `make gold-fix ID=COSGN00C-G1 L=88-91 FL="EIBAID, CCDA-MSG-THANK-YOU"` |
   | Không phải quy tắc nghiệp vụ | `make gold-del ID=COSGN00C-G1` (xong, sang nhãn kế tiếp) |

   Trong `V="..."` được dùng dấu nháy đơn (`'Please enter User ID ...'`), **không** dùng dấu nháy kép `"` hay `$`.
   Viết bằng tiếng Anh cho khớp các nhãn khác. Lệnh in `not saved` thì file không đổi: sửa giá trị rồi dán lại.
3. **Xác nhận**: dán lệnh `correct:` của nhãn đó, ví dụ `make gold-ok ID=COSGN00C-G1`.

#### 4.3. COSGN00C (đăng nhập, 9 nhãn, khoảng 20 phút)

**a. Mở file duyệt:**

```bash
make review PROG=COSGN00C && code out/review/COSGN00C.txt
```

**b. Duyệt từng nhãn** trong file, từ `COSGN00C-G1` đến `COSGN00C-G9`, theo 3 việc ở 4.2. Sau mỗi lần sửa, dán lại khối a để xem bản mới.

**c. Thêm nhãn bị thiếu** (bỏ qua nếu không thiếu). Sau khi đọc hết, nếu thấy một quy tắc chưa có nhãn nào, chép
khối dưới vào trình soạn thảo, thay phần in hoa, rồi dán cả khối vào terminal. Thêm nhãn thứ hai thì đổi `G10`
thành `G11`.

```bash
make gold-add ID=COSGN00C-G10 L=START-END K=validation P=TÊN-PARAGRAPH \
  S="CÂU MÔ TẢ" C="ĐIỀU KIỆN" O="KẾT QUẢ" FL="TÊN-BIẾN-1, TÊN-BIẾN-2"
make gold-ok ID=COSGN00C-G10
```

Loại (`kind`) hợp lệ: `validation`, `calculation`, `routing`, `data-access`, `error-handling`, `authorization`, `other`.

**d. Lưu:**

```bash
make review PROG=COSGN00C && tail -1 out/review/COSGN00C.txt
make check-gold | tail -1
git add gold && git commit -qm "Duyệt nhãn COSGN00C" && git push
```

**Đúng khi:** có dòng `9 rules, 9 reviewed` (số khác nếu bạn đã thêm hoặc xóa nhãn, nhưng hai số phải
bằng nhau), và dòng `N/N gold rules pass the citation check`.

#### 4.4. COBIL00C (thanh toán hóa đơn, 8 nhãn, khoảng 20 phút)

**a. Mở file duyệt:**

```bash
make review PROG=COBIL00C && code out/review/COBIL00C.txt
```

**b. Duyệt từng nhãn** trong file, từ `COBIL00C-G1` đến `COBIL00C-G8`, theo 3 việc ở 4.2. Sau mỗi lần sửa, dán lại khối a để xem bản mới.

**c. Thêm nhãn bị thiếu** (bỏ qua nếu không thiếu). Sau khi đọc hết, nếu thấy một quy tắc chưa có nhãn nào, chép
khối dưới vào trình soạn thảo, thay phần in hoa, rồi dán cả khối vào terminal. Thêm nhãn thứ hai thì đổi `G9`
thành `G10`.

```bash
make gold-add ID=COBIL00C-G9 L=START-END K=validation P=TÊN-PARAGRAPH \
  S="CÂU MÔ TẢ" C="ĐIỀU KIỆN" O="KẾT QUẢ" FL="TÊN-BIẾN-1, TÊN-BIẾN-2"
make gold-ok ID=COBIL00C-G9
```

Loại (`kind`) hợp lệ: `validation`, `calculation`, `routing`, `data-access`, `error-handling`, `authorization`, `other`.

**d. Lưu:**

```bash
make review PROG=COBIL00C && tail -1 out/review/COBIL00C.txt
make check-gold | tail -1
git add gold && git commit -qm "Duyệt nhãn COBIL00C" && git push
```

**Đúng khi:** có dòng `8 rules, 8 reviewed` (số khác nếu bạn đã thêm hoặc xóa nhãn, nhưng hai số phải
bằng nhau), và dòng `N/N gold rules pass the citation check`.

#### 4.5. CBTRN02C (ghi sổ giao dịch hằng ngày, 6 nhãn, khoảng 20 phút)

**a. Mở file duyệt:**

```bash
make review PROG=CBTRN02C && code out/review/CBTRN02C.txt
```

**b. Duyệt từng nhãn** trong file, từ `CBTRN02C-G1` đến `CBTRN02C-G6`, theo 3 việc ở 4.2. Sau mỗi lần sửa, dán lại khối a để xem bản mới.

**c. Thêm nhãn bị thiếu** (bỏ qua nếu không thiếu). Sau khi đọc hết, nếu thấy một quy tắc chưa có nhãn nào, chép
khối dưới vào trình soạn thảo, thay phần in hoa, rồi dán cả khối vào terminal. Thêm nhãn thứ hai thì đổi `G7`
thành `G8`.

```bash
make gold-add ID=CBTRN02C-G7 L=START-END K=validation P=TÊN-PARAGRAPH \
  S="CÂU MÔ TẢ" C="ĐIỀU KIỆN" O="KẾT QUẢ" FL="TÊN-BIẾN-1, TÊN-BIẾN-2"
make gold-ok ID=CBTRN02C-G7
```

Loại (`kind`) hợp lệ: `validation`, `calculation`, `routing`, `data-access`, `error-handling`, `authorization`, `other`.

**d. Lưu:**

```bash
make review PROG=CBTRN02C && tail -1 out/review/CBTRN02C.txt
make check-gold | tail -1
git add gold && git commit -qm "Duyệt nhãn CBTRN02C" && git push
```

**Đúng khi:** có dòng `6 rules, 6 reviewed` (số khác nếu bạn đã thêm hoặc xóa nhãn, nhưng hai số phải
bằng nhau), và dòng `N/N gold rules pass the citation check`.

#### 4.6. CBACT04C (tính lãi hằng tháng, 8 nhãn, khoảng 30 phút)

Chương trình này có lỗi ở dòng 219-220 (bước 11). Nhãn mô tả điều code **thực sự làm**, không phải điều code định làm.

**a. Mở file duyệt:**

```bash
make review PROG=CBACT04C && code out/review/CBACT04C.txt
```

**b. Duyệt từng nhãn** trong file, từ `CBACT04C-G1` đến `CBACT04C-G8`, theo 3 việc ở 4.2. Sau mỗi lần sửa, dán lại khối a để xem bản mới.

**c. Thêm nhãn bị thiếu** (bỏ qua nếu không thiếu). Sau khi đọc hết, nếu thấy một quy tắc chưa có nhãn nào, chép
khối dưới vào trình soạn thảo, thay phần in hoa, rồi dán cả khối vào terminal. Thêm nhãn thứ hai thì đổi `G9`
thành `G10`.

```bash
make gold-add ID=CBACT04C-G9 L=START-END K=validation P=TÊN-PARAGRAPH \
  S="CÂU MÔ TẢ" C="ĐIỀU KIỆN" O="KẾT QUẢ" FL="TÊN-BIẾN-1, TÊN-BIẾN-2"
make gold-ok ID=CBACT04C-G9
```

Loại (`kind`) hợp lệ: `validation`, `calculation`, `routing`, `data-access`, `error-handling`, `authorization`, `other`.

**d. Lưu:**

```bash
make review PROG=CBACT04C && tail -1 out/review/CBACT04C.txt
make check-gold | tail -1
git add gold && git commit -qm "Duyệt nhãn CBACT04C" && git push
```

**Đúng khi:** có dòng `8 rules, 8 reviewed` (số khác nếu bạn đã thêm hoặc xóa nhãn, nhưng hai số phải
bằng nhau), và dòng `N/N gold rules pass the citation check`.

#### 4.7. COTRN02C (thêm giao dịch, 18 nhãn, khoảng 45 phút)

18 nhãn, nhiều nhất. Nếu muốn nghỉ giữa chừng, chạy khối "lưu" ở cuối phần này trước khi nghỉ, rồi quay lại khối "mở".

**a. Mở file duyệt:**

```bash
make review PROG=COTRN02C && code out/review/COTRN02C.txt
```

**b. Duyệt từng nhãn** trong file, từ `COTRN02C-G1` đến `COTRN02C-G18`, theo 3 việc ở 4.2. Sau mỗi lần sửa, dán lại khối a để xem bản mới.

**c. Thêm nhãn bị thiếu** (bỏ qua nếu không thiếu). Sau khi đọc hết, nếu thấy một quy tắc chưa có nhãn nào, chép
khối dưới vào trình soạn thảo, thay phần in hoa, rồi dán cả khối vào terminal. Thêm nhãn thứ hai thì đổi `G19`
thành `G20`.

```bash
make gold-add ID=COTRN02C-G19 L=START-END K=validation P=TÊN-PARAGRAPH \
  S="CÂU MÔ TẢ" C="ĐIỀU KIỆN" O="KẾT QUẢ" FL="TÊN-BIẾN-1, TÊN-BIẾN-2"
make gold-ok ID=COTRN02C-G19
```

Loại (`kind`) hợp lệ: `validation`, `calculation`, `routing`, `data-access`, `error-handling`, `authorization`, `other`.

**d. Lưu:**

```bash
make review PROG=COTRN02C && tail -1 out/review/COTRN02C.txt
make check-gold | tail -1
git add gold && git commit -qm "Duyệt nhãn COTRN02C" && git push
```

**Đúng khi:** có dòng `18 rules, 18 reviewed` (số khác nếu bạn đã thêm hoặc xóa nhãn, nhưng hai số phải
bằng nhau), và dòng `N/N gold rules pass the citation check`.

#### 4.8. Kiểm tra đã duyệt hết

```bash
echo "Đã duyệt $(wc -l < gold/REVIEWED.txt) / $(wc -l < gold/rules.jsonl) nhãn"
make check-gold | tail -1
grep -n "49" README.md
```

**Đúng khi:** hai số ở dòng đầu bằng nhau, dòng sau là `N/N gold rules pass the citation check`.

**Ghi lại:** nếu N khác 49, sửa số 49 ở các dòng mà lệnh `grep` vừa in trong README thành N, rồi:

```bash
git add README.md && git commit -qm "Cập nhật số nhãn" && git push
```

Ghi vào một file nháp những nhãn bạn đã sửa và vì sao. Đó là chuyện để kể khi phỏng vấn.

---

### Bước 4.9. Chốt kết quả duyệt nhãn

**Ở đâu:** terminal Codespace.

**Làm:**

```bash
cd /workspaces/legacylens
git pull -q
echo "Đã duyệt $(sort -u gold/REVIEWED.txt | wc -l) / $(wc -l < gold/rules.jsonl) nhãn"
make check-gold | tail -1
for p in COSGN00C COBIL00C CBTRN02C CBACT04C COTRN02C; do make -s review PROG=$p > /dev/null; echo "$p: $(tail -1 out/review/$p.txt | cut -d. -f1)"; done
```

**Đúng khi:**

- Dòng đầu có hai số bằng nhau, ví dụ `Đã duyệt 50 / 50 nhãn`.
- Dòng sau là `50/50 gold rules pass the citation check` (hoặc N/N với số nhãn của bạn).
- 5 dòng cuối, mỗi chương trình có hai số bằng nhau, ví dụ `CBTRN02C: 7 rules, 7 reviewed`.

**Nếu lỗi:** chương trình nào có số "reviewed" nhỏ hơn số "rules" thì mở lại file duyệt của nó
(`make review PROG=...`, nhãn chưa duyệt ghi `[not reviewed yet]`), đọc rồi `make gold-ok` cho nhãn đó.

Rồi cập nhật số nhãn trong README cho đúng số thật:

```bash
N=$(wc -l < gold/rules.jsonl)
sed -i "s/| Nhãn tay | 49 rule/| Nhãn tay | $N rule/; s/(49 rule)/($N rule)/" README.md
sed -i "s/Mỗi nhãn đã qua \`make check-gold\` và được đọc/Nhãn do AI soạn nháp; mỗi nhãn đã qua \`make check-gold\` và được tôi đọc/" README.md
grep -n "rule)\|Nhãn tay |" README.md
```

**Đúng khi:** các dòng in ra có số nhãn của bạn (ví dụ `50 rule`), không còn `49`.

**Ghi lại:** viết vào một file nháp 3 nhãn bạn đã sửa hoặc thêm (COSGN00C-G5, CBACT04C-G8, CBTRN02C-G7) và vì sao.
Đây là chuyện để kể khi phỏng vấn.

**Đẩy:**

```bash
git add gold README.md && git commit -qm "Chốt nhãn tay: duyệt xong, cập nhật số nhãn" && git push
```

**Đúng khi:** `git push` kết thúc bằng dòng dạng `main -> main`.
