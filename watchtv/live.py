import re
import os
import requests
import urllib3
from bs4 import BeautifulSoup
from urllib.parse import quote

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# =========================================================
# 基本配置
# =========================================================

KEYWORD = os.environ.get("IPTV_KEYWORD", "CCTV1").strip()

# 主入口
TONKIANG_URL = "https://tonkiang.us/?iptv=" + quote(KEYWORD)

# 备用入口
FOODIEGUIDE_URL = (
    "https://www.foodieguide.com/iptvsearch/?iptv="
    + quote(KEYWORD)
)

TIMEOUT = 20

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,image/webp,"
        "image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
}


# =========================================================
# 判断是不是直播地址
# =========================================================

def is_stream_url(url):
    if not url:
        return False

    url = url.strip()

    if not re.match(r"^(https?|rtsp|rtmp|udp)://", url, re.I):
        return False

    lower = url.lower()

    keywords = [
        ".m3u8",
        ".m3u",
        ".ts",
        ".flv",
        ".mp4",
        "rtsp://",
        "rtmp://",
        "/live/",
        "/hls/",
        "/playlist",
        "/stream",
        "/play",
    ]

    return any(x in lower for x in keywords)


# =========================================================
# 从 onclick 中提取 URL
# 例如：
#
# onclick="yaergl('http://xxx/test.m3u8')"
# =========================================================

def extract_urls_from_onclick(value):
    if not value:
        return []

    results = []

    patterns = [
        r"""['"]((?:https?|rtsp|rtmp)://[^'"]+)['"]""",
        r"""['"]((?:https?|rtsp|rtmp):\\/\\/[^'"]+)['"]""",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, value, re.I)

        for item in matches:
            item = item.replace("\\/", "/")

            if is_stream_url(item):
                results.append(item)

    return results


# =========================================================
# 从 HTML 提取直播源
#
# 根据你提供的实际网页源码：
#
# <div class="resultplus">
#   <div class="channel1">
#       ...
#       <td class="nl">
#           http://xxx/live/cctv1.m3u8
#       </td>
#
# 同时兼容：
# onclick="yaergl('http://xxx.m3u8')"
# =========================================================

def parse_streams(html):

    results = []

    soup = BeautifulSoup(html, "html.parser")

    # -----------------------------------------------------
    # 方法一：优先读取 td.nl
    # -----------------------------------------------------

    for td in soup.select("td.nl"):

        text = td.get_text(" ", strip=True)

        if not text:
            continue

        # 一个 td 中可能存在多个地址
        found = re.findall(
            r"""(?:(?:https?|rtsp|rtmp)://[^\s<>"']+)""",
            text,
            re.I
        )

        for url in found:

            # 去掉尾部 HTML/标点
            url = url.rstrip(".,;，。；）)】]")

            if is_stream_url(url):
                results.append(url)

    # -----------------------------------------------------
    # 方法二：寻找 onclick
    # -----------------------------------------------------

    for tag in soup.find_all(True):

        onclick = tag.get("onclick")

        if onclick:

            urls = extract_urls_from_onclick(onclick)

            results.extend(urls)

    # -----------------------------------------------------
    # 方法三：读取 a href
    # -----------------------------------------------------

    for a in soup.find_all("a"):

        href = a.get("href")

        if not href:
            continue

        if is_stream_url(href):
            results.append(href)

    # -----------------------------------------------------
    # 方法四：最后再从 resultplus 区域兜底搜索
    # -----------------------------------------------------

    result_area = soup.select(".resultplus")

    for block in result_area:

        text = block.get_text(" ", strip=True)

        found = re.findall(
            r"""(?:(?:https?|rtsp|rtmp)://[^\s<>"']+)""",
            text,
            re.I
        )

        for url in found:

            url = url.rstrip(".,;，。；）)】]")

            if is_stream_url(url):
                results.append(url)

    # -----------------------------------------------------
    # 去重
    # -----------------------------------------------------

    final_results = []

    seen = set()

    for url in results:

        url = url.strip()

        if not url:
            continue

        if url in seen:
            continue

        seen.add(url)

        final_results.append(url)

    return final_results


# =========================================================
# 请求网页
# =========================================================

def fetch_page(url, verify_ssl=True):

    try:

        print("请求地址：", url)

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=TIMEOUT,
            verify=verify_ssl,
            allow_redirects=True
        )

        print("HTTP状态：", response.status_code)
        print("最终地址：", response.url)
        print("网页长度：", len(response.text))

        return response

    except requests.RequestException as e:

        print("网络请求错误：")
        print(e)

        return None


# =========================================================
# 搜索
# =========================================================

def search():

    print()
    print("=" * 60)
    print("IPTV 直播源搜索")
    print("=" * 60)
    print("搜索关键词：", KEYWORD)
    print()

    html = None
    source = ""

    # =====================================================
    # 第一入口：Tonkiang
    # =====================================================

    print("【1】尝试 Tonkiang 主入口")

    response = fetch_page(
        TONKIANG_URL,
        verify_ssl=True
    )

    if response is not None:

        if response.status_code == 200:

            # Cloudflare 验证页面也可能返回 200
            lower_html = response.text.lower()

            if (
                "not a robot" not in lower_html
                and "cloudflare" not in lower_html
                and "just a moment" not in lower_html
            ):

                html = response.text
                source = "tonkiang"

                print("Tonkiang 页面获取成功")

            else:

                print("Tonkiang 返回验证页面")

        else:

            print("Tonkiang HTTP 状态异常")

    # =====================================================
    # 第二入口：FoodieGuide
    # =====================================================

    if html is None:

        print()
        print("【2】切换 FoodieGuide 备用入口")

        response = fetch_page(
            FOODIEGUIDE_URL,
            verify_ssl=False
        )

        if response is not None:

            if response.status_code == 200:

                html = response.text
                source = "foodieguide"

                print("FoodieGuide 页面获取成功")

            else:

                print("FoodieGuide HTTP 状态异常")

    # =====================================================
    # 两个入口都失败
    # =====================================================

    if html is None:

        print()
        print("=" * 60)
        print("搜索失败")
        print("=" * 60)
        print()
        print("两个入口都无法获取搜索页面。")
        print()
        return []

    # =====================================================
    # 开始解析
    # =====================================================

    print()
    print("使用入口：", source)
    print("开始解析直播源...")
    print()

    streams = parse_streams(html)

    print("找到直播源：", len(streams))

    # =====================================================
    # 显示结果
    # =====================================================

    if streams:

        print()

        for i, url in enumerate(streams, 1):

            print(f"{i}. {url}")

    else:

        print()
        print("没有找到直播源。")
        print()
        print("正在输出网页中与 m3u8/m3u/ts 相关的内容用于调试...")
        print()

        debug_matches = re.findall(
            r"""(?:(?:https?|rtsp|rtmp)://[^\s<>"']+)""",
            html,
            re.I
        )

        debug_count = 0

        for item in debug_matches:

            item = item.rstrip(".,;，。；）)]")

            if any(
                x in item.lower()
                for x in [
                    ".m3u8",
                    ".m3u",
                    ".ts",
                    ".flv",
                    ".mp4"
                ]
            ):

                print(item)

                debug_count += 1

                if debug_count >= 30:
                    break

    return streams


# =========================================================
# 保存 TXT
# =========================================================

def save_txt(streams):

    filename = "live_results.txt"

    try:

        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as f:

            for url in streams:
                f.write(url + "\n")

        print()
        print("TXT 已保存：", filename)

    except Exception as e:

        print("保存 TXT 失败：", e)


# =========================================================
# 保存 M3U
# =========================================================

def save_m3u(streams):

    filename = "live_results.m3u"

    try:

        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as f:

            f.write("#EXTM3U\n")

            for index, url in enumerate(streams, 1):

                f.write(
                    f'#EXTINF:-1,{KEYWORD} {index}\n'
                )

                f.write(url + "\n")

        print("M3U 已保存：", filename)

    except Exception as e:

        print("保存 M3U 失败：", e)


# =========================================================
# 主程序
# =========================================================

if __name__ == "__main__":

    streams = search()

    print()
    print("=" * 60)
    print("搜索结束")
    print("直播源数量：", len(streams))
    print("=" * 60)

    if streams:

        save_txt(streams)
        save_m3u(streams)

    print()
