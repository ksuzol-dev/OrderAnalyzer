from datetime import timedelta

import pandas as pd


def build_daily(df):
    if df.empty:
        return pd.DataFrame(columns=["日期", "订单数", "收入", "客单价"])
    daily = (
        df.groupby("日期")
        .agg(订单数=("订单编号", "nunique"), 收入=("支付金额", "sum"))
        .reset_index()
        .sort_values("日期")
    )
    daily["客单价"] = daily.apply(lambda row: row["收入"] / row["订单数"] if row["订单数"] else 0, axis=1)
    return daily


def build_trend_window(daily, latest_date, days):
    start = latest_date - timedelta(days=days - 1)
    base = pd.DataFrame({"日期": pd.date_range(start, latest_date).date})
    trend = base.merge(daily, on="日期", how="left").fillna({"订单数": 0, "收入": 0, "客单价": 0})
    trend["客单价"] = trend.apply(lambda row: row["收入"] / row["订单数"] if row["订单数"] else 0, axis=1)
    return trend


def day_stats(daily, date_value):
    row = daily[daily["日期"] == date_value]
    if row.empty:
        return {"日期": date_value, "订单数": 0, "收入": 0.0, "客单价": 0.0}
    data = row.iloc[0]
    return {
        "日期": date_value,
        "订单数": int(data["订单数"]),
        "收入": float(data["收入"]),
        "客单价": float(data["客单价"]),
    }


def pct_change(current, previous):
    current = float(current or 0)
    previous = float(previous or 0)
    if previous == 0 and current == 0:
        return "0%", "flat", 0.0
    if previous == 0:
        return "+100%", "up", 100.0
    pct = (current - previous) / previous * 100
    sign = "+" if pct >= 0 else ""
    kind = "up" if pct > 0 else "down" if pct < 0 else "flat"
    return f"{sign}{pct:.1f}%", kind, pct


def get_latest_context(daily, selected_skus, selected_product_lines=None):
    latest_date = daily["日期"].max()
    prev_date = latest_date - timedelta(days=1)
    latest = day_stats(daily, latest_date)
    previous = day_stats(daily, prev_date)
    product_lines = selected_product_lines or []
    line_target = "全部产品线" if not product_lines else "、".join(product_lines[:3]) + (" 等" if len(product_lines) > 3 else "")
    sku_target = "全部 SKU" if not selected_skus else "、".join(selected_skus[:3]) + (" 等" if len(selected_skus) > 3 else "")
    target = f"{line_target} / {sku_target}"
    return {
        "latest_date": latest_date,
        "prev_date": prev_date,
        "latest": latest,
        "previous": previous,
        "target": target,
    }


def sku_summary(df):
    if df.empty:
        return pd.DataFrame(columns=["SKU", "订单数", "收入", "订单数占比", "收入占比"])
    summary = (
        df.groupby("SKU")
        .agg(订单数=("订单编号", "nunique"), 收入=("支付金额", "sum"))
        .reset_index()
        .sort_values(["收入", "订单数"], ascending=False)
    )
    order_total = summary["订单数"].sum()
    revenue_total = summary["收入"].sum()
    summary["订单数占比"] = summary["订单数"] / order_total * 100 if order_total else 0
    summary["收入占比"] = summary["收入"] / revenue_total * 100 if revenue_total else 0
    return summary
