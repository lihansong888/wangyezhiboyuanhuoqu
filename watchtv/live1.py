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

FOODIE_URL = "https://www.foodieguide.com/iptvsearch/"

TONKIANG_BASE = "https://tonkiang.us/"

# =========================================================
# 当前测试频道
#
# 确认这几个频道正常以后，
# 再恢复 CCTV 全部频道即可。
# =========================================================

CHANNELS = [
    "凤凰中文",
    "凤凰资讯",
    "翡翠台",
    "靖天电影",
]

# =========================================================
# 请求头
# =========================================================

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
# 频道搜索关键词
#
# 一个频道可以搜索多个不同写法
# =========================================================

CHANNEL_ALIASES = {

    "凤凰中文": [
        "凤凰中文",
        "凤凰卫视中文台",
        "凤凰卫视",
        "凤凰中文台",
    ],

    "凤凰资讯": [
        "凤凰资讯",
        "凤凰资讯台",
        "凤凰卫视资讯台",
    ],

    "翡翠台": [
        "翡翠台",
        "TVB翡翠台",
        "TVB",
        "翡翠",
    ],

    "靖天电影": [
        "靖天电影",
        "靖天影院",
        "靖天影城",
    ],

    
}


# =========================================================
# URL 清理
# =========================================================

def clean_url(url):

    if not url:
        return ""

    url = html.unescape(url)

    url = url.replace("\\/", "/")
    url = url.replace("\\u002F", "/")
    url = url.replace("\\x2F", "/")

    url = url.strip()

    url = url.strip(
        "\"'<>"
    )

    url = url.rstrip(
        ".,;，。；）)]}>"
    )

    return url


# =========================================================
# 判断 URL 是否像直播源
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
        ".mp4",
        "/live/",
        "/hls/",
        "/rtp/",
        "/rtmp/",
        "/tsfile/",
        "/stream/",
        "/channel/",
        "/playlist/",
        "/play/",
        "/video/",
    ]

    return any(
        x in lower
        for x in keywords
    )


# =========================================================
# 提取网页中的直播地址
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
    # HTTP / HTTPS
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

    for item in pattern.findall(text):

        url = clean_url(item)

        if is_candidate_url(url):

            results.append(url)

    # -----------------------------------------------------
    # 引号 URL
    # -----------------------------------------------------

    pattern2 = re.compile(
        r'["\'](https?://[^"\']+)["\']',
        re.IGNORECASE
    )

    for item in pattern2.findall(text):

        url = clean_url(item)

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
# FoodieGuide 单个关键词搜索
# =========================================================

def foodie_search_keyword(
    session,
    keyword
):

    results = []

    print()
    print(
        "FoodieGuide 搜索：",
        keyword
    )

    # =====================================================
    # 方式 1
    # ?chname=
    # =====================================================

    try:

        response = session.get(
            FOODIE_URL,
            params={
                "chname": keyword
            },
            headers=HEADERS,
            timeout=TIMEOUT,
            verify=False
        )

        print(
            "  chname HTTP：",
            response.status_code,
            "长度：",
            len(response.text)
        )

        if response.status_code == 200:

            results.extend(
                extract_urls(
                    response.text
                )
            )

    except Exception as e:

        print(
            "  chname 失败：",
            e
        )

    # =====================================================
    # 方式 2
    # ?iptv=
    # =====================================================

    try:

        response = session.get(
            FOODIE_URL,
            params={
                "iptv": keyword
            },
            headers=HEADERS,
            timeout=TIMEOUT,
            verify=False
        )

        print(
            "  iptv HTTP：",
            response.status_code,
            "长度：",
            len(response.text)
        )

        if response.status_code == 200:

            results.extend(
                extract_urls(
                    response.text
                )
            )

    except Exception as e:

        print(
            "  iptv 失败：",
            e
        )

    # =====================================================
    # 方式 3
    # page + chname
    # =====================================================

    try:

        response = session.get(
            FOODIE_URL,
            params={
                "page": "1",
                "chname": keyword,
                "l": "0"
            },
            headers=HEADERS,
            timeout=TIMEOUT,
            verify=False
        )

        print(
            "  page HTTP：",
            response.status_code,
            "长度：",
            len(response.text)
        )

        if response.status_code == 200:

            results.extend(
                extract_urls(
                    response.text
                )
            )

    except Exception as e:

        print(
            "  page 失败：",
            e
        )

    # =====================================================
    # 方式 4
    # POST seerch
    # =====================================================

    try:

        response = session.post(
            FOODIE_URL,
            data={
                "seerch": keyword
            },
            headers=HEADERS,
            timeout=TIMEOUT,
            verify=False
        )

        print(
            "  POST HTTP：",
            response.status_code,
            "长度：",
            len(response.text)
        )

        if response.status_code == 200:

            results.extend(
                extract_urls(
                    response.text
                )
            )

    except Exception as e:

        print(
            "  POST 失败：",
            e
        )

    return unique_urls(
        results
    )


# =========================================================
# Tonkiang 单个入口
# =========================================================

def tonkiang_search_endpoint(
    session,
    endpoint,
    keyword
):

    results = []

    url = (
        TONKIANG_BASE
        + endpoint
    )

    print(
        "  Tonkiang：",
        endpoint
    )

    # -----------------------------------------------------
    # GET ?iptv=关键词
    # -----------------------------------------------------

    try:

        response = session.get(
            url,
            params={
                "iptv": keyword
            },
            headers=HEADERS,
            timeout=TIMEOUT,
            verify=False,
            allow_redirects=True
        )

        print(
            "    GET：",
            response.status_code,
            "长度：",
            len(response.text)
        )

        if response.status_code == 200:

            results.extend(
                extract_urls(
                    response.text
                )
            )

    except Exception as e:

        print(
            "    GET失败：",
            e
        )

    # -----------------------------------------------------
    # GET ?chname=关键词
    # -----------------------------------------------------

    try:

        response = session.get(
            url,
            params={
                "chname": keyword
            },
            headers=HEADERS,
            timeout=TIMEOUT,
            verify=False,
            allow_redirects=True
        )

        print(
            "    CHNAME：",
            response.status_code,
            "长度：",
            len(response.text)
        )

        if response.status_code == 200:

            results.extend(
                extract_urls(
                    response.text
                )
            )

    except Exception as e:

        print(
            "    CHNAME失败：",
            e
        )

    # -----------------------------------------------------
    # POST seerch
    # -----------------------------------------------------

    try:

        response = session.post(
            url,
            data={
                "seerch": keyword
            },
            headers=HEADERS,
            timeout=TIMEOUT,
            verify=False,
            allow_redirects=True
        )

        print(
            "    POST：",
            response.status_code,
            "长度：",
            len(response.text)
        )

        if response.status_code == 200:

            results.extend(
                extract_urls(
                    response.text
                )
            )

    except Exception as e:

        print(
            "    POST失败：",
            e
        )

    return unique_urls(
        results
    )


# =========================================================
# Tonkiang 所有类型
# =========================================================

def tonkiang_search(
    session,
    keyword
):

    results = []

    print()
    print(
        "Tonkiang 搜索：",
        keyword
    )

    endpoints = [
        "index.php",
        "iptvhotelx.php",
        "iptvmulticast.php",
        "mqlive.php",
        "iptvproxy.php",
    ]

    for endpoint in endpoints:

        found = tonkiang_search_endpoint(
            session,
            endpoint,
            keyword
        )

        if found:

            print(
                "    找到：",
                len(found),
                "条"
            )

            results.extend(found)

        time.sleep(0.3)

    return unique_urls(
        results
    )


# =========================================================
# 搜索一个频道
# =========================================================

def search_channel(
    session,
    channel
):

    print()
    print("=" * 60)
    print(
        "正在搜索频道：",
        channel
    )
    print("=" * 60)

    aliases = CHANNEL_ALIASES.get(
        channel,
        [channel]
    )

    print(
        "搜索关键词：",
        " / ".join(aliases)
    )

    all_urls = []

    for keyword in aliases:

        # -------------------------------------------------
        # FoodieGuide
        # -------------------------------------------------

        foodie_urls = foodie_search_keyword(
            session,
            keyword
        )

        all_urls.extend(
            foodie_urls
        )

        # -------------------------------------------------
        # Tonkiang
        # -------------------------------------------------

        tonkiang_urls = tonkiang_search(
            session,
            keyword
        )

        all_urls.extend(
            tonkiang_urls
        )

        time.sleep(0.5)

    # -----------------------------------------------------
    # 当前频道去重
    # -----------------------------------------------------

    all_urls = unique_urls(
        all_urls
    )

    print()
    print(
        channel,
        "最终候选源：",
        len(all_urls)
    )

    for index, url in enumerate(
        all_urls,
        1
    ):

        print(
            f"{index}. {url}"
        )

    return all_urls


# =========================================================
# 全局 URL 去重
# =========================================================

def deduplicate(
    channel_results
):

    seen = set()

    result = []

    for channel, urls in channel_results:

        new_urls = []

        for url in urls:

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
# 直播,#genre#
# 凤凰中文,http://xxx
# 凤凰资讯,http://xxx
# 翡翠台,http://xxx
#
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
        "搜索入口："
    )

    print(
        "1. FoodieGuide"
    )

    print(
        "2. Tonkiang 普通"
    )

    print(
        "3. Tonkiang 酒店源"
    )

    print(
        "4. Tonkiang 组播源"
    )

    print(
        "5. Tonkiang 秒开源"
    )

    print(
        "6. Tonkiang 代理源"
    )

    print(
        "不进行播放检测"
    )

    print(
        "不限制最终源数量"
    )

    print("=" * 60)

    session = requests.Session()

    session.headers.update(
        HEADERS
    )

    channel_results = []

    # =====================================================
    # 搜索所有频道
    # =====================================================

    for channel in CHANNELS:

        try:

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

        except Exception as e:

            print()
            print(
                "频道搜索异常：",
                channel
            )

            print(
                e
            )

            channel_results.append(
                (
                    channel,
                    []
                )
            )

        time.sleep(1)

    # =====================================================
    # 全局去重
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
    print("最终搜索结果")
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
    # 检查文件
    # =====================================================

    print()
    print("=" * 60)
    print("文件检查")
    print("=" * 60)

    print(
        "M3U8：",
        M3U_FILE
    )

    print(
        "TXT：",
        TXT_FILE
    )

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
