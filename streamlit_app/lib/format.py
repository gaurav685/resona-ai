def fmt_pct(value: float | None, digits: int = 0) -> str:
    if value is None:
        return "—"
    return f"{value * 100:.{digits}f}%"


def fmt_num(value: float | None, digits: int = 1) -> str:
    if value is None:
        return "—"
    return f"{value:.{digits}f}"


def fmt_reason_code(code: str) -> str:
    return " ".join(w.capitalize() for w in code.split("_"))


def fmt_feature_name(name: str) -> str:
    name = name.removesuffix("_utc")
    return " ".join(w.capitalize() for w in name.split("_"))
