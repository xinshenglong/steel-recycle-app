"""
核心数据处理引擎
负责读取、清洗、汇总所有业务数据
"""
import pandas as pd
import numpy as np
import streamlit as st
from .excel_handler import read_purchase, read_sales, read_expenses

# 全局料型标准化映射
MATERIAL_MAPPING = {
    '三级原料': '三级原料', '三级': '三级原料', '3级原料': '三级原料',
    '二级原料': '二级原料', '二级': '二级原料', '2级原料': '二级原料',
    '统四': '统四', '统料': '统四', '统料四': '统四',
    '油漆桶': '油漆桶', '油桶': '油漆桶',
    '花盒子': '花盒子', '花盒': '花盒子',
    '花盒子压块': '花盒子压块',
    '三级压块': '三级压块',
    '电脑壳子': '电脑壳子', '电脑壳': '电脑壳子',
    '破碎料': '破碎料', '破碎': '破碎料',
    '火烧铁料': '火烧铁料', '火烧铁': '火烧铁料',
    '洋钉': '洋钉',
    '弹簧床': '弹簧床',
    '铁皮彩瓦': '铁皮彩瓦', '彩瓦': '铁皮彩瓦', '纯彩瓦': '铁皮彩瓦',
    '钢筋料': '钢筋料', '钢筋': '钢筋料', '钢筋段': '钢筋料',
    '镀锌料': '镀锌料', '镀锌': '镀锌料',
    '重废': '重废',
    '钢架子': '钢架子', '铁架子': '钢架子',
    '自行车架子': '自行车架子',
    '铁丝': '铁丝',
    '圆管': '圆管',
    '方管': '方管',
    '围栏': '围栏',
    '岩棉接板': '岩棉接板',
    '电瓶车壳子': '电瓶车壳子',
    '尾料': '尾料',
    '涟钢二级': '涟钢二级', '湘钢二级': '湘钢二级', '二级压块': '二级压块',
    '四级料': '四级料', '四级': '四级料',
    '四级压块': '四级压块',
    '一级炉料压块': '一级炉料压块',
}


def _normalize_material(name):
    """标准化料型名称"""
    if pd.isna(name):
        return '其他'
    name = str(name).strip()
    for key, val in MATERIAL_MAPPING.items():
        if key in name:
            return val
    return name


def _safe_numeric(val, default=0):
    """安全转换为数值"""
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


@st.cache_data(ttl=300)
def load_all_data():
    """加载所有数据，返回 (purchase_df, sales_df, expenses_df)"""
    purchase_df = read_purchase()
    sales_df = read_sales()
    expenses_df = read_expenses()
    return purchase_df, sales_df, expenses_df


def process_purchase_data(purchase_df):
    """处理采购数据，添加衍生字段"""
    if purchase_df.empty:
        return purchase_df
    
    df = purchase_df.copy()
    
    # 标准化料型
    material_col = None
    for col in df.columns:
        if '料型' in str(col):
            material_col = col
            break
    if material_col:
        df['料型_标准'] = df[material_col].apply(_normalize_material)
    else:
        df['料型_标准'] = '其他'
    
    # 数值列转换
    numeric_cols = ['净重', '实际净重', '扣杂', '单价', '运费', '扣杂前金额', '扣杂后金额', '实付金额']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # 计算实际净重（如果没有）
    if '实际净重' in df.columns:
        df['实际净重_吨'] = df['实际净重']
    elif '净重' in df.columns and '扣杂' in df.columns:
        df['实际净重_吨'] = df['净重'] - df['扣杂']
    else:
        df['实际净重_吨'] = 0
    
    # 采购成本（含运费）
    if '实付金额' in df.columns:
        df['采购成本'] = df['实付金额']
    elif '扣杂后金额' in df.columns:
        df['采购成本'] = df['扣杂后金额'] + df.get('运费', 0)
    else:
        df['采购成本'] = 0
    
    # 单位成本
    df['单位成本'] = df.apply(
        lambda r: r['采购成本'] / r['实际净重_吨'] if r['实际净重_吨'] > 0 else 0, axis=1
    )
    
    # 供应商标准化
    if '供应商' in df.columns:
        df['供应商_标准'] = df['供应商'].astype(str).str.strip()
    
    # 付款状态
    if '付款人' in df.columns:
        df['已付款'] = df['付款人'].notna() & (df['付款人'].astype(str).str.strip() != '')
    else:
        df['已付款'] = False
    
    df['未付金额'] = df.apply(
        lambda r: 0 if r['已付款'] else r['采购成本'], axis=1
    )
    
    return df


def process_sales_data(sales_df):
    """处理出库数据，添加衍生字段"""
    if sales_df.empty:
        return sales_df
    
    df = sales_df.copy()
    
    # 数值列转换
    numeric_cols_map = {
        '毛重': 0, '皮重': 0, '净重量': 0, '出厂单价': 0, '出厂金额': 0,
        '磅差': 0, '钢厂重量': 0, '钢厂扣杂': 0, '钢厂结算重量': 0,
        '钢厂结算单价': 0, '罚款': 0, '手续费': 0, '销售金额': 0,
        '运费单价': 0, '运费金额': 0
    }
    
    for col, default in numeric_cols_map.items():
        for actual_col in df.columns:
            if col in str(actual_col) or str(actual_col) in col:
                df[col] = pd.to_numeric(df[actual_col], errors='coerce').fillna(default)
                break
    
    # 如果找不到标准列名，尝试模糊匹配
    col_map = {}
    for std_col in numeric_cols_map.keys():
        for actual_col in df.columns:
            ac = str(actual_col).replace('\\n', '').replace(' ', '')
            sc = std_col.replace('\\n', '').replace(' ', '')
            if sc in ac or ac in sc:
                col_map[std_col] = actual_col
                break
    
    for std_col, actual_col in col_map.items():
        if std_col not in df.columns:
            df[std_col] = pd.to_numeric(df[actual_col], errors='coerce').fillna(0)
    
    # 确保数值列存在
    for col in numeric_cols_map:
        if col not in df.columns:
            df[col] = 0
    
    # 标准料型
    if '货物名称' in df.columns:
        df['料型_标准'] = df['货物名称'].apply(_normalize_material)
    else:
        df['料型_标准'] = '其他'
    
    # 到手金额 = 销售金额 - 运费 - 罚款 - 手续费
    df['到手金额'] = df['销售金额'] - df['运费金额'].fillna(0) - df['罚款'].fillna(0) - df['手续费'].fillna(0)
    
    # 收货单位
    if '收货单位' in df.columns:
        df['收货单位_标准'] = df['收货单位'].astype(str).str.strip()
    
    # 基地
    if '基地' in df.columns:
        df['基地_标准'] = df['基地'].astype(str).str.strip()
    
    return df


def process_expenses_data(expenses_df):
    """处理费用数据"""
    if expenses_df.empty:
        return expenses_df
    
    df = expenses_df.copy()
    
    # 确保支出金额为数值
    if '支出金额' not in df.columns:
        for col in df.columns:
            if '支出' in str(col):
                df['支出金额'] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                break
    if '支出金额' not in df.columns:
        df['支出金额'] = 0
    
    # 月份
    if '月份' not in df.columns and '日期' in df.columns:
        df['月份'] = df['日期'].apply(lambda x: x.strftime('%Y-%m') if pd.notna(x) else None)
    
    # 费用类别已在 excel_handler 中标准化
    if '费用类别' not in df.columns:
        df['费用类别'] = '其他'
    
    return df


def get_monthly_summary(purchase_df, sales_df, expenses_df):
    """获取月度汇总数据"""
    months = set()
    for df in [purchase_df, sales_df, expenses_df]:
        if not df.empty and '月份' in df.columns:
            months.update(df['月份'].dropna().unique())
    
    months = sorted(list(months))
    
    summary = []
    for month in months:
        row = {'月份': month}
        
        # 采购数据
        p_month = purchase_df[purchase_df['月份'] == month] if not purchase_df.empty else pd.DataFrame()
        row['采购量_吨'] = p_month['实际净重_吨'].sum() if not p_month.empty else 0
        row['采购金额'] = p_month['采购成本'].sum() if not p_month.empty else 0
        row['采购车次'] = len(p_month) if not p_month.empty else 0
        
        # 出库数据
        s_month = sales_df[sales_df['月份'] == month] if not sales_df.empty else pd.DataFrame()
        row['出库量_吨'] = s_month['净重量'].sum() if not s_month.empty else 0
        row['销售金额'] = s_month['销售金额'].sum() if not s_month.empty else 0
        row['到手金额'] = s_month['到手金额'].sum() if not s_month.empty else 0
        row['出库车次'] = len(s_month) if not s_month.empty else 0
        
        # 费用数据
        e_month = expenses_df[expenses_df['月份'] == month] if not expenses_df.empty else pd.DataFrame()
        row['固定成本'] = e_month['支出金额'].sum() if not e_month.empty else 0
        
        # 利润
        row['毛利'] = row['到手金额'] - row['采购金额']
        row['净利润'] = row['毛利'] - row['固定成本']
        
        summary.append(row)
    
    return pd.DataFrame(summary)


def get_material_summary(purchase_df, sales_df):
    """按料型汇总进出货"""
    result = []
    
    # 获取所有料型
    p_materials = set()
    s_materials = set()
    if not purchase_df.empty and '料型_标准' in purchase_df.columns:
        p_materials = set(purchase_df['料型_标准'].dropna().unique())
    if not sales_df.empty and '料型_标准' in sales_df.columns:
        s_materials = set(sales_df['料型_标准'].dropna().unique())
    
    all_materials = sorted(p_materials | s_materials)
    
    for mat in all_materials:
        row = {'料型': mat}
        
        p = purchase_df[purchase_df['料型_标准'] == mat] if not purchase_df.empty else pd.DataFrame()
        s = sales_df[sales_df['料型_标准'] == mat] if not sales_df.empty else pd.DataFrame()
        
        row['采购量_吨'] = p['实际净重_吨'].sum() if not p.empty else 0
        row['采购金额'] = p['采购成本'].sum() if not p.empty else 0
        row['采购均价'] = row['采购金额'] / row['采购量_吨'] if row['采购量_吨'] > 0 else 0
        
        row['出库量_吨'] = s['净重量'].sum() if not s.empty else 0
        row['销售金额'] = s['销售金额'].sum() if not s.empty else 0
        row['到手金额'] = s['到手金额'].sum() if not s.empty else 0
        row['出库均价'] = row['到手金额'] / row['出库量_吨'] if row['出库量_吨'] > 0 else 0
        
        row['毛利'] = row['到手金额'] - row['采购金额']
        row['库存_吨'] = row['采购量_吨'] - row['出库量_吨']
        
        result.append(row)
    
    return pd.DataFrame(result)


def get_inventory_balance(purchase_df, sales_df, opening_stock=None):
    """计算库存平衡表"""
    if opening_stock is None:
        opening_stock = {}
    
    mat_summary = get_material_summary(purchase_df, sales_df)
    
    if mat_summary.empty:
        return pd.DataFrame()
    
    mat_summary['上月余量_吨'] = mat_summary['料型'].map(opening_stock).fillna(0)
    mat_summary['期末库存_吨'] = mat_summary['上月余量_吨'] + mat_summary['库存_吨']
    
    # 选择需要的列
    cols = ['料型', '上月余量_吨', '采购量_吨', '出库量_吨', '期末库存_吨']
    return mat_summary[cols].copy()


def get_supplier_summary(purchase_df):
    """供应商统计"""
    if purchase_df.empty or '供应商_标准' not in purchase_df.columns:
        return pd.DataFrame()
    
    grouped = purchase_df.groupby('供应商_标准').agg({
        '实际净重_吨': 'sum',
        '采购成本': 'sum',
        '日期': 'count'
    }).reset_index()
    grouped.columns = ['供应商', '供货量_吨', '供货金额', '供货次数']
    grouped = grouped.sort_values('供货量_吨', ascending=False).reset_index(drop=True)
    return grouped


def get_customer_summary(sales_df):
    """收货单位统计"""
    if sales_df.empty or '收货单位_标准' not in sales_df.columns:
        return pd.DataFrame()
    
    grouped = sales_df.groupby('收货单位_标准').agg({
        '净重量': 'sum',
        '销售金额': 'sum',
        '到手金额': 'sum',
        '日期': 'count'
    }).reset_index()
    grouped.columns = ['收货单位', '出货量_吨', '销售金额', '到手金额', '出货次数']
    grouped = grouped.sort_values('出货量_吨', ascending=False).reset_index(drop=True)
    return grouped


def get_unpaid_purchases(purchase_df):
    """获取未付款采购明细"""
    if purchase_df.empty:
        return pd.DataFrame()
    
    unpaid = purchase_df[purchase_df['已付款'] == False] if '已付款' in purchase_df.columns else pd.DataFrame()
    if unpaid.empty:
        return pd.DataFrame()
    
    cols = ['日期', '供应商_标准', '料型_标准', '实际净重_吨', '采购成本', '未付金额', '货车司机']
    available_cols = [c for c in cols if c in unpaid.columns]
    return unpaid[available_cols].reset_index(drop=True)


def get_expense_summary(expenses_df):
    """费用汇总统计"""
    if expenses_df.empty:
        return pd.DataFrame()
    
    grouped = expenses_df.groupby(['月份', '费用类别']).agg({
        '支出金额': 'sum'
    }).reset_index()
    return grouped
