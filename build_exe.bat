@echo off
chcp 65001 >nul
echo ========================================
echo  触控板自动开关工具 - 打包脚本
echo ========================================
echo.

echo [1/6] 正在检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.6+
    pause
    exit /b 1
)

echo [2/6] 正在安装/更新依赖包...
pip install --upgrade pip >nul
pip install --upgrade -r requirements.txt
if errorlevel 1 (
    echo 警告: 部分依赖安装失败，尝试继续...
)

echo [3/6] 正在检查配置文件夹...
if not exist "config\" mkdir config
if not exist "log\" mkdir log

echo [4/6] 正在检查必需文件...
set ERROR=0

if not exist "config\icon.ico" (
    echo 错误: 图标文件 config\icon.ico 不存在！
    echo 请将你的图标文件放在 config 文件夹中
    set ERROR=1
)

if not exist "config\default_config.json" (
    echo 警告: 默认配置文件不存在，正在创建...
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
    echo   }, >> config\default_config.json
    echo   "compatibility": { >> config\default_config.json
    echo     "lenovo_legion": true, >> config\default_config.json
    echo     "try_multiple_registry_paths": true, >> config\default_config.json
    echo     "delay_before_enable": 0.2, >> config\default_config.json
    echo     "min_disable_time": 0.5 >> config\default_config.json
    echo   }, >> config\default_config.json
    echo   "logging": { >> config\default_config.json
    echo     "level": "INFO", >> config\default_config.json
    echo     "max_size_mb": 5, >> config\default_config.json
    echo     "backup_count": 5 >> config\default_config.json
    echo   } >> config\default_config.json
    echo } >> config\default_config.json
    echo ✓ 已创建默认配置文件
)

if %ERROR% == 1 (
    pause
    exit /b 1
)

echo [5/6] 正在清理旧文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__
if exist *.spec del /q *.spec

echo [6/6] 正在生成EXE文件...
echo 正在打包，这可能需要几分钟...
pyinstaller --onefile ^
            --windowed ^
            --icon=config\icon.ico ^
            --add-data "config\icon.ico;config" ^
            --add-data "config\default_config.json;config" ^
            --name "触控板自动开关工具" ^
            --clean ^
            --noconfirm ^
            touchpad_manager.py

if errorlevel 1 (
    echo 打包失败，请检查错误信息
    pause
    exit /b 1
)

echo.
echo ========================================
echo  打包成功！
echo ========================================
echo EXE文件位置: dist\触控板自动开关工具.exe
echo 配置文件目录: config\
echo 日志文件目录: log\
echo.
echo 包含的配置文件:
echo   - config\icon.ico (程序图标)
echo   - config\default_config.json (默认配置)
echo.
echo 使用方法:
echo 1. 以管理员身份运行 EXE 文件
echo 2. 点击"开始监控"按钮
echo 3. 开始使用键盘，触控板会自动管理
echo.
echo 提示: 右键点击EXE文件 -> 以管理员身份运行EXE文件
echo ========================================
echo.
pause