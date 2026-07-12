@echo off
chcp 65001 >nul
title ClipSnap 一键安装

echo.
echo   🖇️  ClipSnap 一键安装
echo   ========================
echo.

REM 检查 Python
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo   ❌ 未找到 Python，请先安装 Python 3.10+
    echo   📥 下载: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 创建安装目录
set "INSTALL_DIR=%USERPROFILE%\clipsnap"
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM 复制文件（%~dp0 = 脚本所在目录）
echo   📦 正在复制文件...
xcopy /E /Y /Q "%~dp0backend" "%INSTALL_DIR%\backend\" >nul
xcopy /E /Y /Q "%~dp0web" "%INSTALL_DIR%\web\" >nul
xcopy /E /Y /Q "%~dp0extension" "%INSTALL_DIR%\extension\" >nul
copy /Y "%~dp0README.md" "%INSTALL_DIR%\" >nul

REM 安装依赖
echo   📥 安装 Python 依赖...
cd /d "%INSTALL_DIR%"
python -m pip install -r backend\requirements.txt -q 2>&1

REM 创建启动脚本
echo @echo off > "%INSTALL_DIR%\启动.bat"
echo cd /d "%INSTALL_DIR%" >> "%INSTALL_DIR%\启动.bat"
echo title ClipSnap >> "%INSTALL_DIR%\启动.bat"
echo echo 🖇️ ClipSnap 启动中... >> "%INSTALL_DIR%\启动.bat"
echo echo 📋 管理面板: http://localhost:8710 >> "%INSTALL_DIR%\启动.bat"
echo echo. >> "%INSTALL_DIR%\启动.bat"
echo python backend\main.py >> "%INSTALL_DIR%\启动.bat"
echo pause >> "%INSTALL_DIR%\启动.bat"

REM 创建桌面快捷方式
powershell -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%USERPROFILE%\Desktop\ClipSnap.lnk');$s.TargetPath='%INSTALL_DIR%\启动.bat';$s.WorkingDirectory='%INSTALL_DIR%';$s.IconLocation='%SystemRoot%\System32\imageres.dll,15';$s.Save()"

echo.
echo   ✅ 安装完成！
echo   📂 安装目录: %INSTALL_DIR%
echo   🖥️  桌面已创建快捷方式: ClipSnap
echo.
echo   🚀 双击桌面 "ClipSnap" 启动
echo   🔌 然后在 Chrome 中加载扩展:
echo      Chrome → 扩展程序 → 开发者模式 → 加载已解压 → 选择:
echo      %INSTALL_DIR%\extension
echo.
pause
