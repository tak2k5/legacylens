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

Làm đúng thứ tự từ trên xuống dưới, bắt đầu ở bước 5.0. Từ bước 6 trở đi, mọi việc trong terminal chỉ cần dán
cả khối, không phải sửa gì (quy tắc ở đầu bước 6). Các mục ghi **"Chỉ khi cần"** thì bỏ qua nếu không gặp tình
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

Bản zip mới nhất có: lệnh `make readme` tự chép số vào README; phần đọc JSON chịu được lỗi định dạng nhỏ của mô
hình 7B; chặn mô hình gọi hàng trăm tool một lượt, ghi nhầm tên chương trình hay đọc quá cửa sổ ngữ cảnh; và chế độ
`--mode chunks` dùng ở bước 8. Nhãn bạn đã duyệt, README đã sửa ở 4.9, `.env` và kết quả trong `out/` được giữ
nguyên. Đã làm 5.0 rồi vẫn làm lại được.

**Làm:**

1. Tải `legacylens.zip` mới nhất về máy, kéo thả vào thư mục gốc của repo trong Codespace (ngang hàng `Makefile`).
2. Kiểm tra zip đã nằm đúng chỗ:

```bash
cd /workspaces/legacylens && ls -la legacylens.zip
```

   Phải in một dòng có `legacylens.zip`. Nếu báo `No such file`, kéo thả lại rồi kiểm tra lại.
3. Dán cả khối. Khối tự dừng ngay ở lỗi đầu tiên (ví dụ thiếu zip) mà không xóa gì:

```bash
bash -e <<'EOF'
test -f legacylens.zip || { echo "DỪNG: chưa thấy legacylens.zip ở thư mục gốc. Kéo thả zip vào rồi dán lại khối này."; exit 1; }
unzip -tq legacylens.zip > /dev/null
git add -A; git commit -qm "Lưu trước khi cập nhật" || true
rm -rf /tmp/giu /tmp/ll && mkdir -p /tmp/giu && cp -a gold README.md /tmp/giu/
for d in reports docs; do if [ -d $d ]; then cp -a $d /tmp/giu/; fi; done
if [ -f onboarding/ket_qua_bam_gio.csv ]; then cp onboarding/ket_qua_bam_gio.csv /tmp/giu/; fi
unzip -q legacylens.zip -d /tmp/ll && test -f /tmp/ll/legacylens/Makefile
rm legacylens.zip
git rm -r -q --cached data 2>/dev/null || true
git ls-files -z | xargs -0 rm -f
cp -a /tmp/ll/legacylens/. .
cp -a /tmp/giu/gold/. gold/ && cp /tmp/giu/README.md README.md
for d in reports docs; do if [ -d /tmp/giu/$d ]; then cp -a /tmp/giu/$d/. $d/; fi; done
if [ -f /tmp/giu/ket_qua_bam_gio.csv ]; then cp /tmp/giu/ket_qua_bam_gio.csv onboarding/; fi
sed -i 's/# [0-9][0-9] test offline/# 43 test offline/' README.md
make install > /dev/null && make test | tail -1 && make check-gold | tail -1
make graph > /dev/null && ls reports/graph.mmd
make help | grep -E "readme|gold-ok"
git add -A && git commit -qm "Cập nhật bản mới: make readme, thử prompt" && git push
echo "XONG"
EOF
```

**Đúng khi:** in `43 passed`, `N/N gold rules pass` với N là số nhãn của bạn, `reports/graph.mmd`, hai dòng
`gold-ok` và `readme`, rồi `main -> main` và `XONG`. Kết quả chấm điểm (`reports/`), tài liệu sinh ra (`docs/`) và kết
quả bấm giờ (`onboarding/`) cũng được giữ nguyên. Nếu in `DỪNG` hoặc dừng giữa chừng mà không có `XONG`, chưa có gì bị đẩy lên GitHub: gửi
lại log trước khi làm tiếp.

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
2. Dán khối ở bước 6.2 để chép 4 dòng `LLM_` mới vào `.env`. Khối đó tự kiểm tra kết nối.

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

**Cách dán từ bước 6 trở đi (áp dụng cho mọi khối bên dưới):**

- Mỗi khối tự `cd /workspaces/legacylens`, nên dán ở terminal nào của Codespace cũng được.
- Dán **cả khối** một lần và không sửa gì trong khối. Không có chỗ nào phải thay số hay thay tên.
- Một số khối hỏi bạn ở dòng cuối, ví dụ số câu đúng, link video, hay một câu ghi chú. Câu hỏi chỉ hiện ra sau khi
  các lệnh khác đã chạy xong. Gõ câu trả lời rồi nhấn Enter.
- Khối chạy lâu được làm để **dán lại an toàn**: nếu Colab ngắt giữa chừng, làm 6.2 rồi dán lại đúng khối đó. Các
  chương trình đã xong sẽ được bỏ qua.
- Khối nào đẩy lên GitHub cũng kiểm tra trước: nếu sắp đẩy `.env` hoặc `data/` thì in `DỪNG` và không đẩy.
- Thấy `DỪNG` thì làm theo câu in ra ngay sau chữ `DỪNG`. Không hiểu thì gửi log cho mình, đừng làm tiếp.

### 6.1. Kiểm tra Codespace còn nối được với Colab

**Ở đâu:** terminal Codespace. Tab Colab đã chạy xong 5.4.

**Làm:**

```bash
cd /workspaces/legacylens
test -f .env || echo "THIẾU .env: làm 6.2"
set -a; . ./.env 2>/dev/null; set +a
echo "Mô hình trong .env: $LLM_MODEL"
curl -sf -m 20 "$LLM_BASE_URL/models" | grep -o '"id": *"[^"]*"' || echo "CHƯA NỐI ĐƯỢC: làm 6.2"
```

**Đúng khi:** dòng cuối dạng `"id":"qwen2.5:7b-instruct"`, cùng tên với dòng `Mô hình trong .env`. Nếu đúng thì
**bỏ qua 6.2**, sang 6.3. Nếu thấy `THIẾU .env` hoặc `CHƯA NỐI ĐƯỢC`, làm 6.2.

### 6.2. Chỉ khi cần: nối lại Colab

Dùng mục này mỗi khi Colab ngắt, kể cả ở các bước sau. Dấu hiệu là 6.1 in `CHƯA NỐI ĐƯỢC`, hoặc một lệnh in
`Connection error`, `530`, `1033`, `524`, `Name or service not known`, hoặc `DỪNG: chưa nối được Colab`.

**Làm:**

1. Tab Colab: menu **Runtime > Run all**. Chờ 5-8 phút tới khi ô 7 in 4 dòng bắt đầu bằng `LLM_`.
2. Bôi đen đúng 4 dòng `LLM_` đó, nhấn Ctrl+C.
3. Tab Codespace, dán khối này:

```bash
cd /workspaces/legacylens
cat > /tmp/noi_colab.sh <<'EOF'
echo ""
echo ">>> Dán 4 dòng LLM_ (Ctrl+V), nhấn Enter, rồi nhấn Ctrl+D:"
grep '^LLM_' > /tmp/env_moi
if ! grep -q '^LLM_BASE_URL=http' /tmp/env_moi; then
  echo "DỪNG: không thấy dòng LLM_BASE_URL. File .env cũ giữ nguyên. Chép lại 4 dòng ở Colab rồi dán lại khối này."
  exit 1
fi
mv /tmp/env_moi .env && echo "đã lưu .env"
set -a; . ./.env; set +a
echo "Đang chờ đường hầm mới (tối đa 1 phút)..."
for i in 1 2 3 4 5 6; do
  curl -sf -m 20 "$LLM_BASE_URL/models" | grep -o '"id": *"[^"]*"' && exit 0
  sleep 10
done
echo "CHƯA NỐI ĐƯỢC: xem tab Colab, ô 7 có in URL chưa và góc phải còn chữ T4 không. Rồi dán lại khối này."
EOF
bash /tmp/noi_colab.sh
```

4. Khi thấy `>>> Dán 4 dòng LLM_`, nhấn Ctrl+V, Enter, rồi Ctrl+D.

**Đúng khi:** in `đã lưu .env` rồi một dòng `"id":"qwen2.5:7b-instruct"` (hoặc tên mô hình bạn đang chạy).

**Nếu lỗi:** Colab báo `Cannot connect to GPU backend` nghĩa là hết GPU miễn phí. Chờ vài giờ. Trong lúc chờ, làm
trước bước 11 (không cần Colab).

### 6.3. Chạy agent cho cả 5 chương trình (30-90 phút)

**Ở đâu:** terminal Codespace. Thỉnh thoảng bấm vào tab Colab để nó không bị coi là để yên.

**Làm:**

```bash
cd /workspaces/legacylens
bash -e <<'EOF'
test -f .env || { echo "DỪNG: chưa có .env. Làm 6.2 rồi dán lại khối này."; exit 1; }
set -a; . ./.env; set +a
curl -sf -m 20 "$LLM_BASE_URL/models" > /dev/null || { echo "DỪNG: chưa nối được Colab. Làm 6.2 rồi dán lại khối này."; exit 1; }
if [ ! -d out/lan1 ]; then
  mkdir -p out/lan1/cu
  mv out/rules out/lan1/cu/ 2>/dev/null || true
  mv reports/runs.jsonl out/lan1/cu/ 2>/dev/null || true
fi
for p in COSGN00C COBIL00C CBTRN02C CBACT04C COTRN02C; do
  if [ -f out/lan1/$p.xong ]; then echo "$p: đã xong ở lần trước, bỏ qua"; continue; fi
  make extract PROGS=$p
  tail -1 reports/runs.jsonl | grep -q "\"program\": \"$p\"" || { echo "DỪNG: $p không ghi được kết quả. Gửi log cho mình."; exit 1; }
  if tail -1 reports/runs.jsonl | grep -qE '"tool_calls": 0[,}]'; then
    echo "DỪNG: $p có 0 tool calls, mô hình không đọc code. Dán lại khối này."; exit 1
  fi
  touch out/lan1/$p.xong
done
echo "XONG: đủ 5 chương trình"
EOF
```

Khối chạy từng chương trình một. Kết quả cũ từ trước bước này (nếu có) được cất vào `out/lan1/cu`, nên không lẫn vào
điểm.

**Đúng khi:** mỗi chương trình in một dòng dạng
`COSGN00C: 8 rules, 8 pass the citation check, 11 tool calls (0 repeats blocked), 41230+2210 tokens, 38.5s`, và dòng
cuối là `XONG: đủ 5 chương trình`.

**Nếu lỗi:** dừng ở giữa thì xem dòng ngay trên:

| Thấy | Làm |
| --- | --- |
| `DỪNG: chưa nối được Colab`, `Connection error`, `530`, `1033`, `524` | 6.2, rồi dán lại khối 6.3 |
| `DỪNG: ... 0 tool calls` hoặc `did not return valid JSON` | Dán lại khối 6.3. Cùng một chương trình lỗi 3 lần thì làm 5.9 |
| `WARNING: a request used ... context tokens` rồi dừng | Dán khối 6.4 |

### 6.4. Chỉ khi cần: một chương trình cứ lỗi vì quá dài

Khối này giống 6.3 nhưng giới hạn agent ở 10 bước đọc code, để hội thoại không vượt cửa sổ ngữ cảnh.

```bash
cd /workspaces/legacylens
bash -e <<'EOF'
set -a; . ./.env; set +a
curl -sf -m 20 "$LLM_BASE_URL/models" > /dev/null || { echo "DỪNG: chưa nối được Colab. Làm 6.2 rồi dán lại khối này."; exit 1; }
for p in COSGN00C COBIL00C CBTRN02C CBACT04C COTRN02C; do
  if [ -f out/lan1/$p.xong ]; then echo "$p: đã xong, bỏ qua"; continue; fi
  make extract PROGS=$p ARGS="--max-steps 10"
  touch out/lan1/$p.xong
done
echo "XONG: đủ 5 chương trình"
EOF
```

**Đúng khi:** dòng cuối là `XONG: đủ 5 chương trình`.

### 6.5. Kiểm tra cả 5 chương trình

```bash
cd /workspaces/legacylens
python3 - <<'PY'
import json
rows = {}
for line in open("reports/runs.jsonl"):
    r = json.loads(line); rows[r["program"]] = r
for p in ["COSGN00C", "COBIL00C", "CBTRN02C", "CBACT04C", "COTRN02C"]:
    r = rows.get(p)
    print(f"{p}: " + ("CHƯA CHẠY, dán lại 6.3" if not r else f"{r['rules']} rules, {r['citations_ok']} trích đúng, {r['tool_calls']} tool calls"))
PY
```

**Đúng khi:** đủ 5 dòng, không dòng nào có `CHƯA CHẠY`.

**Ghi lại:** không có gì. Số liệu được ghi tự động ở bước 7.

**Đẩy:** chưa đẩy. Bước 7 đẩy cùng điểm số.

---

## Bước 7. Chấm điểm và ghi số vào README

**Ở đâu:** terminal Codespace. Tab Colab vẫn mở, vì 7.2 cần mô hình.

### 7.1. Chấm phần trích rule (vài giây, không cần mô hình)

```bash
cd /workspaces/legacylens
make eval > /dev/null && cat reports/eval.md
```

**Đúng khi:** in một bảng có các dòng `Precision`, `Recall`, `F1`. Số thấp vẫn là số thật, cứ để nguyên.

### 7.2. Chấm phần hỏi đáp onboarding (30-60 phút)

```bash
cd /workspaces/legacylens
bash -e <<'EOF'
set -a; . ./.env; set +a
curl -sf -m 20 "$LLM_BASE_URL/models" > /dev/null || { echo "DỪNG: chưa nối được Colab. Làm 6.2 rồi dán lại khối này."; exit 1; }
make eval-qa > /dev/null
python3 - <<'PY'
import json
d = json.load(open("reports/eval_qa.json"))
loi = [r["id"] for r in d["rows"] if r.get("error_type") == "unreachable"]
s = d["summary"]
print(f"Agent đúng {s['correct']}/{s['questions']} câu, mô hình {s.get('model')}")
if loi:
    print(f"DỪNG: {len(loi)} câu không gọi được mô hình ({', '.join(loi)}), số này chưa dùng được. Dán khối 7.2b (làm 6.2 trước nếu Colab đã ngắt).")
else:
    print("XONG: cả 20 câu đã hỏi được mô hình")
PY
EOF
```

Lệnh chạy 30-60 phút mà không in gì cho tới khi xong. Trong lúc chờ, thỉnh thoảng bấm vào tab Colab.

**Đúng khi:** in `Agent đúng N/20 câu` và `XONG: cả 20 câu đã hỏi được mô hình`. Nếu có câu lỗi vì Colab ngắt, câu đó
bị tính sai, nên khối in `DỪNG` để bạn hỏi lại câu đó (7.2b) thay vì giữ một con số thấp giả.

### 7.2b. Chỉ khi cần: hỏi lại các câu bị lỗi kết nối

Chỉ hỏi lại các câu chưa tới được mô hình, giữ nguyên các câu khác. Vài phút.

```bash
cd /workspaces/legacylens
bash -e <<'EOF'
set -a; . ./.env; set +a
curl -sf -m 20 "$LLM_BASE_URL/models" > /dev/null || { echo "DỪNG: chưa nối được Colab. Làm 6.2 rồi dán lại khối này."; exit 1; }
make eval-qa ARGS="--retry-unreachable" | grep "re-asking"
python3 - <<'PY'
import json
d = json.load(open("reports/eval_qa.json"))
loi = [r["id"] for r in d["rows"] if r.get("error_type") == "unreachable"]
s = d["summary"]
print(f"Agent đúng {s['correct']}/{s['questions']} câu, mô hình {s.get('model')}")
if loi:
    print(f"DỪNG: {len(loi)} câu không gọi được mô hình ({', '.join(loi)}), số này chưa dùng được. Dán khối 7.2b (làm 6.2 trước nếu Colab đã ngắt).")
else:
    print("XONG: cả 20 câu đã hỏi được mô hình")
PY
EOF
```

**Đúng khi:** in `re-asking N question(s), keeping ... answer(s)`, `Agent đúng ... câu`, rồi
`XONG: cả 20 câu đã hỏi được mô hình`. Nếu báo `the saved answers come from ...`, nghĩa là `.env` đang trỏ tới mô hình
khác lần chạy 7.2. Đổi lại đúng mô hình, hoặc dán lại khối 7.2.

### 7.3. Ghi số vào README

```bash
cd /workspaces/legacylens
bash -e <<'EOF'
make readme
if [ -f out/lan1/readme.xong ]; then echo "Lần 1 đã có trong bảng Các lần thử, không thêm lại"
else make readme NOTE="Bản đầu, prompt gốc" && touch out/lan1/readme.xong; fi
echo "--- Các dòng còn [X] (chỉ nên còn dòng Người trả lời):"
grep -n '\[X\]' README.md || echo "không còn"
EOF
```

Lệnh đầu chép số vào bảng Kết quả. Lệnh thứ hai thêm dòng 1 vào bảng "Các lần thử". Dán lại khối cũng không tạo dòng
trùng.

**Đúng khi:** in `updated: ...` (dòng `2 [X] left in README` là bình thường), và phần `Các dòng còn [X]` chỉ còn
đúng một dòng bắt đầu bằng `| Người trả lời 20 câu`. Dòng đó điền ở bước 10.

### 7.4. Cất kết quả lần 1 và đẩy

```bash
cd /workspaces/legacylens
cp reports/eval.md reports/eval_lan1.md && cp reports/eval_qa.md reports/eval_qa_lan1.md
rm -rf out/rules_lan1 && cp -r out/rules out/rules_lan1 && cp reports/runs.jsonl out/runs_lan1.jsonl
git add -A
if git diff --cached --name-only --diff-filter=AM | grep -E '^(\.env|data/)'; then echo "DỪNG: có file không được đẩy. Gửi log cho mình."; else git commit -qm "Kết quả lần 1: trích rule và hỏi đáp onboarding" && git push; fi
```

Hai dòng đầu cất bản sao của lần 1 (điểm, rule agent trích, token), để bước 8.4 so sánh và chọn lại được.

**Đúng khi:** dòng cuối có `main -> main`.

---

## Bước 8. Cải thiện 1-2 lần

Đây là phần để kể khi phỏng vấn: thấy lỗi gì, đổi gì, số thay đổi ra sao. Lần 1 cho thấy Qwen 7B tự điều khiển
agent thì đọc quá ít (2-6 đoạn) rồi trả lời, và trích dẫn quá rộng. Lần 2 đổi cách làm: phân tích tĩnh chọn từng
đoạn có quyết định (IF, EVALUATE, COMPUTE, XCTL) và đưa code cho mô hình, mô hình chỉ cần giải thích. Lần 3 thử mô
hình lớn hơn. Mỗi lần được ghi tự động vào bảng "Các lần thử" của README, kể cả khi số giảm.

### 8.1. Xem agent sai ở đâu và ghi kiểu lỗi

```bash
cd /workspaces/legacylens
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
read -rp ">>> Kiểu lỗi lặp lại bạn thấy, một câu (ví dụ: gộp nhiều nhánh WHEN thành một rule): " G && echo "- Lần 1, kiểu lỗi chính: $G" >> reports/ghi_chu_lan_thu.md && echo "đã ghi vào reports/ghi_chu_lan_thu.md"
```

Đọc danh sách bỏ sót và tìm một kiểu lặp lại. Ở lần 1 của bạn, kiểu rõ nhất là: mô hình chỉ đọc vài đoạn rồi trả
lời, gộp nhiều quyết định thành một rule, và trích cả khối 40-90 dòng thay vì vài dòng. Lần 2 nhắm đúng kiểu đó.

**Đúng khi:** in danh sách, rồi `đã ghi vào reports/ghi_chu_lan_thu.md` sau khi bạn gõ câu trả lời.

### 8.2. Lần 2: phân tích tĩnh chọn đoạn code cho mô hình (30-60 phút)

```bash
cd /workspaces/legacylens
bash -e <<'EOF'
L=2
test -d out/rules_lan1 || { echo "DỪNG: chưa cất kết quả lần 1. Dán khối 7.4 trước."; exit 1; }
set -a; . ./.env; set +a
curl -sf -m 20 "$LLM_BASE_URL/models" > /dev/null || { echo "DỪNG: chưa nối được Colab. Làm 6.2 rồi dán lại khối này."; exit 1; }
if [ ! -d out/lan$L ]; then mkdir -p out/lan$L; rm -rf out/rules; rm -f reports/runs.jsonl; fi
for p in COSGN00C COBIL00C CBTRN02C CBACT04C COTRN02C; do
  if [ -f out/lan$L/$p.xong ]; then echo "$p: đã xong ở lần trước, bỏ qua"; continue; fi
  make extract PROGS=$p ARGS="--mode chunks"
  tail -1 reports/runs.jsonl | grep -q "\"program\": \"$p\"" || { echo "DỪNG: $p không ghi được kết quả. Gửi log cho mình."; exit 1; }
  touch out/lan$L/$p.xong
done
make eval > /dev/null && grep -E "Precision|Recall|F1" reports/eval.md
if [ ! -f out/lan$L/readme.xong ]; then make readme NOTE="Phân tích tĩnh chọn đoạn có quyết định, mô hình giải thích từng đoạn" && touch out/lan$L/readme.xong; fi
cp reports/eval.md reports/eval_lan$L.md
rm -rf out/rules_lan$L && cp -r out/rules out/rules_lan$L && cp reports/runs.jsonl out/runs_lan$L.jsonl
echo "XONG LẦN $L"
EOF
```

`--mode chunks` (hàm `extract_rules_chunked` trong `src/legacylens/agent.py`) bỏ qua các đoạn OPEN, CLOSE, báo lỗi
file, chia đoạn dài thành phần tối đa 60 dòng, và gửi từng phần kèm số dòng. Mô hình không gọi tool, nên `0 tool
calls` ở lần này là đúng. Rule nào trích dòng nằm ngoài phần được xem bị bỏ và được đếm vào `rules dropped`.
Khoảng 50 lần gọi mô hình cho cả 5 chương trình.

**Đúng khi:** mỗi chương trình in một dòng `... rules, ... pass the citation check, 0 tool calls ...`, rồi 3 dòng
Precision, Recall, F1 mới, `updated: Lần thử 2`, và `XONG LẦN 2`.

**Nếu lỗi:** giống bảng ở 6.3. Sau khi sửa, dán lại đúng khối 8.2. Các chương trình đã xong được bỏ qua.

### 8.3. Lần 3: mô hình open-weight lớn hơn, Qwen2.5 14B (khoảng 1 giờ)

**Ở đâu:** tab Colab, rồi tab Codespace.

**Làm:**

1. Tab Colab: bấm vào ô 1 (ô có dòng `MODEL = "qwen2.5:7b-instruct"`). Chọn menu **Insert > Code cell**. Một ô trống
   hiện ngay dưới ô 1. Dán 2 dòng này vào ô trống:

```python
MODEL = "qwen2.5:14b-instruct"
CONTEXT = 16384
```

2. Menu **Runtime > Disconnect and delete runtime**, bấm **Yes**. Việc này tắt Ollama đang chạy mô hình 7B.
3. Menu **Runtime > Run all**. Chờ 10-15 phút, vì mô hình 14B nặng 9 GB.
4. Làm 6.2 (bước 2-4) để chép 4 dòng `LLM_` mới vào `.env`. Dòng cuối phải là `"id":"qwen2.5:14b-instruct"`.
5. Tab Codespace, dán:

```bash
cd /workspaces/legacylens
bash -e <<'EOF'
L=3
test -f reports/eval_lan1.md || { echo "DỪNG: chưa có kết quả lần 1. Dán khối 7.4 trước."; exit 1; }
set -a; . ./.env; set +a
case "$LLM_MODEL" in *14b*) ;; *) echo "DỪNG: .env vẫn là $LLM_MODEL. Làm lại bước 1-4 của 8.3."; exit 1;; esac
curl -sf -m 20 "$LLM_BASE_URL/models" > /dev/null || { echo "DỪNG: chưa nối được Colab. Làm 6.2 rồi dán lại khối này."; exit 1; }
f1() { awk -F'|' '$2 ~ /^ *F1 *$/ {gsub(/[ %]/, "", $3); print $3}' reports/eval_lan$1.md; }
MODE="agent"; ARGS="--max-steps 10"; NOTE="Qwen2.5 14B, agent tự đọc, tối đa 10 bước"
if [ -f reports/eval_lan2.md ] && awk -v a="$(f1 2)" -v b="$(f1 1)" 'BEGIN { exit !(a > b) }'; then
  MODE="chunks"; ARGS="--mode chunks"; NOTE="Qwen2.5 14B, phân tích tĩnh chọn đoạn như lần 2"
fi
echo "Cấu hình: $NOTE"
if [ ! -d out/lan$L ]; then mkdir -p out/lan$L; rm -rf out/rules; rm -f reports/runs.jsonl; fi
for p in COSGN00C COBIL00C CBTRN02C CBACT04C COTRN02C; do
  if [ -f out/lan$L/$p.xong ]; then echo "$p: đã xong ở lần trước, bỏ qua"; continue; fi
  make extract PROGS=$p ARGS="$ARGS"
  tail -1 reports/runs.jsonl | grep -q "\"program\": \"$p\"" || { echo "DỪNG: $p không ghi được kết quả. Gửi log cho mình."; exit 1; }
  if [ "$MODE" = agent ] && tail -1 reports/runs.jsonl | grep -qE '"tool_calls": 0[,}]'; then
    echo "DỪNG: $p có 0 tool calls. Dán lại khối này."; exit 1
  fi
  touch out/lan$L/$p.xong
done
make eval > /dev/null && grep -E "Precision|Recall|F1" reports/eval.md
if [ ! -f out/lan$L/readme.xong ]; then make readme NOTE="$NOTE" && touch out/lan$L/readme.xong; fi
cp reports/eval.md reports/eval_lan$L.md
rm -rf out/rules_lan$L && cp -r out/rules out/rules_lan$L && cp reports/runs.jsonl out/runs_lan$L.jsonl
echo "XONG LẦN $L"
EOF
```

Khối tự chọn cách làm: nếu lần 2 có F1 cao hơn lần 1 thì dùng cách chia đoạn của lần 2, không thì dùng agent như lần
1. Dòng `Cấu hình:` cho biết nó đã chọn gì, và README ghi đúng như vậy.

**Đúng khi:** in `Cấu hình: ...`, 3 dòng Precision, Recall, F1, `updated: Lần thử 3`, rồi `XONG LẦN 3`.

**Nếu lỗi:** Colab hết bộ nhớ khi tải 14B (ô 5 hoặc ô 6 báo lỗi `out of memory`) thì bỏ qua 8.3, sang 8.4. Bạn vẫn
có 2 lần thử để kể. Các lỗi khác xử lý như bảng ở 6.3.

### 8.4. Chọn lần tốt nhất cho bảng chính

Khối này tự so F1 của các lần đã chạy, rồi đưa lần cao nhất vào bảng Kết quả và vào `out/rules` (bước 9 dùng thư mục
này). Số hỏi đáp onboarding vẫn là của lần 1 và ghi tên mô hình của lần đó, nên không lẫn.

```bash
cd /workspaces/legacylens
bash -e <<'EOF'
f1() { awk -F'|' '$2 ~ /^ *F1 *$/ {gsub(/[ %]/, "", $3); print $3}' reports/eval_lan$1.md; }
best=1
for k in 1 2 3; do
  if [ -f reports/eval_lan$k.md ]; then
    echo "Lần $k: F1 = $(f1 $k)%"
    if awk -v a="$(f1 $k)" -v b="$(f1 $best)" 'BEGIN { exit !(a > b) }'; then best=$k; fi
  fi
done
echo "Chọn lần $best cho bảng chính"
rm -rf out/rules && cp -r out/rules_lan$best out/rules && cp out/runs_lan$best.jsonl reports/runs.jsonl
make eval > /dev/null && make readme
echo "lần $best" > reports/lan_chon.txt
sed -n '/Trích business rule/,/## Cách chấm/p' README.md
EOF
```

**Đúng khi:** in F1 của từng lần, `Chọn lần N cho bảng chính`, rồi bảng Kết quả và bảng Các lần thử. F1 ở bảng Kết
quả bằng F1 của lần được chọn.

### 8.5. Ghi lại bài học và đẩy

```bash
cd /workspaces/legacylens
cat > /tmp/luu8.sh <<'EOF'
echo ""
for k in 2 3; do
  if [ -f reports/eval_lan$k.md ]; then
    read -rp ">>> Lần $k: số thay đổi ra sao và vì sao bạn nghĩ vậy (1-2 câu): " A
    echo "- Lần $k: $A" >> reports/ghi_chu_lan_thu.md
  fi
done
git add -A
if git diff --cached --name-only --diff-filter=AM | grep -E '^(\.env|data/)'; then echo "DỪNG: có file không được đẩy. Gửi log cho mình."; else git commit -qm "Cải thiện: thử prompt và mô hình 14B" && git push; fi
EOF
bash /tmp/luu8.sh
```

**Đúng khi:** sau khi bạn trả lời từng câu hỏi, dòng cuối có `main -> main`. Ôn lại `reports/ghi_chu_lan_thu.md`
trước phỏng vấn.

---

## Bước 9. Tài liệu thiết kế tiếng Việt và tiếng Nhật (5 phút, không cần Colab)

Tài liệu dùng các rule của lần được chọn ở 8.4 (thư mục `out/rules`).

```bash
cd /workspaces/legacylens
make doc PROGS="COSGN00C COBIL00C CBTRN02C CBACT04C COTRN02C" > /dev/null
echo "Số file: $(ls docs/generated/*.md | wc -l)"
git add -A
if git diff --cached --name-only --diff-filter=AM | grep -E '^(\.env|data/)'; then echo "DỪNG: có file không được đẩy. Gửi log cho mình."; else git commit -qm "Tài liệu thiết kế vi/ja cho 5 chương trình" && git push; fi
code docs/generated/CBACT04C.vi.md
```

Tab `CBACT04C.vi.md` mở ra. Bấm Ctrl+Shift+V để xem bản hiển thị, có sơ đồ Mermaid.

**Đúng khi:** in `Số file: 10` (mỗi chương trình một `.vi.md` và một `.ja.md`), có `main -> main`, và bảng rule
trong tài liệu có cột trích dẫn. Mở `docs/generated/CBACT04C.vi.md` trên github.com, bấm một số dòng trong cột trích
dẫn: GitHub phải mở file CBACT04C.cbl của CardDemo và tô đúng các dòng đó.

---

## Bước 10. Bài kiểm tra bấm giờ với người thật (1-2 giờ)

Bạn đã thuộc code sau bước 4, nên bạn tự làm bài thì kết quả bị lệch. Nhờ 1-2 người biết lập trình nhưng chưa đọc
CardDemo. Bạn điều khiển Codespace và chia sẻ màn hình (Google Meet, Zalo, ...). Người làm bài đọc và nói câu trả lời,
bạn ghi lại.

Mỗi người làm 2 phần, 10 câu mỗi phần:

| Người | Phần 1: chỉ đọc code | Phần 2: dùng LegacyLens |
| --- | --- | --- |
| Người 1 | Q01-Q10 | Q11-Q20 |
| Người 2 (nếu có) | Q11-Q20 | Q01-Q10 |

### 10.1. Mở giao diện

**Ở đâu:** terminal Codespace. Làm 6.1 trước. Nếu 6.1 in `CHƯA NỐI ĐƯỢC` thì làm 6.2.

```bash
cd /workspaces/legacylens
make ui
```

Codespaces hiện thông báo cổng 8501, bấm **Open in Browser**. Terminal này giữ giao diện chạy, đừng đóng.

**Đúng khi:** tab mới mở giao diện LegacyLens. Hỏi thử một câu ở mục Ask, phải ra câu trả lời có trích dẫn.

Mở terminal thứ hai bằng dấu `+` ở khung terminal. Các khối 10.2-10.4 dán vào terminal thứ hai này.

### 10.2. Bấm giờ bắt đầu một phần

Mở `onboarding/BAI_KIEM_TRA.md` cho người làm bài xem câu hỏi. Ngay trước câu đầu tiên của phần, dán:

```bash
cd /workspaces/legacylens && date +%s > /tmp/bat_dau && echo "Bắt đầu lúc $(date +%H:%M:%S)"
```

- Phần chỉ đọc code: người làm bài dùng Explorer và Ctrl+Shift+F (tìm trong toàn bộ file).
- Phần dùng LegacyLens: người làm bài gõ câu hỏi vào mục Ask của giao diện, đọc câu trả lời và trích dẫn.

Bạn ghi câu trả lời của họ ra giấy hoặc file nháp.

### 10.3. Bấm giờ kết thúc, chấm và lưu

Ngay sau câu cuối của phần, dán:

```bash
cd /workspaces/legacylens
cat > /tmp/xong_phan.sh <<'EOF'
giay=$(( $(date +%s) - $(cat /tmp/bat_dau) ))
echo ""
echo "Thời gian phần này: $((giay / 60)) phút $((giay % 60)) giây"
read -rp ">>> Người số mấy (1 hoặc 2): " N
read -rp ">>> Cách làm (1 = chỉ đọc code, 2 = dùng LegacyLens): " C
case "$N$C" in 11|22) Q="Q01-Q10";; 12|21) Q="Q11-Q20";; *) echo "DỪNG: chỉ gõ 1 hoặc 2. Dán lại khối này (giờ vẫn giữ)."; exit 1;; esac
echo ""
echo "Đáp án $Q. Một câu đúng khi câu trả lời có đủ mọi nhóm từ khóa (mỗi nhóm chỉ cần một từ):"
python3 - "$Q" <<'PY'
import json, sys
a, b = (1, 10) if sys.argv[1] == "Q01-Q10" else (11, 20)
for line in open("onboarding/questions.jsonl"):
    q = json.loads(line)
    if a <= int(q["id"][1:]) <= b:
        kw = "; ".join(" hoặc ".join(g) for g in q["keywords"])
        where = ", ".join(f"{e['program']} dòng {e['start_line']}-{e['end_line']}" for e in q["expected"]) or "-"
        print(f"  {q['id']}: phải có [{kw}]  (code: {where})")
PY
read -rp ">>> Số câu đúng trên 10: " D
case "$D" in [0-9]|10) ;; *) echo "DỪNG: gõ một số từ 0 đến 10. Dán lại khối này (giờ vẫn giữ)."; exit 1;; esac
test -f onboarding/ket_qua_bam_gio.csv || echo "nguoi,cach,cau,giay,dung" > onboarding/ket_qua_bam_gio.csv
echo "$N,$C,$Q,$giay,$D" >> onboarding/ket_qua_bam_gio.csv
echo "đã lưu: người $N, cách $C, $Q, $giay giây, đúng $D/10"
EOF
bash /tmp/xong_phan.sh
```

Thời gian được tính ngay khi bạn dán, nên trả lời câu hỏi chậm cũng không tính thêm giờ.

**Đúng khi:** in `đã lưu: ...`.

Mỗi phần chỉ dán 10.3 một lần. Nếu lỡ dán hai lần cho cùng một phần, gửi log cho mình trước khi làm 10.4.

Lặp lại 10.2 và 10.3 cho mỗi phần: người 1 phần 1, người 1 phần 2, rồi người 2 nếu có. Mỗi người làm 2 phần là đủ.

### 10.4. Ghi vào README và đẩy

Làm sau khi mọi người đã xong cả hai phần.

```bash
cd /workspaces/legacylens
python3 - <<'PY'
import csv, subprocess
rows = list(csv.DictReader(open("onboarding/ket_qua_bam_gio.csv")))
def part(c):
    rs = [r for r in rows if r["cach"] == c]
    phut = sum(int(r["giay"]) for r in rs) / 60 / (10 * len(rs))
    return round(phut, 1), f"{sum(int(r['dung']) for r in rs)}/{10 * len(rs)}", len(rs)
read_min, read_ok, n1 = part("1")
tool_min, tool_ok, n2 = part("2")
people = len({r["nguoi"] for r in rows})
print(f"Chỉ đọc code: {read_min} phút mỗi câu, đúng {read_ok}")
print(f"Dùng LegacyLens: {tool_min} phút mỗi câu, đúng {tool_ok}")
if n1 != n2:
    raise SystemExit("DỪNG: số phần đọc code và số phần dùng LegacyLens khác nhau. Làm nốt phần còn thiếu ở 10.2-10.3.")
subprocess.run(["make", "readme", f"READ_MIN={read_min}", f"TOOL_MIN={tool_min}", f"READ_OK={read_ok}",
                f"TOOL_OK={tool_ok}", f"PEOPLE={people} người, 10 câu mỗi cách"], check=True)
PY
git add -A
if git diff --cached --name-only --diff-filter=AM | grep -E '^(\.env|data/)'; then echo "DỪNG: có file không được đẩy. Gửi log cho mình."; else git commit -qm "Kết quả bài kiểm tra onboarding bấm giờ" && git push; fi
```

Khối tự tính phút **mỗi câu** (tổng thời gian chia số câu) và cộng số câu đúng của mọi người. Mẫu nhỏ thì README ghi rõ
số người, nên không cần giải thích thêm.

**Đúng khi:** in hai dòng `Chỉ đọc code` và `Dùng LegacyLens`, `updated: Bài kiểm tra với người thật`,
`no [X] left in README`, rồi `main -> main`.

Bấm Ctrl+C ở terminal đầu tiên để tắt giao diện.

---

## Bước 11. Kiểm tra lại lỗi CBACT04C (15 phút, không cần Colab)

README có mục "Một lỗi gặp khi gán nhãn". Lỗi đã được báo ở issue #64 của CardDemo. Bạn tự chạy để kể được.

```bash
cd /workspaces/legacylens
command -v cobc > /dev/null || { sudo apt-get update -qq && sudo apt-get install -y -qq gnucobol > /dev/null; }
cobc -x -free scripts/repro_cbact04c.cbl -o /tmp/repro && /tmp/repro
echo "----- CBACT04C.cbl, dòng 188-222 -----"
awk 'NR >= 188 && NR <= 222 { printf "%4d  %s\n", NR, $0 }' data/carddemo/app/cbl/CBACT04C.cbl
code scripts/repro_cbact04c.cbl
```

Đọc dòng 188-222 in ra trong terminal, so với file `repro_cbact04c.cbl` vừa mở.

**Đúng khi:** chương trình in 5 dòng: `interest transaction written` hai lần cho account 101,
`balance updated (interest added) for account 101`, `interest transaction written for account 202`, rồi `end of run`.
Điểm mấu chốt: account 202 có giao dịch lãi nhưng **không có** dòng `balance updated`. Hai dòng cảnh báo
`_FORTIFY_SOURCE` lúc biên dịch là vô hại. Bạn tự
giải thích được bằng lời: vòng `PERFORM UNTIL END-OF-FILE = 'Y'` kiểm tra trước mỗi lượt, nên mỗi lượt bắt đầu với
`END-OF-FILE = 'N'`, và nhánh `ELSE` ở dòng 219 không bao giờ chạy. Vì vậy tài khoản cuối cùng không bao giờ được cập
nhật.

Khi kể, nói đúng: "Tôi gặp lỗi này khi duyệt nhãn, viết bản tái hiện bằng GnuCOBOL, rồi thấy nó đã được báo ở
issue #64." Đừng nói là bạn phát hiện đầu tiên.

**Đẩy:** không có gì mới.

---

## Bước 12. Hoàn tất

### 12.1. Kiểm tra lần cuối

```bash
cd /workspaces/legacylens
echo "Số dòng còn [X]: $(grep -c '\[X\]' README.md)"
make test lint check-gold 2>&1 | grep -E "passed|failed|All checks|gold rules"
```

**Đúng khi:** dòng đầu là `Số dòng còn [X]: 0`, sau đó có `43 passed` (hoặc `42 passed, 1 skipped`),
`All checks passed!`, `N/N gold rules pass`.

**Nếu lỗi:** còn `[X]` thì xem bước nào chưa làm: dòng Precision là bước 7, dòng Người trả lời là bước 10. Lint báo
lỗi thì dán `cd /workspaces/legacylens && ruff format . && make lint`.

### 12.2. Quay video demo 2 phút

**Ở đâu:** máy bạn, quay màn hình tab Codespace (Windows: Win+Alt+R của Xbox Game Bar; macOS: Cmd+Shift+5).

Trước khi quay, làm 6.1 (Colab phải chạy cho phần hỏi đáp). Rồi quay theo thứ tự:

1. Terminal: dán `cd /workspaces/legacylens && make stats` (số chương trình, dòng code).
2. Dán `code reports/graph.mmd` (đồ thị phụ thuộc).
3. Dán `make ui`, bấm **Open in Browser**, hỏi một câu ở mục Ask, mở một trích dẫn.
4. Terminal thứ hai: dán `cd /workspaces/legacylens && code docs/generated/CBACT04C.ja.md`, bấm Ctrl+Shift+V.
5. Dán `code README.md`, bấm Ctrl+Shift+V, kéo tới bảng Kết quả và bảng Các lần thử.

Tải video lên YouTube, chế độ **Unlisted**. Bấm **Share > Copy** để chép link. Rồi dán khối này và dán link khi được
hỏi:

```bash
cd /workspaces/legacylens
read -rp ">>> Dán link YouTube (Ctrl+V) rồi Enter: " V && case "$V" in https://*) make readme VIDEO="$V" && git add README.md && git commit -qm "Thêm video demo" && git push;; *) echo "DỪNG: link phải bắt đầu bằng https://. Dán lại khối này.";; esac
```

**Đúng khi:** in `updated: Video` rồi `main -> main`.

### 12.3. Kiểm tra không lộ khóa, xóa file riêng

```bash
cd /workspaces/legacylens
bash <<'EOF'
if git log -p | grep -qE "gsk_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{30,}|API_KEY=[A-Za-z0-9_-]{16,}"; then
  echo "DỪNG: có khóa API trong lịch sử git. KHÔNG để repo Public. Gửi log cho mình."; exit 1
fi
if git ls-files | grep -qE '^\.env$|^data/'; then
  echo "DỪNG: có .env hoặc data/ trong repo. KHÔNG để repo Public. Gửi log cho mình."; exit 1
fi
echo "sạch: không có khóa, không có dữ liệu"
git rm -q --ignore-unmatch HUONG_DAN.md
git commit -qm "Bỏ ghi chú riêng" && git push || echo "HUONG_DAN.md đã được xóa từ trước"
EOF
```

Khối kiểm tra khóa và dữ liệu **trước**, chỉ xóa `HUONG_DAN.md` khi sạch. Bản hướng dẫn này vẫn còn trong thư mục dự
án, bạn không mất nó.

**Đúng khi:** in `sạch: không có khóa, không có dữ liệu` rồi `main -> main`.

### 12.4. Để repo Public

**Ở đâu:** github.com/tak2k5/legacylens. Chỉ làm khi 12.3 in `sạch`.

1. Bấm **Settings** (thanh trên cùng của repo) > **General**.
2. Kéo xuống cuối, mục **Danger Zone** > **Change visibility** > **Change to public**, làm theo các bước xác nhận.
3. Quay lại terminal Codespace, dán:

```bash
cd /workspaces/legacylens && gh run list --limit 1
```

**Đúng khi:** repo hiện nhãn **Public** cạnh tên. Dòng `gh run list` có `completed` và `success`. Nếu `gh` báo lỗi
quyền, mở tab **Actions** của repo: lần chạy `ci` mới nhất phải có dấu xanh.

### 12.5. Thêm vào CV

Khối này lấy số từ các file kết quả (không gõ tay số nào) và in câu cho CV bằng tiếng Việt và tiếng Anh.

```bash
cd /workspaces/legacylens
python3 - <<'PY' | tee out/cv.txt
import csv, json, os
ev = json.load(open("reports/eval.json"))
qa = json.load(open("reports/eval_qa.json"))["summary"]
runs = [json.loads(l) for l in open("reports/runs.jsonl")]
model = runs[-1]["model"]
qa_vi = f" (dùng {qa['model']})" if qa.get("model") != model else ""
qa_en = f" (with {qa['model']})" if qa.get("model") != model else ""
n = sum(1 for l in open("gold/rules.jsonl") if l.strip())
pct = lambda x: f"{x:.0%}"
human_vi = human_en = ""
if os.path.exists("onboarding/ket_qua_bam_gio.csv"):
    rows = list(csv.DictReader(open("onboarding/ket_qua_bam_gio.csv")))
    m = {c: sum(int(r["giay"]) for r in rows if r["cach"] == c) / 60 / (10 * sum(r["cach"] == c for r in rows)) for c in "12"}
    people = len({r["nguoi"] for r in rows})
    human_vi = f" Bài kiểm tra với {people} người: {m['1']:.1f} phút mỗi câu khi chỉ đọc code, {m['2']:.1f} phút khi dùng LegacyLens."
    human_en = f" Timed test with {people} developer(s): {m['1']:.1f} min per question reading code vs {m['2']:.1f} min with LegacyLens."
print("TIẾNG VIỆT:")
print(f"LegacyLens: agent đọc hiểu COBOL trên AWS CardDemo, chạy mô hình open-weight {model} trên Colab T4. "
      f"Trích business rule kèm trích dẫn dòng code: P/R/F1 {pct(ev['precision'])}/{pct(ev['recall'])}/{pct(ev['f1'])} "
      f"trên {n} nhãn (AI soạn nháp, tôi đối chiếu từng nhãn với mã nguồn, sửa và thêm 3 nhãn); "
      f"{pct(ev['citation_validity'])} trích dẫn qua kiểm tra tự động; trả lời đúng {qa['correct']}/{qa['questions']} câu onboarding{qa_vi}.{human_vi}")
print()
print("ENGLISH:")
print(f"LegacyLens: COBOL comprehension agent on AWS CardDemo using open-weight {model} on a Colab T4. "
      f"Extracts business rules with line citations: P/R/F1 {pct(ev['precision'])}/{pct(ev['recall'])}/{pct(ev['f1'])} "
      f"against {n} labels (AI-drafted, each checked against the source by me, 3 corrected or added); "
      f"{pct(ev['citation_validity'])} of citations pass an automatic check; {qa['correct']}/{qa['questions']} onboarding questions answered correctly{qa_en}.{human_en}")
PY
```

Chép câu in ra vào CV, thêm link repo và link video. Câu cũng được lưu ở `out/cv.txt` (không lên GitHub).

**Đúng khi:** in hai đoạn TIẾNG VIỆT và ENGLISH, số khớp với bảng Kết quả trong README.

Nói đúng về nhãn như trong câu: AI soạn nháp, bạn đối chiếu từng nhãn. Nếu được hỏi, nói rõ bản nháp đầu có trợ giúp
của AI. Ôn `reports/ghi_chu_lan_thu.md` và bước 11 trước phỏng vấn.

**Xong toàn bộ khi:** repo Public, CI xanh, README không còn `[X]`, CV có link repo và link video.

---

## Phụ lục A. Lỗi thường gặp

| Thấy | Nghĩa là | Làm |
| --- | --- | --- |
| `error: No LLM endpoint configured` | Chưa có `.env` hay secret | Bước 5.5 |
| `Connection error`, `530`, `1033`, `Connection refused`, `DỪNG: chưa nối được Colab` | Colab đã ngắt, URL đường hầm không còn | Bước 6.2, rồi dán lại khối đang làm |
| `Name or service not known` | `LLM_BASE_URL` sai chính tả hoặc là URL của phiên Colab cũ | Bước 6.2 |
| `Error code: 524` | Cloudflare cắt yêu cầu im lặng quá 100 giây | Bản mới tự bật streaming cho URL trycloudflare; cập nhật repo rồi chạy lại |
| `0 tool calls` trong kết quả extract | Mô hình không đọc code | Dán lại khối đang làm; một chương trình lỗi 3 lần thì xem 5.9 |
| `404` hoặc `model not found` | `LLM_MODEL` khác tên mô hình đã tải | Chạy 5.6, chép đúng tên trong JSON vào `.env` |
| `WARNING: a request used ... context tokens` | Hội thoại chạm giới hạn cửa sổ | Bước 6.4 |
| `did not return valid JSON` | Mô hình trả sai định dạng | Repo phải là bản zip mới nhất (5.0). Vẫn lỗi thì gửi mình dòng `last error: ...` |
| Lệnh chạy rất lâu, không in gì | Mô hình đang chạy trên T4, hoặc Colab treo | Chờ 5 phút; xem ô 8 của notebook |
| Colab: `Cannot connect to GPU backend` | Hết GPU miễn phí | Chờ vài giờ; trong lúc chờ làm trước bước 11 |
| Chỉ khi dùng API dự phòng: `401` | Khóa sai | Sửa `LLM_API_KEY`, không để dấu cách hay dấu nháy |
| Chỉ khi dùng API dự phòng: `429`, `413` | Vượt hạn mức gói miễn phí | `LLM_PAUSE=6` trong `.env`; `413` thì quay lại Colab |
| `configured for Git LFS but 'git-lfs' was not found` rồi `failed to push` | Codespace có hook Git LFS thừa | `grep -l "git-lfs\|git lfs" .git/hooks/* \| xargs -r rm -v` rồi `git push` (repo không dùng LFS) |
| `data/carddemo/app not found` | Chưa tải dữ liệu | `make data` |
| CI đỏ ở bước lint | Code chưa format | `cd /workspaces/legacylens && ruff format . && make lint`, rồi đẩy lại |
| CI đỏ ở `test_readme_fill` sau khi có bảng Các lần thử | Repo đang ở bản zip cũ | Làm lại 5.0 với zip mới nhất (giữ nhãn và README) |

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

**Chỉ để tra lại.** Muốn cập nhật lên zip mới nhất, luôn dùng mục 5.0: nó giữ cả kết quả chấm điểm, tài liệu và kết
quả bấm giờ, còn U1-U6 dưới đây thì không.

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
test -f legacylens.zip && rm -rf /tmp/ll && unzip -q legacylens.zip -d /tmp/ll && test -f /tmp/ll/legacylens/Makefile && rm legacylens.zip && \
git ls-files -z -- . ':!:data' | xargs -0 rm -f
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

**Đúng khi:** `make test` in `43 passed`, `make lint` sạch, dòng cuối `check-gold` là `N/N gold rules pass` với N
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
- `make test` in `43 passed`.
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
