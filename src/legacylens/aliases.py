"""Vietnamese names without diacritics for the CardDemo programs, so a reader can find a program by what it does.

The real program ids stay the key everywhere (citations, gold labels, GitHub links); these names are only shown next to
them and can be typed in a question instead of the id. Each name follows the "Function:" line of the program header.
"""

from __future__ import annotations

import re

ALIASES = {
    "CBACT01C": "doc-file-tai-khoan",
    "CBACT02C": "in-file-the",
    "CBACT03C": "in-tham-chieu-the-tai-khoan",
    "CBACT04C": "tinh-lai-hang-thang",
    "CBCUS01C": "in-file-khach-hang",
    "CBEXPORT": "xuat-du-lieu-chuyen-chi-nhanh",
    "CBIMPORT": "nhap-du-lieu-chuyen-chi-nhanh",
    "CBPAUP0C": "xoa-uy-quyen-het-han",
    "CBSTM03A": "in-sao-ke-tai-khoan",
    "CBSTM03B": "doc-file-cho-sao-ke",
    "CBTRN01C": "doc-giao-dich-hang-ngay",
    "CBTRN02C": "ghi-so-giao-dich-hang-ngay",
    "CBTRN03C": "in-bao-cao-giao-dich",
    "COACCT01": "xem-tai-khoan-qua-mq",
    "COACTUPC": "cap-nhat-tai-khoan",
    "COACTVWC": "xem-tai-khoan",
    "COADM01C": "menu-quan-tri",
    "COBIL00C": "thanh-toan-hoa-don",
    "COBSWAIT": "tien-ich-cho",
    "COBTUPDT": "cap-nhat-loai-giao-dich-batch",
    "COCRDLIC": "danh-sach-the",
    "COCRDSLC": "xem-chi-tiet-the",
    "COCRDUPC": "cap-nhat-the",
    "CODATE01": "lay-ngay-gio-qua-mq",
    "COMEN01C": "menu-chinh",
    "COPAUA0C": "quyet-dinh-uy-quyen-the",
    "COPAUS0C": "tong-hop-uy-quyen",
    "COPAUS1C": "chi-tiet-uy-quyen",
    "COPAUS2C": "danh-dau-gian-lan",
    "CORPT00C": "in-bao-cao-truc-tuyen",
    "COSGN00C": "dang-nhap",
    "COTRN00C": "danh-sach-giao-dich",
    "COTRN01C": "xem-giao-dich",
    "COTRN02C": "them-giao-dich",
    "COTRTLIC": "danh-sach-loai-giao-dich",
    "COTRTUPC": "cap-nhat-loai-giao-dich",
    "COUSR00C": "danh-sach-nguoi-dung",
    "COUSR01C": "them-nguoi-dung",
    "COUSR02C": "sua-nguoi-dung",
    "COUSR03C": "xoa-nguoi-dung",
    "CSUTLDTC": "kiem-tra-ngay-hop-le",
    "DBUNLDGS": "xuat-uy-quyen-ra-gsam",
    "PAUDBLOD": "nap-co-so-du-lieu-uy-quyen",
    "PAUDBUNL": "xuat-co-so-du-lieu-uy-quyen",
}
_BY_NAME = {v: k for k, v in ALIASES.items()}


def label(program: str) -> str:
    """'COBIL00C · thanh-toan-hoa-don', or the id alone when there is no name."""
    name = ALIASES.get(program)
    return f"{program} · {name}" if name else program


def expand(question: str) -> str:
    """Put the program id in front of every Vietnamese name typed in the question, so the agent finds the program."""
    names = sorted(_BY_NAME, key=len, reverse=True)
    pattern = re.compile(r"(?<![\w-])(" + "|".join(map(re.escape, names)) + r")(?![\w-])", re.I)
    return pattern.sub(lambda m: f"{_BY_NAME[m.group(1).lower()]} ({m.group(1).lower()})", question)
