========================================
触控板自动开关工具 v2.2 - 使用说明
========================================
![Logo](config/iocn.ioc)
📁 项目文件结构:
├── touchpad_manager.py    # 主程序文件
├── start_app.bat          # 一键安装依赖并运行（推荐）
├── install_deps_only.bat  # 仅安装依赖
├── run_app.bat            # 仅运行程序（需已安装依赖）
├── uninstall_deps.bat     # 卸载所有依赖
├── build_exe.bat          # 打包为EXE文件
├── requirements.txt       # 依赖包列表
├── config/                # 配置文件夹
│   ├── icon.ico          # 程序图标
│   └── default_config.json # 默认配置文件
└── log/                  # 日志文件夹

📋 配置文件说明:

config/default_config.json - 默认配置文件
----------------------------------------
此文件包含程序的默认设置，包括:
- 空闲时间阈值 (默认5秒)
- 热键设置
- 兼容模式设置
- 外观设置
- 日志设置

程序首次运行时，会自动在config目录下创建此文件。
用户可以在程序中修改设置，修改会保存到config/user_config.json。

🚀 快速开始:
方法0: 一键安装并运行（推荐）
--------------------------------
1. 双击运行 setup_project.bat
2. 按提示一步一步来就行

方法1: 一键安装并运行
--------------------------------
1. 双击运行 start_app.bat
2. 脚本会自动:
   - 检查Python环境
   - 创建config和log文件夹
   - 创建默认配置文件
   - 安装所有依赖包
3. 安装完成后按任意键启动程序

方法2: 分步安装运行
--------------------------------
1. 双击运行 install_deps_only.bat 安装依赖
2. 双击运行 run_app.bat 启动程序

方法3: 直接运行Python脚本
--------------------------------
1. 打开命令提示符
2. 安装依赖: pip install -r requirements.txt
3. 运行程序: python touchpad_manager.py

🛠️ 其他功能:

打包为EXE:
  双击运行 build_exe.bat
  打包后的EXE文件在 dist/ 文件夹中
  注意: EXE文件需要config文件夹一起分发

卸载依赖:
  双击运行 uninstall_deps.bat
  注意: 这将卸载所有项目依赖

⚙️ 配置说明:

1. 主要配置选项:
   - idle_threshold: 空闲时间阈值(1-10秒)
   - enable_compatibility_mode: 兼容模式(推荐联想笔记本启用)
   - hotkeys: 热键设置

2. 配置文件位置:
   - 默认配置: config/default_config.json
   - 用户配置: config/user_config.json (程序运行时生成)

3. 修改配置:
   - 在程序界面中修改设置
   - 或直接编辑config/user_config.json文件

⚠️ 注意事项:

1. 建议以管理员身份运行程序
2. 笔记本建议启用"兼容模式"
3. 如果触控板控制无效，请检查:
   - 是否以管理员身份运行
   - 兼容模式是否启用
   - 查看 log/touchpad_manager.log 错误信息

🔧 技术支持:

如有问题，请检查:
1. 日志文件: log/touchpad_manager.log
2. 配置文件: config/user_config.json
3. 使用程序内的"报告问题"功能生成诊断报告

📞 常见问题:

Q: 程序启动失败怎么办?
A: 1. 检查Python是否安装
   2. 以管理员身份运行
   3. 查看日志文件

Q: 触控板没有反应?
A: 1. 启用兼容模式
   2. 调整空闲时间阈值
   3. 检查触控板驱动程序

Q: 如何修改热键?
A: 1. 在程序界面点击"设置"
   2. 或编辑config/user_config.json中的hotkeys部分

========================================
