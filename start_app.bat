@echo off
chcp 65001 >nul
echo ========================================
echo  触控板自动开关工具 - 运行脚本
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

echo 正在检查依赖...
echo.
echo 检查pywin32...
python -c "import win32api; print('✓ pywin32 已安装')" 2>nul
if errorlevel 1 (
    echo ❌ pywin32 未安装
    echo 请先运行 install_deps_only.bat 安装依赖
    pause
    exit /b 1
)

echo 检查pynput...
python -c "import pynput; print('✓ pynput 已安装')" 2>nul
if errorlevel 1 (
    echo ❌ pynput 未安装
    echo 请先运行 install_deps_only.bat 安装依赖
    pause
    exit /b 1
)

echo 检查win10toast...
python -c "from win10toast import ToastNotifier; print('✓ win10toast 已安装')" 2>nul
if errorlevel 1 (
    echo ⚠  win10toast 未安装，通知功能将受限
)

echo 检查psutil...
python -c "import psutil; print('✓ psutil 已安装')" 2>nul
if errorlevel 1 (
    echo ⚠  psutil 未安装，进程管理功能将受限
)

echo 检查keyboard...
python -c "import keyboard; print('✓ keyboard 已安装')" 2>nul
if errorlevel 1 (
    echo ⚠  keyboard 未安装，备用键盘功能将受限
)

echo 检查pyautogui...
python -c "import pyautogui; print('✓ pyautogui 已安装')" 2>nul
if errorlevel 1 (
    echo ⚠  pyautogui 未安装，键盘模拟功能将受限
)

echo.
echo 检查主程序文件...
if not exist "touchpad_manager.py" (
    echo 错误: 找不到主程序文件 touchpad_manager.py
    echo 请确保脚本在正确的目录中运行
    echo 当前目录文件列表:
    dir /b
    pause
    exit /b 1
)

echo.
echo ========================================
echo  正在启动触控板自动开关工具...
echo ========================================
echo.
python touchpad_manager.py

if errorlevel 1 (
    echo.
    echo 程序启动失败
    echo 可能原因:
    echo 1. 依赖包未正确安装
    echo 2. 配置文件错误
    echo 3. 系统权限不足
    echo.
    echo 建议:
    echo 1. 以管理员身份运行此脚本
    echo 2. 重新安装依赖: install_deps_only.bat
    echo 3. 查看日志文件: log\touchpad_manager.log
    echo.
    pause
    exit /b 1
)

echo.
echo 程序已退出
pause