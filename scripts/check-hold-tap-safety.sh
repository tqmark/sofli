#!/bin/sh

set -eu

keymap_path="${1:-config/sofle.keymap}"

if grep -nE '^[[:space:]]*bindings[[:space:]]*=[[:space:]]*<&mt([[:space:]]|$)' "$keymap_path"; then
    echo "FAIL: a tap dance or custom behavior wraps an undecided mod-tap"
    exit 1
fi

if grep -nF 'compatible = "zmk,behavior-tap-dance"' "$keymap_path"; then
    echo "FAIL: tap dances are intentionally disabled on every layer"
    exit 1
fi

echo "PASS: no custom behavior wraps a mod-tap and no tap dances remain"
