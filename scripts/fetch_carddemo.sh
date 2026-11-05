#!/usr/bin/env bash
# Tải AWS CardDemo (Apache-2.0) vào data/carddemo, ghim đúng commit mà gold/rules.jsonl dùng để đánh số dòng.
set -euo pipefail
COMMIT=59cc6c2fd7ebd7ef7925cad552a01a4b8b6e4d5e
DEST=data/carddemo
if [ -d "$DEST/.git" ]; then echo "$DEST đã có"; exit 0; fi
git clone https://github.com/aws-samples/aws-mainframe-modernization-carddemo.git "$DEST"
git -C "$DEST" checkout -q "$COMMIT"
echo "CardDemo @ $COMMIT -> $DEST"
