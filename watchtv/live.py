import os
import re
import html
import time
import requests
import urllib3
from urllib.parse import quote

urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)

# =========================================================
# 配置
# =========================================================

BASE_URL = "https://www.foodieguide.com/iptvsearch/"

CHANNELS = [
    "CCTV1",
    "CCTV2",
    "CCTV3",
    "CCTV4",
    "CCTV5",
    "CCTV5+",
    "CCTV6",
    "CCTV7",
    "CCTV8",
    "CCTV9",
    "CCTV10",
    "CCTV11",
    "CCTV12",
    "CCTV13",
    "CCTV14",
    "CCTV15",
    "CCTV16",
    "CCTV17",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,"
        "image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
}

TIMEOUT = 30

# =========================================================
# 文件路径
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

M3U_FILE = os.path.join(
    BASE_DIR,
    "live.m3u8"
)

TXT_FILE = os.path.join(
    BASE_DIR,
    "live.txt"
)


# =========================================================
# 清理 URL
# =========================================================

def clean_url(url):

    if not url:
        return ""

    url = html.unescape(url)

    url = url.replace("\\/", "/")
    url = url.replace("\\u002F", "/")
    url = url.replace("\\x2F", "/")

    url = url.strip()
    url = url.strip("\"'<>")

    url = url.rstrip(
        ".,;，。；）)]}>"
    )

    return url


# =========================================================
# 判断直播地址
# =========================================================

def is_live_url(url):

    if not url:
        return False

    lower = url.lower()

    if not (
        lower.startswith("http://")
        or lower.startswith("https://")
    ):
        return False

    keywords = [
        ".m3u8",
        ".m3u",
        ".ts",
        "/rtp/",
        "/live/",
        "/hls/",
        "/tsfile/",
    ]

    return any(
        key in lower
        for key in keywords
    )


# =========================================================
# 提取直播地址
# =========================================================

def extract_urls(text):

    if not text:
        return []

    text = html.unescape(text)

    text = text.replace(
        "\\/",
        "/"
    )

    results = []

    pattern = re.compile(
        r'https?://'
        r'(?:'
        r'\[[0-9a-fA-F:]+\]'
        r'|'
        r'[A-Za-z0-9._:-]+'
        r')'
        r'(?:'
        r'[^"\'<>\s\\)]*'
        r')',
        re.IGNORECASE
    )

    for match in pattern.findall(text):

        url = clean_url(match)

        if is_live_url(url):
            results.append(url)

    pattern2 = re.compile(
        r'["\'](https?://[^"\']+)["\']',
        re.IGNORECASE
    )

    for match in pattern2.findall(text):

        url = clean_url(match)

        if is_live_url(url):
            results.append(url)

    return results


# =========================================================
# 搜索频道
# =========================================================

def search_channel(session, channel):

    print()
    print("=" * 60)
    print("正在搜索：", channel)
    print("=" * 60)

    url = (
        BASE_URL
        + "?chname="
        + quote(channel)
    )

    print("请求入口：", url)

    try:

        response = session.get(
            url,
            headers=HEADERS,
            timeout=TIMEOUT,
            verify=False,
            allow_redirects=True
        )

    except Exception as e:

        print("请求失败：", e)

        return []

    print(
        "HTTP 状态：",
        response.status_code
    )

    print(
        "最终地址：",
        response.url
    )

    print(
        "网页长度：",
        len(response.text)
    )

    if response.status_code != 200:
        print("页面获取失败")
        return []

    print(
        "开始解析：",
        channel
    )

    urls = extract_urls(
        response.text
    )

    # 当前频道去重
    unique = []
    seen = set()

    for url in urls:

        key = url.strip().lower()

        if key in seen:
            continue

        seen.add(key)

        unique.append(url)

    # 每个频道最多保留3条
    unique = unique[:3]

    print()
    print(
        channel,
        "找到直播源：",
        len(unique)
    )

    for index, url in enumerate(
        unique,
        1
    ):

        print(
            f"{index}. {url}"
        )

    return unique


# =========================================================
# 全局去重
# =========================================================

def deduplicate(channel_results):

    result = []

    global_seen = set()

    for channel, urls in channel_results:

        new_urls = []

        for url in urls:

            key = url.strip().lower()

            if key in global_seen:
                continue

            global_seen.add(key)

            new_urls.append(url)

        result.append(
            (
                channel,
                new_urls
            )
        )

    return result


# =========================================================
# 生成 M3U8
# =========================================================

def save_m3u8(channel_results):

    with open(
        M3U_FILE,
        "w",
        encoding="utf-8",
        newline="\n"
    ) as file:

        file.write(
            "#EXTM3U\n"
        )

        for channel, urls in channel_results:

            for url in urls:

                file.write(
                    '#EXTINF:-1 '
                    f'tvg-name="{channel}" '
                    'group-title="央视",'
                    f'{channel}\n'
                )

                file.write(
                    url
                    + "\n"
                )

    print()
    print(
        "M3U8 文件已生成：",
        M3U_FILE
    )


# =========================================================
# 生成 TXT
#
# 正确格式：
#
# 央视,#genre#
# CCTV1,http://xxx
# CCTV1,http://xxx
# CCTV2,http://xxx
# =========================================================

def save_txt(channel_results):

    with open(
        TXT_FILE,
        "w",
        encoding="utf-8",
        newline="\n"
    ) as file:

        # 分类行
        file.write(
            "央视,#genre#\n"
        )

        # 频道 + 地址
        for channel, urls in channel_results:

            for url in urls:

                file.write(
                    f"{channel},{url}\n"
                )

    print(
        "TXT 文件已生成：",
        TXT_FILE
    )


# =========================================================
# 主程序
# =========================================================

def main():

    print()
    print("=" * 60)
    print("IPTV 直播源搜索引擎")
    print("=" * 60)

    print(
        "搜索频道数量：",
        len(CHANNELS)
    )

    print(
        "搜索引擎：FoodieGuide"
    )

    print(
        "输出目录：",
        BASE_DIR
    )

    print("=" * 60)

    session = requests.Session()

    session.headers.update(
        HEADERS
    )

    channel_results = []

    # 搜索全部频道
    for channel in CHANNELS:

        urls = search_channel(
            session,
            channel
        )

        channel_results.append(
            (
                channel,
                urls
            )
        )

        time.sleep(0.5)

    # 全局直播源去重
    channel_results = deduplicate(
        channel_results
    )

    # =====================================================
    # 统计
    # =====================================================

    print()
    print("=" * 60)
    print("搜索结果统计")
    print("=" * 60)

    total = 0

    for channel, urls in channel_results:

        count = len(urls)

        total += count

        print(
            f"{channel}: {count} 条"
        )

    print()
    print(
        "全部直播源：",
        total
    )

    print("=" * 60)

    # =====================================================
    # 生成文件
    # =====================================================

    save_m3u8(
        channel_results
    )

    save_txt(
        channel_results
    )

    # =====================================================
    # 检查文件
    # =====================================================

    print()
    print("=" * 60)
    print("文件检查")
    print("=" * 60)

    print(
        "M3U8 是否存在：",
        os.path.exists(M3U_FILE)
    )

    print(
        "TXT 是否存在：",
        os.path.exists(TXT_FILE)
    )

    if os.path.exists(M3U_FILE):

        print(
            "M3U8 大小：",
            os.path.getsize(M3U_FILE),
            "bytes"
        )

    if os.path.exists(TXT_FILE):

        print(
            "TXT 大小：",
            os.path.getsize(TXT_FILE),
            "bytes"
        )

    print()
    print("=" * 60)
    print("搜索完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
