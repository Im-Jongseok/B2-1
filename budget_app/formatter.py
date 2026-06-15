from __future__ import annotations

import unicodedata

from .constants import TxType, TxField, Fmt, ColHeader, ColWidth


def display_width(s: str) -> int:
    """터미널 출력 기준 문자열 너비 (한글 등 전각 문자는 2칸으로 계산)"""
    return sum(2 if unicodedata.east_asian_width(c) in ('W', 'F') else 1 for c in s)


def ljust_display(s: str, width: int) -> str:
    return s + ' ' * max(0, width - display_width(s))


def rjust_display(s: str, width: int) -> str:
    return ' ' * max(0, width - display_width(s)) + s


def print_tx(r: dict) -> None:
    tx_type    = TxType.INCOME_KO if r[TxField.TYPE] == TxType.INCOME else TxType.EXPENSE_KO
    amount_str = f"{r[TxField.AMOUNT]:,}{Fmt.CURRENCY}"
    print(
        f"{r[TxField.ID]:<{ColWidth.ID}}{Fmt.COL_SEP}"
        f"{r[TxField.DATE]:<{ColWidth.DATE}}{Fmt.COL_SEP}"
        f"{tx_type}{Fmt.COL_SEP}"
        f"{ljust_display(r[TxField.CATEGORY], ColWidth.CATEGORY)}{Fmt.COL_SEP}"
        f"{rjust_display(amount_str, ColWidth.AMOUNT)}"
    )


def print_tx_header() -> None:
    print(ColWidth.SEP_LINE)
    print(
        f"{ColHeader.ID:<{ColWidth.ID}}{Fmt.COL_SEP}"
        f"{ColHeader.DATE:<{ColWidth.DATE}}{Fmt.COL_SEP}"
        f"{ljust_display(ColHeader.TYPE, ColWidth.TYPE)}{Fmt.COL_SEP}"
        f"{ljust_display(ColHeader.CATEGORY, ColWidth.CATEGORY)}{Fmt.COL_SEP}"
        f"{rjust_display(ColHeader.AMOUNT, ColWidth.AMOUNT)}"
    )
    print(ColWidth.SEP_LINE)
