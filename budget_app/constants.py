from pathlib import Path


DEFAULT_DATA_DIR = Path('./data')

DEFAULT_CATEGORIES = [
    'salary', 'food', 'transport', 'rent',
    'shopping', 'utilities', 'healthcare', 'education', 'other',
]


class Files:
    TRANSACTIONS  = 'transactions.jsonl'
    CATEGORIES    = 'categories.jsonl'
    BUDGETS       = 'budgets.jsonl'
    RECURRING     = 'recurring.jsonl'
    EXPORT        = 'transactions.csv'
    BACKUP_DIR    = 'backup'
    BACKUP_TS_FMT = '%Y%m%d_%H%M%S'


class TxType:
    INCOME     = 'income'
    EXPENSE    = 'expense'
    ALL        = (INCOME, EXPENSE)
    INCOME_KO  = '수입'
    EXPENSE_KO = '지출'
    BALANCE_KO = '잔액'


class TxId:
    PREFIX    = 'TX'
    RX_PREFIX = 'RX'
    SEP       = '-'
    FORMAT    = PREFIX + SEP + '{:06d}'
    RX_FORMAT = RX_PREFIX + SEP + '{:06d}'


class TxField:
    ID       = 'id'
    TYPE     = 'type'
    DATE     = 'date'
    AMOUNT   = 'amount'
    CATEGORY = 'category'


class RecurringField:
    ID       = 'id'
    TYPE     = 'type'
    DAY      = 'day'
    CATEGORY = 'category'
    AMOUNT   = 'amount'


class BudgetField:
    MONTH  = 'month'
    AMOUNT = 'amount'


class Prefix:
    ERROR          = '[오류]'
    HINT           = '[힌트]'
    DONE           = '[{} 완료]'
    CATEGORIES     = '[카테고리 목록]'
    INFO           = '[정보]'
    SAVE           = '저장'
    REMOVE         = '삭제'
    BACKUP         = '백업'
    TOP_EXPENSE    = '[카테고리별 지출 TOP {}]'
    WARN           = '[경고]'
    SUMMARY        = '=== {} 월별 요약 ==='
    BUDGET_SECTION = '--- 예산 ---'


class Msg:
    class Error:
        DATE_FORMAT             = '날짜 형식이 올바르지 않습니다.'
        MONTH_FORMAT            = '"{}"은(는) 올바른 월 형식이 아닙니다.'
        TYPE_INVALID            = 'income 또는 expense만 입력 가능합니다.'
        AMOUNT_NOT_NUM          = '숫자만 입력 가능합니다.'
        AMOUNT_NOT_POS          = '0보다 큰 금액을 입력하세요.'
        CATEGORY_NOT_FOUND      = '"{}"은(는) 등록되지 않은 카테고리입니다.'
        CATEGORY_ALREADY_EXIST  = '"{}"은(는) 이미 존재하는 카테고리입니다.'
        CATEGORY_INVALID_CMD    = 'category add / list / remove 중 선택하세요.'
        CATEGORY_USED           = '{} 카테고리를 사용하는 거래가 있어 삭제할 수 없습니다.'
        CATEGORY_EMPTY          = '카테고리를 입력하세요.'
        TX_NOT_FOUND            = '"{}" 거래를 찾을 수 없습니다.'
        NO_CHANGES              = '변경할 항목을 하나 이상 지정하세요.'
        CONFIRM_INVALID         = 'y 또는 n만 입력 가능합니다.'
        BUDGET_INVALID_CMD      = 'budget set 명령을 사용하세요.'
        EXPORT_NO_FILTER        = '--month 또는 --from/--to 조건을 하나 이상 입력하세요.'
        FILE_NOT_FOUND          = '"{}" 파일을 찾을 수 없습니다.'
        JSON_CORRUPT            = '데이터 파일이 손상되었습니다.'
        DAY_INVALID             = '1~31 사이의 숫자를 입력하세요.'
        RECURRING_NOT_FOUND     = '"{}" 반복 내역을 찾을 수 없습니다.'

    class Hint:
        DATE_FORMAT          = '예: 2024-01-15'
        TYPE_INVALID         = '예: income (수입) 또는 expense (지출)'
        AMOUNT               = '예: 50000'
        CATEGORY_LIST        = 'budget_app category list로 현재 카테고리를 조회하세요.'
        CATEGORY_ADD         = 'category add 명령으로 카테고리를 먼저 등록하세요.'
        CATEGORY_USED        = '해당 카테고리를 사용하는 거래를 먼저 삭제하거나 수정하세요.'
        CATEGORY_INVALID_CMD = '예: budget_app category list'
        TX_ID                = '예: TX-000001 (list 명령으로 ID를 확인하세요.)'
        CONFIRM_INVALID      = 'y(삭제) 또는 n(취소)을 입력하세요.'
        BUDGET_INVALID_CMD   = '예: budget_app budget set --month 2024-01 --amount 500000'
        EXPORT_FILTER        = '예: --month 2024-01 또는 --from 2024-01-01 --to 2024-01-31'
        DATA_DIR             = '데이터 디렉토리 또는 파일 경로를 확인하세요.'
        JSONL_FILE           = 'jsonl 파일을 직접 수정했다면 형식을 확인하세요.'
        DAY                  = '예: 25 (매월 25일)'
        RECURRING_ID         = '예: RX-000001 (list --recurring으로 ID를 확인하세요.)'

    class Info:
        SAVE_OK          = 'id={}'
        NO_DATA          = '데이터 없음'
        DELETE_CANCELLED = '삭제를 취소했습니다.'
        INTERRUPTED      = '취소되었습니다.'
        INCOME_TOTAL     = '총수입'
        EXPENSE_TOTAL    = '총지출'
        BALANCE          = '잔  액'
        BUDGET_AMOUNT    = '예산'
        BUDGET_USAGE     = '사용'
        EXPORT_RESULT    = '({} records)'
        IMPORT_IMPORTED  = 'imported'
        IMPORT_SKIPPED   = 'skipped'
        COUNT            = '총 {}건'
        BEFORE           = '[변경 전]'
        AFTER            = '[변경 후]'
        BACKUP_OK        = '경로: {}'
        APPLY_RESULT     = '{} 적용: 생성={}'
        APPLY_SKIPPED    = '중복={}'

    class Warn:
        BUDGET_EXCEEDED = '예산을 {}원 초과했습니다!'
        UNKNOWN_FIELD   = '알 수 없는 필드 무시됨: {}'


class SummaryKey:
    INCOME_TOTAL  = 'income_total'
    EXPENSE_TOTAL = 'expense_total'
    BALANCE       = 'balance'
    TOP_EXPENSE   = 'top_expense'
    BUDGET        = 'budget'


class Confirm:
    YES = 'y'
    NO  = 'n'


class ColHeader:
    ID       = 'ID'
    DATE     = 'DATE'
    TYPE     = '타입'
    CATEGORY = '카테고리'
    AMOUNT   = '금액'


class ColWidth:
    ID       = 9
    DATE     = 10
    TYPE     = 4
    CATEGORY = 12
    AMOUNT   = 12
    SEP      = 59
    SEP_LINE = '-' * SEP


class Fmt:
    CURRENCY       = '원'
    KV_SEP         = '='
    LIST_SEP       = ', '
    COL_SEP        = ' | '
    PERCENT        = '%'
    PERCENT_FACTOR = 100
    MONTHLY_DAY    = '매월 {}일'


class Prompt:
    DATE                    = '날짜(YYYY-MM-DD): '
    TYPE                    = '타입(income/expense): '
    CATEGORY                = '카테고리: '
    UPDATE_FIELDS           = '수정할 필드 (date type category amount, 공백 구분): '
    UPDATE_RECURRING_FIELDS = '수정할 필드 (type day category amount, 공백 구분): '
    DELETE_CONFIRM          = '정말 삭제하시겠습니까? (y/n): '
    AMOUNT                  = '금액(양수): '
    DAY                     = '날짜(매월 몇일, 1-31): '


class CLI:
    PROG          = 'budget_app'
    DESCRIPTION   = '파일 기반 가계부 콘솔 프로그램'
    DATA_DIR_OPT  = '--data-dir'
    DATA_DIR_HELP = '데이터 파일 저장 경로 (기본: ./data)'
    COMMAND_DEST  = 'command'
    COMMAND_HELP  = '사용가능한 명령어'

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
        BACKUP   = 'backup'
        APPLY    = 'apply'

    class Default:
        LIMIT = 10
        TOP   = 5

    class Opt:
        LIMIT     = '--limit'
        FROM      = '--from'
        TO        = '--to'
        CATEGORY  = '--category'
        TYPE      = '--type'
        MONTH     = '--month'
        TOP       = '--top'
        ID        = '--id'
        OUT       = '--out'
        AMOUNT    = '--amount'
        RECURRING = '--recurring'

    class Dest:
        FROM_DATE    = 'from_date'
        TO_DATE      = 'to_date'
        TX_TYPE      = 'tx_type'
        TX_ID        = 'tx_id'
        FROM_FILE    = 'from_file'
        MONTH        = 'month'
        BUDGET_CMD   = 'budget_cmd'
        CATEGORY_CMD = 'category_cmd'

    class Help:
        ADD             = '거래 추가 (--recurring: 반복 내역 등록)'
        LIST            = '거래 목록 조회 (--recurring: 반복 내역 목록)'
        SEARCH          = '거래 검색'
        SUMMARY         = '월별 요약'
        BUDGET          = '예산 관리'
        BUDGET_SET      = '예산 설정'
        CATEGORY        = '카테고리 관리'
        CATEGORY_ADD    = '카테고리 추가 (대화형)'
        CATEGORY_LIST   = '카테고리 목록'
        CATEGORY_REMOVE = '카테고리 삭제 (대화형)'
        UPDATE          = '거래 수정 (옵션 기반)'
        DELETE          = '거래 삭제'
        EXPORT          = 'CSV 내보내기'
        IMPORT          = 'CSV 가져오기'
        BACKUP          = '데이터 백업'
        APPLY           = '반복 내역을 특정 월에 거래로 생성'
        LIMIT           = '표시 건수 (기본: 10)'
        TOP             = 'TOP N (기본: 5)'
        MONTH           = 'YYYY-MM'
        AMOUNT          = '예산 금액'
        TX_ID           = '거래 ID'
        OUT             = '출력 파일 경로'
        FROM_DATE       = '시작일 (YYYY-MM-DD)'
        TO_DATE         = '종료일 (YYYY-MM-DD)'
        TX_TYPE         = '타입'
        CATEGORY_ARG    = '카테고리 필터'
