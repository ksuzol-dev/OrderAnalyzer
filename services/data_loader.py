import re

import pandas as pd


FIELD_SPECS = {
    "订单编号": ["订单编号", "订单号", "Id", "ID"],
    "产品线": ["产品线", "产品线名称", "业务线", "业务线名称", "项目线"],
    "商品ID": ["商品ID", "商品 ID", "商品编号", "商品编码", "sku_id", "SKU ID", "sku id"],
    "SKU": ["商品名", "SKU", "sku", "商品名称", "商品", "VIP 名称"],
    "支付状态": ["支付状态", "订单状态", "状态"],
    "支付金额": ["支付金额", "实付金额", "金额", "订单金额", "开通价格"],
    "支付完成时间": ["支付完成时间", "支付完成时", "支付时间", "付款时间", "完成时间", "更新时间", "订单日期", "开通时间"],
    "来源平台": ["来源平台", "source_platform"],
    "开通方式": ["开通方式", "pay_type"],
    "VIP ID": ["VIP ID", "vip_id", "会员ID", "会员 ID"],
    "VIP 名称": ["VIP 名称", "vip_name"],
    "VIP 类型": ["VIP 类型", "vip_type"],
    "用户ID": ["用户ID", "用户 ID", "会员ID", "会员 ID", "买家ID", "买家 ID", "用户昵称(ID)"],
    "用户名称": ["用户名称", "用户姓名", "用户昵称", "用户昵称(ID)", "用户名", "姓名", "昵称"],
    "用户手机号": ["用户手机号", "手机号", "手机号码", "用户手机", "联系电话"],
    "注册时间": ["注册时间", "用户注册时间", "账号注册时间", "首次注册时间", "注册日期", "创建时间"],
    "班级": ["班级", "班级名称", "所属班级", "用户班级", "班级用户", "课程班级"],
}

REQUIRED_FIELDS = ["SKU", "支付状态", "支付金额", "支付完成时间"]
OPTIONAL_DEFAULTS = {
    "产品线": "未识别产品线",
    "来源平台": "未识别来源",
    "开通方式": "未识别方式",
    "VIP ID": "",
    "VIP 名称": "",
    "VIP 类型": "",
    "用户ID": "",
    "用户名称": "",
    "用户手机号": "",
    "班级": "未识别班级",
}


def clean_money(value):
    if pd.isna(value):
        return 0.0
    text = str(value).replace(",", "")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    return float(match.group()) if match else 0.0


def clean_id(value):
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if re.fullmatch(r"\d+\.0", text):
        return text[:-2]
    return text


def build_sku_label(name, product_id):
    sku_name = str(name).strip() if not pd.isna(name) else ""
    sku_name = sku_name or "未命名商品"
    clean_product_id = clean_id(product_id)
    if clean_product_id:
        return f"{sku_name}（商品ID: {clean_product_id}）"
    return sku_name


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
    df["商品名"] = df[detected["SKU"]].fillna("未命名商品").astype(str)
    if detected["商品ID"]:
        df["商品ID"] = df[detected["商品ID"]].apply(clean_id)
    else:
        df["商品ID"] = ""
    df["SKU"] = df.apply(lambda row: build_sku_label(row["商品名"], row["商品ID"]), axis=1)
    df["支付金额"] = df[detected["支付金额"]].apply(clean_money)
    df["支付完成时间"] = pd.to_datetime(df[detected["支付完成时间"]], errors="coerce")
    df = df.dropna(subset=["支付完成时间"])
    df["日期"] = df["支付完成时间"].dt.date
    for field, default in OPTIONAL_DEFAULTS.items():
        column = detected[field]
        df[field] = df[column].fillna(default).astype(str) if column else default
    df["source_platform"] = df["来源平台"]
    df["product_line"] = df["产品线"]
    df["product_id"] = df["商品ID"]
    df["product_name"] = df["商品名"]
    df["pay_type"] = df["开通方式"]
    df["vip_id"] = df["VIP ID"]
    df["vip_name"] = df["VIP 名称"].where(df["VIP 名称"].str.len() > 0, df["SKU"])
    df["vip_type"] = df["VIP 类型"]
    df["user_id"] = df["用户ID"].where(df["用户ID"].str.len() > 0, df["vip_id"])
    df["user_name"] = df["用户名称"]
    df["user_phone"] = df["用户手机号"]
    df["class_name"] = df["班级"]
    if detected["注册时间"]:
        df["注册时间"] = pd.to_datetime(df[detected["注册时间"]], errors="coerce")
    else:
        df["注册时间"] = pd.NaT
    df["registration_time"] = df["注册时间"]
    return df, detected
