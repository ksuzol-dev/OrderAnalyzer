# OrderAnalyzer 订单分析平台

本地运行的订单分析平台，数据不会上传服务器。

## V0.2 目标

把原来的单页 MVP 升级成一个更像分析平台的结构：

- 今日概览
- 趋势分析
- SKU分析
- 日期对比
- 数据检查

## 启动方式

```bash
cd ~/Downloads/order_analyzer_mvp
pip3 install -r requirements.txt
python3 -m streamlit run app.py
```

## 数据规则

- 只统计支付成功订单
- 支持 CSV / Excel
- 默认使用最新订单日期作为分析基准
- 未选择 SKU 时分析全部 SKU
