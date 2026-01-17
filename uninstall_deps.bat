@echo off
chcp 65001 >nul
echo ========================================
echo  触控板自动开关工具 - 依赖卸载脚本
echo ========================================
echo.

echo 警告: 这将卸载触控板工具的所有依赖包
echo.
echo 将要卸载的包:
echo   - pywin32
echo   - pynput
echo   - win10toast
echo   - psutil
echo   - keyboard
echo.
set /p CONFIRM="确定要卸载吗? (Y/N): "

if /i "%CONFIRM%" NEQ "Y" (
    echo 取消卸载
    pause
    exit /b 0
)

echo.
echo 正在卸载依赖包...

echo 1. 正在卸载keyboard...
pip uninstall keyboard -y

echo 2. 正在卸载psutil...
pip uninstall psutil -y

echo 3. 正在卸载win10toast...
pip uninstall win10toast -y

echo 4. 正在卸载pynput...
pip uninstall pynput -y

echo 5. 正在卸载pywin32...
pip uninstall pywin32 -y

echo.
echo ========================================
echo  依赖卸载完成！
echo ========================================
echo.
echo 注意: 如果程序无法运行，可能需要重新安装依赖
echo.
pause