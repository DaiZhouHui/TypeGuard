@echo off
chcp 65001 >nul
echo ========================================
echo  目录问题修复工具
echo ========================================
echo.
echo 这个工具将修复脚本在错误目录运行的问题
echo.

echo 当前目录: %cd%
echo.
echo 正在查找脚本所在目录...
for %%I in ("%~dp0.") do set SCRIPT_DIR=%%~fI
echo 脚本实际目录: %SCRIPT_DIR%
echo.

if "%cd%"=="%SCRIPT_DIR%" (
    echo ✓ 已经在正确的目录中
) else (
    echo ⚠ 当前目录不正确
    echo 正在切换到正确目录...
    cd /d "%SCRIPT_DIR%"
    echo 新目录: %cd%
)

echo.
echo 当前目录文件列表:
echo ==================
dir /b
echo ==================

echo.
echo 修复完成！
echo.
echo 现在可以正常运行其他脚本:
echo 1. start_app.bat - 安装依赖并运行程序
echo 2. run_app.bat - 仅运行程序（需已安装依赖）
echo.
pause