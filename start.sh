#!/bin/bash
echo "🚀 启动鑫胜隆废钢管理系统..."
echo "📱 请在浏览器中访问: http://localhost:8501"
echo "📱 手机访问: http://$(hostname -I | awk '{print $1}'):8501"
echo "---"
python -m streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --browser.gatherUsageStats false