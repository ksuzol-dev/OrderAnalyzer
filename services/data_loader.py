import re

import pandas as pd


REQUIRED_FIELDS = {
    "订单编号": ["订单编号", "订单号", "Id", "ID"],
    "SKU": ["商品名", "SKU", "sku", "商品名称", "商品"],
    "支付状态": ["支付状态", "订单状态", "状态"],
    "支付金额": ["支付金额", "实付金额", "金额", "订单金额"],
    "支付完成时间": ["支付完成时间", "支付时间", "付款时间", "完成时间", "更新时间", "订单日期"],
}


def clean_money(value):
    if pd.isna(value):
        return 0.0
    text = str(value).replace(",", "")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    return float(match.group()) if match else 0.0


def is_success(value):
    return "支付成功" in str(value)


def find_col(columns, candidates):
    for candidate in candidates:
        if candidate in columns:
            return candidate
    for column in columns:
        for candidate in candidates:
            if candidate.lower() in str(column).lower():
                return column
    return None


def read_file(uploaded_file):
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        try:
            return pd.read_csv(uploaded_file, encoding="utf-8-sig")
        except UnicodeDecodeError:
            uploaded_file.seek(0)
            return pd.read_csv(uploaded_file, encoding="gbk")
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded_file)
    raise ValueError("目前只支持 CSV / Excel 文件")


def prepare_data(raw):
    columns = list(raw.columns)
    detected = {field: find_col(columns, candidates) for field, candidates in REQUIRED_FIELDS.items()}
    missing = [field for field, column in detected.items() if column is None]
    if missing:
        raise ValueError("缺少必要字段：" + "、".join(missing))

    df = raw.copy()
    success_mask = df[detected["支付状态"]].apply(is_success)
    df = df[success_mask].copy()
    df["订单编号"] = df[detected["订单编号"]].astype(str)
    df["SKU"] = df[detected["SKU"]].fillna("未命名商品").astype(str)
    df["支付金额"] = df[detected["支付金额"]].apply(clean_money)
    df["支付完成时间"] = pd.to_datetime(df[detected["支付完成时间"]], errors="coerce")
    df = df.dropna(subset=["支付完成时间"])
    df["日期"] = df["支付完成时间"].dt.date
    return df, detected
