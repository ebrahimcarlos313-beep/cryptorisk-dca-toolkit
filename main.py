import json
from pathlib import Path

DATA_FILE = Path("toolkit_data.json")


def get_float(prompt: str, default: float | None = None) -> float:
    while True:
        suffix = f" [{default}]" if default is not None else ""
        raw = input(f"{prompt}{suffix}: ").strip()
        if raw == "" and default is not None:
            return default
        try:
            value = float(raw)
            if value < 0:
                print("عدد منفی مجاز نیست. دوباره وارد کنید.")
                continue
            return value
        except ValueError:
            print("لطفاً یک عدد معتبر وارد کنید.")


def load_data() -> dict:
    default_data = {
        "dca_orders": [
            {"price": 65000.0, "amount": 500.0},
            {"price": 58000.0, "amount": 700.0},
        ]
    }
    if not DATA_FILE.exists():
        return default_data
    try:
        with DATA_FILE.open("r", encoding="utf-8") as f:
            loaded = json.load(f)
            if isinstance(loaded, dict) and isinstance(loaded.get("dca_orders"), list):
                return loaded
    except (json.JSONDecodeError, OSError):
        pass
    return default_data


def save_data(data: dict) -> None:
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def profit_calculator() -> None:
    print("\n--- محاسبه سود خالص و کارمزد صرافی ---")
    buy_price = get_float("قیمت خرید ($)", 60000.0)
    sell_price = get_float("قیمت فروش / هدف ($)", 66000.0)
    invest = get_float("مبلغ سرمایه‌گذاری ($)", 1000.0)
    fee_pct = get_float("کارمزد هر طرف معامله (%)", 0.1)

    if buy_price <= 0 or invest <= 0:
        print("قیمت خرید و مبلغ سرمایه‌گذاری باید بزرگ‌تر از صفر باشند.")
        return

    fee_rate = fee_pct / 100.0
    buy_fee = invest * fee_rate
    net_invest = invest - buy_fee
    units = net_invest / buy_price
    gross_proceeds = units * sell_price
    sell_fee = gross_proceeds * fee_rate
    net_proceeds = gross_proceeds - sell_fee
    net_profit = net_proceeds - invest
    roi = (net_profit / invest) * 100.0
    total_fees = buy_fee + sell_fee

    denom = units * (1.0 - fee_rate)
    break_even = (invest / denom) if denom > 0 else 0.0

    print(f"سود / زیان خالص: ${net_profit:,.2f}")
    print(f"بازدهی خالص (ROI): {roi:.2f}%")
    print(f"مجموع کارمزد: ${total_fees:,.2f}")
    print(f"قیمت نقطه‌سربه‌سر: ${break_even:,.2f}")


def dca_planner(data: dict) -> None:
    orders = data["dca_orders"]
    while True:
        print("\n--- برنامه‌ریز خرید پله‌ای (DCA) ---")
        total_invested = 0.0
        total_units = 0.0

        if not orders:
            print("هنوز پله‌ای ثبت نشده است.")
        else:
            for idx, order in enumerate(orders, start=1):
                price = float(order["price"])
                amount = float(order["amount"])
                units = amount / price if price > 0 else 0.0
                total_invested += amount
                total_units += units
                print(f"  {idx}. قیمت: ${price:,.2f} | مبلغ: ${amount:,.2f} | واحد: {units:.6f}")

        avg_price = (total_invested / total_units) if total_units > 0 else 0.0
        print(f"میانگین قیمت خرید: ${avg_price:,.2f}")
        print(f"مجموع سرمایه: ${total_invested:,.2f}")
        print(f"مجموع واحدها: {total_units:.6f}")

        print("\n1) افزودن پله خرید جدید")
        print("2) حذف آخرین پله")
        print("3) محاسبه سود/زیان در قیمت فعلی بازار")
        print("0) بازگشت به منوی اصلی")
        choice = input("انتخاب شما: ").strip()

        if choice == "1":
            price = get_float("قیمت این پله ($)")
            amount = get_float("مبلغ این پله ($)")
            if price > 0 and amount > 0:
                orders.append({"price": price, "amount": amount})
                save_data(data)
                print("پله جدید ذخیره شد.")
            else:
                print("قیمت و مبلغ باید بزرگ‌تر از صفر باشند.")
        elif choice == "2":
            if orders:
                orders.pop()
                save_data(data)
                print("آخرین پله حذف شد.")
            else:
                print("پله‌ای برای حذف وجود ندارد.")
        elif choice == "3":
            current_price = get_float("قیمت فعلی بازار ($)", avg_price if avg_price > 0 else 60000.0)
            current_value = total_units * current_price
            pnl = current_value - total_invested
            print(f"ارزش فعلی سبد: ${current_value:,.2f}")
            print(f"سود / زیان لحظه‌ای: ${pnl:,.2f}")
        elif choice == "0":
            break
        else:
            print("گزینه نامعتبر است.")


def risk_calculator() -> None:
    print("\n--- محاسبه‌گر ریسک و حجم معامله ---")
    balance = get_float("موجودی حساب ($)", 5000.0)
    risk_pct = get_float("درصد ریسک مجاز در هر معامله (%)", 1.5)
    entry = get_float("قیمت ورود ($)", 62000.0)
    stop = get_float("قیمت حد ضرر ($)", 60500.0)
    target = get_float("قیمت حد سود ($)", 66500.0)

    max_risk_usd = balance * (risk_pct / 100.0)
    risk_per_unit = abs(entry - stop)

    if risk_per_unit <= 0 or max_risk_usd <= 0:
        print("فاصله قیمت ورود و حد ضرر باید بزرگ‌تر از صفر باشد.")
        return

    pos_units = max_risk_usd / risk_per_unit
    pos_size_usd = pos_units * entry
    reward_per_unit = abs(target - entry)
    rr = (reward_per_unit / risk_per_unit) if target > 0 else 0.0

    print(f"حداکثر مبلغ ریسک: ${max_risk_usd:,.2f}")
    print(f"حجم معامله ($): ${pos_size_usd:,.2f}")
    print(f"تعداد واحد معامله: {pos_units:.6f}")
    print(f"نسبت ریسک به ریوارد (R:R): {rr:.2f} R")


def main() -> None:
    data = load_data()
    while True:
        print("\n=== Crypto Toolkit (PyCharm Starter) ===")
        print("1. محاسبه سود و کارمزد صرافی")
        print("2. برنامه‌ریز خرید پله‌ای (DCA)")
        print("3. محاسبه ریسک و حجم معامله")
        print("0. خروج")

        choice = input("یک گزینه انتخاب کنید: ").strip()
        if choice == "1":
            profit_calculator()
        elif choice == "2":
            dca_planner(data)
        elif choice == "3":
            risk_calculator()
        elif choice == "0":
            save_data(data)
            print("خروج انجام شد. موفق باشید!")
            break
        else:
            print("گزینه نامعتبر است.")


if __name__ == "__main__":
    main()