@echo off
chcp 65001 >nul
echo ========================================
echo  触控板自动开关工具 - 依赖安装脚本
echo ========================================
echo.

REM 获取脚本所在目录
set SCRIPT_DIR=%~dp0
echo 脚本目录: %SCRIPT_DIR%

REM 切换到脚本目录
cd /d "%SCRIPT_DIR%"
echo 当前目录: %cd%
echo.

echo 正在检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.6+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python版本:
python --version
echo.

echo 正在更新pip...
python -m pip install --upgrade pip >nul 2>&1
if errorlevel 1 (
    echo 警告: pip更新失败，尝试继续安装...
)

echo.
echo ========================================
echo  开始安装依赖包
echo ========================================
echo.

set ERROR_COUNT=0

echo 1. 正在安装pywin32...
pip install pywin32>=305 >nul 2>&1
if errorlevel 1 (
    echo ❌ pywin32安装失败
    set /a ERROR_COUNT+=1
) else (
    echo ✓ pywin32安装成功
)

echo.
echo 2. 正在安装pynput...
pip install pynput>=1.7.6 >nul 2>&1
if errorlevel 1 (
    echo ❌ pynput安装失败
    set /a ERROR_COUNT+=1
) else (
    echo ✓ pynput安装成功
)

echo.
echo 3. 正在安装win10toast...
pip install win10toast>=0.9 >nul 2>&1
if errorlevel 1 (
    echo ❌ win10toast安装失败
    set /a ERROR_COUNT+=1
) else (
    echo ✓ win10toast安装成功
)

echo.
echo 4. 正在安装psutil...
pip install psutil>=5.9.0 >nul 2>&1
if errorlevel 1 (
    echo ❌ psutil安装失败
    set /a ERROR_COUNT+=1
) else (
    echo ✓ psutil安装成功
)

echo.
echo 5. 正在安装keyboard...
pip install keyboard>=0.13.5 >nul 2>&1
if errorlevel 1 (
    echo ❌ keyboard安装失败
    set /a ERROR_COUNT+=1
) else (
    echo ✓ keyboard安装成功
)

echo.
echo 6. 正在安装pyautogui...
pip install pyautogui>=0.9.53 >nul 2>&1
if errorlevel 1 (
    echo ❌ pyautogui安装失败
    set /a ERROR_COUNT+=1
) else (
    echo ✓ pyautogui安装成功
)

echo.
echo ========================================
echo  依赖安装完成！
echo ========================================
echo.
if %ERROR_COUNT% == 0 (
    echo ✓ 所有依赖安装成功！
    echo.
    echo 现在可以运行程序:
    echo 1. 双击运行 start_app.bat 启动程序
    echo 2. 或手动运行: python touchpad_manager.py
) else (
    echo ⚠  有 %ERROR_COUNT% 个依赖安装失败
    echo.
    echo 建议:
    echo 1. 检查网络连接
    echo 2. 以管理员身份运行此脚本
    echo 3. 手动安装失败的依赖
)

echo.
pause