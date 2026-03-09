import re

FORBIDDEN = [
    r";",
    r"\blet\b",
    r"\bexternaldata\b",
    r"\bunion\s+\*\b",
    r"\bset\s+query_",
    r"\bfork\b",
]


def guard_fragment(fragment: str, context: str):
    if not fragment:
        return
    for pat in FORBIDDEN:
        if re.search(pat, fragment, re.IGNORECASE):
            raise ValueError(f"KQL safety violation in {context}: pattern '{pat}' found.")


def guard_query_parts(source_func: str, where: str, reduce: str):
    if not re.match(r"^fn_[a-z0-9_]+_v\d+$", source_func):
        raise ValueError(f"Invalid function name: {source_func}")
    guard_fragment(where, "where")
    guard_fragment(reduce, "reduce")
