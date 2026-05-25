from datetime import datetime, date

def _expiry_badge(expiry_str):
    if not expiry_str:
        return "expiry-ok", "No Expiry"

    try:
        expiry_dt = datetime.strptime(expiry_str, "%Y-%m-%d").date()
        days_left = (expiry_dt - date.today()).days

        if days_left < 0:
            return "expiry-urgent", "EXPIRED"
        if days_left <= 7:
            return "expiry-urgent", f"{days_left}d left"
        if days_left <= 14:
            return "expiry-warn", f"{days_left}d left"
        return "expiry-ok", f"{days_left}d left"

    except ValueError:
        return "expiry-ok", "No Expiry"


def _lt_badge(listing_type, price=None):
    if listing_type == "sell":
        return "lt-sell", f"💵 RM {float(price):.2f}" if price else "💵 Sell"
    if listing_type == "exchange":
        return "lt-exchange", "🔄 Exchange"
    return "lt-free", "🆓 Free"