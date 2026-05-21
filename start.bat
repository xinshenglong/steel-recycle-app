@echo off
chcp 65001 >nul
echo 🚀 启动鑫胜隆废钢管理系统...
echo 📱 请在浏览器中访问: http://localhost:8501
echo ---
python -m streamlit run app.py --server.port 8501 --server.headless true --browser.gatherUsageStats false
pause