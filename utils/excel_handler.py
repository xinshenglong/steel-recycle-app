"""
Excel 文件读写操作模块 — 废钢台账专用解析器
处理三个台账文件的读取和追加写入
"""
import pandas as pd
import numpy as np
from datetime import datetime
import os


def _parse_excel_date(val):
    """安全解析 Excel 日期（数字序列号或字符串）"""
    if pd.isna(val) or val == '':
        return None
    if isinstance(val, (pd.Timestamp, datetime)):
        return val
    if isinstance(val, (int, float)) and val > 30000:  # Excel 日期序列号
        try:
            return pd.Timestamp('1899-12-30') + pd.Timedelta(days=int(val))
        except:
            pass
    try:
        result = pd.to_datetime(val, errors='coerce')
        return result if pd.notna(result) else None
    except:
        return None


def _find_header_row(df_raw, max_rows=10):
    """在原始 DataFrame 中找到数据表头行索引
    策略：找到包含关键列名（日期、车牌、经手人等）最多的行
    """
    if len(df_raw) == 0:
        return None
    
    keywords = ['日期', '车牌', '供应商', '料型', '经手人', '科目', '摘要', '支出',
                '毛重', '皮重', '净重', '单价', '收货单位', '货物名称', '出货日期']
    
    best_row = None
    best_score = 0
    
    for i in range(min(max_rows, len(df_raw))):
        row_values = df_raw.iloc[i].astype(str).tolist()
        score = sum(1 for kw in keywords if any(kw in str(v) for v in row_values if pd.notna(v)))
        if score > best_score:
            best_score = score
            best_row = i
    
    return best_row


def _extract_data_block(df_raw, header_row):
    """从原始 DataFrame 提取数据区域"""
    if header_row is None or header_row >= len(df_raw):
        return None
    
    # 提取表头
    headers = df_raw.iloc[header_row].tolist()
    
    # 清理表头：去掉NaN，去重
    clean_headers = []
    seen = set()
    for h in headers:
        h_str = str(h).strip() if pd.notna(h) else ''
        if h_str == '' or h_str == 'nan':
            h_str = f'Col_{len(clean_headers)}'
        # 去重
        orig = h_str
        counter = 1
        while h_str in seen:
            h_str = f'{orig}_{counter}'
            counter += 1
        seen.add(h_str)
        clean_headers.append(h_str)
    
    # 提取数据行（从header下一行开始）
    data_rows = df_raw.iloc[header_row + 1:].copy()
    data_rows.columns = clean_headers
    
    # 过滤掉全空行和汇总行
    def is_valid_row(row):
        vals = [str(v).strip() for v in row.values if pd.notna(v)]
        if not vals:
            return False
        # 排除汇总行
        text = ' '.join(vals)
        if any(kw in text for kw in ['合计', '总计', '汇总', '平均']):
            return False
        # 至少有一个非空值
        return any(v != '' and v != 'nan' for v in vals)
    
    data_rows = data_rows[data_rows.apply(is_valid_row, axis=1)]
    return data_rows.reset_index(drop=True)


def read_purchase(file_path="data/purchase.xlsx"):
    """读取采购台账，返回标准化的 DataFrame"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full_path = os.path.join(base_dir, file_path)
    
    try:
        xls = pd.ExcelFile(full_path)
    except Exception as e:
        return pd.DataFrame()
    
    all_data = []
    for sheet_name in xls.sheet_names:
        try:
            df_raw = pd.read_excel(full_path, sheet_name=sheet_name, header=None)
            header_row = _find_header_row(df_raw)
            if header_row is None:
                continue
            
            df = _extract_data_block(df_raw, header_row)
            if df is None or df.empty:
                continue
            
            # 标准化列名映射
            col_mapping = {}
            for col in df.columns:
                col_str = str(col)
                if '日期' in col_str and '付款' not in col_str:
                    col_mapping['日期'] = col
                elif '车牌' in col_str:
                    col_mapping['车牌'] = col
                elif '供应商' in col_str:
                    col_mapping['供应商'] = col
                elif '料型' in col_str:
                    col_mapping['料型'] = col
                elif '方式' in col_str:
                    col_mapping['方式'] = col
                elif '提货净重' in col_str:
                    col_mapping['提货净重'] = col
                elif '磅差' in col_str:
                    col_mapping['磅差'] = col
                elif '毛重' in col_str:
                    col_mapping['毛重'] = col
                elif '皮重' in col_str:
                    col_mapping['皮重'] = col
                elif str(col) == '净重' or col_str.endswith('净重'):
                    if '实际' not in col_str:
                        col_mapping['净重'] = col
                elif '扣杂' in col_str and '钢厂' not in col_str and '前' not in col_str and '后' not in col_str:
                    col_mapping['扣杂'] = col
                elif '实际净重' in col_str:
                    col_mapping['实际净重'] = col
                elif '单价' in col_str:
                    col_mapping['单价'] = col
                elif '运费' in col_str and '单价' not in col_str:
                    col_mapping['运费'] = col
                elif '扣杂前金额' in col_str or ('扣杂前' in col_str and '金额' in col_str):
                    col_mapping['扣杂前金额'] = col
                elif '扣杂后金额' in col_str or ('扣杂后' in col_str and '金额' in col_str):
                    col_mapping['扣杂后金额'] = col
                elif '未加运费' in col_str or ('未加' in col_str and '运费' in col_str):
                    col_mapping['未加运费'] = col
                elif '实付金额' in col_str or ('实付' in col_str and '金额' in col_str):
                    col_mapping['实付金额'] = col
                elif '付款人' in col_str:
                    col_mapping['付款人'] = col
                elif '付款日期' in col_str:
                    col_mapping['付款日期'] = col
                elif '司机' in col_str:
                    col_mapping['货车司机'] = col
            
            # 创建标准化DataFrame
            std_df = pd.DataFrame()
            for std_name, orig_col in col_mapping.items():
                std_df[std_name] = df[orig_col]
            
            # 解析日期
            if '日期' in std_df.columns:
                std_df['日期'] = std_df['日期'].apply(_parse_excel_date)
                std_df = std_df[std_df['日期'].notna()]
                std_df['月份'] = std_df['日期'].apply(lambda x: x.strftime('%Y-%m') if pd.notna(x) else None)
            
            # 数值列转换
            numeric_cols = ['提货净重', '磅差', '毛重', '皮重', '净重', '扣杂', '实际净重',
                          '单价', '运费', '扣杂前金额', '扣杂后金额', '未加运费', '实付金额']
            for col in numeric_cols:
                if col in std_df.columns:
                    std_df[col] = pd.to_numeric(std_df[col], errors='coerce')
            
            if not std_df.empty:
                all_data.append(std_df)
                
        except Exception as e:
            continue
    
    if all_data:
        result = pd.concat(all_data, ignore_index=True)
        return result
    return pd.DataFrame()


def read_sales(file_path="data/sales.xlsx"):
    """读取出库台账，返回标准化的 DataFrame
    
    出库台账有特殊的两级表头结构：
    第1行: 出货日期 | 基地 | 收货单位 | 车牌号 | 车皮号 | 货物名称 | 出厂情况 | ... | 钢厂情况 | ...
    第2行:   -    |  -   |    -     |   -    |   -   |    -     |  毛重   | 皮重 | ...
    需要合并这两级表头来正确识别列
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full_path = os.path.join(base_dir, file_path)
    
    try:
        xls = pd.ExcelFile(full_path)
    except Exception as e:
        return pd.DataFrame()
    
    # 出库台账的固定列映射（按列位置）
    # 基于分析：日期[0], 基地[1], 收货单位[2], 车牌号[3], 车皮号[4], 货物名称[5],
    # 毛重[6], 皮重[7], 净重量[8], 单价[9], 金额[10], 磅差[11],
    # 钢厂重量[12], 钢厂扣杂[13], 钢厂结算重量[14], 钢厂结算单价[15],
    # 罚款[16], 手续费[17], 销售金额/到手金额[18], 运费单价[19], 运费金额[20], 备注[...]
    SALES_COL_MAP = {
        0: '出货日期', 1: '基地', 2: '收货单位', 3: '车牌号', 4: '车皮号',
        5: '货物名称', 6: '毛重', 7: '皮重', 8: '净重量', 9: '出厂单价',
        10: '出厂金额', 11: '磅差', 12: '钢厂重量', 13: '钢厂扣杂',
        14: '钢厂结算重量', 15: '钢厂结算单价', 16: '罚款', 17: '手续费',
        18: '销售金额', 19: '运费单价', 20: '运费金额'
    }
    
    all_data = []
    for sheet_name in xls.sheet_names:
        try:
            df_raw = pd.read_excel(full_path, sheet_name=sheet_name, header=None)
            if len(df_raw) < 4:
                continue
            
            # 使用固定列位置提取数据（跳过前3行header）
            data_start_row = 3
            data_rows = df_raw.iloc[data_start_row:].reset_index(drop=True)
            
            # 根据实际列数创建DataFrame
            max_cols = min(len(SALES_COL_MAP), len(df_raw.columns))
            
            std_df = pd.DataFrame()
            for col_idx in range(max_cols):
                if col_idx in SALES_COL_MAP and col_idx < len(data_rows.columns):
                    col_name = SALES_COL_MAP[col_idx]
                    std_df[col_name] = data_rows.iloc[:, col_idx]
            
            # 最后一列可能是备注
            if len(df_raw.columns) > 21:
                std_df['备注'] = data_rows.iloc[:, -1]
            
            if std_df.empty or len(std_df) == 0:
                continue
            
            # 解析日期
            std_df['日期'] = std_df['出货日期'].apply(_parse_excel_date)
            std_df = std_df[std_df['日期'].notna()].copy()
            
            if std_df.empty:
                continue
                
            std_df['月份'] = std_df['日期'].apply(lambda x: x.strftime('%Y-%m') if pd.notna(x) else None)
            
            # 数值列转换
            numeric_cols = ['毛重', '皮重', '净重量', '出厂单价', '出厂金额', '磅差',
                          '钢厂重量', '钢厂扣杂', '钢厂结算重量', '钢厂结算单价',
                          '罚款', '手续费', '销售金额', '运费单价', '运费金额']
            for col in numeric_cols:
                if col in std_df.columns:
                    std_df[col] = pd.to_numeric(std_df[col], errors='coerce')
            
            # 计算到手金额（如果原始数据没有）
            if '销售金额' in std_df.columns:
                freight = std_df.get('运费金额', pd.Series([0]*len(std_df)))
                fine = std_df.get('罚款', pd.Series([0]*len(std_df)))
                fee = std_df.get('手续费', pd.Series([0]*len(std_df)))
                std_df['到手金额'] = std_df['销售金额'].fillna(0) - freight.fillna(0) - fine.fillna(0) - fee.fillna(0)
            
            # 过滤掉全空行
            key_cols = ['日期', '基地', '收货单位', '货物名称']
            has_data = std_df[key_cols].notna().any(axis=1)
            std_df = std_df[has_data].reset_index(drop=True)
            
            if not std_df.empty:
                all_data.append(std_df)
                
        except Exception as e:
            continue
    
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return pd.DataFrame()


def read_expenses(file_path="data/expenses.xlsx"):
    """读取费用报销台账，返回标准化的 DataFrame"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full_path = os.path.join(base_dir, file_path)
    
    try:
        xls = pd.ExcelFile(full_path)
    except Exception as e:
        return pd.DataFrame()
    
    all_data = []
    for sheet_name in xls.sheet_names:
        # 跳过汇总sheet
        if '汇总' in str(sheet_name) or '明细' in str(sheet_name) or 'Sheet1' in str(sheet_name):
            continue
            
        try:
            df_raw = pd.read_excel(full_path, sheet_name=sheet_name, header=None)
            header_row = _find_header_row(df_raw)
            if header_row is None:
                continue
            
            df = _extract_data_block(df_raw, header_row)
            if df is None or df.empty:
                continue
            
            # 费用台账的第一列可能是空的，需要处理
            # 找到实际的数据起始列
            first_valid_col = 0
            for i, col in enumerate(df.columns):
                if df[col].notna().sum() > len(df) * 0.3:  # 至少30%非空
                    first_valid_col = i
                    break
            
            # 标准化列名映射
            col_mapping = {}
            for col in df.columns:
                col_str = str(col).replace('\\n', '').replace(' ', '')
                orig_col = col
                
                if '日期' in col_str and '报销' not in col_str:
                    col_mapping['日期'] = orig_col
                elif '经手人' in col_str:
                    col_mapping['经手人'] = orig_col
                elif '科目' in col_str:
                    col_mapping['科目'] = orig_col
                elif '摘要' in col_str:
                    col_mapping['摘要'] = orig_col
                elif '支出' in col_str:
                    col_mapping['支出'] = orig_col
                elif '报销日期' in col_str:
                    col_mapping['报销日期'] = orig_col
            
            std_df = pd.DataFrame()
            for std_name, orig_col in col_mapping.items():
                std_df[std_name] = df[orig_col]
            
            # 解析日期
            if '日期' in std_df.columns:
                std_df['日期'] = std_df['日期'].apply(_parse_excel_date)
                std_df = std_df[std_df['日期'].notna()]
                std_df['月份'] = std_df['日期'].apply(lambda x: x.strftime('%Y-%m') if pd.notna(x) else None)
            
            # 数值列
            if '支出' in std_df.columns:
                std_df['支出金额'] = pd.to_numeric(std_df['支出'], errors='coerce').fillna(0)
            else:
                std_df['支出金额'] = 0
            
            # 标准化费用类别
            std_df['费用类别'] = std_df.apply(_classify_expense, axis=1)
            
            if not std_df.empty:
                all_data.append(std_df)
                
        except Exception as e:
            continue
    
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return pd.DataFrame()


def _classify_expense(row):
    """根据科目和摘要标准化费用分类"""
    subject = str(row.get('科目', ''))
    desc = str(row.get('摘要', ''))
    text = subject + desc
    
    categories = {
        '工资': ['工资', '薪酬'],
        '电费': ['电费'],
        '油费': ['加油', '柴油', '汽油', '油费', '液压油', '齿轮油'],
        '食堂餐费': ['食堂', '买菜', '买肉', '聚餐', '大米', '粮油'],
        '修理费': ['维修', '修理', '保养', '配件', '轮胎', '零件'],
        '差旅费': ['差旅', '出差', '过路费', '高速费', '停车费', '高铁', '车票'],
        '招待费': ['招待', '烟酒', '餐饮', '吃饭', '酒店', '住宿'],
        '办公费': ['办公', '快递', '网卡', '网络', '电话', '打印', 'wps'],
        '运输费': ['运输'],
        '福利费': ['福利'],
        '税费': ['税费', '增值税'],
        '低值易耗品': ['低值易耗', '电池', '手套', '劳保'],
    }
    
    for cat, keywords in categories.items():
        for kw in keywords:
            if kw in text:
                return cat
    return '其他'


def append_to_purchase(file_path, record):
    """追加采购记录到 Excel — 占位实现"""
    pass


def append_to_sales(file_path, record):
    """追加出库记录到 Excel — 占位实现"""
    pass


def append_to_expenses(file_path, record):
    """追加费用记录到 Excel — 占位实现"""
    pass
