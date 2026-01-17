@echo off
chcp 65001 >nul
echo ========================================
echo  触控板自动开关工具 - 启动脚本
echo ========================================
echo.

echo [1/4] 正在检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.6+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python版本:
python --version

echo [2/4] 正在检查并创建文件夹...
if not exist "config\" mkdir config
if not exist "log\" mkdir log

echo ✓ 配置文件夹: config\
echo ✓ 日志文件夹: log\

echo [3/4] 正在检查配置文件...
if not exist "config\default_config.json" (
    echo 警告: 未找到默认配置文件
    echo 正在从项目创建默认配置...
    
    REM 检查是否在项目目录中
    if exist "default_config.json" (
        copy "default_config.json" "config\" >nul
        echo ✓ 已复制默认配置文件到 config\
    ) else (
        echo 正在创建默认配置文件...
        echo { > config\default_config.json
        echo   "version": "2.2", >> config\default_config.json
        echo   "description": "触控板自动开关工具 - 默认配置文件", >> config\default_config.json
        echo   "idle_threshold": 5.0, >> config\default_config.json
        echo   "auto_start": false, >> config\default_config.json
        echo   "start_minimized": false, >> config\default_config.json
        echo   "enable_sounds": true, >> config\default_config.json
        echo   "enable_notifications": true, >> config\default_config.json
        echo   "use_alt_keyboard_lib": false, >> config\default_config.json
        echo   "enable_compatibility_mode": true, >> config\default_config.json
        echo   "hotkeys": { >> config\default_config.json
        echo     "toggle_touchpad": "ctrl+alt+t", >> config\default_config.json
        echo     "toggle_monitoring": "ctrl+alt+m", >> config\default_config.json
        echo     "exit_app": "ctrl+alt+q" >> config\default_config.json
        echo   }, >> config\default_config.json
        echo   "appearance": { >> config\default_config.json
        echo     "theme": "default", >> config\default_config.json
        echo     "font_size": 10, >> config\default_config.json
        echo     "window_width": 900, >> config\default_config.json
        echo     "window_height": 700 >> config\default_config.json
        echo   } >> config\default_config.json
        echo } >> config\default_config.json
        echo ✓ 已创建默认配置文件
    )
) else (
    echo ✓ 找到默认配置文件
)

if exist "config\icon.ico" (
    echo ✓ 找到图标文件
) else (
    echo 警告: 未找到图标文件 config\icon.ico
    echo 程序将使用默认图标
)

echo [4/4] 正在安装依赖包...
echo 这将安装以下依赖:
echo   - pywin32     (Windows API访问)
echo   - pynput      (键盘监听)
echo   - win10toast  (Windows 10通知)
echo   - psutil      (系统进程管理)
echo   - keyboard    (备用键盘库)
echo.

echo 请确保网络连接正常...
echo 正在更新pip...
python -m pip install --upgrade pip >nul

echo.
echo 正在安装pywin32...
pip install pywin32>=305 >nul
if errorlevel 1 (
    echo ❌ pywin32安装失败，Windows功能将受限
) else (
    echo ✓ pywin32安装成功
)

echo.
echo 正在安装pynput...
pip install pynput>=1.7.6 >nul
if errorlevel 1 (
    echo ❌ pynput安装失败，键盘监听功能将受限
) else (
    echo ✓ pynput安装成功
)

echo.
echo 正在安装win10toast...
pip install win10toast>=0.9 >nul
if errorlevel 1 (
    echo ❌ win10toast安装失败，通知功能将受限
) else (
    echo ✓ win10toast安装成功
)

echo.
echo 正在安装psutil...
pip install psutil>=5.9.0 >nul
if errorlevel 1 (
    echo ❌ psutil安装失败，进程管理功能将受限
) else (
    echo ✓ psutil安装成功
)

echo.
echo 正在安装keyboard...
pip install keyboard>=0.13.5 >nul
if errorlevel 1 (
    echo ❌ keyboard安装失败，备用键盘功能将受限
) else (
    echo ✓ keyboard安装成功
)

echo.
echo 正在安装pyautogui...
pip install pyautogui>=0.9.53 >nul
if errorlevel 1 (
    echo ❌ pyautogui安装失败，键盘模拟功能将受限
) else (
    echo ✓ pyautogui安装成功
)

echo.
echo ========================================
echo  准备完成！
echo ========================================
echo.
echo 重要提示:
echo 1. 建议以管理员身份运行程序
echo 2. 触控板控制需要管理员权限
echo 3. 配置文件位置: config\default_config.json
echo 4. 日志文件位置: log\touchpad_manager.log
echo.
echo 按任意键启动触控板管理工具...
pause >nul

echo.
echo [启动] 正在启动触控板自动开关工具...
echo.
python touchpad_manager.py

if errorlevel 1 (
    echo.
    echo 程序启动失败，可能原因:
    echo 1. 依赖包未正确安装
    echo 2. 配置文件错误
    echo 3. 系统权限不足
    echo.
    echo 建议:
    echo 1. 以管理员身份运行此脚本
    echo 2. 查看日志文件: log\touchpad_manager.log
    echo.
    pause
    exit /b 1
)

echo.
echo 程序已退出
pause