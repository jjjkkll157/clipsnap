# ── 启动 ClipSnap ──
# 双击运行此文件启动后端服务

cd /d "%~dp0backend"
echo 🖇️  ClipSnap 启动中...
echo.
echo 📋 管理面板: http://localhost:8710
echo 🔌 Chrome 扩展: 加载 extension/ 目录
echo.
echo 按 Ctrl+C 停止服务
echo ============================================

uv run python main.py
pause
