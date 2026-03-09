# Hobby - 个人兴趣与性格分析

通过分析数字足迹认识自己。支持浏览器自动化采集、定时任务、历史追踪、对话探索。

**核心原则：所有数据处理在本地完成，不上传任何个人数据。**

## 功能

- **数据采集** - 从小红书、B站、闲鱼、微博、知乎等平台采集浏览/点赞/收藏数据
- **兴趣分析** - 自动归类到12个领域（科技/数码、美妆/时尚、游戏/动漫等）
- **性格推断** - 基于大五人格模型推断性格特征
- **对话探索** - 通过问答深入了解自己的兴趣和性格
- **趋势追踪** - 查看兴趣随时间的变化趋势
- **定时采集** - 支持每日自动采集更新

## 快速开始

### 安装依赖

```bash
cd ~/hobby
python -m venv .venv
source .venv/bin/activate
pip install playwright
playwright install chromium
```

### 使用

将此项目作为 Claude Code Skill 使用：

1. 复制 `SKILL.md` 到 `~/.claude/skills/hobby/skill.md`
2. 在 Claude Code 中执行 `/hobby` 命令

### 可用命令

| 命令 | 功能 |
|------|------|
| `/hobby collect` | 采集数据并更新数字画像 |
| `/hobby chat` | 通过对话深入了解自己 |
| `/hobby trend` | 查看兴趣变化趋势 |
| `/hobby setup` | 设置每日定时采集 |

## 数据目录

默认使用 `~/hobby-data` 存储用户数据，可通过环境变量自定义：

```bash
export HOBBY_DATA_DIR=~/my-custom-data-dir
```

数据目录结构：
```
~/hobby-data/
├── crawled/                    # 爬取的原始数据
├── history/                    # 历史画像
├── conversations/              # 对话记录
├── hotspots_cache.json         # 热点缓存
└── current_profile.json        # 当前画像
```

## 隐私说明

- 所有数据处理在本地完成
- 不上传任何个人信息到云端
- 用户数据与代码隔离存储
- 用户可随时删除所有数据

## 许可证

MIT License
