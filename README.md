# 🤖 AI 自动化迷宫游戏

一个使用 Pygame 开发的智能迷宫游戏，支持手动模式和 AI 自动模式。在 AI 模式下，游戏使用大语言模型（LLM）如 GPT-4o 来自动控制玩家移动，智能求解迷宫。

## 🎬 演示视频

<video width="800" controls>
  <source src="AI自动化迷宫.mp4" type="video/quicktime">
  <source src="AI自动化迷宫.mp4" type="video/mp4">
  您的浏览器不支持视频播放。请 [下载视频](AI自动化迷宫.mp4) 或使用支持 HTML5 视频的浏览器。
</video>

> 💡 **提示**：如果视频无法播放，请 [点击下载视频文件](AI自动化迷宫.mp4) 在本地观看。

## ✨ 功能特性

### 🎮 游戏功能
- **随机迷宫生成**：使用递归回溯算法生成随机迷宫
- **手动模式**：使用方向键手动控制玩家移动
- **AI 自动模式**：使用 LLM 自动控制玩家移动，智能求解迷宫
- **实时可视化**：清晰的图形界面，实时显示玩家位置和移动轨迹
- **移动历史追踪**：记录所有访问过的位置，帮助 AI 避免重复路径
- **循环检测**：智能检测 AI 的重复移动模式，自动纠正

### 🤖 AI 功能
- **智能路径规划**：LLM 根据迷宫状态、当前位置、目标位置和移动历史做出决策
- **循环避免**：自动检测并避免来回移动的循环模式
- **回溯策略**：在必要时允许回溯，但优先选择未访问的路径
- **详细日志**：输出详细的推理过程，方便调试和分析

## 📋 系统要求

- Python >= 3.11
- pygame >= 2.6.1
- openai >= 1.0.0
- python-dotenv >= 1.0.0

## 🚀 安装步骤

### 1. 克隆或下载项目

```bash
cd llm_pygame
```

### 2. 安装依赖

使用 pip 安装：

```bash
pip install -r requirements.txt
```

或使用 uv（如果已安装）：

```bash
uv pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env.example` 文件为 `.env`：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的 OpenAI API 配置：

```env
# OpenAI API 配置
OPENAI_API_KEY=your-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1/

# LLM 模型配置
LLM_MODEL=gpt-4o

# 自动模式配置（可选）
# AUTO_MODE=true
```

**注意**：
- 如果你使用的是兼容 OpenAI API 的服务（如代理服务），请修改 `OPENAI_BASE_URL`
- 支持的模型包括：`gpt-4o`、`gpt-4o-mini`、`gpt-4-turbo` 等
- `.env` 文件已添加到 `.gitignore`，不会被提交到版本控制

## 🎯 使用方法

### 手动模式

直接运行程序，使用方向键控制：

```bash
python main.py
```

### AI 自动模式

使用 `--auto` 参数启动自动模式：

```bash
python main.py --auto
```

或者在 `.env` 文件中设置 `AUTO_MODE=true`：

```bash
python main.py
```

## 🎮 游戏控制

### 手动模式控制
- **↑ ↓ ← →**：移动玩家
- **R**：重新开始游戏
- **T**：切换到自动模式（需要已配置 LLM）

### 自动模式控制
- **T**：切换到手动模式
- **R**：重新开始游戏（重新生成迷宫）
- **ESC** 或关闭窗口：退出游戏

## 📁 项目结构

```
llm_pygame/
├── main.py              # 主程序入口
├── maze_game.py         # 迷宫游戏核心逻辑
├── llm_client.py        # LLM 客户端封装
├── requirements.txt     # Python 依赖列表
├── pyproject.toml       # 项目配置文件
├── .env                 # 环境变量配置（需自行创建）
├── .env.example         # 环境变量配置示例
├── .gitignore          # Git 忽略文件
└── README.md           # 项目说明文档
```

## 🔧 配置说明

### 迷宫大小

在 `main.py` 中修改迷宫大小（必须是奇数）：

```python
game = MazeGame(
    maze_width=21,    # 宽度（必须是奇数）
    maze_height=21,   # 高度（必须是奇数）
    auto_mode=auto_mode,
    llm_client=llm_client
)
```

### LLM 调用间隔

在 `maze_game.py` 的 `__init__` 方法中修改：

```python
self.llm_call_interval = 1.0  # LLM调用间隔（秒）
```

### 游戏速度

在 `maze_game.py` 的 `run` 方法中修改：

```python
self.clock.tick(60)  # 帧率（FPS）
```

## 🧠 AI 工作原理

1. **状态收集**：收集当前迷宫状态、玩家位置、目标位置、移动历史等信息
2. **循环检测**：分析最近的移动模式，检测是否存在循环
3. **LLM 推理**：将状态信息发送给 LLM，获取下一步移动决策
4. **移动验证**：验证 LLM 返回的坐标是否有效（可通行且相邻）
5. **执行移动**：执行移动并更新游戏状态
6. **循环纠正**：如果检测到循环，强制选择未访问的相邻位置

## 📊 技术栈

- **Pygame**：游戏引擎，用于图形界面和用户交互
- **OpenAI API**：大语言模型 API，用于智能决策
- **递归回溯算法**：迷宫生成算法
- **python-dotenv**：环境变量管理

## ⚠️ 注意事项

1. **API 费用**：AI 模式会调用 LLM API，可能产生费用，请注意使用
2. **网络连接**：AI 模式需要网络连接以访问 API
3. **迷宫大小**：迷宫宽度和高度必须是奇数，否则可能导致生成失败
4. **性能考虑**：较大的迷宫会增加 LLM 的推理时间
5. **API 限制**：注意 API 的调用频率限制，避免过于频繁的请求

## 🐛 故障排除

### 问题：无法启动自动模式

**解决方案**：
- 检查 `.env` 文件是否存在且配置正确
- 确认 `OPENAI_API_KEY` 已正确设置
- 检查网络连接是否正常
- 验证 API 密钥是否有效

### 问题：AI 移动不合理

**解决方案**：
- 查看控制台输出的详细日志
- 检查是否检测到循环模式
- 尝试调整 `llm_call_interval` 给 AI 更多思考时间
- 尝试使用更强大的模型（如 `gpt-4o`）

### 问题：迷宫生成失败

**解决方案**：
- 确保迷宫宽度和高度都是奇数
- 检查是否有足够的系统资源

## 📝 开发计划

- [ ] 支持更多 LLM 提供商（Claude、Gemini 等）
- [ ] 添加难度等级选择
- [ ] 实现移动动画效果
- [ ] 添加统计信息（步数、时间等）
- [ ] 支持保存和加载游戏状态
- [ ] 添加多种迷宫生成算法

## 📄 许可证

本项目采用 MIT 许可证。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**享受游戏，体验 AI 的魅力！** 🎮🤖

