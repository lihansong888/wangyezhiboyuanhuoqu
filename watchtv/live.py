import os
import re
import html
import time
import requests
import urllib3

urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)

# =========================================================
# 配置
# =========================================================

FOODIE_URL = "https://www.foodieguide.com/iptvsearch/"

# 这里可以直接修改测试频道
CHANNELS = [
    "凤凰中文",
    "凤凰资讯",
    "翡翠台",
    "靖天电影",
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

TIMEOUT = 20

# =========================================================
# 输出文件
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
# 判断是否可能是直播地址
# =========================================================

def is_candidate_url(url):

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
        ".flv",
        "/live/",
        "/hls/",
        "/rtp/",
        "/tsfile/",
        "/stream/",
        "/channel/",
        "/playlist/",
    ]

    return any(
        item in lower
        for item in keywords
    )


# =========================================================
# 从网页源码提取直播地址
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

    # -----------------------------------------------------
    # 普通 HTTP / HTTPS URL
    # -----------------------------------------------------

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

        if is_candidate_url(url):

            results.append(url)

    # -----------------------------------------------------
    # 引号中的 URL
    # -----------------------------------------------------

    pattern2 = re.compile(
        r'["\'](https?://[^"\']+)["\']',
        re.IGNORECASE
    )

    for match in pattern2.findall(text):

        url = clean_url(match)

        if is_candidate_url(url):

            results.append(url)

    return results


# =========================================================
# URL 去重
# =========================================================

def unique_urls(urls):

    result = []
    seen = set()

    for url in urls:

        url = clean_url(url)

        if not url:
            continue

        key = url.lower()

        if key in seen:
            continue

        seen.add(key)

        result.append(url)

    return result


# =========================================================
# 全局去重
# =========================================================

def deduplicate(channel_results):

    seen = set()

    result = []

    for channel, urls in channel_results:

        new_urls = []

        for url in urls:

            url = clean_url(url)

            if not url:
                continue

            key = url.lower()

            if key in seen:
                continue

            seen.add(key)

            new_urls.append(url)

        result.append(
            (
                channel,
                new_urls
            )
        )

    return result


# =========================================================
# FoodieGuide 搜索
# =========================================================

def search_foodieguide(
    session,
    channel
):

    print()
    print("=" * 60)
    print(
        "FoodieGuide：",
        channel
    )
    print("=" * 60)

    urls = []

    # =====================================================
    # 入口 1
    # ?chname=频道
    # =====================================================

    try:

        response = session.get(
            FOODIE_URL,
            params={
                "chname": channel
            },
            headers=HEADERS,
            timeout=TIMEOUT,
            verify=False,
            allow_redirects=True
        )

        print(
            "入口1 HTTP：",
            response.status_code
        )

        print(
            "入口1 最终地址：",
            response.url
        )

        print(
            "入口1 页面长度：",
            len(response.text)
        )

        if response.status_code == 200:

            found = extract_urls(
                response.text
            )

            print(
                "入口1 找到：",
                len(found),
                "条"
            )

            urls.extend(found)

    except Exception as e:

        print(
            "入口1失败：",
            e
        )

    # =====================================================
    # 入口 2
    # ?page=1&chname=频道&l=0
    # =====================================================

    try:

        response = session.get(
            FOODIE_URL,
            params={
                "page": "1",
                "chname": channel,
                "l": "0"
            },
            headers=HEADERS,
            timeout=TIMEOUT,
            verify=False,
            allow_redirects=True
        )

        print(
            "入口2 HTTP：",
            response.status_code
        )

        print(
            "入口2 最终地址：",
            response.url
        )

        print(
            "入口2 页面长度：",
            len(response.text)
        )

        if response.status_code == 200:

            found = extract_urls(
                response.text
            )

            print(
                "入口2 找到：",
                len(found),
                "条"
            )

            urls.extend(found)

    except Exception as e:

        print(
            "入口2失败：",
            e
        )

    # =====================================================
    # 入口 3
    # POST seerch=频道
    # =====================================================

    try:

        response = session.post(
            FOODIE_URL,
            data={
                "seerch": channel
            },
            headers=HEADERS,
            timeout=TIMEOUT,
            verify=False,
            allow_redirects=True
        )

        print(
            "POST HTTP：",
            response.status_code
        )

        print(
            "POST 最终地址：",
            response.url
        )

        print(
            "POST 页面长度：",
            len(response.text)
        )

        if response.status_code == 200:

            found = extract_urls(
                response.text
            )

            print(
                "POST 找到：",
                len(found),
                "条"
            )

            urls.extend(found)

    except Exception as e:

        print(
            "POST失败：",
            e
        )

    # =====================================================
    # 当前频道去重
    # =====================================================

    urls = unique_urls(urls)

    print()
    print(
        channel,
        "最终候选源：",
        len(urls)
    )

    for index, url in enumerate(
        urls,
        1
    ):

        print(
            f"{index}. {url}"
        )

    return urls


# =========================================================
# 生成 M3U8
# =========================================================

def save_m3u8(
    channel_results
):

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
                    'group-title="直播",'
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
# 格式：
#
# 央视,#genre#
# CCTV1,http://xxx
# CCTV1,http://xxx
#
# 现在测试其他频道也保持相同格式
# =========================================================

def save_txt(
    channel_results
):

    with open(
        TXT_FILE,
        "w",
        encoding="utf-8",
        newline="\n"
    ) as file:

        file.write(
            "直播,#genre#\n"
        )

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
        "频道数量：",
        len(CHANNELS)
    )

    print(
        "搜索入口：FoodieGuide"
    )

    print(
        "当前模式：只搜索，不检测播放"
    )

    print(
        "最终源数量：不限制"
    )

    print("=" * 60)

    session = requests.Session()

    session.headers.update(
        HEADERS
    )

    # =====================================================
    # 搜索所有频道
    # =====================================================

    channel_results = []

    for channel in CHANNELS:

        urls = search_foodieguide(
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

    # =====================================================
    # 全局 URL 去重
    # =====================================================

    print()
    print("=" * 60)
    print("全局 URL 去重")
    print("=" * 60)

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

        print(
            f"{channel}: {count} 条"
        )

        total += count

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
    # 文件检查
    # =====================================================

    print()
    print("=" * 60)
    print("文件检查")
    print("=" * 60)

    print(
        "M3U8 存在：",
        os.path.exists(M3U_FILE)
    )

    print(
        "TXT 存在：",
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


# =========================================================
# 启动
# =========================================================

if __name__ == "__main__":
    main()
