from __future__ import annotations

import functools
import json

from .constants import Prefix, Msg


def handle_errors(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            print(f'{Prefix.ERROR} {Msg.Error.FILE_NOT_FOUND.format(e.filename)}')
            print(f'{Prefix.HINT} {Msg.Hint.DATA_DIR}')
            return 1
        except json.JSONDecodeError:
            print(f'{Prefix.ERROR} {Msg.Error.JSON_CORRUPT}')
            print(f'{Prefix.HINT} {Msg.Hint.JSONL_FILE}')
            return 1
        except ValueError as e:
            print(f'{Prefix.ERROR} {e}')
            return 1
        except KeyboardInterrupt:
            print(f'\n{Prefix.INFO} {Msg.Info.INTERRUPTED}')
            return 0
    return wrapper
