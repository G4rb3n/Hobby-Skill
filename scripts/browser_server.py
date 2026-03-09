#!/usr/bin/env python3
"""
Hobby 数据采集脚本
支持持久化登录状态，浏览器保持打开
"""

import asyncio
import os
import sys
import json
import signal
from datetime import datetime
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print(json.dumps({"error": "请安装 playwright"}))
    sys.exit(1)

PLATFORMS = {
    "xiaohongshu": {
        "name": "小红书",
        "url": "https://www.xiaohongshu.com",
        "pages": {
            "发现": "https://www.xiaohongshu.com/explore",
            # 个人页面需要在登录后动态获取用户ID
            # 格式: /user/profile/{user_id}?tab=xxx
            "我的点赞": "https://www.xiaohongshu.com/user/profile/self?tab=liked",
            "我的收藏": "https://www.xiaohongshu.com/user/profile/self?tab=fav&subTab=note",
        }
    },
    "bilibili": {
        "name": "B站",
        "url": "https://www.bilibili.com",
        "pages": {
            "首页推荐": "https://www.bilibili.com",
            "历史记录": "https://www.bilibili.com/account/history",
            "我的收藏": "https://space.bilibili.com/favlist",
        }
    },
    "xianyu": {
        "name": "闲鱼",
        "url": "https://www.goofish.com",
        "pages": {
            "首页推荐": "https://www.goofish.com",
            "我的发布": "https://www.goofish.com/personal",
        }
    },
    "weibo": {
        "name": "微博",
        "url": "https://weibo.com",
        "pages": {
            "首页": "https://weibo.com",
            "我的收藏": "https://weibo.com/fav",
        }
    },
    "zhihu": {
        "name": "知乎",
        "url": "https://www.zhihu.com",
        "pages": {
            "首页推荐": "https://www.zhihu.com",
            "热榜": "https://www.zhihu.com/hot",
            "我的收藏": "https://www.zhihu.com/collections",
        }
    },
}

LOGIN_INDICATORS = {
    "xiaohongshu": {"in": ["[class*='avatar']"], "out": ["text=登录"]},
    "bilibili": {"in": [".bili-avatar"], "out": ["text=登录"]},
    "xianyu": {"in": ["[class*='avatar']"], "out": ["text=登录"]},
    "weibo": {"in": [".woo-avatar"], "out": ["text=登录"]},
    "zhihu": {"in": [".AppHeader-profile"], "out": ["text=登录"]},
}

# 数据存储目录（用户可通过环境变量 HOBBY_DATA_DIR 自定义）
DATA_DIR = Path(os.environ.get("HOBBY_DATA_DIR", Path.home() / "hobby-data")) / "crawled"
CRAWLER_DATA_DIR = Path.home() / ".crawler_data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_user_data_dir(platform: str) -> Path:
    return CRAWLER_DATA_DIR / platform


def output(data: dict):
    print(json.dumps(data, ensure_ascii=False), flush=True)


async def cmd_status():
    """检查所有平台登录状态"""
    results = []
    for platform, config in PLATFORMS.items():
        playwright = None
        context = None
        try:
            playwright = await async_playwright().start()
            user_dir = str(get_user_data_dir(platform))
            context = await playwright.chromium.launch_persistent_context(
                user_data_dir=user_dir,
                headless=True,
                viewport={"width": 1280, "height": 900},
            )
            page = await context.new_page()
            await page.goto(config["url"], wait_until="networkidle", timeout=20000)

            indicators = LOGIN_INDICATORS.get(platform, LOGIN_INDICATORS["xiaohongshu"])

            logged_in = False
            for sel in indicators["in"]:
                elem = await page.query_selector(sel)
                if elem and await elem.is_visible():
                    logged_in = True
                    break

            results.append({
                "platform": platform,
                "name": config["name"],
                "logged_in": logged_in,
                "status": "已登录" if logged_in else "未登录"
            })
        except Exception as e:
            results.append({
                "platform": platform,
                "name": config["name"],
                "logged_in": False,
                "status": f"检查失败"
            })
        finally:
            if context:
                await context.close()
            if playwright:
                await playwright.stop()

    output({"platforms": results})


async def cmd_open(platform: str):
    """打开浏览器供用户登录，保持打开直到被终止"""
    playwright = None
    context = None
    try:
        playwright = await async_playwright().start()
        user_dir = str(get_user_data_dir(platform))
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=user_dir,
            headless=False,
            viewport={"width": 1280, "height": 900},
            locale="zh-CN",
        )
        page = await context.new_page()
        await page.goto(PLATFORMS[platform]["url"])

        output({"status": "opened", "message": "浏览器已打开，请在浏览器中操作，登录完成后回复'登录好了'", "url": PLATFORMS[platform]["url"]})

        # 保持浏览器打开，直到进程被终止
        while True:
            await asyncio.sleep(1)

    except asyncio.CancelledError:
        output({"status": "closed", "message": "浏览器已关闭"})
    except Exception as e:
        output({"status": "error", "message": str(e)})
    finally:
        if context:
            await context.close()
        if playwright:
            await playwright.stop()


async def cmd_crawl(platform: str, url: str, name: str = ""):
    """爬取页面（无头模式，使用已保存的cookie）"""
    playwright = None
    context = None
    try:
        playwright = await async_playwright().start()
        user_dir = str(get_user_data_dir(platform))
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=user_dir,
            headless=True,  # 无头模式，不显示浏览器
            viewport={"width": 1280, "height": 900},
            locale="zh-CN",
        )
        page = await context.new_page()
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(2)

        items = []
        seen = set()

        for _ in range(3):
            links = await page.query_selector_all("a[href]")
            for link in links:
                try:
                    href = await link.get_attribute("href")
                    text = await link.inner_text()
                    if href and href not in seen and len(text.strip()) > 5:
                        seen.add(href)
                        img = await link.query_selector("img")
                        img_src = await img.get_attribute("src") if img else ""
                        base = page.url.split("/")[2]
                        full_url = href if href.startswith("http") else f"https://{base}{href}"
                        items.append({
                            "title": text.strip()[:200],
                            "url": full_url,
                            "image": img_src,
                        })
                except:
                    continue

            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(1.5)

        # 去重
        unique = []
        seen_titles = set()
        for item in items:
            key = item["title"][:50]
            if key not in seen_titles and "备案" not in item["title"] and "许可证" not in item["title"]:
                seen_titles.add(key)
                unique.append(item)

        output({"page": name, "url": url, "count": len(unique), "items": unique[:100]})

    except Exception as e:
        output({"error": str(e), "page": name, "url": url, "items": []})
    finally:
        if context:
            await context.close()
        if playwright:
            await playwright.stop()


def cmd_save(platform: str, data_json: str):
    """保存数据"""
    pages_data = json.loads(data_json)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = DATA_DIR / f"{platform}_{timestamp}.json"

    result = {
        "platform": platform,
        "platform_name": PLATFORMS[platform]["name"],
        "crawl_time": datetime.now().isoformat(),
        "pages": pages_data,
        "total_items": sum(p.get("count", 0) for p in pages_data),
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    output({"saved": str(filepath), "total_items": result["total_items"]})


def cmd_pages(platform: str):
    """获取平台可用页面"""
    if platform not in PLATFORMS:
        output({"error": f"未知平台: {platform}"})
    else:
        output({
            "platform": platform,
            "name": PLATFORMS[platform]["name"],
            "pages": PLATFORMS[platform]["pages"]
        })


async def main():
    if len(sys.argv) < 2:
        output({"error": "缺少命令。可用: status, open, crawl, save, pages, platforms"})
        return

    cmd = sys.argv[1]

    if cmd == "platforms":
        output({"platforms": [{k: v["name"]} for k, v in PLATFORMS.items()]})
        return

    if cmd == "status":
        await cmd_status()
        return

    if cmd == "pages":
        if len(sys.argv) < 3:
            output({"error": "缺少平台参数"})
            return
        cmd_pages(sys.argv[2])
        return

    if cmd == "open":
        if len(sys.argv) < 3:
            output({"error": "缺少平台参数"})
            return
        await cmd_open(sys.argv[2])
        return

    if cmd == "crawl":
        if len(sys.argv) < 4:
            output({"error": "缺少参数: crawl <platform> <url> [name]"})
            return
        platform = sys.argv[2]
        url = sys.argv[3]
        name = sys.argv[4] if len(sys.argv) > 4 else ""
        await cmd_crawl(platform, url, name)
        return

    if cmd == "save":
        if len(sys.argv) < 4:
            output({"error": "缺少参数: save <platform> <json_data>"})
            return
        cmd_save(sys.argv[2], sys.argv[3])
        return

    output({"error": f"未知命令: {cmd}"})


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        output({"status": "interrupted", "message": "用户中断"})
