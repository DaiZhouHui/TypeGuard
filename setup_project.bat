@echo off
chcp 65001 >nul
echo ========================================
echo  触控板自动开关工具 - 一键安装脚本
echo ========================================
echo.

echo 这个脚本将帮助您快速设置项目
echo.

REM 获取脚本所在目录
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

echo 当前目录: %cd%
echo.

echo [1/5] 检查目录结构...
call project_structure.bat >nul 2>&1

echo [2/5] 修复目录问题...
call fix_directory_issue.bat >nul 2>&1

echo [3/5] 安装依赖包...
echo.
call install_deps_only.bat

if errorlevel 1 (
    echo 警告: 依赖安装可能有问题
    echo 按任意键继续...
    pause >nul
)

echo [4/5] 检查主程序...
if not exist "touchpad_manager.py" (
    echo 错误: 主程序文件不存在
    echo 请确保 touchpad_manager.py 在当前目录
    pause
    exit /b 1
)

echo [5/5] 创建必需文件...
if not exist "config\" mkdir config
if not exist "log\" mkdir log

if not exist "config\icon.ico" (
    echo 正在创建默认图标...
    python create_icon.py >nul 2>&1
)

if not exist "keyboard_shortcut_test.py" (
    echo 错误: 缺少测试工具
    echo 请确保所有文件都在同一目录
    pause
    exit /b 1
)

echo.
echo ========================================
echo  项目设置完成！
echo ========================================
echo.
echo 现在可以:
echo.
echo 1. 运行程序: start_app.bat
echo 2. 测试快捷键: python keyboard_shortcut_test.py
echo 3. 打包EXE: build_exe.bat
echo.
echo 如果遇到问题:
echo 1. 运行 fix_touchpad_issue.bat
echo 2. 查看 log\touchpad_manager.log
echo.
pause