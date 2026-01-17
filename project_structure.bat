@echo off
chcp 65001 >nul
echo ========================================
echo  项目结构查看工具
echo ========================================
echo.

REM 获取脚本所在目录
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

echo 当前项目目录: %cd%
echo.
echo 项目结构:
echo ==================
tree /f /a
echo ==================

echo.
echo 重要文件检查:
echo.

if exist "touchpad_manager.py" (
    echo ✓ touchpad_manager.py (主程序)
) else (
    echo ❌ 缺少 touchpad_manager.py
)

if exist "config\" (
    echo ✓ config\ (配置目录)
    if exist "config\icon.ico" (
        echo ✓ config\icon.ico (图标文件)
    ) else (
        echo ⚠ 缺少 config\icon.ico
    )
    if exist "config\default_config.json" (
        echo ✓ config\default_config.json (默认配置)
    ) else (
        echo ⚠ 缺少 config\default_config.json
    )
) else (
    echo ❌ 缺少 config\ 目录
)

if exist "log\" (
    echo ✓ log\ (日志目录)
) else (
    echo ⚠ 缺少 log\ 目录
)

echo.
echo 脚本文件:
if exist "start_app.bat" echo ✓ start_app.bat
if exist "run_app.bat" echo ✓ run_app.bat
if exist "install_deps_only.bat" echo ✓ install_deps_only.bat
if exist "build_exe.bat" echo ✓ build_exe.bat
if exist "uninstall_deps.bat" echo ✓ uninstall_deps.bat
if exist "fix_directory_issue.bat" echo ✓ fix_directory_issue.bat

echo.
echo ========================================
echo  检查完成！
echo ========================================
echo.
pause