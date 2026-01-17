#!/usr/bin/env python3
"""
触控板自动开关工具
版本：2.2
作者：AI助手
更新：修复触控板控制问题，优化文件结构，添加键盘快捷键支持
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import time
import sys
import os
import json
import traceback
import ctypes
from datetime import datetime, timedelta
from enum import Enum
import logging
import logging.handlers
from typing import Optional, Dict, Any, List, Callable, Union
import atexit
import subprocess
import webbrowser
import platform

# 检测操作系统
PLATFORM = sys.platform
IS_WINDOWS = PLATFORM == 'win32'

# 导入平台相关模块 - 增强容错性
HAS_WINDOWS_DEPS = False
HAS_KEYBOARD_ALT = False

if IS_WINDOWS:
    try:
        import win32api
        import win32con
        import winreg
        HAS_WINDOWS_DEPS = True
    except ImportError as e:
        print(f"无法导入Windows依赖: {e}")
        HAS_WINDOWS_DEPS = False

try:
    from pynput import keyboard
    HAS_PYNPUT = True
except ImportError:
    HAS_PYNPUT = False

try:
    import keyboard as keyboard_alt
    HAS_KEYBOARD_ALT = True
except ImportError:
    HAS_KEYBOARD_ALT = False

# 尝试导入其他可选模块
try:
    from win10toast import ToastNotifier
    HAS_WIN10TOAST = True
except ImportError:
    HAS_WIN10TOAST = False

try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# 创建必要的目录
def create_directories():
    """创建必要的目录结构"""
    directories = ['config', 'log', 'dist']
    for directory in directories:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory, exist_ok=True)
                print(f"创建目录: {directory}")
            except Exception as e:
                print(f"创建目录 {directory} 失败: {e}")

create_directories()

# 配置日志 - 使用轮转文件处理器防止日志过大
def setup_logging():
    """设置日志配置"""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    # 清除现有处理器
    if logger.handlers:
        logger.handlers.clear()
    
    # 创建格式器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 文件处理器 - 带轮转，最大5MB，保留5个备份
    try:
        log_file = os.path.join('log', 'touchpad_manager.log')
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"无法创建日志文件: {e}")
        # 使用控制台日志作为后备
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()

class TouchpadState(Enum):
    """触控板状态枚举"""
    ENABLED = "enabled"
    DISABLED = "disabled"
    UNKNOWN = "unknown"
    
    @classmethod
    def from_bool(cls, value: bool):
        """从布尔值转换"""
        return cls.ENABLED if value else cls.DISABLED

class RegistryManager:
    """注册表管理器 - 增强版：支持多种控制方式"""
    
    # 多种可能的触控板注册表路径
    TOUCHPAD_KEY_PATHS = [
        # 微软精确式触控板 (Precision TouchPad)
        (r"Software\Microsoft\Windows\CurrentVersion\PrecisionTouchPad\Status", "Enabled"),
        
        # Synaptics 触控板 (常见于联想)
        (r"Software\Synaptics\SynTP\TouchPadPS2", "DisableDevice"),
        (r"Software\Synaptics\SynTPEnh", "DisableTouchPad"),
        
        # ELAN 触控板
        (r"Software\Elantech\SmartPad", "Disable"),
        
        # Alps 触控板
        (r"Software\Alps\Apoint\TouchPad", "Disable"),
        
        # 通用触控板设置
        (r"Software\Microsoft\Windows\CurrentVersion\Explorer", "DisableTouchPad"),
    ]
    
    AUTO_RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
    
    def __init__(self):
        self.detected_key_path: Optional[str] = None
        self.detected_value_name: Optional[str] = None
        self.key_value_type = winreg.REG_DWORD
        self.invert_logic = False
        self.compatibility_mode = False
        self.use_keyboard_shortcut = False  # 是否使用键盘快捷键
        self.keyboard_simulator = None
        
        # 检测控制方式
        self.detect_control_method()
    
    def detect_control_method(self):
        """检测最佳的控制方式"""
        # 先尝试注册表检测
        if self.detect_touchpad_registry():
            print("检测到有效的注册表控制方式")
            return True
        else:
            # 尝试初始化键盘模拟器
            try:
                from keyboard_simulator import get_keyboard_simulator
                self.keyboard_simulator = get_keyboard_simulator()
                if self.keyboard_simulator:
                    self.use_keyboard_shortcut = True
                    self.compatibility_mode = True
                    print("将使用键盘快捷键控制触控板")
                    return True
            except ImportError:
                print("键盘模拟器不可用")
            
            print("未找到有效的触控板控制方式")
            return False
    
    def set_touchpad_state(self, enable: bool) -> bool:
        """设置触控板状态 - 使用多种方法"""
        # 记录操作
        action = "启用" if enable else "禁用"
        print(f"尝试{action}触控板...")
        
        # 方法1: 如果检测到注册表方式，优先使用
        if not self.compatibility_mode and self.detected_key_path:
            success = self._set_via_registry(enable)
            if success:
                return True
        
        # 方法2: 使用键盘快捷键（用于切换触控板）
        if self.use_keyboard_shortcut and self.keyboard_simulator:
            # 注意：快捷键通常是切换而不是设置特定状态
            # 所以我们先检测当前状态，然后决定是否需要切换
            current_state = self.get_touchpad_state()
            if current_state is not None:
                # 如果当前状态与目标状态不同，发送快捷键
                if (enable and not current_state) or (not enable and current_state):
                    print(f"通过快捷键切换触控板状态")
                    return self._send_touchpad_hotkey()
                else:
                    print(f"触控板已经是目标状态，无需操作")
                    return True
            else:
                # 无法检测状态，直接发送快捷键
                print(f"无法检测当前状态，直接发送切换快捷键")
                return self._send_touchpad_hotkey()
        
        # 方法3: 使用兼容模式（设备管理器）
        return self._set_via_compatibility(enable)
    
    def _send_touchpad_hotkey(self) -> bool:
        """发送触控板切换快捷键"""
        if not self.keyboard_simulator:
            return False
        
        try:
            # 检查模拟器是否有 toggle_touchpad_hotkey 方法
            if hasattr(self.keyboard_simulator, 'toggle_touchpad_hotkey'):
                return self.keyboard_simulator.toggle_touchpad_hotkey()
            # 如果有 send_shortcut 方法，使用默认快捷键
            elif hasattr(self.keyboard_simulator, 'send_shortcut'):
                # 发送 F11 快捷键（最常见的触控板切换键）
                return self.keyboard_simulator.send_shortcut(['F11'])
            else:
                print("键盘模拟器没有可用的快捷键发送方法")
                return False
        except Exception as e:
            print(f"发送触控板快捷键失败: {e}")
            return False
    
    def _set_via_registry(self, enable: bool) -> bool:
        """通过注册表设置触控板状态"""
        try:
            # 检查必需的注册表键值
            if not self.detected_key_path or not self.detected_value_name:
                print("注册表键路径或值名称为空，无法通过注册表设置")
                return False
            
            # 根据逻辑反转设置计算值
            if self.invert_logic:
                value = 0 if enable else 1  # 启用=0, 禁用=1
            else:
                value = 1 if enable else 0  # 启用=1, 禁用=0
            
            # 打开注册表键进行写操作
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, 
                self.detected_key_path, 
                0, 
                winreg.KEY_SET_VALUE | winreg.KEY_READ
            )
            
            winreg.SetValueEx(key, self.detected_value_name, 0, self.key_value_type, value)
            winreg.CloseKey(key)
            
            # 通知系统设置已更改
            try:
                # 修复：确保传递正确的参数类型
                win32api.SendMessage(win32con.HWND_BROADCAST, win32con.WM_SETTINGCHANGE, 0, 0)
            except Exception as e:
                print(f"发送设置更改消息失败: {e}")
                # 继续执行，这不是致命错误
            
            print(f"通过注册表设置触控板: {'启用' if enable else '禁用'} (值={value})")
            return True
            
        except Exception as e:
            print(f"注册表设置失败: {e}")
            return False
    
    def _set_via_compatibility(self, enable: bool) -> bool:
        """兼容模式设置触控板状态"""
        try:
            if enable:
                # 启用触控板
                cmd = 'powershell "Enable-PnpDevice -Confirm:$false -InstanceId (Get-PnpDevice -Class HIDClass | Where-Object {$_.FriendlyName -like \"*TouchPad*\" -or $_.FriendlyName -like \"*Touch Pad*\"}).InstanceId"'
            else:
                # 禁用触控板
                cmd = 'powershell "Disable-PnpDevice -Confirm:$false -InstanceId (Get-PnpDevice -Class HIDClass | Where-Object {$_.FriendlyName -like \"*TouchPad*\" -or $_.FriendlyName -like \"*Touch Pad*\"}).InstanceId"'
            
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            
            if result.returncode == 0:
                print(f"兼容模式: 触控板已{'启用' if enable else '禁用'}")
                return True
            else:
                print(f"兼容模式设置失败: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"兼容模式执行失败: {e}")
            return False
    
    def detect_touchpad_registry(self) -> bool:
        """检测触控板注册表位置"""
        if not HAS_WINDOWS_DEPS:
            return False
            
        print("正在检测触控板注册表位置...")
        
        for key_path, value_name in self.TOUCHPAD_KEY_PATHS:
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
                try:
                    value, reg_type = winreg.QueryValueEx(key, value_name)
                    
                    # 记录找到的键
                    self.detected_key_path = key_path
                    self.detected_value_name = value_name
                    self.key_value_type = reg_type
                    
                    print(f"检测到触控板注册表: {key_path}\\{value_name}")
                    print(f"注册表类型: {reg_type}, 当前值: {value}")
                    
                    # 判断是否需要反转逻辑
                    if "Disable" in value_name:
                        self.invert_logic = True
                        print("检测到禁用式注册表键，启用反转逻辑")
                    
                    winreg.CloseKey(key)
                    return True
                    
                except FileNotFoundError:
                    winreg.CloseKey(key)
                    continue
                except Exception as e:
                    winreg.CloseKey(key)
                    print(f"读取注册表失败 {key_path}\\{value_name}: {e}")
                    
            except FileNotFoundError:
                continue
            except Exception as e:
                print(f"打开注册表键失败 {key_path}: {e}")
        
        print("未找到标准触控板注册表键")
        return False
    
    def get_touchpad_state(self) -> Optional[bool]:
        """获取触控板状态 - 通过多种方法"""
        if not HAS_WINDOWS_DEPS:
            return None
        
        # 方法1: 通过注册表
        if self.detected_key_path and not self.compatibility_mode:
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.detected_key_path, 0, winreg.KEY_READ)
                value, _ = winreg.QueryValueEx(key, self.detected_value_name)
                winreg.CloseKey(key)
                
                # 根据逻辑反转设置返回状态
                if self.invert_logic:
                    return bool(value == 0)
                else:
                    return bool(value)
                    
            except Exception as e:
                print(f"注册表读取失败: {e}")
        
        # 方法2: 通过设备管理器（兼容模式）
        try:
            cmd = 'powershell "(Get-PnpDevice -Class HIDClass | Where-Object {$_.FriendlyName -like \"*TouchPad*\" -or $_.FriendlyName -like \"*Touch Pad*\"}).Status"'
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            
            if result.returncode == 0:
                status = result.stdout.strip()
                print(f"设备管理器状态: {status}")
                return "OK" in status or "Running" in status
            else:
                print(f"设备管理器查询失败: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"设备管理器查询异常: {e}")
            return None
    
    def set_auto_start(self, app_name: str, app_path: str, enable: bool) -> bool:
        """设置开机自启动"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.AUTO_RUN_KEY_PATH, 0, winreg.KEY_SET_VALUE)
            
            if enable:
                # 添加开机启动
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{app_path}" --minimized')
                print(f"已设置开机自启动: {app_name}")
            else:
                # 移除开机启动
                try:
                    winreg.DeleteValue(key, app_name)
                    print(f"已移除开机自启动: {app_name}")
                except FileNotFoundError:
                    # 如果键不存在，那就算了
                    pass
            
            winreg.CloseKey(key)
            return True
            
        except Exception as e:
            print(f"设置开机自启动失败: {e}")
            return False

class HotkeyManager:
    """热键管理器 - 支持多种热键库"""
    
    def __init__(self):
        self.hotkeys: Dict[str, Callable] = {}
        self.listener = None
        self.alt_listener = None
        
    def register_hotkey(self, key_combination: str, callback: Callable, use_alt_lib=False):
        """注册热键"""
        self.hotkeys[key_combination] = callback
        logger.info(f"注册热键: {key_combination}")
        
        # 如果使用备用键盘库且支持
        if use_alt_lib and HAS_KEYBOARD_ALT:
            try:
                keyboard_alt.add_hotkey(key_combination, callback)
                logger.info(f"使用keyboard库注册热键: {key_combination}")
            except Exception as e:
                logger.error(f"使用keyboard库注册热键失败: {e}")
    
    def start_listening(self, use_pynput=True):
        """开始监听热键"""
        # 如果pynput可用，优先使用
        if use_pynput and HAS_PYNPUT and not self.listener:
            try:
                self.listener = keyboard.GlobalHotKeys(self.hotkeys)
                self.listener.start()
                logger.info("pynput热键监听已启动")
            except Exception as e:
                logger.error(f"pynput热键监听启动失败: {e}")
                self.listener = None
        
        # 如果pynput不可用或启动失败，尝试备用库
        if not self.listener and HAS_KEYBOARD_ALT:
            try:
                # keyboard库不需要额外启动，已通过add_hotkey注册
                logger.info("keyboard热键监听已准备")
                return True
            except Exception as e:
                logger.error(f"keyboard热键监听准备失败: {e}")
        
        return self.listener is not None or HAS_KEYBOARD_ALT
    
    def stop_listening(self):
        """停止监听热键"""
        # 停止pynput监听器
        if self.listener:
            try:
                self.listener.stop()
                self.listener = None
                logger.info("pynput热键监听已停止")
            except Exception as e:
                logger.error(f"停止pynput热键监听失败: {e}")
        
        # 清除keyboard库的热键
        if HAS_KEYBOARD_ALT:
            try:
                keyboard_alt.unhook_all_hotkeys()
                logger.info("keyboard热键已清除")
            except Exception as e:
                logger.error(f"清除keyboard热键失败: {e}")

class ConfigManager:
    """配置管理器"""
    
    CONFIG_VERSION = "2.2"
    
    def __init__(self):
        self.config_dir = "config"
        self.log_dir = "log"
        
        # 默认配置路径
        self.default_config_path = os.path.join(self.config_dir, "default_config.json")
        self.user_config_path = os.path.join(self.config_dir, "user_config.json")
        
        # 确保目录存在
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)
        
        # 加载配置
        self.config = self.load_config()
    
    def get_default_config(self):
        """获取默认配置"""
        return {
            "version": self.CONFIG_VERSION,
            "idle_threshold": 5.0,  # 默认5秒
            "auto_start": False,
            "start_minimized": False,
            "enable_sounds": True,
            "enable_notifications": True,
            "use_keyboard_shortcut": False,
            "enable_compatibility_mode": True,  # 启用兼容模式
            "hotkeys": {
                "toggle_touchpad": "ctrl+alt+t",
                "toggle_monitoring": "ctrl+alt+m",
                "exit_app": "ctrl+alt+q"
            },
            "appearance": {
                "theme": "default",
                "font_size": 10,
                "window_width": 900,
                "window_height": 700
            },
            "compatibility": {
                "lenovo_legion": True,
                "try_multiple_registry_paths": True,
                "delay_before_enable": 0.2,
                "min_disable_time": 0.5
            },
            "logging": {
                "level": "INFO",
                "max_size_mb": 5,
                "backup_count": 5
            },
            "keyboard_shortcut": {
                "enabled": False,
                "keys": ["F11"],
                "display": "F11"
            }
        }
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置"""
        # 首先加载默认配置
        default_config = self.get_default_config()
        
        # 尝试加载用户配置
        if os.path.exists(self.user_config_path):
            try:
                with open(self.user_config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                
                # 合并配置，用户配置覆盖默认配置
                config = self.merge_configs(default_config, user_config)
                logger.info(f"从 {self.user_config_path} 加载用户配置")
                return config
            except Exception as e:
                logger.error(f"加载用户配置失败: {e}")
        
        # 如果用户配置不存在，尝试加载默认配置文件
        if os.path.exists(self.default_config_path):
            try:
                with open(self.default_config_path, 'r', encoding='utf-8') as f:
                    default_file_config = json.load(f)
                
                # 合并配置
                config = self.merge_configs(default_config, default_file_config)
                logger.info(f"从 {self.default_config_path} 加载默认配置")
                return config
            except Exception as e:
                logger.error(f"加载默认配置文件失败: {e}")
        
        # 都没有，返回默认配置
        logger.info("使用内置默认配置")
        return default_config.copy()
    
    def merge_configs(self, base_config: Dict, override_config: Dict) -> Dict:
        """深度合并两个配置字典"""
        result = base_config.copy()
        
        for key, value in override_config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self.merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def save_config(self) -> bool:
        """保存用户配置"""
        try:
            with open(self.user_config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"配置已保存到 {self.user_config_path}")
            return True
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            return False
    
    def get(self, key: str, default=None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any, save=True):
        """设置配置值"""
        keys = key.split('.')
        config = self.config
        
        # 导航到嵌套字典的最后一个键
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        
        if save:
            self.save_config()

class TouchpadManager:
    """触控板管理器 - 增强版：支持多种控制方式和状态检测"""
    
    def __init__(self):
        self.touchpad_state = TouchpadState.UNKNOWN
        self.last_activity_time = time.time()
        self.is_monitoring = False
        self.monitor_thread = None
        self.keyboard_listener = None
        self.idle_threshold = 5.0  # 默认5秒
        
        # 统计数据
        self.stats = {
            "disabled_count": 0,
            "enabled_count": 0,
            "total_runtime": 0,
            "start_time": None,
            "last_disable_time": None,
            "last_enable_time": None,
            "last_keypress_time": None
        }
        
        # 初始化管理器
        self.config_manager = ConfigManager()
        self.registry_manager = RegistryManager()
        self.hotkey_manager = HotkeyManager()
        
        # 加载配置
        self.load_config()
        
        # 注册退出清理
        atexit.register(self.cleanup)
        
        logger.info("触控板管理器初始化完成")
    
    def load_config(self):
        """加载配置"""
        self.idle_threshold = self.config_manager.get("idle_threshold", 5.0)
        logger.info(f"加载配置: 空闲阈值={self.idle_threshold}秒")
    
    def detect_touchpad(self) -> bool:
        """检测触控板状态"""
        try:
            state = self.registry_manager.get_touchpad_state()
            if state is not None:
                self.touchpad_state = TouchpadState.from_bool(state)
                logger.info(f"触控板状态: {self.touchpad_state.value}")
                return True
            else:
                self.touchpad_state = TouchpadState.UNKNOWN
                logger.warning("无法检测触控板状态")
                return False
        except Exception as e:
            logger.error(f"检测触控板时出错: {e}")
            self.touchpad_state = TouchpadState.UNKNOWN
            return False
    
    def set_touchpad(self, enable: bool, force=False) -> bool:
        """设置触控板状态"""
        # 如果状态相同且不强制，则跳过
        current_state_bool = self.touchpad_state == TouchpadState.ENABLED
        if not force and current_state_bool == enable:
            logger.debug(f"触控板状态已为{'启用' if enable else '禁用'}，跳过设置")
            return True
        
        try:
            if self.registry_manager.set_touchpad_state(enable):
                self.touchpad_state = TouchpadState.ENABLED if enable else TouchpadState.DISABLED
                
                # 更新统计
                if enable:
                    self.stats["enabled_count"] += 1
                    self.stats["last_enable_time"] = time.time()
                else:
                    self.stats["disabled_count"] += 1
                    self.stats["last_disable_time"] = time.time()
                
                # 播放声音提示
                if self.config_manager.get("enable_sounds") and HAS_WINSOUND:
                    self.play_sound(enable)
                
                logger.info(f"触控板已{'启用' if enable else '禁用'}")
                return True
            else:
                logger.error(f"触控板{'启用' if enable else '禁用'}失败")
                return False
        except Exception as e:
            logger.error(f"设置触控板时出错: {e}")
            return False
    
    def play_sound(self, enable: bool):
        """播放声音提示"""
        try:
            if enable:
                winsound.Beep(1000, 100)  # 启用声音
            else:
                winsound.Beep(500, 100)   # 禁用声音
        except Exception as e:
            logger.warning(f"播放声音失败: {e}")
    
    def on_key_press(self, key):
        """键盘按下事件处理"""
        try:
            current_time = time.time()
            self.last_activity_time = current_time
            self.stats["last_keypress_time"] = current_time
            
            # 只有在监控中且触控板启用时才禁用它
            if self.is_monitoring and self.touchpad_state == TouchpadState.ENABLED:
                logger.debug("检测到按键，禁用触控板")
                self.set_touchpad(False)
            
            return True  # 继续传递事件
        except Exception as e:
            logger.error(f"处理按键事件时出错: {e}")
            return True
    
    def start_keyboard_listener(self):
        """启动键盘监听器"""
        if HAS_PYNPUT:
            try:
                self.keyboard_listener = keyboard.Listener(on_press=self.on_key_press)
                self.keyboard_listener.start()
                logger.info("pynput键盘监听器已启动")
                return True
            except Exception as e:
                logger.error(f"启动pynput键盘监听器失败: {e}")
                return False
        else:
            logger.warning("pynput不可用，键盘监听不可用")
            return False
    
    def monitor_activity(self):
        """监控活动状态"""
        logger.info("开始监控活动状态")
        
        # 添加延迟，避免立即启用
        last_disable_time = time.time()
        
        while self.is_monitoring:
            try:
                current_time = time.time()
                idle_time = current_time - self.last_activity_time
                
                # 获取配置的延迟时间
                delay_before_enable = self.config_manager.get("compatibility.delay_before_enable", 0.2)
                min_disable_duration = self.config_manager.get("compatibility.min_disable_time", 0.5)  # 最小禁用时间
                
                # 计算从上次禁用到现在的时间
                time_since_last_disable = current_time - last_disable_time
                
                # 如果空闲时间超过阈值且触控板被禁用，启用它
                if (idle_time >= self.idle_threshold and 
                    self.touchpad_state == TouchpadState.DISABLED and
                    time_since_last_disable >= min_disable_duration):
                    
                    logger.debug(f"空闲 {idle_time:.1f}秒，启用触控板")
                    
                    # 添加一个小延迟，确保系统准备好
                    time.sleep(delay_before_enable)
                    self.set_touchpad(True)
                    last_disable_time = current_time
                
                # 更新运行时间统计
                if self.stats["start_time"]:
                    self.stats["total_runtime"] = current_time - self.stats["start_time"]
                
                # 降低CPU使用率
                time.sleep(0.3)  # 稍微增加睡眠时间
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"监控循环错误: {e}")
                time.sleep(1)
        
        logger.info("活动监控线程结束")
    
    def start_monitoring(self) -> bool:
        """开始监控"""
        if self.is_monitoring:
            logger.warning("监控已在运行中")
            return False
        
        # 检测触控板状态
        if not self.detect_touchpad():
            logger.warning("触控板检测失败，但将继续尝试")
        
        self.is_monitoring = True
        self.stats["start_time"] = time.time()
        self.last_activity_time = time.time()
        
        # 启动键盘监听
        if not self.start_keyboard_listener():
            logger.warning("键盘监听启动失败，触控板自动禁用功能可能无法正常工作")
        
        # 启动活动监控线程
        try:
            self.monitor_thread = threading.Thread(
                target=self.monitor_activity,
                daemon=True,
                name="ActivityMonitor"
            )
            self.monitor_thread.start()
            logger.info("活动监控线程已启动")
        except Exception as e:
            logger.error(f"启动监控线程失败: {e}")
            self.is_monitoring = False
            return False
        
        logger.info("触控板监控已启动")
        return True
    
    def stop_monitoring(self) -> bool:
        """停止监控"""
        if not self.is_monitoring:
            logger.info("监控未运行")
            return True
        
        logger.info("正在停止监控...")
        self.is_monitoring = False
        
        # 停止键盘监听
        if self.keyboard_listener:
            try:
                self.keyboard_listener.stop()
                logger.info("键盘监听器已停止")
            except Exception as e:
                logger.error(f"停止键盘监听器失败: {e}")
            finally:
                self.keyboard_listener = None
        
        # 等待监控线程结束
        if self.monitor_thread and self.monitor_thread.is_alive():
            try:
                self.monitor_thread.join(timeout=3.0)
                logger.info("监控线程已停止")
            except Exception as e:
                logger.error(f"等待监控线程停止时出错: {e}")
        
        # 确保触控板被启用
        if self.touchpad_state == TouchpadState.DISABLED:
            self.set_touchpad(True, force=True)
        
        # 更新统计信息
        if self.stats["start_time"]:
            self.stats["total_runtime"] = time.time() - self.stats["start_time"]
            self.stats["start_time"] = None
        
        logger.info("触控板监控已停止")
        return True
    
    def toggle_monitoring(self) -> bool:
        """切换监控状态"""
        if self.is_monitoring:
            return self.stop_monitoring()
        else:
            return self.start_monitoring()
    
    def toggle_touchpad(self) -> bool:
        """手动切换触控板状态"""
        if self.touchpad_state == TouchpadState.ENABLED:
            return self.set_touchpad(False)
        else:
            return self.set_touchpad(True)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self.stats.copy()
        
        if self.stats["start_time"]:
            stats["total_runtime"] = time.time() - self.stats["start_time"]
        
        # 计算平均禁用间隔
        if stats["disabled_count"] > 1 and stats["last_disable_time"] and stats["last_enable_time"]:
            stats["avg_disable_interval"] = (stats["last_disable_time"] - stats["last_enable_time"]) / max(1, stats["disabled_count"] - 1)
        else:
            stats["avg_disable_interval"] = 0
        
        # 当前会话时间
        stats["current_session"] = time.time() - self.stats["start_time"] if self.stats["start_time"] else 0
        
        # 空闲阈值
        stats["idle_threshold"] = self.idle_threshold
        
        return stats
    
    def cleanup(self):
        """清理资源"""
        logger.info("正在清理资源...")
        self.stop_monitoring()
        self.hotkey_manager.stop_listening()
        logger.info("资源清理完成")

class TouchpadApp:
    """主应用程序"""
    
    def __init__(self):
        self.root = None
        self.manager = None
        self.config_manager = None
        
        # 初始化状态
        self.is_minimized = False
        self.update_interval = 1000  # UI更新间隔(ms)
        self.last_update_time = 0
        
        # 初始化UI组件引用
        self.status_labels = {}
        self.stats_labels = {}
        self.log_text = None
        
        # Tkinter变量将在initialize_app中创建
        self.auto_start_var = None
        self.start_minimized_var = None
        self.enable_sounds_var = None
        self.enable_notifications_var = None
        self.use_keyboard_shortcut_var = None
        self.compatibility_mode_var = None
        self.idle_var = None
        self.idle_label = None
        
        try:
            self.initialize_app()
        except Exception as e:
            logger.critical(f"应用程序初始化失败: {e}")
            traceback.print_exc()
            # 注意：此时还没有创建根窗口，不能使用messagebox
            print(f"应用程序启动失败:\n{str(e)}")
            sys.exit(1)
    
    def initialize_app(self):
        """初始化应用程序"""
        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("触控板自动开关工具 v2.2版")
        
        # 设置默认窗口大小
        default_width = 900
        default_height = 700
        
        # 获取屏幕尺寸
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 计算窗口位置（居中）
        x = (screen_width - default_width) // 2
        y = (screen_height - default_height) // 2
        
        self.root.geometry(f"{default_width}x{default_height}+{x}+{y}")
        self.root.resizable(True, True)
        
        # 设置窗口图标
        self.set_window_icon()
        
        # 初始化管理器
        self.manager = TouchpadManager()
        self.config_manager = self.manager.config_manager
        
        # 初始化Tkinter变量（必须在创建根窗口后）
        self.auto_start_var = tk.BooleanVar()
        self.start_minimized_var = tk.BooleanVar()
        self.enable_sounds_var = tk.BooleanVar()
        self.enable_notifications_var = tk.BooleanVar()
        self.use_keyboard_shortcut_var = tk.BooleanVar()
        self.compatibility_mode_var = tk.BooleanVar()
        
        # 加载窗口大小配置
        self.load_window_geometry()
        
        # 设置UI
        self.setup_ui()
        
        # 加载设置
        self.load_settings()
        
        # 设置热键
        self.setup_hotkeys()
        
        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 绑定窗口事件
        self.bind_window_events()
        
        # 启动UI更新循环
        self.update_ui()
        
        # 检查启动参数
        self.handle_startup_arguments()
        
        logger.info("应用程序初始化完成")
    
    def set_window_icon(self):
        """设置窗口图标"""
        icon_paths = [
            os.path.join("config", "icon.ico"),
            "config/icon.ico",
            os.path.join(sys._MEIPASS, "config", "icon.ico") if getattr(sys, 'frozen', False) else None
        ]
        
        for icon_path in icon_paths:
            if icon_path and os.path.exists(icon_path):
                try:
                    self.root.iconbitmap(icon_path)
                    logger.info(f"已设置窗口图标: {icon_path}")
                    return
                except Exception as e:
                    logger.warning(f"设置图标失败 {icon_path}: {e}")
        
        logger.warning("未找到可用的图标文件")
    
    def load_window_geometry(self):
        """加载窗口几何设置"""
        try:
            width = self.config_manager.get("appearance.window_width", 900)
            height = self.config_manager.get("appearance.window_height", 700)
            
            # 确保窗口大小在合理范围内
            width = max(600, min(1920, width))
            height = max(400, min(1080, height))
            
            self.root.geometry(f"{width}x{height}")
        except Exception as e:
            logger.warning(f"加载窗口几何设置失败: {e}")
    
    def save_window_geometry(self):
        """保存窗口几何设置"""
        try:
            geometry = self.root.geometry()
            # 格式: "宽度x高度+x坐标+y坐标"
            dimensions = geometry.split('+')[0]
            width, height = map(int, dimensions.split('x'))
            
            self.config_manager.set("appearance.window_width", width)
            self.config_manager.set("appearance.window_height", height)
            logger.debug(f"保存窗口大小: {width}x{height}")
        except Exception as e:
            logger.warning(f"保存窗口几何设置失败: {e}")
    
    def bind_window_events(self):
        """绑定窗口事件"""
        # 窗口大小改变事件
        self.root.bind('<Configure>', self.on_window_configure)
        
        # 窗口获得焦点事件
        self.root.bind('<FocusIn>', self.on_window_focus)
        
        # 键盘快捷键
        self.root.bind('<Control-s>', lambda e: self.start_monitoring())
        self.root.bind('<Control-p>', lambda e: self.stop_monitoring())
        self.root.bind('<Control-t>', lambda e: self.toggle_touchpad())
        self.root.bind('<Control-q>', lambda e: self.on_closing())
    
    def on_window_configure(self, event):
        """窗口配置改变事件"""
        if event.widget == self.root:
            # 防抖：只在窗口大小稳定后保存
            current_time = time.time()
            if current_time - self.last_update_time > 0.5:  # 500ms防抖
                self.save_window_geometry()
                self.last_update_time = current_time
    
    def on_window_focus(self, event):
        """窗口获得焦点事件"""
        # 更新状态显示
        if self.manager:
            self.manager.detect_touchpad()
    
    def setup_ui(self):
        """设置用户界面"""
        # 设置字体
        default_font = ("Microsoft YaHei", 10)
        
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # 标题栏
        self.create_title_bar(main_frame)
        
        # 主内容区域
        self.create_main_content(main_frame)
        
        # 状态栏
        self.create_status_bar(main_frame)
        
        logger.info("UI设置完成")
    
    def create_title_bar(self, parent):
        """创建标题栏"""
        title_frame = ttk.Frame(parent)
        title_frame.grid(row=0, column=0, columnspan=3, pady=(0, 10), sticky=(tk.W, tk.E))
        
        # 标题
        title_label = ttk.Label(
            title_frame, 
            text="🖱️ 触控板自动开关工具 v2.2",
            font=("Microsoft YaHei", 16, "bold")
        )
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        # 版本信息
        version_label = ttk.Label(
            title_frame,
            text="专为笔记本优化 | 打字时自动禁用触控板，停止后恢复",
            font=("Microsoft YaHei", 9)
        )
        version_label.grid(row=1, column=0, sticky=tk.W, pady=(2, 0))
        
        # 右侧按钮组
        button_frame = ttk.Frame(title_frame)
        button_frame.grid(row=0, column=1, rowspan=2, sticky=tk.E)
        
        # 控制按钮
        ttk.Button(button_frame, text="设置", command=self.open_settings, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="最小化", command=self.minimize_window, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="退出", command=self.on_closing, width=8).pack(side=tk.LEFT, padx=2)
        
        title_frame.columnconfigure(0, weight=1)
    
    def create_main_content(self, parent):
        """创建主内容区域"""
        # 创建笔记本(选项卡)
        notebook = ttk.Notebook(parent)
        notebook.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 主控制选项卡
        control_frame = ttk.Frame(notebook, padding="15")
        notebook.add(control_frame, text="主控制")
        
        # 状态显示区域
        self.create_status_display(control_frame)
        
        # 控制按钮区域
        self.create_control_buttons(control_frame)
        
        # 设置区域
        self.create_settings_area(control_frame)
        
        # 统计信息选项卡
        stats_frame = ttk.Frame(notebook, padding="15")
        notebook.add(stats_frame, text="统计信息")
        self.create_stats_display(stats_frame)
        
        # 日志选项卡
        log_frame = ttk.Frame(notebook, padding="15")
        notebook.add(log_frame, text="操作日志")
        self.create_log_display(log_frame)
        
        # 关于选项卡
        about_frame = ttk.Frame(notebook, padding="15")
        notebook.add(about_frame, text="关于")
        self.create_about_display(about_frame)
        
        # 配置网格权重
        control_frame.columnconfigure(0, weight=1)
        control_frame.rowconfigure(3, weight=1)
    
    def create_status_display(self, parent):
        """创建状态显示区域"""
        status_frame = ttk.LabelFrame(parent, text="当前状态", padding="15")
        status_frame.grid(row=0, column=0, columnspan=2, pady=(0, 15), sticky=(tk.W, tk.E))
        
        # 状态网格
        status_grid = ttk.Frame(status_frame)
        status_grid.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # 触控板状态
        ttk.Label(status_grid, text="触控板状态:", font=("Microsoft YaHei", 10)).grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.status_labels['touchpad'] = ttk.Label(
            status_grid, 
            text="未知", 
            font=("Microsoft YaHei", 10, "bold"),
            foreground="gray"
        )
        self.status_labels['touchpad'].grid(row=0, column=1, sticky=tk.W, padx=(0, 30))
        
        # 监控状态
        ttk.Label(status_grid, text="监控状态:", font=("Microsoft YaHei", 10)).grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.status_labels['monitoring'] = ttk.Label(
            status_grid, 
            text="已停止", 
            font=("Microsoft YaHei", 10, "bold"),
            foreground="red"
        )
        self.status_labels['monitoring'].grid(row=0, column=3, sticky=tk.W)
        
        # 状态指示器
        self.status_indicator = tk.Canvas(
            status_frame, 
            width=20, 
            height=20, 
            bg="white", 
            relief="sunken", 
            bd=1,
            highlightthickness=0
        )
        self.status_indicator.grid(row=1, column=0, pady=(10, 0), sticky=tk.W)
        
        # 状态描述
        self.status_description = ttk.Label(
            status_frame, 
            text="就绪", 
            font=("Microsoft YaHei", 9)
        )
        self.status_description.grid(row=1, column=0, pady=(10, 0), padx=(30, 0), sticky=tk.W)
        
        status_frame.columnconfigure(0, weight=1)
    
    def create_control_buttons(self, parent):
        """创建控制按钮区域"""
        button_frame = ttk.LabelFrame(parent, text="控制", padding="15")
        button_frame.grid(row=1, column=0, columnspan=2, pady=(0, 15), sticky=(tk.W, tk.E))
        
        # 主控制按钮
        self.start_button = ttk.Button(
            button_frame, 
            text="▶ 开始监控",
            command=self.start_monitoring,
            width=15
        )
        self.start_button.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_button = ttk.Button(
            button_frame,
            text="⏹ 停止监控",
            command=self.stop_monitoring,
            width=15,
            state=tk.DISABLED
        )
        self.stop_button.grid(row=0, column=1, padx=(0, 10))
        
        self.toggle_button = ttk.Button(
            button_frame,
            text="🔄 手动切换",
            command=self.toggle_touchpad,
            width=15
        )
        self.toggle_button.grid(row=0, column=2)
        
        # 空闲时间设置
        idle_frame = ttk.Frame(button_frame)
        idle_frame.grid(row=1, column=0, columnspan=3, pady=(15, 0))
        
        ttk.Label(idle_frame, text="空闲时间(秒):").pack(side=tk.LEFT)
        
        self.idle_var = tk.DoubleVar(value=self.manager.idle_threshold)
        idle_scale = ttk.Scale(
            idle_frame,
            from_=1.0,
            to=10.0,
            variable=self.idle_var,
            orient=tk.HORIZONTAL,
            length=200,
            command=self.update_idle_threshold
        )
        idle_scale.pack(side=tk.LEFT, padx=(10, 5))
        
        self.idle_label = ttk.Label(idle_frame, text=f"{self.idle_var.get():.1f}秒")
        self.idle_label.pack(side=tk.LEFT)
        
        # 测试按钮
        ttk.Button(
            idle_frame,
            text="测试触控板",
            command=self.test_touchpad,
            width=10
        ).pack(side=tk.LEFT, padx=(20, 0))
        
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)
    
    def create_settings_area(self, parent):
        """创建设置区域"""
        settings_frame = ttk.LabelFrame(parent, text="快速设置", padding="15")
        settings_frame.grid(row=2, column=0, columnspan=2, pady=(0, 15), sticky=(tk.W, tk.E))
        
        # 第一行
        row1_frame = ttk.Frame(settings_frame)
        row1_frame.grid(row=0, column=0, sticky=tk.W)
        
        # 自动启动
        auto_start_cb = ttk.Checkbutton(
            row1_frame,
            text="开机自动启动",
            variable=self.auto_start_var,
            command=self.toggle_auto_start
        )
        auto_start_cb.grid(row=0, column=0, sticky=tk.W)
        
        # 启动最小化
        start_minimized_cb = ttk.Checkbutton(
            row1_frame,
            text="启动时最小化到托盘",
            variable=self.start_minimized_var,
            command=self.toggle_start_minimized
        )
        start_minimized_cb.grid(row=0, column=1, sticky=tk.W, padx=(20, 0))
        
        # 第二行
        row2_frame = ttk.Frame(settings_frame)
        row2_frame.grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        
        # 启用声音
        enable_sounds_cb = ttk.Checkbutton(
            row2_frame,
            text="启用声音提示",
            variable=self.enable_sounds_var,
            command=self.toggle_sounds
        )
        enable_sounds_cb.grid(row=0, column=0, sticky=tk.W)
        
        # 启用通知
        enable_notifications_cb = ttk.Checkbutton(
            row2_frame,
            text="启用桌面通知",
            variable=self.enable_notifications_var,
            command=self.toggle_notifications
        )
        enable_notifications_cb.grid(row=0, column=1, sticky=tk.W, padx=(20, 0))
        
        # 第三行
        row3_frame = ttk.Frame(settings_frame)
        row3_frame.grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
        
        # 键盘快捷键模式
        use_keyboard_shortcut_cb = ttk.Checkbutton(
            row3_frame,
            text="使用键盘快捷键控制触控板",
            variable=self.use_keyboard_shortcut_var,
            command=self.toggle_keyboard_shortcut
        )
        use_keyboard_shortcut_cb.grid(row=0, column=0, sticky=tk.W)

        # 测试快捷键按钮
        ttk.Button(
            row3_frame,
            text="测试快捷键",
            command=self.test_keyboard_shortcut,
            width=12
        ).grid(row=0, column=1, sticky=tk.W, padx=(20, 0))
                        
        # 第四行  
        row4_frame = ttk.Frame(settings_frame)
        row4_frame.grid(row=3, column=0, sticky=tk.W, pady=(10, 0))                                                      
        
        # 兼容模式
        compatibility_mode_cb = ttk.Checkbutton(
            row4_frame,
            text="启用兼容模式(推荐笔记本使用)",
            variable=self.compatibility_mode_var,
            command=self.toggle_compatibility_mode
        )
        compatibility_mode_cb.grid(row=0, column=0, sticky=tk.W)
        
        settings_frame.columnconfigure(0, weight=1)
    
    def create_stats_display(self, parent):
        """创建统计信息显示"""
        stats_frame = ttk.Frame(parent)
        stats_frame.pack(fill=tk.BOTH, expand=True)
        
        # 统计信息网格
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 统计信息标签
        stats_data = [
            ("禁用次数", "disabled_count", "次"),
            ("启用次数", "enabled_count", "次"),
            ("总运行时间", "total_runtime", ""),
            ("当前会话", "current_session", ""),
            ("最后按键", "last_keypress_time", ""),
            ("空闲阈值", "idle_threshold", "秒")
        ]
        
        for i, (label, key, unit) in enumerate(stats_data):
            row = i // 2
            col = i % 2
            
            frame = ttk.LabelFrame(stats_grid, text=label, padding="10")
            frame.grid(row=row, column=col, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            self.stats_labels[key] = ttk.Label(
                frame,
                text="0",
                font=("Microsoft YaHei", 12, "bold")
            )
            self.stats_labels[key].pack()
            
            if unit:
                ttk.Label(frame, text=unit).pack()
        
        # 配置网格权重
        for i in range(2):
            stats_grid.columnconfigure(i, weight=1)
        for i in range(3):
            stats_grid.rowconfigure(i, weight=1)
        
        # 重置统计按钮
        button_frame = ttk.Frame(stats_frame)
        button_frame.pack(pady=20)
        
        ttk.Button(
            button_frame,
            text="重置统计",
            command=self.reset_stats
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="导出统计",
            command=self.export_stats
        ).pack(side=tk.LEFT, padx=5)
    
    def create_log_display(self, parent):
        """创建日志显示"""
        log_frame = ttk.Frame(parent)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # 日志文本框
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            width=80,
            height=20,
            font=("Consolas", 9),
            bg="#f5f5f5",
            relief=tk.SUNKEN,
            bd=1
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 日志控制按钮
        button_frame = ttk.Frame(log_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(
            button_frame,
            text="清除日志",
            command=self.clear_log
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            button_frame,
            text="保存日志",
            command=self.save_log
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            button_frame,
            text="打开日志文件",
            command=self.open_log_file
        ).pack(side=tk.LEFT)
    
    def create_about_display(self, parent):
        """创建关于页面"""
        about_frame = ttk.Frame(parent)
        about_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 应用信息
        info_text = """触控板自动开关工具 v2.2

专为笔记本优化

功能说明:
• 打字时自动禁用触控板，避免误触
• 停止打字后自动恢复触控板
• 支持自定义空闲时间阈值(1-10秒)
• 支持热键控制
• 支持开机自启
• 提供详细统计信息

系统要求:
• Windows 7/8/10/11
• Python 3.6+ 或打包版exe
• 精确式触控板(Precision Touchpad)

针对笔记本的特殊优化:
• 支持多种触控板注册表路径
• 兼容模式支持
• 优化的响应时间

作者: dai
更新: 2026年

使用方法:
1. 点击"开始监控"按钮
2. 开始打字，触控板会自动禁用
3. 停止打字5秒后，触控板会自动恢复
4. 使用热键快速控制(可在设置中配置)
"""
        
        info_label = ttk.Label(
            about_frame,
            text=info_text,
            justify=tk.LEFT,
            font=("Microsoft YaHei", 10)
        )
        info_label.pack(pady=20)
        
        # 按钮框架
        button_frame = ttk.Frame(about_frame)
        button_frame.pack(pady=20)
        
        ttk.Button(
            button_frame,
            text="检查更新",
            command=self.check_for_updates
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="打开日志目录",
            command=self.open_log_directory
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="报告问题",
            command=self.report_issue
        ).pack(side=tk.LEFT, padx=5)
    
    def create_status_bar(self, parent):
        """创建状态栏"""
        status_bar = ttk.Frame(parent, relief=tk.SUNKEN, height=24)
        status_bar.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E))
        status_bar.grid_propagate(False)
        
        # 左侧状态
        self.statusbar_left = ttk.Label(
            status_bar, 
            text="就绪", 
            relief=tk.SUNKEN, 
            anchor=tk.W,
            padding=(5, 2)
        )
        self.statusbar_left.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 中间状态
        self.statusbar_center = ttk.Label(
            status_bar,
            text="",
            relief=tk.SUNKEN,
            anchor=tk.CENTER,
            padding=(5, 2)
        )
        self.statusbar_center.pack(side=tk.LEFT, fill=tk.X)
        
        # 右侧状态
        self.statusbar_right = ttk.Label(
            status_bar, 
            text="", 
            relief=tk.SUNKEN, 
            anchor=tk.E,
            padding=(5, 2)
        )
        self.statusbar_right.pack(side=tk.RIGHT)
    
    def setup_hotkeys(self):
        """设置热键"""
        use_alt_lib = self.config_manager.get("use_keyboard_shortcut", False)
        hotkeys = self.config_manager.get("hotkeys", {})
        
        # 注册热键
        self.manager.hotkey_manager.register_hotkey(
            hotkeys.get("toggle_touchpad", "ctrl+alt+t"),
            self.toggle_touchpad_hotkey,
            use_alt_lib
        )
        
        self.manager.hotkey_manager.register_hotkey(
            hotkeys.get("toggle_monitoring", "ctrl+alt+m"),
            self.toggle_monitoring_hotkey,
            use_alt_lib
        )
        
        self.manager.hotkey_manager.register_hotkey(
            hotkeys.get("exit_app", "ctrl+alt+q"),
            self.exit_app_hotkey,
            use_alt_lib
        )
        
        # 启动热键监听
        success = self.manager.hotkey_manager.start_listening(not use_alt_lib)
        if not success:
            logger.warning("热键监听启动失败，热键功能可能不可用")
            self.show_notification("警告", "热键功能初始化失败，请检查键盘库安装")
    
    def load_settings(self):
        """加载设置"""
        try:
            # 更新UI中的设置值
            self.auto_start_var.set(self.config_manager.get("auto_start", False))
            self.start_minimized_var.set(self.config_manager.get("start_minimized", False))
            self.enable_sounds_var.set(self.config_manager.get("enable_sounds", True))
            self.enable_notifications_var.set(self.config_manager.get("enable_notifications", True))
            self.use_keyboard_shortcut_var.set(self.config_manager.get("use_keyboard_shortcut", False))
            self.compatibility_mode_var.set(self.config_manager.get("enable_compatibility_mode", True))
            
            # 更新空闲阈值
            idle_threshold = self.config_manager.get("idle_threshold", 5.0)
            self.idle_var.set(idle_threshold)
            self.idle_label.config(text=f"{idle_threshold:.1f}秒")
            
            logger.info("设置加载完成")
        except Exception as e:
            logger.error(f"加载设置失败: {e}")
    
    def handle_startup_arguments(self):
        """处理启动参数"""
        # 检查是否需要最小化启动
        if getattr(sys, 'frozen', False) and self.config_manager.get("start_minimized"):
            self.minimize_window()
        elif "--minimized" in sys.argv:
            self.minimize_window()
        elif "--debug" in sys.argv:
            # 启用调试模式
            logging.getLogger().setLevel(logging.DEBUG)
            logger.info("调试模式已启用")
    
    def start_monitoring(self):
        """开始监控"""
        try:
            if self.manager.start_monitoring():
                self.start_button.config(state=tk.DISABLED)
                self.stop_button.config(state=tk.NORMAL)
                self.show_notification("监控已启动", "触控板监控正在运行")
                logger.info("监控已通过UI启动")
            else:
                self.show_notification("启动失败", "无法启动触控板监控")
        except Exception as e:
            logger.error(f"启动监控时出错: {e}")
            messagebox.showerror("错误", f"启动监控失败:\n{str(e)}")
    
    def stop_monitoring(self):
        """停止监控"""
        try:
            if self.manager.stop_monitoring():
                self.start_button.config(state=tk.NORMAL)
                self.stop_button.config(state=tk.DISABLED)
                self.show_notification("监控已停止", "触控板监控已停止")
                logger.info("监控已通过UI停止")
            else:
                self.show_notification("停止失败", "无法停止触控板监控")
        except Exception as e:
            logger.error(f"停止监控时出错: {e}")
            messagebox.showerror("错误", f"停止监控失败:\n{str(e)}")
    
    def toggle_monitoring_hotkey(self):
        """热键切换监控状态"""
        self.root.after(0, self.toggle_monitoring)
    
    def toggle_monitoring(self):
        """切换监控状态"""
        if self.manager.is_monitoring:
            self.stop_monitoring()
        else:
            self.start_monitoring()
    
    def toggle_touchpad_hotkey(self):
        """热键切换触控板"""
        self.root.after(0, self.toggle_touchpad)
    
    def toggle_touchpad(self):
        """手动切换触控板"""
        try:
            if self.manager.toggle_touchpad():
                state = self.manager.touchpad_state.value
                self.show_notification("触控板切换", f"触控板已{state}")
            else:
                self.show_notification("切换失败", "无法切换触控板状态")
        except Exception as e:
            logger.error(f"切换触控板时出错: {e}")
            messagebox.showerror("错误", f"切换触控板失败:\n{str(e)}")
    
    def exit_app_hotkey(self):
        """热键退出应用"""
        self.root.after(0, self.on_closing)
    
    def update_idle_threshold(self, value=None):
        """更新空闲时间阈值"""
        try:
            threshold = self.idle_var.get()
            self.manager.idle_threshold = threshold
            self.idle_label.config(text=f"{threshold:.1f}秒")
            self.config_manager.set("idle_threshold", threshold)
            logger.info(f"空闲阈值更新为: {threshold:.1f}秒")
        except Exception as e:
            logger.error(f"更新空闲阈值失败: {e}")
    
    def toggle_auto_start(self):
        """切换开机自启"""
        try:
            auto_start = self.auto_start_var.get()
            self.config_manager.set("auto_start", auto_start)
            
            # 设置开机自启
            app_name = "TouchpadManager"
            
            if getattr(sys, 'frozen', False):
                app_path = sys.executable
            else:
                app_path = os.path.abspath(sys.argv[0])
            
            success = self.manager.registry_manager.set_auto_start(app_name, app_path, auto_start)
            
            if success:
                status = "已启用" if auto_start else "已禁用"
                self.show_notification("开机自启", f"开机自启{status}")
            else:
                self.auto_start_var.set(not auto_start)  # 恢复原状态
                messagebox.showerror("错误", "设置开机自启失败，请检查权限")
        except Exception as e:
            logger.error(f"切换开机自启失败: {e}")
            messagebox.showerror("错误", f"设置开机自启失败:\n{str(e)}")
    
    def toggle_start_minimized(self):
        """切换启动最小化"""
        try:
            self.config_manager.set("start_minimized", self.start_minimized_var.get())
        except Exception as e:
            logger.error(f"切换启动最小化失败: {e}")
    
    def toggle_sounds(self):
        """切换声音"""
        try:
            self.config_manager.set("enable_sounds", self.enable_sounds_var.get())
        except Exception as e:
            logger.error(f"切换声音设置失败: {e}")
    
    def toggle_notifications(self):
        """切换通知"""
        try:
            self.config_manager.set("enable_notifications", self.enable_notifications_var.get())
        except Exception as e:
            logger.error(f"切换通知设置失败: {e}")
    
    def toggle_compatibility_mode(self):
        """切换兼容模式"""
        try:
            enable = self.compatibility_mode_var.get()
            self.config_manager.set("enable_compatibility_mode", enable)
            
            status = "已启用" if enable else "已禁用"
            self.show_notification("兼容模式", f"兼容模式{status}")
            
            # 重新初始化注册表管理器
            self.manager.registry_manager = RegistryManager()
            
        except Exception as e:
            logger.error(f"切换兼容模式失败: {e}")
    
    def toggle_keyboard_shortcut(self):
        """切换键盘快捷键模式"""
        try:
            use_keyboard = self.use_keyboard_shortcut_var.get()
            self.config_manager.set("use_keyboard_shortcut", use_keyboard)
            
            # 重新初始化触控板管理器
            self.manager.registry_manager.use_keyboard_shortcut = use_keyboard
            
            status = "已启用" if use_keyboard else "已禁用"
            self.show_notification("键盘快捷键", f"键盘快捷键模式{status}")
            
        except Exception as e:
            logger.error(f"切换键盘快捷键模式失败: {e}")
    
    def test_keyboard_shortcut(self):
        """测试键盘快捷键"""
        try:
            # 尝试导入测试工具
            import subprocess
            script_path = "keyboard_shortcut_test.py"
            
            if os.path.exists(script_path):
                subprocess.Popen([sys.executable, script_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
                self.show_notification("快捷键测试", "已启动快捷键测试工具")
            else:
                self.show_notification("错误", "测试工具不存在，请下载完整的项目文件")
        except Exception as e:
            logger.error(f"启动快捷键测试工具失败: {e}")
            messagebox.showerror("错误", f"启动测试工具失败:\n{str(e)}")
    
    def minimize_window(self):
        """最小化窗口"""
        self.root.iconify()
        self.is_minimized = True
        logger.info("窗口已最小化")
    
    def show_notification(self, title: str, message: str, duration=3):
        """显示通知"""
        if not self.config_manager.get("enable_notifications", True):
            return
        
        try:
            if HAS_WIN10TOAST:
                toaster = ToastNotifier()
                toaster.show_toast(
                    title,
                    message,
                    duration=duration,
                    threaded=True
                )
            else:
                # 回退到tkinter消息框
                self.root.after(0, lambda: messagebox.showinfo(title, message))
        except Exception as e:
            logger.error(f"显示通知失败: {e}")
            # 最终回退
            self.root.after(0, lambda: messagebox.showinfo(title, message))
    
    def update_ui(self):
        """更新UI状态"""
        try:
            # 更新状态标签
            state_texts = {
                TouchpadState.ENABLED: ("已启用", "green"),
                TouchpadState.DISABLED: ("已禁用", "red"),
                TouchpadState.UNKNOWN: ("未知", "gray")
            }
            
            text, color = state_texts.get(self.manager.touchpad_state, ("未知", "gray"))
            self.status_labels['touchpad'].config(text=text, foreground=color)
            
            # 更新监控状态
            if self.manager.is_monitoring:
                monitoring_text = "运行中"
                monitoring_color = "green"
                desc = "监控中 - 等待输入"
                
                if self.manager.touchpad_state == TouchpadState.DISABLED:
                    idle_time = time.time() - self.manager.last_activity_time
                    desc = f"监控中 - 打字中(触控板禁用) - 空闲 {idle_time:.1f}秒"
            else:
                monitoring_text = "已停止"
                monitoring_color = "red"
                desc = "监控已停止"
            
            self.status_labels['monitoring'].config(
                text=monitoring_text, 
                foreground=monitoring_color
            )
            
            # 更新状态指示器颜色
            self.status_indicator.delete("all")
            if self.manager.is_monitoring:
                if self.manager.touchpad_state == TouchpadState.ENABLED:
                    indicator_color = "green"
                else:
                    indicator_color = "red"
            else:
                indicator_color = "gray"
            
            self.status_indicator.create_oval(2, 2, 18, 18, fill=indicator_color, outline="black")
            self.status_description.config(text=desc)
            
            # 更新统计信息
            stats = self.manager.get_stats()
            for key, label in self.stats_labels.items():
                if key in stats:
                    value = stats[key]
                    
                    if key == "idle_threshold":
                        label.config(text=f"{self.manager.idle_threshold:.1f}")
                    elif key.endswith("_time") and value:
                        # 格式化时间
                        if isinstance(value, (int, float)):
                            time_str = time.strftime("%H:%M:%S", time.localtime(value))
                            label.config(text=time_str)
                        else:
                            label.config(text=str(value))
                    elif key == "total_runtime" or key == "current_session":
                        # 格式化运行时间
                        if value >= 3600:  # 小时
                            hours = int(value // 3600)
                            minutes = int((value % 3600) // 60)
                            label.config(text=f"{hours}h {minutes}m")
                        elif value >= 60:  # 分钟
                            minutes = int(value // 60)
                            seconds = int(value % 60)
                            label.config(text=f"{minutes}m {seconds}s")
                        else:  # 秒
                            label.config(text=f"{value:.0f}s")
                    else:
                        label.config(text=str(value))
            
            # 更新状态栏
            self.statusbar_left.config(text=f"状态: {desc}")
            self.statusbar_center.config(text=f"触控板: {text}")
            self.statusbar_right.config(text=f"空闲阈值: {self.manager.idle_threshold:.1f}秒 | {time.strftime('%H:%M:%S')}")
            
            # 更新日志显示
            self.update_log_display()
            
        except Exception as e:
            logger.error(f"更新UI时出错: {e}")
        
        # 安排下一次更新
        self.root.after(self.update_interval, self.update_ui)
    
    def update_log_display(self):
        """更新日志显示"""
        try:
            log_file = os.path.join('log', 'touchpad_manager.log')
            if os.path.exists(log_file):
                # 获取文件大小
                file_size = os.path.getsize(log_file)
                
                if file_size > 5 * 1024 * 1024:  # 大于5MB
                    self.statusbar_center.config(text="日志文件过大，请清理")
                    return
                
                # 读取最后50行
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    recent_lines = lines[-50:] if len(lines) > 50 else lines
                
                # 更新文本
                current_content = self.log_text.get(1.0, tk.END).strip()
                new_content = ''.join(recent_lines).strip()
                
                if current_content != new_content:
                    self.log_text.delete(1.0, tk.END)
                    self.log_text.insert(1.0, new_content)
                    self.log_text.see(tk.END)
        except Exception as e:
            logger.error(f"更新日志显示失败: {e}")
    
    def reset_stats(self):
        """重置统计信息"""
        if messagebox.askyesno("确认", "确定要重置统计信息吗？"):
            self.manager.stats = {
                "disabled_count": 0,
                "enabled_count": 0,
                "total_runtime": 0,
                "start_time": None,
                "last_disable_time": None,
                "last_enable_time": None,
                "last_keypress_time": None
            }
            messagebox.showinfo("成功", "统计信息已重置")
            logger.info("统计信息已重置")
    
    def export_stats(self):
        """导出统计信息"""
        try:
            stats = self.manager.get_stats()
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = os.path.join("log", f"touchpad_stats_{timestamp}.json")
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
            
            messagebox.showinfo("成功", f"统计信息已导出到: {filename}")
            logger.info(f"统计信息已导出: {filename}")
        except Exception as e:
            logger.error(f"导出统计信息失败: {e}")
            messagebox.showerror("错误", f"导出统计信息失败:\n{str(e)}")
    
    def clear_log(self):
        """清除日志"""
        if messagebox.askyesno("确认", "确定要清除日志吗？"):
            self.log_text.delete(1.0, tk.END)
            logger.info("日志显示已清除")
    
    def save_log(self):
        """保存日志"""
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = filedialog.asksaveasfilename(
                defaultextension=".log",
                filetypes=[
                    ("日志文件", "*.log"),
                    ("文本文件", "*.txt"),
                    ("所有文件", "*.*")
                ],
                initialfile=f"touchpad_log_{timestamp}.log",
                initialdir="log"
            )
            
            if filename:
                content = self.log_text.get(1.0, tk.END)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("成功", f"日志已保存到: {filename}")
                logger.info(f"日志已保存: {filename}")
        except Exception as e:
            logger.error(f"保存日志失败: {e}")
            messagebox.showerror("错误", f"保存日志失败:\n{str(e)}")
    
    def open_log_file(self):
        """打开日志文件"""
        try:
            log_file = os.path.join('log', 'touchpad_manager.log')
            if os.path.exists(log_file):
                if IS_WINDOWS:
                    os.startfile(log_file)
                else:
                    subprocess.run(['open', log_file] if sys.platform == 'darwin' else ['xdg-open', log_file])
            else:
                messagebox.showwarning("警告", "日志文件不存在")
        except Exception as e:
            logger.error(f"打开日志文件失败: {e}")
            messagebox.showerror("错误", f"打开日志文件失败:\n{str(e)}")
    
    def open_log_directory(self):
        """打开日志目录"""
        try:
            log_dir = os.path.abspath('log')
            if IS_WINDOWS:
                os.startfile(log_dir)
            else:
                subprocess.run(['open', log_dir] if sys.platform == 'darwin' else ['xdg-open', log_dir])
        except Exception as e:
            logger.error(f"打开日志目录失败: {e}")
            messagebox.showerror("错误", f"打开日志目录失败:\n{str(e)}")
    
    def test_touchpad(self):
        """测试触控板功能"""
        try:
            # 获取当前状态
            current_state = self.manager.touchpad_state
            
            # 临时禁用
            if current_state == TouchpadState.ENABLED:
                self.manager.set_touchpad(False)
                time.sleep(0.5)
                self.manager.set_touchpad(True)
            else:
                self.manager.set_touchpad(True)
                time.sleep(0.5)
                self.manager.set_touchpad(False)
                time.sleep(0.5)
                self.manager.set_touchpad(True)
            
            messagebox.showinfo("测试", "触控板测试完成")
            logger.info("触控板测试完成")
        except Exception as e:
            logger.error(f"触控板测试失败: {e}")
            messagebox.showerror("错误", f"触控板测试失败:\n{str(e)}")
    
    def check_for_updates(self):
        """检查更新"""
        try:
            messagebox.showinfo("检查更新", "当前已是最新版本 (v2.2)")
            logger.info("检查更新: 当前已是最新版本")
        except Exception as e:
            logger.error(f"检查更新失败: {e}")
            messagebox.showinfo("检查更新", f"检查更新失败:\n{str(e)}")
    
    def report_issue(self):
        """报告问题"""
        try:
            # 收集系统信息
            system_info = {
                "platform": PLATFORM,
                "windows_version": platform.version(),
                "python_version": sys.version,
                "has_windows_deps": HAS_WINDOWS_DEPS,
                "has_pynput": HAS_PYNPUT,
                "has_keyboard_alt": HAS_KEYBOARD_ALT,
                "app_version": "2.2",
                "idle_threshold": self.manager.idle_threshold,
                "compatibility_mode": self.config_manager.get("enable_compatibility_mode")
            }
            
            # 保存问题报告
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = os.path.join("log", f"issue_report_{timestamp}.json")
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(system_info, f, indent=2, ensure_ascii=False)
            
            messagebox.showinfo("报告问题", 
                f"问题报告已保存到: {filename}\n"
                "请将此文件发送给开发者以便诊断问题。"
            )
            logger.info(f"问题报告已保存: {filename}")
        except Exception as e:
            logger.error(f"生成问题报告失败: {e}")
            messagebox.showerror("错误", f"生成问题报告失败:\n{str(e)}")
    
    def open_settings(self):
        """打开设置窗口"""
        # 创建设置对话框
        settings_dialog = tk.Toplevel(self.root)
        settings_dialog.title("高级设置")
        settings_dialog.geometry("500x400")
        settings_dialog.resizable(False, False)
        settings_dialog.transient(self.root)
        settings_dialog.grab_set()
        
        # 居中显示
        settings_dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - settings_dialog.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - settings_dialog.winfo_height()) // 2
        settings_dialog.geometry(f"+{x}+{y}")
        
        # 设置内容
        notebook = ttk.Notebook(settings_dialog, padding="10")
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # 热键设置选项卡
        hotkey_frame = ttk.Frame(notebook, padding="10")
        notebook.add(hotkey_frame, text="热键设置")
        
        ttk.Label(hotkey_frame, text="切换触控板:").grid(row=0, column=0, sticky=tk.W, pady=5)
        toggle_entry = ttk.Entry(hotkey_frame, width=20)
        toggle_entry.grid(row=0, column=1, pady=5, padx=(10, 0))
        toggle_entry.insert(0, self.config_manager.get("hotkeys.toggle_touchpad", "ctrl+alt+t"))
        
        ttk.Label(hotkey_frame, text="切换监控:").grid(row=1, column=0, sticky=tk.W, pady=5)
        monitor_entry = ttk.Entry(hotkey_frame, width=20)
        monitor_entry.grid(row=1, column=1, pady=5, padx=(10, 0))
        monitor_entry.insert(0, self.config_manager.get("hotkeys.toggle_monitoring", "ctrl+alt+m"))
        
        ttk.Label(hotkey_frame, text="退出程序:").grid(row=2, column=0, sticky=tk.W, pady=5)
        exit_entry = ttk.Entry(hotkey_frame, width=20)
        exit_entry.grid(row=2, column=1, pady=5, padx=(10, 0))
        exit_entry.insert(0, self.config_manager.get("hotkeys.exit_app", "ctrl+alt+q"))
        
        # 保存按钮
        def save_hotkeys():
            self.config_manager.set("hotkeys.toggle_touchpad", toggle_entry.get())
            self.config_manager.set("hotkeys.toggle_monitoring", monitor_entry.get())
            self.config_manager.set("hotkeys.exit_app", exit_entry.get())
            
            # 重启热键监听
            self.manager.hotkey_manager.stop_listening()
            self.setup_hotkeys()
            
            messagebox.showinfo("成功", "热键设置已保存")
            settings_dialog.destroy()
        
        ttk.Button(
            hotkey_frame, 
            text="保存设置", 
            command=save_hotkeys
        ).grid(row=3, column=0, columnspan=2, pady=20)
        
        # 高级设置选项卡
        advanced_frame = ttk.Frame(notebook, padding="10")
        notebook.add(advanced_frame, text="高级设置")
        
        # UI更新间隔
        ttk.Label(advanced_frame, text="UI更新间隔(ms):").grid(row=0, column=0, sticky=tk.W, pady=5)
        update_var = tk.IntVar(value=self.update_interval)
        update_spinbox = ttk.Spinbox(
            advanced_frame, 
            from_=100, 
            to=5000, 
            increment=100, 
            textvariable=update_var,
            width=10
        )
        update_spinbox.grid(row=0, column=1, pady=5, padx=(10, 0))
        
        # 最小禁用时间
        ttk.Label(advanced_frame, text="最小禁用时间(秒):").grid(row=1, column=0, sticky=tk.W, pady=5)
        min_disable_var = tk.DoubleVar(value=0.5)
        min_disable_spinbox = ttk.Spinbox(
            advanced_frame,
            from_=0.1,
            to=2.0,
            increment=0.1,
            textvariable=min_disable_var,
            width=10
        )
        min_disable_spinbox.grid(row=1, column=1, pady=5, padx=(10, 0))
        
        def save_advanced():
            self.update_interval = update_var.get()
            # 保存最小禁用时间
            self.config_manager.set("compatibility.min_disable_time", min_disable_var.get())
            
            messagebox.showinfo("成功", "高级设置已保存")
            settings_dialog.destroy()
        
        ttk.Button(
            advanced_frame,
            text="保存设置",
            command=save_advanced
        ).grid(row=2, column=0, columnspan=2, pady=20)
    
    def on_closing(self):
        """窗口关闭事件"""
        if messagebox.askyesno("确认退出", "确定要退出程序吗？"):
            logger.info("正在退出程序...")
            
            # 停止所有监控
            self.manager.stop_monitoring()
            
            # 停止热键监听
            self.manager.hotkey_manager.stop_listening()
            
            # 保存配置
            self.save_window_geometry()
            self.config_manager.save_config()
            
            # 关闭窗口
            self.root.quit()
            self.root.destroy()
            
            logger.info("程序已退出")
    
    def run(self):
        """运行主循环"""
        try:
            logger.info("启动主循环")
            self.root.mainloop()
        except KeyboardInterrupt:
            logger.info("收到键盘中断信号")
            self.on_closing()
        except Exception as e:
            logger.critical(f"主循环运行错误: {e}")
            traceback.print_exc()
            messagebox.showerror("致命错误", f"程序运行出错:\n{str(e)}")

def main():
    """主函数"""
    print("=" * 70)
    print("触控板自动开关工具 v2.2")
    print("专为笔记本优化")
    print("=" * 70)
    print("正在启动...")
    
    # 检查依赖
    if IS_WINDOWS and not HAS_WINDOWS_DEPS:
        print("警告: 缺少Windows依赖，部分功能可能无法使用")
        print("请安装: pip install pywin32")
    
    if not HAS_PYNPUT and not HAS_KEYBOARD_ALT:
        print("警告: 缺少键盘监听库")
        print("请安装: pip install pynput 或 pip install keyboard")
    
    # 设置高DPI支持
    if IS_WINDOWS:
        try:
            # Windows 8.1及以上版本
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except AttributeError:
            # Windows 8及以下版本
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except:
                pass
        except Exception as e:
            print(f"设置DPI感知失败: {e}")
    
    # 创建并运行应用
    app = TouchpadApp()
    app.run()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"程序启动失败: {e}")
        traceback.print_exc()
        input("按回车键退出...")