PY ?= python
SRC ?= data/carddemo/app
CLI = PYTHONPATH=src $(PY) -m legacylens.cli --src $(SRC)
PROGS ?= CBTRN02C
PROG ?= COSGN00C
ARGS ?=
Q ?= Which program validates the user id and password at sign-on?
# .env là tùy chọn: không có thì dùng biến môi trường (Codespaces secrets)
LOADENV = if [ -f .env ]; then set -a; . ./.env; set +a; fi;

.PHONY: help install data test lint stats graph check-gold review ask extract doc eval eval-qa ui

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
ask:           ## Hỏi một câu (cần khóa LLM). Ví dụ: make ask Q="Mật khẩu được kiểm tra ở đâu?"
	$(LOADENV) $(CLI) ask "$(Q)"
extract:       ## Trích business rule bằng agent (cần khóa LLM). Ví dụ: make extract PROGS="CBTRN02C COSGN00C"
	$(LOADENV) $(CLI) extract $(PROGS) --out out/rules $(ARGS)
doc:           ## Sinh tài liệu thiết kế tiếng Việt và tiếng Nhật -> docs/generated/
	$(CLI) doc $(PROGS) --lang vi && $(CLI) doc $(PROGS) --lang ja
eval:          ## Chấm điểm rule trích ra so với nhãn tay -> reports/eval.md
	$(CLI) eval --gold gold/rules.jsonl --pred out/rules --out reports/eval.md
eval-qa:       ## Agent trả lời 20 câu onboarding, chấm tự động (cần khóa LLM) -> reports/eval_qa.md
	$(LOADENV) $(CLI) eval-qa $(ARGS)
ui:            ## Giao diện hỏi đáp (Streamlit)
	$(LOADENV) PYTHONPATH=src LEGACYLENS_SRC=$(SRC) streamlit run app.py --server.headless true
