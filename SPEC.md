# 废钢再生资源实时数据跟踪分析系统 — 技术规格

## 1. 系统架构

### 技术栈
- **框架**: Streamlit (Python Web UI)
- **数据处理**: Pandas, NumPy
- **图表**: Plotly (交互式，支持移动端)
- **Excel 读写**: openpyxl
- **数据存储**: Excel 文件（向后兼容现有流程）

### 文件结构
```
/mnt/agents/output/steel_recycle_app/
├── app.py                    # Streamlit 入口，侧边栏导航，页面路由
├── requirements.txt          # Python 依赖
├── data/                     # 数据存储目录
│   ├── expenses.xlsx         # 费用报销台账
│   ├── purchase.xlsx         # 采购台账
│   └── sales.xlsx            # 出库台账
├── utils/                    # 工具模块
│   ├── data_processor.py     # 核心数据处理引擎
│   ├── excel_handler.py      # Excel 读写操作
│   └── calculators.py        # 业务计算工具
├── views/                    # 页面模块
│   ├── dashboard.py          # 统计看板
│   ├── data_entry.py         # 数据录入
│   ├── cost_analysis.py      # 成本利润分析
│   ├── inventory.py          # 库存管理
│   ├── payments.py           # 付款跟踪
│   └── reports.py            # 报表导出
```

## 2. 数据模型

### 2.1 采购数据 (purchase_df)
| 字段 | 类型 | 说明 |
|------|------|------|
| 日期 | datetime | 采购日期 |
| 月份 | str | YYYY-MM 格式 |
| 车牌 | str | 运输车辆 |
| 供应商 | str | 供货方 |
| 料型 | str | 废钢品种（三级原料、统四、油漆桶、花盒子、二级原料等） |
| 方式 | str | 送厂/自提 |
| 提货净重 | float | 吨 |
| 磅差 | float | 吨 |
| 毛重 | float | 吨 |
| 皮重 | float | 吨 |
| 净重 | float | 吨 |
| 扣杂 | float | 吨 |
| 实际净重 | float | 净重 - 扣杂 |
| 单价 | float | 元/吨 |
| 运费 | float | 元 |
| 扣杂前金额 | float | 元 |
| 扣杂后金额 | float | 元 |
| 未加运费 | float | 元 |
| 实付金额 | float | 元（含运费） |
| 付款人 | str | |
| 付款日期 | datetime | |
| 货车司机 | str | |
| 已付款 | bool | |

### 2.2 出库数据 (sales_df)
| 字段 | 类型 | 说明 |
|------|------|------|
| 出货日期 | datetime | |
| 月份 | str | YYYY-MM |
| 基地 | str | 信阳基地/新郑基地 |
| 收货单位 | str | 钢厂名称 |
| 车牌号 | str | |
| 车皮号 | str | |
| 货物名称 | str | 出库料型 |
| 毛重 | float | 吨 |
| 皮重 | float | 吨 |
| 净重量 | float | 吨 |
| 出厂单价 | float | 元/吨 |
| 出厂金额 | float | 元 |
| 磅差 | float | 吨 |
| 钢厂重量 | float | 吨 |
| 钢厂扣杂 | float | 吨 |
| 钢厂结算重量 | float | 吨 |
| 钢厂结算单价 | float | 元/吨 |
| 罚款 | float | 元（胶条罚款等） |
| 手续费 | float | 元（甩挂费等） |
| 销售金额 | float | 元 |
| 运费单价 | float | 元/吨 |
| 运费金额 | float | 元 |
| 到手金额 | float | 销售金额 - 运费 - 罚款 - 手续费 |
| 备注 | str | |

### 2.3 费用数据 (expenses_df)
| 字段 | 类型 | 说明 |
|------|------|------|
| 日期 | datetime | 单据日期 |
| 月份 | str | YYYY-MM |
| 经手人 | str | |
| 科目 | str | 管理费用/销售费用/制造费用/财务费用 |
| 摘要 | str | 具体用途 |
| 支出 | float | 金额（元） |
| 报销日期 | datetime | |
| 费用类别 | str | 标准化分类：工资、电费、油费、食堂餐费、修理费、差旅费、招待费、办公费、运输费、福利费、税费、低值易耗品 |

## 3. 核心计算逻辑

### 3.1 成本计算
- **采购成本(含运费)**: 实付金额 = 扣杂后金额 + 运费
- **单位采购成本**: 实付金额 / 实际净重
- **加工成本**: 按料型分摊固定成本中的制造费用
- **总成本**: 采购成本 + 运费 + 加工成本分摊

### 3.2 收入计算
- **出厂金额**: 净重量 × 出厂单价
- **钢厂结算金额**: 钢厂结算重量 × 钢厂结算单价 - 罚款 - 手续费
- **到手金额**: 钢厂结算金额 - 运费金额
- **单位到手价**: 到手金额 / 钢厂结算重量

### 3.3 利润计算
- **毛利**: 到手金额 - 采购成本
- **净利润**: 毛利 - 分摊固定成本
- **料型利润**: 按料型汇总的毛利
- **月度利润**: 按月汇总

### 3.4 库存计算
- **期初库存**: 上月余量（用户录入或系统计算）
- **本期入库**: 当月采购实际净重合计
- **本期出库**: 当月出库净重量合计
- **期末库存**: 期初 + 入库 - 出库（按料型分别计算）

## 4. 页面模块规格

### 4.1 统计看板 (dashboard.py)
**功能**: 关键指标一览、时间趋势、料型对比

**关键指标卡**:
- 本月采购总量(吨)
- 本月出库总量(吨)
- 当前库存总量(吨)
- 本月毛利(元)
- 本月固定成本支出(元)
- 本月净利润(元)

**图表**:
1. 月度采购量/出库量趋势折线图 (双Y轴)
2. 各料型采购量柱状图
3. 各料型出货量柱状图
4. 月度利润趋势图
5. 供应商供货量 TOP 10 横向柱状图
6. 收货单位出货量 TOP 10 横向柱状图
7. 费用类别饼图

### 4.2 数据录入 (data_entry.py)
**功能**: 表单录入新数据

**三个子标签页**:
1. **采购录入**: 日期、供应商、料型、重量信息、价格信息、运费
2. **出库录入**: 日期、基地、收货单位、料型、重量、价格、钢厂信息、运费
3. **费用录入**: 日期、经手人、科目、摘要、金额

每个表单提交后追加到对应 Excel sheet，显示成功提示。

### 4.3 成本利润分析 (cost_analysis.py)
**功能**: 深度成本和利润分析

**四个子标签页**:
1. **采购成本分析**: 
   - 各料型采购均价表
   - 各料型运费占比
   - 采购成本时间趋势
2. **销售分析**:
   - 各料型出厂均价、结算均价
   - 各料型扣杂率对比
   - 到手价趋势
3. **利润分析**:
   - 各料型毛利对比表和图
   - 月度毛利/费用/净利润对比
   - 料型利润排名
4. **费用明细**:
   - 按类别的月度费用明细表
   - 费用趋势图
   - 人员工资/电费/油费等单独展示

### 4.4 库存管理 (inventory.py)
**功能**: 库存实时跟踪

**内容**:
1. 上月余量录入/修改（按料型）
2. 各料型库存汇总表：期初、入库、出库、期末
3. 库存预警（期末库存<阈值的料型高亮）
4. 库存料型占比饼图

### 4.5 付款跟踪 (payments.py)
**功能**: 应收应付款管理

**三个子标签页**:
1. **应付账款（供应商）**:
   - 各供应商未付款明细
   - 标记时间、谁收的货、谁的货、多少钱、未付金额
   - 付款状态标记功能
2. **应收账款（收货单位）**:
   - 各收货单位应收款明细
3. **汇总**:
   - 总应付、总应收、净额

### 4.6 报表导出 (reports.py)
**功能**: 导出数据

**导出选项**:
1. 导出完整采购台账 Excel
2. 导出完整出库台账 Excel
3. 导出费用台账 Excel
4. 导出月度分析报表（含图表的Excel）

## 5. 界面设计

### 侧边栏导航
- 标题: "鑫胜隆废钢管理系统 v1.0"
- 导航项: 📊 统计看板、📝 数据录入、💰 成本利润、📦 库存管理、💳 付款跟踪、📤 报表导出
- 底部: 当前日期、版本信息

### 响应式设计
- 手机端自动适配单列布局
- 图表使用 plotly 支持缩放
- 表单使用 st.form 确保移动友好
- 字体大小适中

## 6. 数据持久化

### 读取策略
- 应用启动时读取三个 Excel 文件
- 使用 @st.cache_data(ttl=300) 缓存，5分钟刷新
- 每次写操作后清除缓存并重新加载

### 写入策略
- 新增记录追加到对应 DataFrame
- 使用 openpyxl 写回 Excel（保留原有格式）
- 写完后 st.rerun() 刷新页面

## 7. 接口契约

### data_processor.py 导出函数
```python
def load_all_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """返回 (purchase_df, sales_df, expenses_df)"""

def get_monthly_summary(purchase_df, sales_df, expenses_df) -> pd.DataFrame:
    """返回月度汇总数据"""

def get_inventory_balance(purchase_df, sales_df, opening_stock: dict) -> pd.DataFrame:
    """返回库存平衡表"""

def get_profit_analysis(purchase_df, sales_df, expenses_df) -> pd.DataFrame:
    """返回利润分析数据"""

def get_material_summary(purchase_df, sales_df) -> pd.DataFrame:
    """按料型汇总进出货"""
```

### calculators.py 导出函数
```python
def calc_purchase_cost(row) -> float:
def calc_sales_revenue(row) -> float:
def calc_gross_profit(purchase_row, sales_row) -> float:
def calc_net_profit(gross_profit, expense_allocation) -> float:
```

### excel_handler.py 导出函数
```python
def read_purchase(file_path) -> pd.DataFrame:
def read_sales(file_path) -> pd.DataFrame:
def read_expenses(file_path) -> pd.DataFrame:
def append_to_purchase(file_path, record: dict):
def append_to_sales(file_path, record: dict):
def append_to_expenses(file_path, record: dict):
```
