PY ?= python
SRC ?= data/carddemo/app
CLI = PYTHONPATH=src $(PY) -m legacylens.cli --src $(SRC)
PROGS ?= CBTRN02C
PROG ?= COSGN00C
ARGS ?=
F ?= summary
# chỉ truyền phần được đặt: S summary, C condition, O outcome, FL fields, P paragraph, K kind, L lines
GOLD_OPTS = $(if $(S),--new-summary "$(S)") $(if $(C),--new-condition "$(C)") $(if $(O),--new-outcome "$(O)") \
	$(if $(FL),--new-fields "$(FL)") $(if $(P),--new-paragraph "$(P)") $(if $(K),--new-kind "$(K)") $(if $(L),--new-lines "$(L)")
Q ?= Which program validates the user id and password at sign-on?
# .env là tùy chọn: không có thì dùng biến môi trường (Codespaces secrets)
LOADENV = if [ -f .env ]; then set -a; . ./.env; set +a; fi;

.PHONY: help install data test lint stats graph check-gold review gold-ok gold-set gold-lines gold-fix gold-add gold-copy gold-del ask extract doc eval eval-qa readme ui

help:          ## Liệt kê lệnh
	@grep -E '^[a-z-]+:.*##' Makefile | awk -F':.*## ' '{printf "  %-12s %s\n", $$1, $$2}'
install:       ## Cài thư viện (CPU, không cần GPU)
	$(PY) -m pip install -e ".[dev,ui]"
data:          ## Tải AWS CardDemo, ghim commit
	bash scripts/fetch_carddemo.sh
test:          ## Test offline với LLM giả lập (vài giây, không cần mạng)
	PYTHONPATH=src $(PY) -m pytest
lint:          ## Kiểm tra code style
	ruff check . && ruff format --check .
stats:         ## Đếm chương trình, copybook, job, dòng code của CardDemo
	$(CLI) stats
graph:         ## Đồ thị phụ thuộc -> reports/graph.json, reports/graph.mmd
	$(CLI) graph --out reports
check-gold:    ## Kiểm tra nhãn tay trong gold/ trích đúng dòng code
	$(CLI) check-gold --gold gold/rules.jsonl
review:        ## Xem nhãn tay của một chương trình cạnh dòng code. Ví dụ: make review PROG=COSGN00C
	@mkdir -p out/review && $(CLI) review-gold $(PROG) > out/review/$(PROG).txt && echo "mở out/review/$(PROG).txt"
gold-ok:       ## Đánh dấu nhãn đã duyệt là đúng. Ví dụ: make gold-ok ID=COSGN00C-G1
	$(CLI) gold-edit ok $(ID)
gold-set:      ## Sửa chữ của nhãn. Ví dụ: make gold-set ID=COSGN00C-G1 F=summary V="..."
	$(CLI) gold-edit set $(ID) "$(V)" --field $(F)
gold-lines:    ## Sửa dòng trích. Ví dụ: make gold-lines ID=COSGN00C-G1 L=88-90
	$(CLI) gold-edit lines $(ID) $(L)
gold-fix:      ## Sửa nhiều phần một lúc (để trống phần không đổi). Ví dụ: make gold-fix ID=COSGN00C-G1 L=88-91 FL="EIBAID"
	$(CLI) gold-edit fix $(ID) $(GOLD_OPTS)
gold-add:      ## Thêm nhãn mới, mọi phần một lần. Xem bước 4 trong HUONG_DAN.md
	$(CLI) gold-edit add $(ID) $(GOLD_OPTS)
gold-copy:     ## Thêm nhãn mới bằng cách chép một nhãn có sẵn. Ví dụ: make gold-copy ID=COSGN00C-G9 NEW=COSGN00C-G10
	$(CLI) gold-edit copy $(ID) $(NEW)
gold-del:      ## Xóa một nhãn. Ví dụ: make gold-del ID=COSGN00C-G10
	$(CLI) gold-edit delete $(ID)
ask:           ## Hỏi một câu (cần khóa LLM). Ví dụ: make ask Q="Mật khẩu được kiểm tra ở đâu?"
	$(LOADENV) $(CLI) ask "$(Q)"
extract:       ## Trích business rule bằng agent (cần khóa LLM). Ví dụ: make extract PROGS="CBTRN02C COSGN00C"
	$(LOADENV) $(CLI) extract $(PROGS) --out out/rules $(ARGS)
doc:           ## Sinh tài liệu thiết kế tiếng Việt và tiếng Nhật -> docs/generated/
	$(LOADENV) $(CLI) doc $(PROGS) --lang vi $(ARGS) && $(CLI) doc $(PROGS) --lang ja $(ARGS)
eval:          ## Chấm điểm rule trích ra so với nhãn tay -> reports/eval.md
	$(CLI) eval --gold gold/rules.jsonl --pred out/rules --out reports/eval.md
eval-qa:       ## Agent trả lời 20 câu onboarding, chấm tự động (cần khóa LLM) -> reports/eval_qa.md
	$(LOADENV) $(CLI) eval-qa $(ARGS)
readme:        ## Chép số đo vào bảng Kết quả của README. Thêm NOTE="..." để ghi một lần thử, VIDEO=link để thêm video
	$(CLI) readme $(if $(NOTE),--attempt "$(NOTE)") $(if $(QA_NOTE),--qa-attempt "$(QA_NOTE)") $(if $(VIDEO),--video "$(VIDEO)") \
	  $(if $(READ_MIN),--read-min "$(READ_MIN)" --tool-min "$(TOOL_MIN)" --read-ok "$(READ_OK)" --tool-ok "$(TOOL_OK)" --people "$(PEOPLE)")
ui:            ## Giao diện hỏi đáp (Streamlit)
	$(LOADENV) PYTHONPATH=src LEGACYLENS_SRC=$(SRC) streamlit run app.py --server.headless true
