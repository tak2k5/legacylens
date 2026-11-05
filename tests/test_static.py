from pathlib import Path

import pytest

from legacylens.index import Index
from legacylens.parser import parse_jcl, parse_program
from legacylens.tools import Toolbox

FIX = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def idx() -> Index:
    return Index.build(FIX)


def test_program_basics():
    p = parse_program(FIX / "cbl/PAYCHK.cbl")
    assert p.program_id == "PAYCHK"
    assert p.kind == "batch"
    assert [(c.name, c.line) for c in p.copybooks] == [("PAYREC", 11)]
    assert p.selects == {"PAY-FILE": "PAYIN", "REJ-FILE": "PAYREJ"}


def test_value_on_next_line_resolves_dynamic_call():
    p = parse_program(FIX / "cbl/PAYCHK.cbl")
    assert p.transfers() == [("CALL", "PAYPOST", 23)]


def test_comments_and_strings_are_not_code():
    p = parse_program(FIX / "cbl/PAYCHK.cbl")
    names = {c.name for c in p.calls}
    assert "'NOTREAL'" not in names and "FAILED" not in names


def test_paragraphs_and_performs():
    p = parse_program(FIX / "cbl/PAYCHK.cbl")
    names = [x.name for x in p.paragraphs]
    assert names == ["MAIN", "1000-CHECK-AMOUNT", "2000-LOG", "2000-EXIT"]
    main = p.paragraph("MAIN")
    assert (main.start, main.end) == (17, 25)
    assert [r.name for r in main.performs] == ["1000-CHECK-AMOUNT"]  # PERFORM UNTIL is not a target
    check = p.paragraph("1000-CHECK-AMOUNT")
    assert (check.start, check.end) == (26, 31)  # trailing blank line excluded
    assert [r.name for r in check.performs] == ["2000-LOG", "2000-EXIT"]
    assert p.paragraph_at(28).name == "1000-CHECK-AMOUNT"


def test_cics_file_and_xctl_with_moves():
    p = parse_program(FIX / "cbl/MENU01.cbl")
    assert p.kind == "online"
    assert [(o.file, o.mode, o.line) for o in p.file_ops] == [("PAYDAT", "read", 9)]
    assert sorted(t for _, t, _ in p.transfers()) == ["PAYCHK", "SIGNON"]
    read = p.cics[0]
    assert (read.verb, read.line, read.end_line) == ("READ", 9, 12)


def test_jcl_steps_and_continued_dd():
    steps = parse_jcl(FIX / "jcl/PAYJOB.jcl")
    assert [(s.job, s.step, s.program) for s in steps] == [("PAYJOB", "STEP01", "PAYCHK"), ("PAYJOB", "STEP02", "SORT")]
    assert steps[0].dds == {"PAYIN": "PROD.PAY.DAILY", "PAYREJ": "PROD.PAY.REJECTS(+1)"}


def test_graph_maps_files_to_datasets(idx):
    g = idx.graph
    assert g.has_edge("file:PROD.PAY.DAILY", "program:PAYCHK")
    assert g.has_edge("program:PAYCHK", "file:PROD.PAY.REJECTS(+1)")
    assert g.has_edge("job:PAYJOB", "program:PAYCHK")
    assert g.has_edge("program:MENU01", "program:PAYCHK")
    assert g.nodes["program:SIGNON"]["external"] is True


def test_impact_of_copybook_and_program(idx):
    assert idx.impact("PAYREC") == ["MENU01", "PAYCHK"]  # includer, then its caller
    assert idx.impact("PAYCHK") == ["MENU01"]
    assert "MENU01" in {c["from"].split(":")[1] for c in idx.callers("PAYCHK")}


def test_stats_and_exports(idx):
    s = idx.stats()
    assert (s["programs"], s["copybooks"], s["jcl_steps"]) == (2, 1, 2)
    assert '"graph"' in idx.to_json()
    mmd = idx.to_mermaid()
    assert mmd.startswith("flowchart LR") and "PAYCHK" in mmd
    assert "PAYREC" in idx.to_mermaid(focus="PAYCHK")


def test_tools(idx):
    tb = Toolbox(idx)
    outline = tb.program_outline("paychk")
    assert "PAY-FILE -> PROD.PAY.DAILY" in outline and "1000-CHECK-AMOUNT [26-31]" in outline
    para = tb.read_paragraph("PAYCHK", "1000-CHECK-AMOUNT")
    assert para.splitlines()[0].startswith("   26:") and "5000" in para
    assert "PAY-AMT" in tb.open_copybook("PAYREC")
    assert "PAYCHK:27" in tb.search_code(r"PAY-AMT > 5000")
    assert "DIRECT" in tb.who_uses("PAYCHK")
    assert tb.call("read_lines", '{"program": "NOPE", "start": 1, "end": 2}').startswith("ERROR")
    assert tb.call("nope", "{}").startswith("ERROR")
    assert {s["function"]["name"] for s in tb.specs()} >= {"read_lines", "program_outline"}
