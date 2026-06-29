# OrderAnalyzer 订单分析平台

本地运行的订单分析平台，数据不会上传服务器。

## V0.3 Foundation

本版本把 V0.2 的单文件应用整理为更稳定的分析平台结构：

- Dashboard：首页展示今日订单、今日收入、客单价和环比
- 趋势分析：趋势图 + 每日数据表
- SKU 分析：订单数占比、收入占比、TOP10 明细
- 用户分析：预留模块入口
- 数据检查：显示字段、订单数、支付成功数

## 启动方式

```bash
cd ~/Documents/OrderAnalyzer/stable/OrderAnalyzer
pip3 install -r requirements.txt
python3 -m streamlit run app.py
```

## 项目结构

```text
OrderAnalyzer/
├── app.py
├── pages/
├── components/
├── services/
├── assets/
├── docs/
├── README.md
├── CHANGELOG.md
├── ROADMAP.md
├── requirements.txt
└── .gitignore
```

## 数据规则

- 只统计支付成功订单
- 支持 CSV / Excel
- 默认使用最新订单日期作为分析基准
- 未选择 SKU 时分析全部 SKU
- 不提交真实订单数据，CSV / Excel / zip 文件已加入 `.gitignore`
