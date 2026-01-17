"""
键盘快捷键测试工具
用于检测有效的触控板切换快捷键
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
import time
import threading

# 添加当前目录到路径，确保可以导入模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from keyboard_simulator import KeyboardSimulator, PyAutoGUISimulator, get_keyboard_simulator
    HAS_SIMULATOR = True
except ImportError:
    HAS_SIMULATOR = False
    print("警告: 无法导入键盘模拟器")

class ShortcutTester:
    """快捷键测试器"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("触控板快捷键测试工具")
        self.root.geometry("600x500")
        
        # 使窗口始终置顶
        self.root.attributes('-topmost', True)
        
        self.simulator = None
        self.current_test_index = 0
        self.test_results = []
        self.testing = False
        
        # 常见的触控板切换快捷键
        self.shortcuts_to_test = [
            ['F11'],
            ['F6'],
            ['F9'],
            ['F10'],
            ['control', 'F11'],
            ['control', 'F6'],
            ['control', 'F9'],
            ['control', 'F10'],
            ['alt', 'F11'],
            ['alt', 'F6'],
            ['fn', 'F11'],  # 某些笔记本需要Fn键
            ['fn', 'F6'],
        ]
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(
            main_frame,
            text="🖱️ 触控板快捷键测试工具",
            font=("Microsoft YaHei", 14, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # 说明文字
        instructions = """使用方法:
1. 确保您的触控板当前是启用的
2. 点击"开始测试"按钮
3. 程序会自动尝试各种快捷键组合
4. 每次测试后，请观察触控板是否被禁用
5. 如果触控板被禁用，请点击"是，这个快捷键有效"
6. 如果触控板没有被禁用，请点击"否，继续测试下一个"
7. 测试完成后，程序会保存有效的快捷键到配置文件
"""
        
        instructions_label = ttk.Label(
            main_frame,
            text=instructions,
            justify=tk.LEFT,
            font=("Microsoft YaHei", 10)
        )
        instructions_label.pack(pady=(0, 20))
        
        # 当前测试显示
        self.current_label = ttk.Label(
            main_frame,
            text="等待开始测试...",
            font=("Microsoft YaHei", 11, "bold")
        )
        self.current_label.pack(pady=(0, 10))
        
        # 测试进度
        self.progress_label = ttk.Label(
            main_frame,
            text="",
            font=("Microsoft YaHei", 9)
        )
        self.progress_label.pack(pady=(0, 20))
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            main_frame,
            variable=self.progress_var,
            maximum=len(self.shortcuts_to_test)
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 20))
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        self.start_button = ttk.Button(
            button_frame,
            text="开始测试",
            command=self.start_testing,
            width=15
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.yes_button = ttk.Button(
            button_frame,
            text="是，这个快捷键有效",
            command=lambda: self.record_result(True),
            state=tk.DISABLED,
            width=20
        )
        self.yes_button.pack(side=tk.LEFT, padx=5)
        
        self.no_button = ttk.Button(
            button_frame,
            text="否，继续测试下一个",
            command=lambda: self.record_result(False),
            state=tk.DISABLED,
            width=20
        )
        self.no_button.pack(side=tk.LEFT, padx=5)
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="测试日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        self.log_text = tk.Text(
            log_frame,
            height=8,
            font=("Consolas", 9),
            bg="#f5f5f5",
            wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(self.log_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.log_text.yview)
        
    def log(self, message):
        """添加日志"""
        timestamp = time.strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        
    def start_testing(self):
        """开始测试"""
        if not HAS_SIMULATOR:
            messagebox.showerror("错误", "键盘模拟器不可用，请确保已安装依赖")
            return
            
        try:
            self.simulator = get_keyboard_simulator()
            if not self.simulator:
                messagebox.showerror("错误", "无法初始化键盘模拟器")
                return
        except Exception as e:
            messagebox.showerror("错误", f"初始化键盘模拟器失败:\n{str(e)}")
            return
            
        self.testing = True
        self.current_test_index = 0
        self.test_results = []
        
        self.start_button.config(state=tk.DISABLED)
        self.yes_button.config(state=tk.NORMAL)
        self.no_button.config(state=tk.NORMAL)
        
        self.log("开始测试触控板快捷键...")
        self.log("请确保触控板当前是启用的状态")
        self.log("每次测试后，请观察触控板是否被禁用")
        
        self.test_next_shortcut()
        
    def test_next_shortcut(self):
        """测试下一个快捷键"""
        if self.current_test_index >= len(self.shortcuts_to_test):
            self.finish_testing()
            return
            
        shortcut = self.shortcuts_to_test[self.current_test_index]
        
        # 更新显示
        self.current_label.config(
            text=f"正在测试: {'+'.join(shortcut).upper()}"
        )
        self.progress_label.config(
            text=f"进度: {self.current_test_index + 1}/{len(self.shortcuts_to_test)}"
        )
        self.progress_var.set(self.current_test_index + 1)
        
        self.log(f"测试快捷键: {'+'.join(shortcut).upper()}")
        self.log("请观察触控板是否被禁用...")
        
        # 等待用户准备
        self.root.after(2000, self.send_shortcut_test, shortcut)
        
    def send_shortcut_test(self, shortcut):
        """发送快捷键测试"""
        try:
            # 尝试发送快捷键
            if hasattr(self.simulator, 'send_shortcut'):
                success = self.simulator.send_shortcut(shortcut)
            else:
                # 回退方法
                import pyautogui
                if len(shortcut) == 1:
                    pyautogui.press(shortcut[0])
                else:
                    pyautogui.hotkey(*shortcut)
                success = True
                
            if success:
                self.log(f"✓ 已发送快捷键: {'+'.join(shortcut).upper()}")
            else:
                self.log(f"✗ 发送快捷键失败: {'+'.join(shortcut).upper()}")
                
        except Exception as e:
            self.log(f"✗ 发送快捷键时出错: {str(e)}")
            
    def record_result(self, worked):
        """记录测试结果"""
        shortcut = self.shortcuts_to_test[self.current_test_index]
        shortcut_str = '+'.join(shortcut).upper()
        
        if worked:
            self.test_results.append(shortcut)
            self.log(f"✅ 快捷键有效: {shortcut_str}")
        else:
            self.log(f"❌ 快捷键无效: {shortcut_str}")
            
        self.current_test_index += 1
        
        # 继续测试下一个
        self.root.after(1000, self.test_next_shortcut)
        
    def finish_testing(self):
        """完成测试"""
        self.testing = False
        
        self.current_label.config(text="测试完成!")
        self.start_button.config(state=tk.NORMAL)
        self.yes_button.config(state=tk.DISABLED)
        self.no_button.config(state=tk.DISABLED)
        
        if self.test_results:
            self.log("\n✅ 测试完成！找到有效快捷键:")
            for shortcut in self.test_results:
                self.log(f"  - {'+'.join(shortcut).upper()}")
                
            # 保存到配置文件
            self.save_to_config(self.test_results[0])
            
            messagebox.showinfo(
                "测试完成",
                f"找到了 {len(self.test_results)} 个有效快捷键！\n"
                f"已保存首选快捷键: {'+'.join(self.test_results[0]).upper()}\n\n"
                "现在可以关闭测试工具并使用触控板管理工具了。"
            )
        else:
            self.log("\n❌ 测试完成！未找到有效快捷键")
            messagebox.showwarning(
                "测试完成",
                "未找到有效的触控板快捷键。\n"
                "可能需要手动设置快捷键，或使用其他控制方法。"
            )
            
    def save_to_config(self, shortcut):
        """保存快捷键到配置文件"""
        config_path = os.path.join("config", "default_config.json")
        if not os.path.exists("config"):
            os.makedirs("config")
            
        import json
        
        config = {
            "keyboard_shortcut": {
                "enabled": True,
                "keys": shortcut,
                "display": '+'.join(shortcut).upper()
            }
        }
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            self.log(f"已保存快捷键到配置文件: {config_path}")
        except Exception as e:
            self.log(f"保存配置文件失败: {str(e)}")
            
    def run(self):
        """运行测试工具"""
        self.root.mainloop()

if __name__ == "__main__":
    print("=" * 60)
    print("触控板快捷键测试工具")
    print("=" * 60)
    print("请以管理员身份运行此程序")
    
    # 检查管理员权限
    if os.name == 'nt':
        try:
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if not is_admin:
                print("警告: 建议以管理员身份运行此程序")
                print("某些快捷键可能需要管理员权限才能正常工作")
        except:
            pass
            
    tester = ShortcutTester()
    tester.run()