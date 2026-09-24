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
# 提取直播源
# =========================================================

def extract_urls(html):

    if not html:
        return []

    # 处理网页中的各种转义
    html = html.replace("\\/", "/")
    html = html.replace("\\:", ":")
    html = html.replace("\\u002F", "/")
    html = html.replace("\\x2F", "/")
    html = html.replace("&amp;", "&")

    results = []

    # =====================================================
    # 直接提取 http / https 地址
    # =====================================================

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

        # 直播地址特征
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

def search_channel(
    session,
    channel
):

    print()
    print("=" * 60)
    print(
        "正在搜索：",
        channel
    )
    print("=" * 60)

    # =====================================================
    # 第一入口
    # =====================================================

    params = {
        "chname": channel
    }

    search_url = (
        BASE_URL
        + "?chname="
        + quote(channel)
    )

    print(
        "请求入口：",
        search_url
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
    # 第二入口
    #
    # 如果第一入口没有找到源，
    # 再尝试：
    #
    # page=1&chname=CCTV1&l=0
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

    # =====================================================
    # 显示当前频道结果
    # =====================================================

    for index, stream in enumerate(
        unique,
        1
    ):

        print(
            f"{index}. {stream}"
        )

    return unique


# =========================================================
# 保存总 M3U
# =========================================================

def save_m3u(all_streams):

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

            for channel, streams in all_streams:

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
            "M3U 文件已生成：",
            filename
        )

    except Exception as e:

        print(
            "M3U 保存失败：",
            e
        )


# =========================================================
# 保存总 TXT
# =========================================================

def save_txt(all_streams):

    filename = "live_results.txt"

    try:

        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as file:

            for channel, streams in all_streams:

                for stream in streams:

                    file.write(
                        channel
                        + " | "
                        + stream
                        + "\n"
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
# 总去重
#
# 相同频道 + 相同地址：
# 删除重复
#
# 相同频道 + 不同地址：
# 全部保留
#
# 不同频道 + 相同地址：
# 暂时也保留
#
# =========================================================

def deduplicate(
    channel_results
):

    final_results = []

    seen = set()

    for channel, streams in channel_results:

        unique_streams = []

        for stream in streams:

            key = (
                channel,
                stream
            )

            if key in seen:
                continue

            seen.add(key)

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

    print("=" * 60)

    session = requests.Session()

    session.headers.update(
        HEADERS
    )

    channel_results = []

    # =====================================================
    # 依次搜索所有频道
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
    # 总去重
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
    # 保存
    # =====================================================

    if total > 0:

        save_m3u(
            channel_results
        )

        save_txt(
            channel_results
        )

    else:

        print()
        print(
            "没有找到任何直播源。"
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
