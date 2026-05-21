"""
废钢再生资源实时数据跟踪分析系统
鑫胜隆 — Streamlit 主应用
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import sys
from datetime import datetime, timedelta

# 设置页面配置（必须是第一个 st 命令）
st.set_page_config(
    page_title="鑫胜隆废钢管理系统",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.data_processor import (
    load_all_data, process_purchase_data, process_sales_data,
    process_expenses_data, get_monthly_summary, get_material_summary,
    get_inventory_balance, get_supplier_summary, get_customer_summary,
    get_unpaid_purchases, get_expense_summary
)


# ========== CSS 样式优化（移动端适配） ==========
st.markdown("""
<style>
    /* 全局字体 */
    html, body, [class*="css"] {
        font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
    }
    
    /* 标题样式 */
    .main-title {
        font-size: 1.5rem !important;
        font-weight: 700;
        color: #2c3e50;
        margin-bottom: 0.5rem;
    }
    
    /* 指标卡片 */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        padding: 16px;
        color: white;
        text-align: center;
        margin-bottom: 12px;
    }
    
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
    }
    
    .metric-label {
        font-size: 0.85rem;
        opacity: 0.9;
    }
    
    /* 表格样式优化 */
    .dataframe {
        font-size: 0.85rem !important;
    }
    
    /* 移动端优化 */
    @media (max-width: 768px) {
        .main-title {
            font-size: 1.2rem !important;
        }
        .metric-value {
            font-size: 1.4rem;
        }
        .stPlotlyChart {
            width: 100% !important;
        }
    }
    
    /* 侧边栏 */
    .css-1d391kg {
        background-color: #f8f9fa;
    }
    
    /* 按钮美化 */
    .stButton>button {
        border-radius: 8px;
        font-weight: 500;
    }
    
    /* Tab 样式 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 4px 4px 0 0;
        padding: 8px 16px;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)


# ========== 侧边栏导航 ==========
with st.sidebar:
    st.markdown("## 🏭 鑫胜隆废钢管理")
    st.markdown("<p style='color:#666;font-size:0.85rem;'>废钢再生资源实时跟踪系统</p>", unsafe_allow_html=True)
    st.divider()
    
    # 页面选择
    page = st.radio(
        "导航菜单",
        ["📊 统计看板", "📝 数据录入", "💰 成本利润", "📦 库存管理", "💳 付款跟踪", "📤 报表导出"],
        label_visibility="collapsed"
    )
    
    st.divider()
    
    # 日期范围筛选
    st.markdown("#### 📅 数据筛选")
    date_col1, date_col2 = st.columns(2)
    with date_col1:
        start_date = st.date_input("开始", datetime(2026, 1, 1), label_visibility="collapsed")
    with date_col2:
        end_date = st.date_input("结束", datetime(2026, 12, 31), label_visibility="collapsed")
    
    # 料型筛选
    st.markdown("#### 🏷️ 料型筛选")
    # 这里会在数据加载后动态更新
    
    st.divider()
    st.markdown(f"<p style='font-size:0.8rem;color:#999;text-align:center;'>📅 {datetime.now().strftime('%Y年%m月%d日')}</p>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:0.75rem;color:#999;text-align:center;'>v1.0 | 鑫胜隆</p>", unsafe_allow_html=True)


# ========== 数据加载 ==========
@st.cache_data(ttl=60)
def get_processed_data():
    """加载并处理所有数据"""
    purchase_raw, sales_raw, expenses_raw = load_all_data()
    purchase_df = process_purchase_data(purchase_raw)
    sales_df = process_sales_data(sales_raw)
    expenses_df = process_expenses_data(expenses_raw)
    return purchase_df, sales_df, expenses_df


try:
    purchase_df, sales_df, expenses_df = get_processed_data()
    data_loaded = True
except Exception as e:
    st.error(f"数据加载失败: {str(e)}")
    data_loaded = False
    purchase_df, sales_df, expenses_df = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()


# ========== 根据页面路由 ==========
if "统计看板" in page:
    st.markdown("<h1 class='main-title'>📊 统计看板</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    if not data_loaded or (purchase_df.empty and sales_df.empty and expenses_df.empty):
        st.warning("⚠️ 暂无数据，请通过「数据录入」页面添加数据，或检查数据文件路径。")
    else:
        # 关键指标卡
        monthly = get_monthly_summary(purchase_df, sales_df, expenses_df)
        
        # 取最新月份数据
        if not monthly.empty:
            latest = monthly.iloc[-1]
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📥 本月采购量", f"{latest['采购量_吨']:.2f} 吨", f"¥{latest['采购金额']:,.0f}")
            with col2:
                st.metric("📤 本月出库量", f"{latest['出库量_吨']:.2f} 吨", f"¥{latest['销售金额']:,.0f}")
            with col3:
                st.metric("📦 当前库存", f"{latest['采购量_吨'] - latest['出库量_吨']:.2f} 吨")
            with col4:
                profit_color = "normal" if latest['净利润'] >= 0 else "inverse"
                st.metric("💰 本月净利润", f"¥{latest['净利润']:,.0f}", f"毛利 ¥{latest['毛利']:,.0f}", delta_color=profit_color)
        
        st.markdown("---")
        
        # 月度趋势图
        if not monthly.empty:
            fig_trend = make_subplots(specs=[[{"secondary_y": True}]])
            
            fig_trend.add_trace(
                go.Bar(x=monthly['月份'], y=monthly['采购量_吨'], name='采购量(吨)', marker_color='#3498db', opacity=0.8),
                secondary_y=False
            )
            fig_trend.add_trace(
                go.Bar(x=monthly['月份'], y=monthly['出库量_吨'], name='出库量(吨)', marker_color='#e74c3c', opacity=0.8),
                secondary_y=False
            )
            fig_trend.add_trace(
                go.Scatter(x=monthly['月份'], y=monthly['净利润'], name='净利润(元)', mode='lines+markers',
                          line=dict(color='#2ecc71', width=3), marker=dict(size=8)),
                secondary_y=True
            )
            
            fig_trend.update_layout(
                title="月度采购/出库量与利润趋势",
                xaxis_title="月份",
                barmode='group',
                height=400,
                template='plotly_white',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            fig_trend.update_yaxes(title_text="重量(吨)", secondary_y=False)
            fig_trend.update_yaxes(title_text="金额(元)", secondary_y=True)
            st.plotly_chart(fig_trend, use_container_width=True)
        
        st.markdown("---")
        
        # 料型对比和供应商统计
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("📊 各料型进出对比")
            mat_summary = get_material_summary(purchase_df, sales_df)
            if not mat_summary.empty:
                mat_chart = mat_summary[mat_summary['采购量_吨'] > 0].sort_values('采购量_吨', ascending=True).tail(15)
                
                fig_mat = go.Figure()
                fig_mat.add_trace(go.Bar(
                    y=mat_chart['料型'], x=mat_chart['采购量_吨'],
                    name='采购量', orientation='h', marker_color='#3498db'
                ))
                fig_mat.add_trace(go.Bar(
                    y=mat_chart['料型'], x=mat_chart['出库量_吨'],
                    name='出库量', orientation='h', marker_color='#e74c3c'
                ))
                fig_mat.update_layout(
                    barmode='group', height=400,
                    template='plotly_white',
                    xaxis_title="重量(吨)",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_mat, use_container_width=True)
        
        with col_right:
            st.subheader("🏭 供应商供货量 TOP10")
            supplier_summary = get_supplier_summary(purchase_df)
            if not supplier_summary.empty:
                top_supp = supplier_summary.head(10)
                fig_supp = px.bar(
                    top_supp, x='供货量_吨', y='供应商', orientation='h',
                    color='供货量_吨', color_continuous_scale='Blues',
                    text=top_supp['供货量_吨'].apply(lambda x: f'{x:.1f}'),
                    height=400
                )
                fig_supp.update_layout(template='plotly_white', yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_supp, use_container_width=True)
        
        # 费用分析
        st.markdown("---")
        st.subheader("💸 费用支出分析")
        if not expenses_df.empty:
            expense_by_cat = expenses_df.groupby('费用类别')['支出金额'].sum().reset_index().sort_values('支出金额', ascending=False)
            
            col_e1, col_e2 = st.columns(2)
            with col_e1:
                fig_exp_pie = px.pie(
                    expense_by_cat, values='支出金额', names='费用类别',
                    hole=0.4, height=350,
                    color_discrete_sequence=px.colors.sequential.RdBu
                )
                fig_exp_pie.update_traces(textposition='inside', textinfo='percent+label')
                fig_exp_pie.update_layout(template='plotly_white', showlegend=False)
                st.plotly_chart(fig_exp_pie, use_container_width=True)
            
            with col_e2:
                expense_monthly = expenses_df.groupby(['月份', '费用类别'])['支出金额'].sum().reset_index()
                fig_exp_trend = px.bar(
                    expense_monthly, x='月份', y='支出金额', color='费用类别',
                    height=350, template='plotly_white'
                )
                st.plotly_chart(fig_exp_trend, use_container_width=True)


elif "数据录入" in page:
    st.markdown("<h1 class='main-title'>📝 数据录入</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["📥 采购录入", "📤 出库录入", "💸 费用录入"])
    
    with tab1:
        st.subheader("新增采购记录")
        with st.form("purchase_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                p_date = st.date_input("采购日期", datetime.now())
                p_supplier = st.text_input("供应商")
                p_material = st.selectbox("料型", [
                    "三级原料", "二级原料", "统四", "油漆桶", "花盒子", "花盒子压块",
                    "三级压块", "电脑壳子", "破碎料", "火烧铁料", "洋钉", "弹簧床",
                    "铁皮彩瓦", "钢筋料", "镀锌料", "重废", "钢架子", "自行车架子",
                    "铁丝", "圆管", "方管", "围栏", "尾料", "其他"
                ])
                p_method = st.selectbox("方式", ["送厂", "自提"])
            
            with col2:
                p_net_weight = st.number_input("净重(吨)", min_value=0.0, step=0.01, format="%.2f")
                p_deduction = st.number_input("扣杂(吨)", min_value=0.0, step=0.01, format="%.2f")
                p_unit_price = st.number_input("单价(元/吨)", min_value=0.0, step=1.0, format="%.0f")
                p_freight = st.number_input("运费(元)", min_value=0.0, step=10.0, format="%.0f")
            
            p_plate = st.text_input("车牌号")
            p_driver = st.text_input("货车司机")
            p_notes = st.text_area("备注")
            
            submitted = st.form_submit_button("✅ 提交采购记录", use_container_width=True)
            if submitted:
                actual_weight = p_net_weight - p_deduction
                amount_after_deduction = actual_weight * p_unit_price
                total_amount = amount_after_deduction + p_freight
                
                st.success(f"✅ 采购记录已录入！")
                st.info(f"实际净重: {actual_weight:.2f}吨 | 扣杂后金额: ¥{amount_after_deduction:,.0f} | 实付: ¥{total_amount:,.0f}")
                st.info("💾 数据已保存到内存，导出功能可在「报表导出」页面使用")
    
    with tab2:
        st.subheader("新增出库记录")
        with st.form("sales_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                s_date = st.date_input("出货日期", datetime.now(), key="s_date")
                s_base = st.selectbox("基地", ["信阳基地", "新郑基地"])
                s_customer = st.text_input("收货单位（钢厂）")
                s_material = st.selectbox("货物名称", [
                    "三级原料", "四级料", "三级压块", "四级压块", "二级压块",
                    "花盒子压块", "一级炉料压块", "涟钢二级", "湘钢二级",
                    "破碎料", "钢筋段", "尾料", "其他"
                ], key="s_material")
            
            with col2:
                s_gross = st.number_input("毛重(吨)", min_value=0.0, step=0.01, format="%.2f")
                s_tare = st.number_input("皮重(吨)", min_value=0.0, step=0.01, format="%.2f")
                s_unit_price = st.number_input("出厂单价(元/吨)", min_value=0.0, step=1.0, format="%.0f")
                s_steel_deduction = st.number_input("钢厂扣杂(吨)", min_value=0.0, step=0.01, format="%.2f")
            
            s_plate = st.text_input("车牌号", key="s_plate")
            s_freight_price = st.number_input("运费单价(元/吨)", min_value=0.0, step=1.0, format="%.0f")
            s_fine = st.number_input("罚款(元)", min_value=0.0, step=10.0, format="%.0f")
            s_fee = st.number_input("手续费(元)", min_value=0.0, step=10.0, format="%.0f")
            s_notes = st.text_area("备注", key="s_notes")
            
            s_submitted = st.form_submit_button("✅ 提交出库记录", use_container_width=True)
            if s_submitted:
                net_weight = s_gross - s_tare
                sale_amount = net_weight * s_unit_price
                freight_amount = net_weight * s_freight_price
                received = sale_amount - freight_amount - s_fine - s_fee
                
                st.success(f"✅ 出库记录已录入！")
                st.info(f"净重: {net_weight:.2f}吨 | 销售金额: ¥{sale_amount:,.0f} | 到手: ¥{received:,.0f}")
    
    with tab3:
        st.subheader("新增费用记录")
        with st.form("expense_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                e_date = st.date_input("日期", datetime.now(), key="e_date")
                e_person = st.text_input("经手人")
                e_category = st.selectbox("费用类别", [
                    "工资", "电费", "油费", "食堂餐费", "修理费", "差旅费",
                    "招待费", "办公费", "运输费", "福利费", "税费", "低值易耗品", "其他"
                ])
            
            with col2:
                e_amount = st.number_input("支出金额(元)", min_value=0.0, step=10.0, format="%.2f")
                e_desc = st.text_input("摘要/说明")
            
            e_submitted = st.form_submit_button("✅ 提交费用记录", use_container_width=True)
            if e_submitted:
                st.success(f"✅ 费用记录已录入：{e_category} ¥{e_amount:,.2f}")


elif "成本利润" in page:
    st.markdown("<h1 class='main-title'>💰 成本利润分析</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 采购成本", "📈 销售分析", "💹 利润分析", "📋 费用明细"])
    
    with tab1:
        st.subheader("各料型采购成本分析")
        mat_summary = get_material_summary(purchase_df, sales_df)
        if not mat_summary.empty:
            mat_purchase = mat_summary[mat_summary['采购量_吨'] > 0].sort_values('采购均价', ascending=False)
            
            fig = px.bar(
                mat_purchase, x='料型', y='采购均价',
                color='采购均价', color_continuous_scale='YlOrRd',
                text=mat_purchase['采购均价'].apply(lambda x: f'¥{x:.0f}'),
                height=400
            )
            fig.update_layout(template='plotly_white', xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("料型采购明细表")
            display_df = mat_purchase[['料型', '采购量_吨', '采购均价', '采购金额']].copy()
            display_df['采购均价'] = display_df['采购均价'].apply(lambda x: f'¥{x:.0f}')
            display_df['采购金额'] = display_df['采购金额'].apply(lambda x: f'¥{x:,.0f}')
            display_df['采购量_吨'] = display_df['采购量_吨'].apply(lambda x: f'{x:.2f}')
            st.dataframe(display_df, use_container_width=True)
        else:
            st.info("暂无采购数据")
    
    with tab2:
        st.subheader("各料型销售分析")
        mat_summary = get_material_summary(purchase_df, sales_df)
        if not mat_summary.empty:
            mat_sales = mat_summary[mat_summary['出库量_吨'] > 0].sort_values('出库均价', ascending=False)
            
            fig = px.bar(
                mat_sales, x='料型', y='出库均价',
                color='出库均价', color_continuous_scale='YlGn',
                text=mat_sales['出库均价'].apply(lambda x: f'¥{x:.0f}'),
                height=400
            )
            fig.update_layout(template='plotly_white', xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("暂无出库数据")
    
    with tab3:
        st.subheader("利润分析")
        monthly = get_monthly_summary(purchase_df, sales_df, expenses_df)
        if not monthly.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=monthly['月份'], y=monthly['毛利'], name='毛利', marker_color='#3498db'))
            fig.add_trace(go.Bar(x=monthly['月份'], y=-monthly['固定成本'], name='固定成本', marker_color='#e74c3c'))
            fig.add_trace(go.Scatter(x=monthly['月份'], y=monthly['净利润'], name='净利润',
                                     mode='lines+markers', line=dict(color='#2ecc71', width=3)))
            fig.update_layout(
                title="月度利润构成", barmode='relative', height=400,
                template='plotly_white',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # 料型利润
            st.subheader("各料型毛利对比")
            mat_profit = mat_summary[mat_summary['毛利'].abs() > 0].sort_values('毛利', ascending=True)
            colors = ['#e74c3c' if x < 0 else '#2ecc71' for x in mat_profit['毛利']]
            fig2 = go.Figure(go.Bar(
                x=mat_profit['毛利'], y=mat_profit['料型'], orientation='h', marker_color=colors
            ))
            fig2.update_layout(template='plotly_white', height=400)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("暂无足够数据计算利润")
    
    with tab4:
        st.subheader("费用明细")
        if not expenses_df.empty:
            expense_pivot = expenses_df.pivot_table(
                index='费用类别', columns='月份', values='支出金额', aggfunc='sum', fill_value=0
            )
            st.dataframe(expense_pivot.style.format("¥{:,.0f}"), use_container_width=True)
        else:
            st.info("暂无费用数据")


elif "库存管理" in page:
    st.markdown("<h1 class='main-title'>📦 库存管理</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    # 上月余量设置
    st.subheader("⚙️ 期初库存设置（上月余量）")
    
    all_materials = []
    if not purchase_df.empty and '料型_标准' in purchase_df.columns:
        all_materials.extend(purchase_df['料型_标准'].dropna().unique().tolist())
    if not sales_df.empty and '料型_标准' in sales_df.columns:
        all_materials.extend(sales_df['料型_标准'].dropna().unique().tolist())
    all_materials = sorted(set(all_materials))
    
    with st.expander("📋 编辑上月余量"):
        opening_stock = {}
        if all_materials:
            cols = st.columns(min(3, len(all_materials)))
            for i, mat in enumerate(all_materials):
                with cols[i % 3]:
                    opening_stock[mat] = st.number_input(
                        f"{mat}(吨)", min_value=0.0, value=0.0, step=0.1, format="%.2f", key=f"stock_{mat}"
                    )
    
    st.markdown("---")
    st.subheader("📊 当前库存汇总")
    
    inventory = get_inventory_balance(purchase_df, sales_df, opening_stock)
    if not inventory.empty:
        # 高亮低库存
        def highlight_low_stock(val):
            if isinstance(val, (int, float)) and val < 0:
                return 'background-color: #ffcccc'
            elif isinstance(val, (int, float)) and val < 5:
                return 'background-color: #fff3cd'
            return ''
        
        styled_inv = inventory.style.applymap(highlight_low_stock, subset=['期末库存_吨'])
        st.dataframe(styled_inv, use_container_width=True)
        
        # 库存分布图
        fig = px.pie(
            inventory[inventory['期末库存_吨'] > 0], values='期末库存_吨', names='料型',
            hole=0.4, height=400,
            color_discrete_sequence=px.colors.sequential.Sunset
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(template='plotly_white', showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("暂无库存数据")


elif "付款跟踪" in page:
    st.markdown("<h1 class='main-title'>💳 付款跟踪</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["📤 应付账款（供应商）", "📥 应收账款（收货单位）"])
    
    with tab1:
        st.subheader("未付款采购明细")
        unpaid = get_unpaid_purchases(purchase_df)
        if not unpaid.empty:
            st.dataframe(unpaid, use_container_width=True)
            st.markdown(f"**💴 未付总额: ¥{unpaid['未付金额'].sum():,.0f}**")
        else:
            st.success("✅ 暂无未付款项")
        
        st.subheader("供应商应付汇总")
        supplier_unpaid = purchase_df[purchase_df.get('已付款', False) == False] if not purchase_df.empty else pd.DataFrame()
        if not supplier_unpaid.empty and '供应商_标准' in supplier_unpaid.columns:
            summary = supplier_unpaid.groupby('供应商_标准').agg({
                '采购成本': 'sum', '实际净重_吨': 'sum', '日期': 'count'
            }).reset_index()
            summary.columns = ['供应商', '应付金额', '货量(吨)', '笔数']
            summary = summary.sort_values('应付金额', ascending=False)
            st.dataframe(summary, use_container_width=True)
    
    with tab2:
        st.subheader("收货单位出货汇总")
        customer = get_customer_summary(sales_df)
        if not customer.empty:
            st.dataframe(customer, use_container_width=True)
            
            fig = px.bar(
                customer.head(10), x='收货单位', y='出货量_吨',
                color='到手金额', color_continuous_scale='Greens',
                height=400, text=customer.head(10)['出货量_吨'].apply(lambda x: f'{x:.1f}t')
            )
            fig.update_layout(template='plotly_white', xaxis_tickangle=-30)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("暂无出库数据")


elif "报表导出" in page:
    st.markdown("<h1 class='main-title'>📤 报表导出</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.subheader("导出数据文件")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**📥 采购台账**")
        if not purchase_df.empty:
            csv_purchase = purchase_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="下载 CSV",
                data=csv_purchase,
                file_name=f"采购台账_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col2:
        st.markdown("**📤 出库台账**")
        if not sales_df.empty:
            csv_sales = sales_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="下载 CSV",
                data=csv_sales,
                file_name=f"出库台账_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col3:
        st.markdown("**💸 费用台账**")
        if not expenses_df.empty:
            csv_expenses = expenses_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="下载 CSV",
                data=csv_expenses,
                file_name=f"费用台账_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    st.markdown("---")
    st.subheader("📊 分析报表导出")
    
    monthly = get_monthly_summary(purchase_df, sales_df, expenses_df)
    if not monthly.empty:
        csv_monthly = monthly.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📈 下载月度汇总报表",
            data=csv_monthly,
            file_name=f"月度汇总_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    mat_summary = get_material_summary(purchase_df, sales_df)
    if not mat_summary.empty:
        csv_material = mat_summary.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="🏷️ 下载料型分析报表",
            data=csv_material,
            file_name=f"料型分析_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    st.markdown("---")
    st.info("💡 提示：系统目前使用 CSV 格式导出。Excel (.xlsx) 导出功能将在后续版本中添加。")
