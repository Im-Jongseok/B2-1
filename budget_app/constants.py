from pathlib import Path


DEFAULT_DATA_DIR = Path('./data')

DEFAULT_CATEGORIES = {
    'food',
    'shopping',
}


class Files:
    TRANSACTIONS = 'transactions.jsonl'
    CATEGORIES   = 'categories.jsonl'
    BUDGETS      = 'budgets.jsonl'


class TxType:
    INCOME  = 'income'
    EXPENSE = 'expense'
    ALL     = (INCOME, EXPENSE)


class TxId:
    PREFIX = 'TX'
    SEP = '-'
    FORMAT = PREFIX + SEP + '{:06d}'


class Prefix:
    ERROR    = '[오류]'
    HINT     = '[힌트]'
    SAVE_OK  = '[저장 완료]'
    INFO     = '[등록된 카테고리]'


class Msg:
    class Error:
        DATE_FORMAT        = '날짜 형식이 올바르지 않습니다.'
        TYPE_INVALID       = 'income 또는 expense만 입력 가능합니다.'
        AMOUNT_NOT_NUM     = '숫자만 입력 가능합니다.'
        AMOUNT_NOT_POS     = '0보다 큰 금액을 입력하세요.'
        CATEGORY_NOT_FOUND = '"{}"은(는) 등록되지 않은 카테고리입니다.'
        CATEGORY_EMPTY     = '카테고리를 입력하세요.'

    class Hint:
        DATE_FORMAT   = '예: 2024-01-15'
        CATEGORY_ADD  = 'category add 명령으로 카테고리를 먼저 등록하세요.'

    class Info:
        CATEGORIES = '{}'
        SAVE_OK    = 'id={}'


class TxField:
    ID       = 'id'
    TYPE     = 'type'
    DATE     = 'date'
    AMOUNT   = 'amount'
    CATEGORY = 'category'
    MEMO     = 'memo'
    TAGS     = 'tags'


class CLI:
    PROG        = 'budget_app'
    DESCRIPTION = '파일 기반 가계부 콘솔 프로그램'

    class Command:
        ADD      = 'add'
        LIST     = 'list'
        SEARCH   = 'search'
        SUMMARY  = 'summary'
        BUDGET   = 'budget'
        CATEGORY = 'category'
        UPDATE   = 'update'
        DELETE   = 'delete'
        EXPORT   = 'export'
        IMPORT   = 'import'
        SET      = 'set'
        REMOVE   = 'remove'

    class Opt:
        DATA_DIR = '--data-dir'
        LIMIT    = '--limit'
        FROM     = '--from'
        TO       = '--to'
        CATEGORY = '--category'
        TYPE     = '--type'
        Q        = '--q'
        TAG      = '--tag'
        MONTH    = '--month'
        TOP      = '--top'
        ID       = '--id'
        OUT      = '--out'
        DATE     = '--date'
        MEMO     = '--memo'
        TAGS     = '--tags'
        AMOUNT   = '--amount'

    class Dest:
        COMMAND        = 'command'
        FROM_DATE      = 'from_date'
        TO_DATE        = 'to_date'
        TX_TYPE        = 'tx_type'
        TX_ID          = 'tx_id'
        FROM_FILE      = 'from_file'
        BUDGET_COMMAND = 'budget_command'
        CAT_COMMAND    = 'cat_command'

    class Default:
        LIMIT = 10
        TOP   = 5

    class Help:
        DATA_DIR     = '데이터 파일 저장 경로 (기본: ./data)'
        COMMAND      = '사용가능한 명령어'
        ADD          = '거래 추가'
        LIST         = '거래 목록 조회'
        SEARCH       = '거래 검색'
        SUMMARY      = '월별 요약'
        BUDGET       = '예산 관리'
        BUDGET_SET   = '예산 설정'
        CATEGORY     = '카테고리 관리'
        CAT_ADD      = '카테고리 추가 (대화형)'
        CAT_LIST     = '카테고리 목록'
        CAT_REMOVE   = '카테고리 삭제 (대화형)'
        UPDATE       = '거래 수정 (옵션 기반)'
        DELETE       = '거래 삭제'
        EXPORT       = 'CSV 내보내기'
        IMPORT       = 'CSV 가져오기'
        LIMIT        = '표시 건수 (기본: 10)'
        TOP          = 'TOP N (기본: 5)'
        MONTH        = 'YYYY-MM'
        AMOUNT       = '예산 금액'
        TX_ID        = '거래 ID'
        OUT          = '출력 파일 경로'
        FROM_DATE    = '시작일 (YYYY-MM-DD)'
        TO_DATE      = '종료일 (YYYY-MM-DD)'
        CATEGORY_ARG = '카테고리'
        TX_TYPE      = '타입'
        KEYWORD      = '메모 키워드'
        TAG          = '태그'
        DATE_ARG     = '변경할 날짜'
        TYPE_ARG     = '변경할 타입'
        CAT_ARG      = '변경할 카테고리'
        AMOUNT_ARG   = '변경할 금액'
        MEMO_ARG     = '변경할 메모'
        TAGS_ARG     = '변경할 태그 (쉼표 구분)'


class Prompt:
    DATE     = '날짜(YYYY-MM-DD): '
    TYPE     = '타입(income/expense): '
    CATEGORY = '카테고리: '
    AMOUNT   = '금액(양수): '
    MEMO     = '메모(선택): '
    TAGS     = '태그(쉼표로 구분, 없으면 엔터): '
