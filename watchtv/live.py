import requests
import re
import urllib3
from urllib.parse import quote

urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)

# =========================================================
# 配置
# =========================================================

KEYWORD = "凤凰中文"

# 同一个频道使用多个关键词搜索
SEARCH_KEYWORDS = [
    "凤凰中文",
    "凤凰卫视中文",
    "凤凰卫视",
    "Phoenix Chinese",
    "Phoenix TV"
]

BASE_URL = "https://www.foodieguide.com/iptvsearch/"

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
    "Referer": "https://www.foodieguide.com/",
}

TIMEOUT = 30


# =========================================================
# 判断是否像直播源
# =========================================================

def is_stream_url(url):

    if not url:
        return False

    lower = url.lower()

    # 常见协议
    if lower.startswith("http://"):
        return True

    if lower.startswith("https://"):
        return True

    if lower.startswith("rtp://"):
        return True

    if lower.startswith("udp://"):
        return True

    if lower.startswith("rtsp://"):
        return True

    if lower.startswith("igmp://"):
        return True

    # 常见直播格式
    stream_extensions = [
        ".m3u8",
        ".m3u",
        ".ts",
        ".flv",
        ".mp4",
        ".mpd",
        ".aac"
    ]

    if any(
        ext in lower
        for ext in stream_extensions
    ):
        return True

    # 常见 IPTV 路径
    stream_paths = [
        "/live/",
        "/stream/",
        "/channel/",
        "/playlist/",
        "/play/",
        "/rtp/",
        "/udp/",
        "/hls/",
        "/flv/",
        "/ts/",
        "/video/",
        "/tv/",
        "/iptv/",
        "/liveplay/",
        "/live_stream/",
        "/livestream/",
        "/media/",
        "/p2p/"
    ]

    if any(
        path in lower
        for path in stream_paths
    ):
        return True

    # 组播地址
    multicast = re.search(
        r'(?<![\d.])'
        r'(22[4-9]|23[0-9])'
        r'(?:\.\d{1,3}){3}'
        r'(?:[:]\d{1,6})?',
        url
    )

    if multicast:
        return True

    return False


# =========================================================
# 清理 URL
# =========================================================

def clean_url(url):

    if not url:
        return ""

    url = url.strip()

    url = url.replace("\\/", "/")
    url = url.replace("\\:", ":")
    url = url.replace("\\u002F", "/")
    url = url.replace("\\x2F", "/")
    url = url.replace("\\u003A", ":")
    url = url.replace("\\x3A", ":")
    url = url.replace("&amp;", "&")

    url = url.rstrip(
        ".,;，。；）)]}>\"'"
    )

    return url


# =========================================================
# 提取直播源
# =========================================================

def extract_urls(html):

    if not html:
        return []

    html = html.replace("\\/", "/")
    html = html.replace("\\:", ":")
    html = html.replace("\\u002F", "/")
    html = html.replace("\\x2F", "/")
    html = html.replace("\\u003A", ":")
    html = html.replace("\\x3A", ":")
    html = html.replace("&amp;", "&")

    results = []

    # =====================================================
    # HTTP / HTTPS / RTP / UDP / RTSP / IGMP
    # =====================================================

    urls = re.findall(
        r'(?:https?|rtp|udp|rtsp|igmp)://[^\s"\'<>\\]+',
        html,
        re.IGNORECASE
    )

    for url in urls:

        url = clean_url(url)

        if is_stream_url(url):

            if url not in results:
                results.append(url)

    # =====================================================
    # 转义 URL
    # =====================================================

    escaped_urls = re.findall(
        r'(?:https?|rtp|udp|rtsp|igmp)\\?://[^\s"\'<>]+',
        html,
        re.IGNORECASE
    )

    for url in escaped_urls:

        url = clean_url(url)

        if is_stream_url(url):

            if url not in results:
                results.append(url)

    # =====================================================
    # 组播地址
    # =====================================================

    multicast_urls = re.findall(
        r'(?<![\d.])'
        r'(?:22[4-9]|23[0-9])'
        r'(?:\.\d{1,3}){3}'
        r'(?:[:]\d{1,6})?',
        html
    )

    for multicast in multicast_urls:

        url = "udp://" + multicast

        if url not in results:
            results.append(url)

    # =====================================================
    # 裸 IP:端口
    # =====================================================

    ip_port_pattern = re.findall(
        r'(?<![\d/])'
        r'(?:\d{1,3}\.){3}\d{1,3}'
        r':\d{2,6}'
        r'(?!\d)',
        html
    )

    stream_ports = {
        "80",
        "81",
        "443",
        "554",
        "8000",
        "8001",
        "8080",
        "8081",
        "8088",
        "8888",
        "9000",
        "9090",
        "9981",
        "9982"
    }

    for ip_port in ip_port_pattern:

        port = ip_port.rsplit(
            ":",
            1
        )[1]

        if port not in stream_ports:
            continue

        url = "http://" + ip_port

        if url not in results:
            results.append(url)

    # =====================================================
    # 最终去重
    # =====================================================

    unique = []

    seen = set()

    for url in results:

        url = clean_url(url)

        if not url:
            continue

        if url in seen:
            continue

        seen.add(url)

        unique.append(url)

    return unique


# =========================================================
# 单个关键词搜索
# =========================================================

def search_keyword(session, keyword):

    streams = []

    print()
    print("-" * 60)
    print("搜索关键词：", keyword)
    print("-" * 60)

    # =====================================================
    # 第一入口
    # =====================================================

    params = {
        "chname": keyword
    }

    try:

        response = session.get(
            BASE_URL,
            params=params,
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
            "网页长度：",
            len(response.text)
        )

        if response.status_code == 200:

            found = extract_urls(
                response.text
            )

            print(
                "入口1找到：",
                len(found)
            )

            streams.extend(found)

    except Exception as e:

        print(
            "入口1失败：",
            e
        )

    # =====================================================
    # 第二入口
    # =====================================================

    params = {
        "page": "1",
        "chname": keyword,
        "l": "0"
    }

    try:

        response = session.get(
            BASE_URL,
            params=params,
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
            "网页长度：",
            len(response.text)
        )

        if response.status_code == 200:

            found = extract_urls(
                response.text
            )

            print(
                "入口2找到：",
                len(found)
            )

            streams.extend(found)

    except Exception as e:

        print(
            "入口2失败：",
            e
        )

    return streams


# =========================================================
# 多关键词搜索
# =========================================================

def search_foodieguide():

    session = requests.Session()

    session.headers.update(
        HEADERS
    )

    print()
    print("=" * 60)
    print("FoodieGuide 多关键词 IPTV 搜索")
    print("=" * 60)

    print(
        "主频道：",
        KEYWORD
    )

    print(
        "搜索关键词数量：",
        len(SEARCH_KEYWORDS)
    )

    all_streams = []

    # =====================================================
    # 逐个关键词搜索
    # =====================================================

    for keyword in SEARCH_KEYWORDS:

        found = search_keyword(
            session,
            keyword
        )

        all_streams.extend(
            found
        )

    # =====================================================
    # 全部去重
    # =====================================================

    unique = []

    seen = set()

    for stream in all_streams:

        stream = clean_url(stream)

        if not stream:
            continue

        if stream in seen:
            continue

        seen.add(stream)

        unique.append(stream)

    # =====================================================
    # 输出结果
    # =====================================================

    print()
    print("=" * 60)
    print("全部搜索完成")
    print("=" * 60)

    print(
        "搜索关键词：",
        len(SEARCH_KEYWORDS)
    )

    print(
        "原始结果数量：",
        len(all_streams)
    )

    print(
        "去重后直播源：",
        len(unique)
    )

    print("=" * 60)

    for index, stream in enumerate(
        unique,
        1
    ):

        print(
            f"{index}. {stream}"
        )

    return unique


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
        ) as file:

            file.write(
                "#EXTM3U\n"
            )

            for index, stream in enumerate(
                streams,
                1
            ):

                file.write(
                    f"#EXTINF:-1,{KEYWORD} {index}\n"
                )

                file.write(
                    stream + "\n"
                )

        print()
        print(
            "M3U 文件已生成：",
            filename
        )

    except Exception as e:

        print(
            "M3U 保存失败：",
            e
        )


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
        ) as file:

            for stream in streams:

                file.write(
                    stream + "\n"
                )

        print(
            "TXT 文件已生成：",
            filename
        )

    except Exception as e:

        print(
            "TXT 保存失败：",
            e
        )


# =========================================================
# 主程序
# =========================================================

if __name__ == "__main__":

    streams = search_foodieguide()

    if streams:

        save_m3u(
            streams
        )

        save_txt(
            streams
        )

    else:

        print()
        print(
            "没有找到直播源。"
        )

    print()
    print("=" * 60)
    print("搜索完成")
    print("=" * 60)
