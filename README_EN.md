# Hobby-Skill - Personal Interest & Personality Analysis

<div align="center">

**Discover yourself through your digital footprint**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-purple.svg)](https://claude.ai/code)

English | [简体中文](./README.md)

</div>

---

## What is this?

Have you ever wondered: **What does my browsing history say about who I am?**

Hobby-Skill is a local-first tool that analyzes your browsing history, likes, and bookmarks from platforms like Xiaohongshu (Little Red Book), Bilibili, Weibo, and Zhihu to automatically infer your interests and personality traits.

**Core Principle: All data processing happens locally. No personal data is uploaded to the cloud.**

---

## Features

| Feature | Description |
|---------|-------------|
| **Data Collection** | Collect browsing/likes/bookmarks from Xiaohongshu, Bilibili, Weibo, Zhihu |
| **Interest Analysis** | Auto-categorize into 12 domains (Tech, Beauty/Fashion, Gaming/Anime, etc.) |
| **Personality Inference** | Infer personality traits based on Big Five model |
| **Chat Exploration** | Deep dive into your interests through Q&A |
| **Trend Tracking** | View how your interests change over time |
| **Scheduled Collection** | Support daily automatic data collection |

---

## Screenshots

### `/hobby collect` - Collect data and generate profile
![collect.png](collect.png)

### `/hobby chat` - Explore yourself through conversation
![chat.png](chat.png)

### `/hobby trend` - View interest trends over time
![trend.png](trend.png)

### `/hobby setup` - Setup daily scheduled collection
![setup.png](setup.png)

---

## Quick Start

### 1. Install Dependencies

```bash
cd ~/hobby-skill
python -m venv .venv
source .venv/bin/activate
pip install playwright
playwright install chromium
```

### 2. Use as Claude Code Skill

1. Copy `SKILL.md` to `~/.claude/skills/hobby/SKILL.md`
2. Run `/hobby` command in Claude Code

### 3. Available Commands

| Command | Description |
|---------|-------------|
| `/hobby collect` | Collect data and update digital profile |
| `/hobby chat` | Explore yourself through conversation |
| `/hobby trend` | View interest change trends |
| `/hobby setup` | Setup daily scheduled collection |

---

## Supported Platforms

| Platform | Collectable Pages |
|----------|-------------------|
| Xiaohongshu (小红书) | Discover, My Likes, My Bookmarks |
| Bilibili (B站) | Homepage, History, My Favorites |
| Weibo (微博) | Homepage, My Favorites |
| Zhihu (知乎) | Homepage, Hot List, My Favorites |

---

## Analysis Dimensions

### Interest Categories (12 Domains)
Tech/Digital, Beauty/Fashion, Gaming/Anime, Food/Cooking, Travel/Outdoor, Music/Movies, Sports/Fitness, Finance/Investment, Education/Career, Home/Lifestyle, Pets, Automotive

### Personality Inference (Big Five)
Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism

---

## Data Directory

Default data storage: `~/hobby-data` (customizable via environment variable):

```bash
export HOBBY_DATA_DIR=~/my-custom-data-dir
```

Directory structure:
```
~/hobby-data/
├── crawled/                    # Raw collected data
├── history/                    # Historical profiles
├── conversations/              # Conversation records
├── hotspots_cache.json         # Hot topics cache
└── current_profile.json        # Current profile
```

---

## Use Cases

- **Self-Discovery** - Find out what you're truly interested in
- **Time Tracking** - Understand your browsing habits and time allocation
- **Personality Exploration** - Know yourself through behavioral data, not questionnaires
- **Trend Observation** - Track how your interests change over time

---

## Privacy

- **Local-First** - All data processing happens locally
- **Data Isolation** - User data is stored separately from code
- **Full Control** - Users can delete all data at any time
- **No Upload** - No personal information is uploaded to the cloud

---

## Roadmap

- [ ] Support more platforms (Douyin, Kuaishou, etc.)
- [ ] Web visualization interface
- [ ] Export reports (PDF/HTML)
- [ ] Multi-device data sync
- [ ] AI-powered insights and suggestions

---

## Contributing

Issues and Pull Requests are welcome!

---

## License

[MIT License](LICENSE)
