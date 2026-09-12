import math

def format_balatro_number(value):
    try:
        f_val = float(value)
        if math.isinf(f_val) or math.isnan(f_val) or f_val > 1.79e308:
            return "naneinf"

        # 1 digit: up to 2 decimal places
        if f_val < 10:
            return f"{f_val:.2f}".rstrip("0").rstrip(".")

        # 2 digits: up to 1 decimal place
        elif f_val < 100:
            return f"{f_val:.1f}".rstrip("0").rstrip(".")

        # 3+ digits: no decimals, rounded
        elif f_val < 1_000_000:
            return str(round(f_val))
    except (ValueError, TypeError, OverflowError):
        pass

    # From here on, handle large integers and check against the 1.79e308 limit
    try:
        val_int = int(value)
        if float(val_int) > 1.79e308:
            return "naneinf"
    except (ValueError, TypeError, OverflowError):
        return "naneinf"

    s = str(val_int)
    exponent = len(s) - 1

    exp_str = f"E{exponent}"
    allowed_mantissa_len = 7 - len(exp_str)

    if allowed_mantissa_len < 3:
        head = int(s[:2])
        rounded = (head + 5) // 10

        if rounded == 10:
            return f"1E{exponent + 1}"

        return f"{rounded}{exp_str}"

    sig_figs = allowed_mantissa_len - 1
    head = int(s[:sig_figs + 1])
    rounded = (head + 5) // 10

    if len(str(rounded)) > sig_figs:
        exponent += 1
        exp_str = f"E{exponent}"
        allowed_mantissa_len = 7 - len(exp_str)

        if allowed_mantissa_len < 3:
            return f"1{exp_str}"

        decimals = "0" * (allowed_mantissa_len - 2)
        return f"1.{decimals}{exp_str}"

    r_str = str(rounded)
    return f"{r_str[0]}.{r_str[1:]}{exp_str}"