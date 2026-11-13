"""Per-game versions that fit the Switch NACP display-version field."""
import re


def validate(value):
    value = value.strip()
    if not re.fullmatch(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)', value):
        raise ValueError('Version must be MAJOR.MINOR.PATCH, for example 0.2.1')
    if len(value.encode('utf-8')) > 15:
        raise ValueError('Version must fit the 15-byte Switch display-version limit')
    return value


def next_patch(value):
    major, minor, patch = map(int, validate(value).split('.'))
    return validate(f'{major}.{minor}.{patch + 1}')
