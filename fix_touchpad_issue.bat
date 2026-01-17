@echo off
chcp 65001 >nul
echo ========================================
echo  触控板问题修复工具
echo ========================================
echo.

echo 这个工具将帮助修复触控板控制问题
echo.
echo 步骤:
echo 1. 安装键盘模拟依赖
echo 2. 测试触控板快捷键
echo 3. 配置程序使用正确的快捷键
echo.

echo [1/3] 正在安装键盘模拟依赖...
pip install pyautogui>=0.9.53
if errorlevel 1 (
    echo 警告: pyautogui安装失败，键盘模拟功能可能受限
    echo 尝试使用pip3安装...
    pip3 install pyautogui>=0.9.53
)

echo.
echo [2/3] 正在准备测试工具...
if not exist keyboard_shortcut_test.py (
    echo 错误: keyboard_shortcut_test.py 文件不存在
    echo 请确保它与本脚本在同一目录
    pause
    exit /b 1
)

echo.
echo [3/3] 正在启动快捷键测试工具...
echo.
echo 重要提示:
echo 1. 请以管理员身份运行此测试
echo 2. 请仔细观察每次测试后触控板状态
echo 3. 准备好您的触控板用于测试
echo.
echo 按任意键启动测试工具...
pause >nul

python keyboard_shortcut_test.py

echo.
echo ========================================
echo  修复完成！
echo ========================================
echo.
echo 下一步:
echo 1. 如果找到了有效的快捷键，程序会自动配置
echo 2. 重新启动触控板管理工具
echo 3. 程序将使用键盘快捷键控制触控板
echo.
echo 按任意键退出...
pause >nul