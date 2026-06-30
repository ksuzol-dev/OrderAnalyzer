import re

import pandas as pd


FIELD_SPECS = {
    "订单编号": ["订单编号", "订单号", "Id", "ID"],
    "SKU": ["商品名", "SKU", "sku", "商品名称", "商品", "VIP 名称"],
    "支付状态": ["支付状态", "订单状态", "状态"],
    "支付金额": ["支付金额", "实付金额", "金额", "订单金额", "开通价格"],
    "支付完成时间": ["支付完成时间", "支付时间", "付款时间", "完成时间", "更新时间", "订单日期", "开通时间"],
    "来源平台": ["来源平台", "source_platform"],
    "开通方式": ["开通方式", "pay_type"],
    "VIP ID": ["VIP ID", "vip_id", "会员ID", "会员 ID"],
    "VIP 名称": ["VIP 名称", "vip_name"],
    "VIP 类型": ["VIP 类型", "vip_type"],
}

REQUIRED_FIELDS = ["SKU", "支付状态", "支付金额", "支付完成时间"]
OPTIONAL_DEFAULTS = {
    "来源平台": "未识别来源",
    "开通方式": "未识别方式",
    "VIP ID": "",
    "VIP 名称": "",
    "VIP 类型": "",
}


def clean_money(value):
    if pd.isna(value):
        return 0.0
    text = str(value).replace(",", "")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    return float(match.group()) if match else 0.0


def is_success(value):
    status = str(value).strip()
    return status == "已支付" or "支付成功" in status


def find_col(columns, candidates):
    for candidate in candidates:
        if candidate in columns:
            return candidate
    for column in columns:
        for candidate in candidates:
            if len(candidate) > 2 and candidate.lower() in str(column).lower():
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
    detected = {field: find_col(columns, candidates) for field, candidates in FIELD_SPECS.items()}
    missing = [field for field in REQUIRED_FIELDS if detected[field] is None]
    if missing:
        raise ValueError("缺少必要字段：" + "、".join(missing))

    df = raw.copy()
    success_mask = df[detected["支付状态"]].apply(is_success)
    df = df[success_mask].copy()
    if detected["订单编号"]:
        df["订单编号"] = df[detected["订单编号"]].astype(str)
    else:
        df["订单编号"] = "ROW-" + df.index.astype(str)
    df["SKU"] = df[detected["SKU"]].fillna("未命名商品").astype(str)
    df["支付金额"] = df[detected["支付金额"]].apply(clean_money)
    df["支付完成时间"] = pd.to_datetime(df[detected["支付完成时间"]], errors="coerce")
    df = df.dropna(subset=["支付完成时间"])
    df["日期"] = df["支付完成时间"].dt.date
    for field, default in OPTIONAL_DEFAULTS.items():
        column = detected[field]
        df[field] = df[column].fillna(default).astype(str) if column else default
    df["source_platform"] = df["来源平台"]
    df["pay_type"] = df["开通方式"]
    df["vip_id"] = df["VIP ID"]
    df["vip_name"] = df["VIP 名称"].where(df["VIP 名称"].str.len() > 0, df["SKU"])
    df["vip_type"] = df["VIP 类型"]
    return df, detected
