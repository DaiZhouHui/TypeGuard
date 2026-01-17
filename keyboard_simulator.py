"""
键盘模拟器 - 用于模拟Fn+F11等系统快捷键
"""

import ctypes
import time
import threading
from ctypes import wintypes

# Windows API 常量
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105

VK_CONTROL = 0x11
VK_MENU = 0x12  # ALT键
VK_SHIFT = 0x10
VK_F11 = 0x7A
VK_F6 = 0x75
VK_FN = 0xFF  # FN键没有标准虚拟键码

# 导入Windows API
user32 = ctypes.windll.user32

class KeyboardSimulator:
    """键盘模拟器 - 用于模拟系统快捷键"""
    
    # 常见的触控板切换快捷键组合
    TOGGLE_SHORTCUTS = [
        ['F11'],           # F11
        ['F6'],            # F6
        ['F9'],            # F9
        ['F10'],           # F10
        ['control', 'F11'],  # Ctrl+F11
        ['control', 'F6'],   # Ctrl+F6
        ['alt', 'F11'],      # Alt+F11
        ['alt', 'F6'],       # Alt+F6
    ]
    
    def __init__(self):
        self.current_shortcut = None
        self.detect_best_shortcut()
    
    def detect_best_shortcut(self):
        """检测最佳的触控板切换快捷键"""
        # 默认使用F11，这在很多联想笔记本上有效
        self.current_shortcut = ['F11']
        print(f"使用默认快捷键: {self.current_shortcut}")
    
    def vk_from_key_name(self, key_name):
        """将按键名称转换为虚拟键码"""
        key_map = {
            'F6': 0x75,
            'F7': 0x76,
            'F8': 0x77,
            'F9': 0x78,
            'F10': 0x79,
            'F11': 0x7A,
            'F12': 0x7B,
            'control': 0x11,
            'ctrl': 0x11,
            'alt': 0x12,
            'shift': 0x10,
            'windows': 0x5B,
        }
        return key_map.get(key_name.upper(), 0)
    
    def send_key(self, vk_code, keydown=True):
        """发送单个按键事件"""
        # 找到活动窗口
        hwnd = user32.GetForegroundWindow()
        
        if keydown:
            user32.SendMessageW(hwnd, WM_KEYDOWN, vk_code, 0)
        else:
            user32.SendMessageW(hwnd, WM_KEYUP, vk_code, 0)
        
        time.sleep(0.05)  # 短暂延迟
    
    def send_shortcut(self, keys):
        """发送快捷键组合"""
        try:
            # 先按下所有修饰键
            for key in keys[:-1]:  # 除了最后一个键都是修饰键
                if key.lower() in ['control', 'ctrl', 'alt', 'shift', 'windows']:
                    self.send_key(self.vk_from_key_name(key), True)
            
            # 按下功能键
            self.send_key(self.vk_from_key_name(keys[-1]), True)
            time.sleep(0.1)
            
            # 释放功能键
            self.send_key(self.vk_from_key_name(keys[-1]), False)
            
            # 释放所有修饰键（逆序）
            for key in reversed(keys[:-1]):
                if key.lower() in ['control', 'ctrl', 'alt', 'shift', 'windows']:
                    self.send_key(self.vk_from_key_name(key), False)
            
            print(f"发送快捷键: {keys}")
            return True
        except Exception as e:
            print(f"发送快捷键失败: {e}")
            return False
    
    def toggle_touchpad_hotkey(self):
        """发送触控板切换快捷键"""
        return self.send_shortcut(self.current_shortcut)

# 备用方案：使用pyautogui
try:
    import pyautogui
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False

class PyAutoGUISimulator:
    """使用pyautogui模拟按键"""
    
    def __init__(self):
        self.shortcuts = [
            ['f11'],
            ['f6'],
            ['f9'],
            ['ctrl', 'f11'],
            ['ctrl', 'f6'],
            ['alt', 'f11'],
            ['alt', 'f6'],
        ]
    
    def send_shortcut(self, keys):
        """发送快捷键"""
        try:
            # 将按键组合转换为pyautogui格式
            if len(keys) == 1:
                pyautogui.press(keys[0])
            else:
                # 构建hotkey字符串
                modifiers = keys[:-1]
                key = keys[-1]
                
                # pyautogui的hotkey函数
                pyautogui.hotkey(*modifiers, key)
            
            print(f"PyAutoGUI发送快捷键: {keys}")
            return True
        except Exception as e:
            print(f"PyAutoGUI发送快捷键失败: {e}")
            return False

def get_keyboard_simulator():
    """获取键盘模拟器实例"""
    try:
        # 先尝试Windows API方法
        return KeyboardSimulator()
    except Exception as e:
        print(f"Windows API键盘模拟器初始化失败: {e}")
        
        # 回退到pyautogui
        if HAS_PYAUTOGUI:
            print("使用PyAutoGUI作为备选")
            return PyAutoGUISimulator()
        else:
            print("警告: 没有可用的键盘模拟器")
            return None