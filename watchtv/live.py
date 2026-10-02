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

    url = url.strip()
    lower = url.lower()

    # -----------------------------------------------------
    # 常见直播协议
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # 常见直播文件
    # -----------------------------------------------------

    stream_extensions = [
        ".m3u8",
        ".m3u",
        ".ts",
        ".flv",
        ".mp4",
        ".mpd",
        ".aac",
        ".mkv"
    ]

    if any(
        ext in lower
        for ext in stream_extensions
    ):
        return True

    # -----------------------------------------------------
    # 常见 IPTV 路径
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # 组播地址
    # 224.0.0.0 - 239.255.255.255
    # -----------------------------------------------------

    multicast_pattern = re.search(
        r'(?<![\d.])'
        r'(22[4-9]|23[0-9])'
        r'(?:\.\d{1,3}){3}'
        r'(?:[:]\d{1,6})?',
        url
    )

    if multicast_pattern:
        return True

    return False


# =========================================================
# 清理 URL
# =========================================================

def clean_url(url):

    if not url:
        return ""

    url = url.strip()

    # 网页转义
    url = url.replace("\\/", "/")
    url = url.replace("\\:", ":")
    url = url.replace("\\u002F", "/")
    url = url.replace("\\x2F", "/")
    url = url.replace("&amp;", "&")
    url = url.replace("\\u003A", ":")
    url = url.replace("\\x3A", ":")

    # 去掉 JSON / HTML 常见尾巴
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

    # -----------------------------------------------------
    # 网页转义
    # -----------------------------------------------------

    html = html.replace("\\/", "/")
    html = html.replace("\\:", ":")
    html = html.replace("\\u002F", "/")
    html = html.replace("\\x2F", "/")
    html = html.replace("\\u003A", ":")
    html = html.replace("\\x3A", ":")
    html = html.replace("&amp;", "&")

    results = []

    # =====================================================
    # 第一类
    # 完整 HTTP / HTTPS / RTP / UDP / RTSP / IGMP
    # =====================================================

    protocol_urls = re.findall(
        r'(?:https?|rtp|udp|rtsp|igmp)://[^\s"\'<>\\]+',
        html,
        re.IGNORECASE
    )

    for url in protocol_urls:

        url = clean_url(url)

        if not url:
            continue

        if is_stream_url(url):

            if url not in results:
                results.append(url)

    # =====================================================
    # 第二类
    # HTML / JSON 中被转义的协议
    # =====================================================

    escaped_urls = re.findall(
        r'(?:https?|rtp|udp|rtsp|igmp)\\?://[^\s"\'<>]+',
        html,
        re.IGNORECASE
    )

    for url in escaped_urls:

        url = clean_url(url)

        if not url:
            continue

        if is_stream_url(url):

            if url not in results:
                results.append(url)

    # =====================================================
    # 第三类
    # 单独提取组播地址
    # =====================================================

    multicast_urls = re.findall(
        r'(?<![\d.])'
        r'(?:22[4-9]|23[0-9])'
        r'(?:\.\d{1,3}){3}'
        r'(?:[:]\d{1,6})?',
        html
    )

    for multicast in multicast_urls:

        # 如果网页里只是普通 IP，则先转换成 UDP
        # 方便后续统一处理
        if ":" in multicast:

            url = "udp://" + multicast

        else:

            url = "udp://" + multicast

        if url not in results:
            results.append(url)

    # =====================================================
    # 第四类
    # 裸 IP + 端口
    #
    # 例如：
    # 1.2.3.4:8080
    # 5.6.7.8:8000
    #
    # 注意：
    # 这里只收常见 IPTV 端口，避免误抓网页中的普通 IP。
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

        # 裸地址统一转换成 HTTP 候选
        url = "http://" + ip_port

        if url not in results:
            results.append(url)

    # =====================================================
    # 第五类
    # 清理并再次去重
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
# 搜索 FoodieGuide
# =========================================================

def search_foodieguide(keyword):

    session = requests.Session()

    session.headers.update(
        HEADERS
    )

    print()
    print("=" * 60)
    print("FoodieGuide IPTV 搜索")
    print("=" * 60)

    print(
        "搜索关键词：",
        keyword
    )

    # =====================================================
    # 方式一
    # =====================================================

    url = BASE_URL

    params = {
        "chname": keyword
    }

    print()
    print(
        "请求入口：",
        BASE_URL + "?chname=" + quote(keyword)
    )

    try:

        response = session.get(
            url,
            params=params,
            headers=HEADERS,
            timeout=TIMEOUT,
            verify=False,
            allow_redirects=True
        )

    except Exception as e:

        print()
        print(
            "请求失败：",
            e
        )

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

        print(
            "FoodieGuide 请求失败"
        )

        return []

    # =====================================================
    # 解析
    # =====================================================

    print()
    print(
        "开始解析直播源..."
    )

    streams = extract_urls(
        response.text
    )

    # =====================================================
    # 如果第一页没有源
    # =====================================================

    if not streams:

        print(
            "主入口没有直接找到直播源。"
        )

        print(
            "尝试第二入口..."
        )

        params = {
            "page": "1",
            "chname": keyword,
            "l": "0"
        }

        try:

            response = session.get(
                url,
                params=params,
                headers=HEADERS,
                timeout=TIMEOUT,
                verify=False,
                allow_redirects=True
            )

            print(
                "第二入口 HTTP：",
                response.status_code
            )

            print(
                "第二入口最终地址：",
                response.url
            )

            print(
                "第二入口网页长度：",
                len(response.text)
            )

            if response.status_code == 200:

                streams = extract_urls(
                    response.text
                )

        except Exception as e:

            print(
                "第二入口请求失败：",
                e
            )

    # =====================================================
    # 去重
    # =====================================================

    unique = []

    seen = set()

    for stream in streams:

        stream = stream.strip()

        if not stream:
            continue

        if stream in seen:
            continue

        seen.add(stream)

        unique.append(stream)

    # =====================================================
    # 输出
    # =====================================================

    print()
    print("=" * 60)

    print(
        "找到候选直播源：",
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

    streams = search_foodieguide(
        KEYWORD
    )

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
