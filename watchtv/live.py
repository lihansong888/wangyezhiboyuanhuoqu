import requests
import re
import urllib3
import os
from urllib.parse import quote

urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)

# =========================================================
# 配置
# =========================================================

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
# 关键：文件固定生成到 live.py 所在的 watchtv 文件夹
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
# 提取直播源
# =========================================================

def extract_urls(html):

    if not html:
        return []

    html = html.replace("\\/", "/")
    html = html.replace("\\:", ":")
    html = html.replace("\\u002F", "/")
    html = html.replace("\\x2F", "/")
    html = html.replace("&amp;", "&")

    results = []

    urls = re.findall(
        r'https?://[^\s"\'<>\\]+',
        html,
        re.IGNORECASE
    )

    for url in urls:

        url = url.strip()

        url = url.rstrip(
            ".,;，。；）)]}>"
        )

        lower = url.lower()

        if any(
            key in lower
            for key in [
                ".m3u8",
                ".m3u",
                ".ts",
                ".flv",
                "/rtp/",
                "/live/",
                "/stream/",
                "/channel/",
                "/playlist/"
            ]
        ):

            if url not in results:
                results.append(url)

    return results


# =========================================================
# 搜索单个频道
# =========================================================

def search_channel(session, channel):

    print()
    print("=" * 60)
    print("正在搜索：", channel)
    print("=" * 60)

    params = {
        "chname": channel
    }

    print(
        "请求入口：",
        BASE_URL + "?chname=" + quote(channel)
    )

    try:

        response = session.get(
            BASE_URL,
            params=params,
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

        print(
            "请求失败，跳过：",
            channel
        )

        return []

    print(
        "开始解析：",
        channel
    )

    streams = extract_urls(
        response.text
    )

    # =====================================================
    # 第一入口没有结果时，尝试第二入口
    # =====================================================

    if not streams:

        print(
            "第一入口没有找到直播源。"
        )

        print(
            "尝试第二入口..."
        )

        params = {
            "page": "1",
            "chname": channel,
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
    # 当前频道内部去重
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

    print()
    print(
        channel,
        "找到直播源：",
        len(unique)
    )

    for index, stream in enumerate(
        unique,
        1
    ):

        print(
            f"{index}. {stream}"
        )

    return unique


# =========================================================
# 总去重
#
# 同一个直播地址如果出现在不同频道结果中，
# 只保留第一次出现的地址。
# =========================================================

def deduplicate(channel_results):

    final_results = []

    global_seen = set()

    for channel, streams in channel_results:

        unique_streams = []

        for stream in streams:

            stream = stream.strip()

            if not stream:
                continue

            # 直播源地址完全相同则去重
            if stream in global_seen:
                continue

            global_seen.add(stream)

            unique_streams.append(
                stream
            )

        final_results.append(
            (
                channel,
                unique_streams
            )
        )

    return final_results


# =========================================================
# 生成 M3U8
# =========================================================

def save_m3u8(channel_results):

    try:

        with open(
            M3U_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(
                "#EXTM3U\n"
            )

            for channel, streams in channel_results:

                for stream in streams:

                    file.write(
                        "#EXTINF:-1,"
                        + channel
                        + "\n"
                    )

                    file.write(
                        stream
                        + "\n"
                    )

        print()
        print(
            "M3U8 文件已生成：",
            M3U_FILE
        )

    except Exception as e:

        print(
            "M3U8 文件生成失败：",
            e
        )


# =========================================================
# 生成 TXT
# =========================================================

def save_txt(channel_results):

    try:

        with open(
            TXT_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            for channel, streams in channel_results:

                for stream in streams:

                    file.write(
                        channel
                        + " | "
                        + stream
                        + "\n"
                    )

        print(
            "TXT 文件已生成：",
            TXT_FILE
        )

    except Exception as e:

        print(
            "TXT 文件生成失败：",
            e
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

    print(
        "M3U8 文件：",
        M3U_FILE
    )

    print(
        "TXT 文件：",
        TXT_FILE
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

        streams = search_channel(
            session,
            channel
        )

        channel_results.append(
            (
                channel,
                streams
            )
        )

    # =====================================================
    # 直播源地址去重
    # =====================================================

    channel_results = deduplicate(
        channel_results
    )

    # =====================================================
    # 统计
    # =====================================================

    total = 0

    print()
    print("=" * 60)
    print("搜索结果统计")
    print("=" * 60)

    for channel, streams in channel_results:

        count = len(streams)

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

    if total > 0:

        save_m3u8(
            channel_results
        )

        save_txt(
            channel_results
        )

    else:

        print()
        print(
            "没有找到任何直播源，"
            "不生成空文件。"
        )

    print()
    print("=" * 60)
    print("搜索完成")
    print("=" * 60)


# =========================================================
# 程序入口
# =========================================================

if __name__ == "__main__":
    main()
