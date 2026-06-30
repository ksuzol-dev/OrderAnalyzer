# OrderAnalyzer 订单分析平台

本地运行的订单分析平台，数据不会上传服务器。

## V0.3 Foundation

本版本把 V0.2 的单文件应用整理为更稳定的分析平台结构：

- Dashboard：首页展示今日订单、今日收入、客单价和环比
- 趋势分析：趋势图 + 每日数据表
- SKU 分析：订单数占比、收入占比、TOP10 明细
- 用户分析：预留模块入口
- 数据检查：显示字段、订单数、支付成功数
- V0.3.2：升级为运营后台风格布局，增加卡片式指标、字段识别状态表和统一图表样式

## 启动方式

同事下载 ZIP 后，推荐直接双击：

```text
start.command
```

如果使用终端，需要先进入解压后的项目目录，例如：

```bash
cd ~/Downloads/OrderAnalyzer-0.3.2
python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py
```

更多说明见 `docs/INSTALL.md`。

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

## V0.3.1 新业务线字段

新增标准字段：
- `source_platform`：来源平台
- `vip_id`：VIP ID
- `vip_name`：VIP 名称
- `vip_type`：VIP 类型
- `pay_type`：开通方式

新业务线映射：
- VIP 名称 -> SKU
- 开通价格 -> 支付金额
- 开通时间 -> 支付完成时间
- 支付状态 = 已支付 -> 支付成功订单

## V0.3.3 用户分析

用户分析支持两类表格式：

- VIP / 来源平台表：分析 VIP ID、来源平台、VIP 类型和渠道结构。
- 注册时间 / 班级用户表：分析用户注册时间趋势、班级用户数量和用户明细。

新增标准字段：
- `user_id`：用户 ID
- `user_name`：用户名称
- `user_phone`：用户手机号
- `registration_time`：注册时间
- `class_name`：班级
