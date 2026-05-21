"""
业务计算工具模块
"""
import numpy as np


def calc_unit_profit(purchase_cost_per_ton, sale_revenue_per_ton, processing_cost_per_ton=0, transport_to_steel_per_ton=0):
    """计算每吨利润"""
    return sale_revenue_per_ton - purchase_cost_per_ton - processing_cost_per_ton - transport_to_steel_per_ton


def calc_processing_cost(total_manufacturing_cost, total_output_tons):
    """计算单位加工成本"""
    if total_output_tons <= 0:
        return 0
    return total_manufacturing_cost / total_output_tons


def calc_expense_allocation(total_expenses, allocation_basis='output', **kwargs):
    """计算费用分摊
    allocation_basis: 'output'按出货量, 'revenue'按收入, 'equal'平均
    """
    if allocation_basis == 'output':
        total_output = kwargs.get('total_output', 1)
        material_output = kwargs.get('material_output', 0)
        if total_output <= 0:
            return 0
        return total_expenses * (material_output / total_output)
    elif allocation_basis == 'revenue':
        total_revenue = kwargs.get('total_revenue', 1)
        material_revenue = kwargs.get('material_revenue', 0)
        if total_revenue <= 0:
            return 0
        return total_expenses * (material_revenue / total_revenue)
    else:
        num_materials = kwargs.get('num_materials', 1)
        if num_materials <= 0:
            return 0
        return total_expenses / num_materials


def calc_gross_margin(sales_amount, purchase_cost):
    """计算毛利率"""
    if sales_amount <= 0:
        return 0
    return (sales_amount - purchase_cost) / sales_amount * 100


def calc_net_margin(sales_amount, purchase_cost, expenses):
    """计算净利率"""
    if sales_amount <= 0:
        return 0
    return (sales_amount - purchase_cost - expenses) / sales_amount * 100


def calc_inventory_turnover(cost_of_goods_sold, avg_inventory):
    """计算库存周转率"""
    if avg_inventory <= 0:
        return 0
    return cost_of_goods_sold / avg_inventory
