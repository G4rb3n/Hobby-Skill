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
    "douban": {
        "name": "豆瓣",
        "url": "https://www.douban.com",
        "pages": {
            "电影想看": "https://movie.douban.com/mine?status=wish",
            "电影看过": "https://movie.douban.com/mine?status=collect",
            "书影音档案": "https://www.douban.com/mine/",
            "我的小组": "https://www.douban.com/group/mine",
        }
    },
    "neteasemusic": {
        "name": "网易云音乐",
        "url": "https://music.163.com",
        "pages": {
            "我的歌单": "https://music.163.com/#/my/m/music/playlist",
            "听歌排行": "https://music.163.com/#/my/m/music/record",
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
    "bilibili": {"in": [".bili-avatar", ".header-avatar-wrap", "[class*='avatar']"], "out": ["text=登录"]},
    "douban": {"in": [".nav-user-avatar", ".user-avatar", "a[href*='/mine/']"], "out": ["text=登录", "text=注册"]},
    "neteasemusic": {"in": [".name", "[data-res-id='my']"], "out": ["text=登录"]},
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
        # 使用现有页面而非新建标签页
        pages = context.pages
        if pages:
            page = pages[0]
        else:
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
    import re
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

        # B站首页特殊处理：提取视频标题
        if platform == "bilibili" and ("bilibili.com$" in url or "bilibili.com/$" in url or url.endswith("bilibili.com")):
            # 滚动加载更多内容
            for _ in range(4):
                await page.evaluate("window.scrollBy(0, 600)")
                await asyncio.sleep(0.8)

            # 使用精确的标题选择器
            title_selectors = [
                ".bili-video-card__info--tit",
                ".feed-card .title",
                "[class*='video-title']",
                "h3[class*='title']"
            ]

            for selector in title_selectors:
                elements = await page.query_selector_all(selector)
                for elem in elements:
                    try:
                        text = await elem.inner_text()
                        text = text.strip()
                        # 过滤：长度>5，不是纯数字/时间格式
                        if text and len(text) > 5:
                            if not re.match(r'^[\d.\s万千百:]+$', text):
                                if not re.match(r'^\d+[:\d]+$', text):
                                    if text not in seen:
                                        seen.add(text)
                                        items.append({
                                            "title": text[:200],
                                            "url": "",
                                            "image": "",
                                        })
                    except:
                        pass

            # 备用：从带title属性的视频链接获取
            if len(items) < 30:
                links = await page.query_selector_all("a[href*='video/BV'][title]")
                for link in links:
                    try:
                        title = await link.get_attribute("title")
                        href = await link.get_attribute("href")
                        if title and len(title) > 5 and title not in seen:
                            if not re.match(r'^[\d.\s万千百:]+$', title):
                                seen.add(title)
                                base = page.url.split("/")[2]
                                full_url = href if href.startswith("http") else f"https://{base}{href}"
                                items.append({
                                    "title": title[:200],
                                    "url": full_url,
                                    "image": "",
                                })
                    except:
                        pass

        # B站收藏页面特殊处理
        elif platform == "bilibili" and "favlist" in url:
            # 滚动加载更多内容
            for _ in range(6):
                await page.evaluate("window.scrollBy(0, 500)")
                await asyncio.sleep(0.6)

            # 收藏页面的视频卡片选择器
            fav_selectors = [
                ".bili-video-card .bili-video-card__info--tit",
                ".video-card .title",
                "[class*='video-card'] [class*='title']",
                ".fav-video-list .title",
            ]

            for selector in fav_selectors:
                elements = await page.query_selector_all(selector)
                for elem in elements:
                    try:
                        # 尝试获取title属性或文本
                        text = await elem.get_attribute("title")
                        if not text:
                            text = await elem.inner_text()
                        text = text.strip() if text else ""

                        if text and len(text) > 8 and text not in seen:
                            if not re.match(r'^[\d.\s万千百:]+$', text):
                                if "纪录片" not in text[:4] and "电影" not in text[:3]:
                                    seen.add(text)
                                    items.append({
                                        "title": text[:200],
                                        "url": "",
                                        "image": "",
                                    })
                    except:
                        pass

            # 备用方法：查找视频链接
            if len(items) < 10:
                video_links = await page.query_selector_all("a[href*='video/BV']")
                for link in video_links:
                    try:
                        # 尝试多种方式获取标题
                        title = await link.get_attribute("title")
                        if not title:
                            # 查找子元素中的标题
                            title_elem = await link.query_selector("[class*='title'], [class*='tit']")
                            if title_elem:
                                title = await title_elem.inner_text()
                        if not title:
                            title = await link.inner_text()

                        href = await link.get_attribute("href")
                        title = title.strip() if title else ""

                        if title and len(title) > 8 and title not in seen:
                            if not re.match(r'^[\d.\s万千百:]+$', title):
                                if "纪录片" not in title[:4] and "电影" not in title[:3]:
                                    seen.add(title)
                                    base = page.url.split("/")[2]
                                    full_url = href if href.startswith("http") else f"https://{base}{href}"
                                    items.append({
                                        "title": title[:200],
                                        "url": full_url,
                                        "image": "",
                                    })
                    except:
                        pass

        # B站历史记录页面特殊处理
        elif platform == "bilibili" and "history" in url:
            for _ in range(5):
                await page.evaluate("window.scrollBy(0, 500)")
                await asyncio.sleep(0.6)

            # 历史记录的标题提取
            history_selectors = [
                ".history-list .title",
                "[class*='history'] [class*='title']",
                "a[href*='video/BV'][title]",
            ]

            for selector in history_selectors:
                elements = await page.query_selector_all(selector)
                for elem in elements:
                    try:
                        text = await elem.get_attribute("title")
                        if not text:
                            text = await elem.inner_text()
                        text = text.strip() if text else ""

                        if text and len(text) > 8 and text not in seen:
                            if not re.match(r'^[\d.\s万千百:]+$', text):
                                seen.add(text)
                                items.append({
                                    "title": text[:200],
                                    "url": "",
                                    "image": "",
                                })
                    except:
                        pass

        # 豆瓣页面特殊处理
        elif platform == "douban":
            await asyncio.sleep(2)

            # 豆瓣电影/书籍列表
            douban_selectors = [
                ".item .title a",
                ".list .title a",
                "[class*='item'] [class*='title'] a",
                "a[href*='subject'][title]",
            ]

            for selector in douban_selectors:
                elements = await page.query_selector_all(selector)
                for elem in elements:
                    try:
                        title = await elem.get_attribute("title")
                        if not title:
                            title = await elem.inner_text()
                        title = title.strip() if title else ""

                        href = await elem.get_attribute("href")

                        if title and len(title) > 3 and title not in seen:
                            # 过滤无效标题
                            if not re.match(r'^[\d.\s万千百:]+$', title):
                                if "备案" not in title and "许可证" not in title:
                                    if "登录" not in title and "注册" not in title:
                                        seen.add(title)
                                        base = page.url.split("/")[2]
                                        full_url = href if (href and href.startswith("http")) else f"https://{base}{href}" if href else ""
                                        items.append({
                                            "title": title[:200],
                                            "url": full_url,
                                            "image": "",
                                        })
                    except:
                        pass

        # 网易云音乐页面特殊处理（iframe嵌套）
        elif platform == "neteasemusic":
            # 网易云音乐使用 iframe，            await asyncio.sleep(3)

            # 尝试获取 iframe 内容
            frame = page.frame_locator("iframe[name='contentFrame']")
            if frame:
                # 在 iframe 中查找歌单
                song_selectors = [
                    ".m-playlist .title",
                    "[class*='playlist'] [class*='name']",
                    ".n-song",
                ]

                for selector in song_selectors:
                    elements = await frame.query_selector_all(selector)
                    for elem in elements:
                        try:
                            title = await elem.inner_text()
                            title = title.strip() if title else ""

                            if title and len(title) > 2 and title not in seen:
                                if not re.match(r'^[\d.\s万千百:]+$', title):
                                    if "播放" not in title[:3] and "收藏" not in title[:3]:
                                        seen.add(title)
                                        items.append({
                                            "title": title[:200],
                                            "url": "",
                                            "image": "",
                                        })
                        except:
                            pass
            else:
                # 如果没有 iframe，尝试直接获取
                music_selectors = [
                    ".m-playlist .title",
                    "[class*='playlist'] [class*='name']",
                    ".song-list .song-name",
                ]

                for selector in music_selectors:
                    elements = await page.query_selector_all(selector)
                    for elem in elements:
                        try:
                            title = await elem.inner_text()
                            title = title.strip() if title else ""

                            if title and len(title) > 2 and title not in seen:
                                seen.add(title)
                                items.append({
                                    "title": title[:200],
                                    "url": "",
                                    "image": "",
                                })
                        except:
                            pass

        else:
            # 通用爬取逻辑
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

        # 去重和清理
        unique = []
        seen_titles = set()
        for item in items:
            title = item["title"]
            key = title[:50]

            # 过滤无效条目
            if key not in seen_titles:
                # 过滤备案、许可证等
                if "备案" in title or "许可证" in title:
                    continue
                # 过滤 "UP主名 · 收藏于日期" 格式的条目
                if re.match(r'^[^·]+·\s*收藏于', title):
                    continue
                # 过滤纯UP主名（通常是短文本加 · 符号）
                if "·" in title and len(title.split("·")[0]) < 10:
                    continue
                # 过滤B站知识学院等非视频标题
                if "B站知识学院" in title or "周侃侃plus" in title:
                    continue

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
