def format_balatro_number(value):
    # Ensure we are working with an integer to avoid native float scientific notation
    val_int = int(value)
    
    if val_int < 1_000_000:
        return str(val_int)
        
    s = str(val_int)
    exponent = len(s) - 1
    
    if exponent >= 99999:
        return "9E99999"
        
    exp_str = f"E{exponent}"
    allowed_mantissa_len = 7 - len(exp_str)
    
    if allowed_mantissa_len < 3:
        head = int(s[:2])
        rounded = (head + 5) // 10
        if rounded == 10:
            return f"1E{exponent + 1}"
        return f"{rounded}{exp_str}"
    else:
        sig_figs = allowed_mantissa_len - 1
        head = int(s[:sig_figs + 1])
        rounded = (head + 5) // 10
        
        if len(str(rounded)) > sig_figs:
            exponent += 1
            exp_str = f"E{exponent}"
            allowed_mantissa_len = 7 - len(exp_str)
            
            if allowed_mantissa_len < 3:
                return f"1{exp_str}"
            else:
                decimals = "0" * (allowed_mantissa_len - 2)
                return f"1.{decimals}{exp_str}"
        else:
            r_str = str(rounded)
            return f"{r_str[0]}.{r_str[1:]}{exp_str}"