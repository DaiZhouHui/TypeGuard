#!/usr/bin/env python3
"""
键盘快捷键测试工具 - 用于找到正确的触控板切换快捷键
"""

import sys
import os
import time

# 添加当前目录到路径，以便导入模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from keyboard_simulator import KeyboardSimulator, PyAutoGUISimulator
    HAS_KEYBOARD_SIM = True
except ImportError:
    HAS_KEYBOARD_SIM = False

def test_keyboard_shortcuts():
    """测试各种键盘快捷键"""
    print("=" * 60)
    print("触控板快捷键测试工具")
    print("=" * 60)
    print()
    print("说明: 这个工具会测试各种触控板切换快捷键")
    print("请观察每次测试后触控板是否被切换")
    print()
    
    if not HAS_KEYBOARD_SIM:
        print("错误: 无法导入键盘模拟器模块")
        return
    
    # 测试的快捷键组合
    test_shortcuts = [
        ['F11'],
        ['F6'],
        ['F9'],
        ['F10'],
        ['control', 'F11'],
        ['ctrl', 'F11'],
        ['control', 'F6'],
        ['ctrl', 'F6'],
        ['alt', 'F11'],
        ['alt', 'F6'],
        ['shift', 'F11'],
        ['shift', 'F6'],
        ['windows', 'F11'],
    ]
    
    print(f"将测试 {len(test_shortcuts)} 种快捷键组合")
    print()
    
    for i, shortcut in enumerate(test_shortcuts, 1):
        print(f"测试 {i}/{len(test_shortcuts)}: {shortcut}")
        print(f"请准备好观察触控板状态...")
        
        # 倒计时
        for j in range(3, 0, -1):
            print(f"{j}...", end=' ', flush=True)
            time.sleep(1)
        print("开始!")
        
        # 发送快捷键
        try:
            # 尝试Windows API方法
            sim = KeyboardSimulator()
            if sim.send_shortcut(shortcut):
                print(f"✓ 已发送快捷键: {shortcut}")
            else:
                print(f"✗ 发送快捷键失败: {shortcut}")
        except Exception as e:
            print(f"✗ 发送快捷键异常: {e}")
        
        print()
        print("触控板状态切换了吗? (观察触摸板是否能使用)")
        print("1. 切换成功 - 触控板状态改变了")
        print("2. 切换失败 - 触控板状态没变化")
        print("3. 不确定")
        
        choice = input("请输入选择 (1/2/3): ").strip()
        
        if choice == '1':
            print(f"✓ 成功! 有效的快捷键是: {shortcut}")
            print()
            print("请将这个快捷键配置到程序中:")
            print(f"在config/user_config.json中添加:")
            print(f'  "keyboard_shortcut": {shortcut}')
            return shortcut
        elif choice == '2':
            print("继续测试下一个快捷键...")
        else:
            print("继续测试下一个快捷键...")
        
        print()
        time.sleep(2)  # 给用户时间观察
    
    print("所有快捷键测试完成，没有找到有效的快捷键")
    return None

def save_config(shortcut):
    """保存找到的快捷键到配置文件"""
    config_file = "config/user_config.json"
    
    # 创建配置目录
    os.makedirs("config", exist_ok=True)
    
    config_data = {}
    
    # 读取现有配置
    if os.path.exists(config_file):
        try:
            import json
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        except:
            pass
    
    # 添加快捷键配置
    config_data['keyboard_shortcut'] = shortcut
    config_data['use_keyboard_shortcut'] = True
    
    # 保存配置
    try:
        import json
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        print(f"✓ 已保存快捷键配置到: {config_file}")
        return True
    except Exception as e:
        print(f"✗ 保存配置失败: {e}")
        return False

if __name__ == "__main__":
    print("注意: 请确保程序有管理员权限")
    print()
    
    shortcut = test_keyboard_shortcuts()
    
    if shortcut:
        print()
        print("=" * 60)
        print(f"找到有效的快捷键: {shortcut}")
        
        if input("是否保存配置到文件? (Y/N): ").strip().upper() == 'Y':
            save_config(shortcut)
            print()
            print("配置已保存! 现在可以运行主程序了")
            print("程序将使用这个快捷键来控制触控板")
        else:
            print("配置未保存，请手动配置")
    else:
        print()
        print("=" * 60)
        print("未找到有效的快捷键")
        print("可能的原因:")
        print("1. 您的笔记本使用特殊的FN组合键")
        print("2. 需要安装特定的驱动程序")
        print("3. 可能需要使用设备管理器手动禁用")
        print()
        print("建议:")
        print("1. 查找您笔记本型号的触控板切换快捷键")
        print("2. 检查是否安装了触控板驱动程序")
        print("3. 尝试使用兼容模式")
    
    input("\n按回车键退出...")