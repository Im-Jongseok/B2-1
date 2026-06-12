from __future__ import annotations

import argparse

from datetime import date
from pathlib import Path

from .constants import DEFAULT_DATA_DIR
from .service import BudgetService


""" parser 구축 """
def _build_parser():
    parser = argparse.ArgumentParser(
        prog="budget_app",
        description="파일 기반 가계부 콘솔 프로그램",
    )
    parser.add_argument(
        '--data-dir',
        type=Path, 
        default=DEFAULT_DATA_DIR, 
        help="데이터 파일 저장 경로 (기본: ./data)"
    )

    sub = parser.add_subparsers(dest='command', help='사용가능한 명령어')

    sub.add_parser('add', help='거래 추가')

    return parser

""" 사용자 입력 """
def _input_tx(svc: BudgetService) -> dict:
    tx_date = _ask_date()
    tx_type = _ask_type()
    tx_category = _ask_category(svc)
    tx_amount = _ask_amount()

    return {'date': tx_date, 'type': tx_type, 'category': tx_category, 'amount': tx_amount}
        
def _ask_date() -> str:
    while True:
        raw = input("날짜(YYYY-MM-DD): ").strip()
        try:
            date.fromisoformat(raw)
            return raw
        except ValueError:
            print()

def _ask_type() -> str:
    while True:
        raw = input("타입(income/expense): ").strip().lower()
        if raw in ("income", "expense"):
            return raw


def _ask_category(svc: BudgetService) -> str:
    categories = svc.category_repo.list_categories()
    while True:
        print(f"[등록된 카테고리] {', '.join(categories)}")
        raw = input("카테고리: ").strip().lower()
        if not raw:
            continue
        if raw not in categories:
            continue
        return raw


def _ask_amount() -> int:
    while True:
        raw = input("금액(양수): ").strip()
        try:
            amount = int(raw)
            if amount <= 0:
                continue
            return amount
        except ValueError:
            print()


""" 거레 추가 """
def cmd_add(args: argparse.Namespace) -> int:

    service = BudgetService(args.data_dir)

    tx = _input_tx(service)
    service.add_transaction(**tx)

    return 0

_COMMANDS = {
    'add': cmd_add,
}


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0
    
    handler = _COMMANDS.get(args.command)
    if handler is None:
        return 1
    
    return handler(args)

if __name__ == "__main__":
    main()