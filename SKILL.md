---
name: hobby
description: |
  个人兴趣与性格分析工具。通过分析多平台数字足迹（小红书、B站、闲鱼等）推断兴趣爱好和性格特征。

  触发词：/hobby collect、/hobby chat、/hobby trend、/hobby setup、分析我的兴趣、我的数字画像
---

# Hobby-Skill - 个人兴趣与性格分析

**核心原则：所有数据处理在本地完成，不上传任何个人数据。**

## 命令

| 命令 | 功能 |
|------|------|
| `/hobby collect` | 采集数据并更新数字画像 |
| `/hobby chat` | 通过对话深入了解自己 |
| `/hobby trend` | 查看兴趣变化趋势 |
| `/hobby setup` | 设置每日定时采集 |

---

## 一、采集流程 (`/hobby collect`)

**流程：检查登录 → 选择平台/页面 → 爬取 → 分析 → 显示画像**

### 1. 检查登录状态

```bash
cd ~/hobby-skill && source .venv/bin/activate && python scripts/browser_server.py status
```

向用户显示各平台登录状态（✅已登录/❌未登录）。

### 2. 选择平台

支持：小红书、B站、闲鱼、微博、知乎

- 已登录平台：直接采集
- 未登录平台：执行 `python scripts/browser_server.py open <platform>` 打开浏览器，用户登录后回复"登录好了"

### 3. 选择页面并爬取

根据平台显示可用页面，用户选择后执行无头爬取：

```bash
python scripts/browser_server.py crawl <platform> <url> <page_name>
python scripts/browser_server.py save <platform> '[数据]'
```

### 4. 分析并显示画像

读取 `~/hobby-data/crawled/` 数据，分析后更新 `~/hobby-data/current_profile.json` 并显示画像。

---

## 二、对话探索 (`/hobby chat`)

### 核心原则

- 每次只问一个问题，提供3个选项（A/B/C），**用户也可自由输入**
- 每次回答后立即保存到画像
- 2-3轮后询问是否继续

### 问题来源（优先级）

1. **画像标签** - 基于用户已有标签生成（无需联网）
2. **缓存热点** - 基于当日缓存热点（无需联网）
3. **基础问题** - 通用探索类问题
4. **联网补充** - 仅缓存为空且无画像时联网

### 对话示例

```
🤖 嗨！看了你的画像：科技80%，游戏60%。

你关注科技资讯主要是为了？
A. 工作需要  B. 个人兴趣  C. 了解行业动态
（也可以自由回答）

👤 B，喜欢了解新事物

🤖 懂了！[正在保存...]
换个话题～你玩游戏主要是为了？
A. 放松娱乐  B. 社交互动  C. 挑战成就

👤 主要是下班后解压，偶尔也和朋友联机

🤖 休闲玩家，兼顾社交！[正在保存...]

还想继续聊吗？
```

---

## 三、定时采集 (`/hobby setup`)

### 1. 检查已有任务

```bash
launchctl list | grep hobby
```

如果已存在，显示任务状态；如果不存在，进入创建流程。

### 2. 创建定时任务

创建 launchd 定时任务，每天 22:00 自动采集，结果保存到 `~/hobby-data/history/`

```bash
# 创建脚本
mkdir -p ~/hobby-data/history
cat > ~/hobby-data/daily_collect.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y-%m-%d)
cd ~/hobby-skill && source .venv/bin/activate
claude -p "/hobby collect" > ~/hobby-data/history/profile_$DATE.json 2>&1
EOF
chmod +x ~/hobby-data/daily_collect.sh

# 创建 launchd 任务
cat > ~/Library/LaunchAgents/com.hobby.daily.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.hobby.daily</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/$(whoami)/hobby-data/daily_collect.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>22</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
</dict>
</plist>
EOF

launchctl load ~/Library/LaunchAgents/com.hobby.daily.plist
```

### 3. 验证任务

```bash
launchctl list | grep hobby
```

---

## 四、查看趋势 (`/hobby trend`)

对比 `~/hobby-data/history/` 下历史文件，输出兴趣变化趋势报告。

---

## 数据存储

**目录**：`~/hobby-data`（可通过 `HOBBY_DATA_DIR` 环境变量自定义）

```
~/hobby-data/
├── crawled/              # 爬取的原始数据
├── history/              # 历史画像
├── conversations/        # 对话记录
├── hotspots_cache.json   # 热点缓存
└── current_profile.json  # 当前画像
```

## 平台页面

| 平台 | 公开页面 | 需登录页面 |
|------|----------|------------|
| 小红书 | 发现 | 我的点赞、我的收藏 |
| B站 | 首页 | 历史记录、我的收藏 |
| 闲鱼 | 首页 | 我的发布 |
| 微博 | 首页 | 我的收藏 |
| 知乎 | 首页、热榜 | 我的收藏 |

## 分析维度

- **兴趣分类**（12领域）：科技/数码、美妆/时尚、游戏/动漫、美食/烹饪、旅行/户外、音乐/影视、运动/健身、财经/投资、教育/职场、家居/生活、宠物、汽车
- **性格推断**（大五人格）：开放性、尽责性、外向性、宜人性、神经质

## 输出格式

```markdown
# 🔍 你的数字画像 (2026-03-09)

## 📊 兴趣分布
| 领域 | 热度 |
|------|------|
| 科技/数码 | ████████░░ 80% |
| 游戏/动漫 | ██████░░░░ 60% |

## 🏷️ 核心标签
`科技爱好者` `游戏玩家`

## 🧠 性格画像
开放性 ■■■■■■■□□□ | 尽责性 ■■■■■■■□□□

## 💡 今日洞察
- 新增关注：AI应用
- 热度上升：科技/数码 (+5%)
```

## 依赖

```bash
pip install playwright
playwright install chromium
```
