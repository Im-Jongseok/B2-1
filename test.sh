#!/usr/bin/env bash

DATA="/tmp/budget_test_data"
rm -rf "$DATA" && mkdir -p "$DATA"

CMD=(python -m budget_app --data-dir "$DATA")
PASS=0; FAIL=0

green='\033[32m'; red='\033[31m'
bold='\033[1m'; dim='\033[2m'; reset='\033[0m'

_summary() {
    printf "\n══════════════════════════════════\n"
    printf "결과: ${green}%d 통과${reset} / ${red}%d 실패${reset} / 총 %d\n" \
        $PASS $FAIL $((PASS+FAIL))
}
trap '_summary; exit 0' INT TERM

_result() {
    local expect_fail="$1" code="$2"
    local ok=0
    { [ "$expect_fail" = 0 ] && [ $code -eq 0 ]; } && ok=1
    { [ "$expect_fail" = 1 ] && [ $code -ne 0 ]; } && ok=1
    if [ $ok -eq 1 ]; then
        printf "\n${green}✓ PASS${reset}"
        PASS=$((PASS+1))
    else
        printf "\n${red}✗ FAIL  (exit $code)${reset}"
        FAIL=$((FAIL+1))
    fi
    printf "  ${dim}[Enter → 계속  /  ^C → 종료]${reset} "
    [ -t 0 ] && read -r < /dev/tty || echo ""
}

_run() {
    local ef="$1" name="$2" display="$3"; shift 3
    clear
    printf "${bold}━━━ %s${reset}\n" "$name"
    printf "${dim}\$${reset} ${bold}%s${reset}\n\n" "$display"
    "$@" 2>&1; local code=$?
    _result "$ef" $code
}

_run_i() {
    local ef="$1" name="$2" display="$3" input="$4"; shift 4
    clear
    printf "${bold}━━━ %s${reset}\n" "$name"
    printf "${dim}\$${reset} ${bold}%s${reset}\n\n" "$display"

    local cyan=$'\033[96m' rst=$'\033[0m'
    local -a vals=()
    while IFS= read -r line; do vals+=("$line"); done < <(printf '%b' "$input")

    local raw; raw=$(printf '%b' "$input" | "$@" 2>&1)
    local code=$?

    local idx=0 result='' remaining="$raw"
    while [[ "$remaining" == *": "* ]]; do
        result+="${remaining%%": "*}: "
        (( idx < ${#vals[@]} )) && result+="${cyan}${vals[$idx]}${rst}"$'\n'
        (( idx++ ))
        remaining="${remaining#*": "}"
    done
    printf '%s\n' "${result}${remaining}"
    _result "$ef" $code
}

run()       { _run   0 "$@"; }
run_err()   { _run   1 "$@"; }
run_i()     { _run_i 0 "$@"; }
run_err_i() { _run_i 1 "$@"; }
section()   { printf "\n${bold}═══ %s ═══${reset}\n" "$1"; }

list_tx()  { _run 0 "→ list"             "budget_app list"              "${CMD[@]}" list; }
list_rx()  { _run 0 "→ list --recurring" "budget_app list --recurring"  "${CMD[@]}" list --recurring; }
list_cat() { _run 0 "→ category list"    "budget_app category list"     "${CMD[@]}" category list; }

# ── 기본 ──────────────────────────────────────────────────────────
section "기본"
run "help" "budget_app --help" "${CMD[@]}" --help

# ── 카테고리 ──────────────────────────────────────────────────────
section "카테고리"
run_i "category add (hobby)"            "budget_app category add"    "hobby\n"          "${CMD[@]}" category add
list_cat
run_i "category add (entertainment)"    "budget_app category add"    "entertainment\n"  "${CMD[@]}" category add
list_cat
run_i "category remove (entertainment)" "budget_app category remove" "entertainment\n"  "${CMD[@]}" category remove
list_cat

# ── 거래 추가 ─────────────────────────────────────────────────────
section "거래 추가"
run_i "add income 1"  "budget_app add" \
    "2024-01-15\nincome\nsalary\n3000000\n"     "${CMD[@]}" add
run_i "add expense 1" "budget_app add" \
    "2024-01-05\nexpense\ntransport\n45000\n"   "${CMD[@]}" add
run_i "add expense 2" "budget_app add" \
    "2024-01-20\nexpense\nfood\n50000\n"        "${CMD[@]}" add
run_i "add expense 3" "budget_app add" \
    "2024-01-25\nexpense\nshopping\n120000\n"   "${CMD[@]}" add
run_i "add expense 4" "budget_app add" \
    "2024-01-28\nexpense\nutilities\n85000\n"   "${CMD[@]}" add
run_i "add income 2"  "budget_app add" \
    "2024-02-10\nincome\nsalary\n3000000\n"     "${CMD[@]}" add
run_i "add expense 5" "budget_app add" \
    "2024-02-05\nexpense\nhealthcare\n30000\n"  "${CMD[@]}" add
run_i "add expense 6" "budget_app add" \
    "2024-02-15\nexpense\nrent\n500000\n"       "${CMD[@]}" add
run_i "add income 3"  "budget_app add" \
    "2024-03-10\nincome\nsalary\n3200000\n"     "${CMD[@]}" add
run_i "add expense 7" "budget_app add" \
    "2024-03-01\nexpense\nrent\n500000\n"       "${CMD[@]}" add
run_i "add expense 8" "budget_app add" \
    "2024-03-18\nexpense\nfood\n75000\n"        "${CMD[@]}" add
list_tx

# ── 반복 내역 추가 ────────────────────────────────────────────────
section "반복 내역 추가"
run_i "add --recurring 1" "budget_app add --recurring" \
    "income\nsalary\n25\n5000000\n"   "${CMD[@]}" add --recurring
run_i "add --recurring 2" "budget_app add --recurring" \
    "expense\nrent\n1\n400000\n"      "${CMD[@]}" add --recurring
list_rx

# ── 조회 ──────────────────────────────────────────────────────────
section "조회"
run "list"             "budget_app list"             "${CMD[@]}" list
run "list --limit 2"   "budget_app list --limit 2"   "${CMD[@]}" list --limit 2
run "list --recurring" "budget_app list --recurring" "${CMD[@]}" list --recurring
run "category list"    "budget_app category list"    "${CMD[@]}" category list

# ── 검색 ──────────────────────────────────────────────────────────
section "검색"
run "search --type"      "budget_app search --type income"                       "${CMD[@]}" search --type income
run "search --from --to" "budget_app search --from 2024-01-01 --to 2024-01-31"  "${CMD[@]}" search --from 2024-01-01 --to 2024-01-31
run "search --category"  "budget_app search --category salary"                   "${CMD[@]}" search --category salary

# ── 예산 / 요약 ───────────────────────────────────────────────────
section "예산 / 요약"
run "budget set 01"    "budget_app budget set --month 2024-01 --amount 5000000"  "${CMD[@]}" budget set --month 2024-01 --amount 5000000
run "summary"          "budget_app summary --month 2024-01"                      "${CMD[@]}" summary --month 2024-01
run "budget set 02"    "budget_app budget set --month 2024-02 --amount 4000000"  "${CMD[@]}" budget set --month 2024-02 --amount 4000000
run "summary (budget)" "budget_app summary --month 2024-02"                      "${CMD[@]}" summary --month 2024-02

# ── 수정 (거래) ───────────────────────────────────────────────────
section "수정 (거래)"
TX_ID=$("${CMD[@]}" list 2>/dev/null | grep -o 'TX-[0-9]*' | head -1)
run_i "update amount"  "budget_app update --id $TX_ID" \
    "amount\n4000000\n"                  "${CMD[@]}" update --id "$TX_ID"
list_tx
run_i "update date"    "budget_app update --id $TX_ID" \
    "date\n2024-01-16\n"                 "${CMD[@]}" update --id "$TX_ID"
list_tx
run_i "update multi"   "budget_app update --id $TX_ID" \
    "amount date\n5000000\n2024-01-17\n" "${CMD[@]}" update --id "$TX_ID"
list_tx

# ── 수정 (반복 내역) ──────────────────────────────────────────────
section "수정 (반복 내역)"
RX_ID=$("${CMD[@]}" list --recurring 2>/dev/null | grep -o 'RX-[0-9]*' | head -1)
run_i "update recurring day"    "budget_app update --id $RX_ID" \
    "day\n28\n"         "${CMD[@]}" update --id "$RX_ID"
list_rx
run_i "update recurring amount" "budget_app update --id $RX_ID" \
    "amount\n6000000\n" "${CMD[@]}" update --id "$RX_ID"
list_rx
run "apply"   "budget_app apply --month 2024-03" "${CMD[@]}" apply --month 2024-03
list_tx

# ── export / import / backup ───────────────────────────────────────
section "export / import / backup"
run "export --month"  "budget_app export --month 2024-01 --out out.csv" \
    "${CMD[@]}" export --month 2024-01 --out "$DATA/out.csv"
run "export --from"   "budget_app export --from 2024-01-01 --to 2024-01-31 --out out2.csv" \
    "${CMD[@]}" export --from 2024-01-01 --to 2024-01-31 --out "$DATA/out2.csv"
run "import"          "budget_app import --from out.csv" \
    "${CMD[@]}" import --from "$DATA/out.csv"
list_tx
run "backup"  "budget_app backup" "${CMD[@]}" backup

# ── 삭제 ──────────────────────────────────────────────────────────
section "삭제"
TX_ID2=$("${CMD[@]}" list 2>/dev/null | grep -o 'TX-[0-9]*' | head -1)
run_i "delete (n → 취소)" "budget_app delete --id $TX_ID2" \
    "n\n"  "${CMD[@]}" delete --id "$TX_ID2"
run_i "delete (y → 확인)" "budget_app delete --id $TX_ID2" \
    "y\n"  "${CMD[@]}" delete --id "$TX_ID2"
list_tx
RX_ID2=$("${CMD[@]}" list --recurring 2>/dev/null | grep -o 'RX-[0-9]*' | tail -1)
run_i "delete --recurring" "budget_app delete --id $RX_ID2" \
    "y\n"  "${CMD[@]}" delete --id "$RX_ID2"
list_rx

# ── 오류 케이스 ───────────────────────────────────────────────────
section "오류 케이스 (exit 1 예상)"
TX_ID3=$("${CMD[@]}" list 2>/dev/null | grep -o 'TX-[0-9]*' | head -1)

# 존재하지 않는 ID
run_err   "TX not found"           "budget_app update --id TX-999999"    "${CMD[@]}" update --id TX-999999
run_err   "RX not found"           "budget_app delete --id RX-999999"    "${CMD[@]}" delete --id RX-999999

# 삭제 확인 오류
run_err_i "delete invalid confirm" "budget_app delete --id $TX_ID3 [x 입력]" \
    "x\n"  "${CMD[@]}" delete --id "$TX_ID3"

# add 입력 오류 (잘못된 값 이후 EOF → exit 1)
run_err_i "add invalid date"       "budget_app add [날짜 오류]" \
    "9999-99-99\n"                  "${CMD[@]}" add
run_err_i "add invalid type"       "budget_app add [타입 오류]" \
    "2024-01-01\ncash\n"            "${CMD[@]}" add
run_err_i "add amount zero"        "budget_app add [금액=0]" \
    "2024-01-01\nincome\nsalary\n0\n"     "${CMD[@]}" add
run_err_i "add amount negative"    "budget_app add [금액 음수]" \
    "2024-01-01\nincome\nsalary\n-1000\n" "${CMD[@]}" add

# add --recurring 입력 오류
run_err_i "add recurring day=32"   "budget_app add --recurring [day 범위 초과]" \
    "income\nsalary\n32\n"          "${CMD[@]}" add --recurring

# update 변경 없음
run_err_i "update no changes"      "budget_app update --id $TX_ID3 [필드 미입력]" \
    "\n"  "${CMD[@]}" update --id "$TX_ID3"

# 파일 오류
run_err   "import missing file"    "budget_app import --from missing.csv" \
    "${CMD[@]}" import --from "$DATA/missing.csv"

# 카테고리 오류 (중복 → retry → EOF → exit 1)
run_err_i "category add duplicate" "budget_app category add [salary 중복]" \
    "salary\n"  "${CMD[@]}" category add
run_err_i "category remove (used)" "budget_app category remove [salary]" \
    "salary\n"  "${CMD[@]}" category remove

_summary
