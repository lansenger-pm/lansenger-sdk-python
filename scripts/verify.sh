#!/usr/bin/env bash
# lansenger-sdk 统一验证入口（Harness ⑤验证层）
#
# 四态语义：PASS / FAIL（新增违规，阻断，EXIT=1）/ SKIP（原因+修复命令必填）/ WARN（存量已知，不阻断）
# EXIT 规则：FAIL>0 → 1，否则 0（SKIP/WARN 不影响退出码）；--strict：SKIP 或 WARN>0 → 2
# 日志统一落 harness/verify-logs/（已 gitignore）。
set -u
cd "$(dirname "$0")/.."
mkdir -p harness/verify-logs

declare -i FAIL=0 WARN=0 SKIP=0
STRICT=0
[ "${1:-}" = "--strict" ] && STRICT=1

have() { command -v "$1" >/dev/null 2>&1; }

pass() { printf '  PASS %s\n' "$2"; }
fail() { printf '  FAIL %s（日志: harness/verify-logs/%s.log）\n' "$2" "$2"; FAIL+=1; }
skip() { printf '  SKIP %s —— %s\n' "$1" "$2"; SKIP+=1; }
warn() { printf '  WARN %s —— %s\n' "$1" "$2"; WARN+=1; }
run()  { printf '▶ %s\n' "$1"; if eval "$1" >"harness/verify-logs/$2.log" 2>&1; then pass "$1" "$2"; else fail "$1" "$2"; fi; }

echo "==== lansenger-sdk verify ===="

# 1) Lint（对齐 CI：ruff check src tests）
if have uv; then
  run "uv run --frozen ruff check src tests" lint
elif have ruff; then
  run "ruff check src tests" lint
else
  skip "lint" "无 uv 也无 ruff；修复：brew install uv（或 pip install ruff 后 ruff check src tests）"
fi

# 2) 单元测试（pytest + pytest-asyncio；--frozen 不动 uv.lock）
if have uv; then
  run "uv run --frozen --extra dev pytest -q" test
elif have pytest; then
  run "pytest -q" test
else
  skip "test" "无 uv 也无 pytest；修复：pip install -e '.[dev]' 后重跑"
fi

# 3) 构建（uv build → dist/，验证包可构建）
if have uv; then
  run "uv build" build
else
  skip "build" "无 uv；修复：brew install uv 后重跑（或 pip install build && python -m build）"
fi

# 4) 凭证扫描（元数据级，永不回显值；--ratchet 与 harness/verify-allowlist 比对）
if have python3; then
  echo "▶ secrets scan: python3 scripts/scan_secrets.py --ratchet"
  scan_out=$(python3 scripts/scan_secrets.py --ratchet 2>"harness/verify-logs/secrets.err")
  scan_rc=$?
  { [ -n "$scan_out" ] && printf '%s\n' "$scan_out"; cat "harness/verify-logs/secrets.err"; } > "harness/verify-logs/secrets.log"
  if [ "$scan_rc" -eq 0 ]; then
    baseline=$(sed -n '/^\[存量棘轮段\]/,/^\[/p' harness/verify-allowlist 2>/dev/null | grep -v '^\[' | grep -v '^#' | grep -v '^$' || true)
    new_hits=""
    while IFS= read -r line; do
      [ -z "$line" ] && continue
      case "$line" in \#*) continue ;; esac
      if printf '%s\n' "$baseline" | grep -qxF "$line"; then
        warn "secrets: $line" "存量已知（见 harness/verify-allowlist）"
      else
        new_hits+="$line"$'\n'
      fi
    done <<<"$scan_out"
    if [ -n "$new_hits" ]; then
      printf '%s' "$new_hits" > "harness/verify-logs/secrets-new.log"
      echo "  → 原因：新增凭证形态命中（文件|键名|次数见 harness/verify-logs/secrets-new.log；值按纪律不读取不回显）"
      fail "secrets" "secrets"
    else
      pass "secrets" "secrets"
      rm -f "harness/verify-logs/secrets-new.log"
    fi
  else
    echo "  → 原因：扫描器自身异常（见 harness/verify-logs/secrets.err）"
    fail "secrets" "secrets"
  fi
else
  skip "secrets" "无 python3；修复：brew install python@3.12 后重跑"
fi

echo "==== verify FAIL=${FAIL} WARN=${WARN} SKIP=${SKIP}（EXIT $(( FAIL > 0 ? 1 : ( STRICT > 0 && ( SKIP > 0 || WARN > 0 ) ? 2 : 0 ) ))）===="
exit $(( FAIL > 0 ? 1 : ( STRICT > 0 && ( SKIP > 0 || WARN > 0 ) ? 2 : 0 ) ))
