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

KEYWORD = "CCTV1"

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

    # 处理网页中的转义
    html = html.replace("\\/", "/")
    html = html.replace("\\:", ":")
    html = html.replace("\\u002F", "/")
    html = html.replace("\\x2F", "/")
    html = html.replace("&amp;", "&")

    results = []

    # -----------------------------------------------------
    # 第一种：直接寻找完整 URL
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # 第二种：处理网页中可能没有完整协议的情况
    # -----------------------------------------------------

    escaped_urls = re.findall(
        r'https?\\?://[^\s"\'<>]+',
        html,
        re.IGNORECASE
    )

    for url in escaped_urls:

        url = (
            url
            .replace("\\/", "/")
            .replace("\\:", ":")
        )

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
                "/channel/"
            ]
        ):

            if url not in results:
                results.append(url)

    return results


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
    # 已验证可以返回搜索结果
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
    # 再尝试 page=1&chname=CCTV1&l=0
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
        "找到直播源：",
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
