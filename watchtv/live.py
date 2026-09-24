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

    # 普通 URL
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

    # 引号里的 URL
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
# 单个频道内部去重
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
# 全局直播源去重
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
    print("FoodieGuide：", channel)
    print("=" * 60)

    urls = []

    # -----------------------------------------------------
    # 方式 1
    # ?chname=CCTV1
    # -----------------------------------------------------

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
            "页面长度：",
            len(response.text)
        )

        if response.status_code == 200:

            urls.extend(
                extract_urls(
                    response.text
                )
            )

    except Exception as e:

        print(
            "入口1失败：",
            e
        )

    # -----------------------------------------------------
    # 方式 2
    # ?page=1&chname=CCTV1&l=0
    # -----------------------------------------------------

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
            "页面长度：",
            len(response.text)
        )

        if response.status_code == 200:

            urls.extend(
                extract_urls(
                    response.text
                )
            )

    except Exception as e:

        print(
            "入口2失败：",
            e
        )

    # -----------------------------------------------------
    # 方式 3
    # POST seerch=CCTV1
    # -----------------------------------------------------

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
            "POST 页面长度：",
            len(response.text)
        )

        if response.status_code == 200:

            urls.extend(
                extract_urls(
                    response.text
                )
            )

    except Exception as e:

        print(
            "POST失败：",
            e
        )

    urls = unique_urls(urls)

    print(
        channel,
        "候选源：",
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
# 检测直播源
# =========================================================

def check_stream(
    session,
    url
):

    lower = url.lower()

    # RTP / UDP / 组播
    # GitHub Actions 无法可靠验证
    if (
        "/rtp/" in lower
        or lower.startswith("rtp://")
        or lower.startswith("udp://")
    ):
        return None

    try:

        response = session.get(
            url,
            headers={
                **HEADERS,
                "Range": "bytes=0-8191",
            },
            timeout=8,
            verify=False,
            allow_redirects=True,
            stream=True
        )

        status = response.status_code

        content_type = (
            response.headers
            .get(
                "Content-Type",
                ""
            )
            .lower()
        )

        if status not in (
            200,
            206
        ):

            response.close()
            return False

        # -------------------------------------------------
        # M3U8 检测
        # -------------------------------------------------

        if (
            ".m3u8" in lower
            or "mpegurl" in content_type
            or "application/vnd.apple.mpegurl"
            in content_type
        ):

            try:

                data = response.raw.read(
                    8192
                )

                response.close()

                text = data.decode(
                    "utf-8",
                    errors="ignore"
                )

                if (
                    "#EXTM3U" in text
                    or "#EXTINF" in text
                    or "#EXT-X-" in text
                ):

                    return True

                return False

            except Exception:

                response.close()
                return False

        # -------------------------------------------------
        # 其他 HTTP 直播源
        # -------------------------------------------------

        response.close()

        return True

    except Exception:

        return False


# =========================================================
# 检测所有直播源
# =========================================================

def validate_streams(
    session,
    channel_results
):

    print()
    print("=" * 60)
    print("开始检测直播源")
    print("=" * 60)

    final_results = []

    total = 0
    alive = 0
    unknown = 0

    for channel, urls in channel_results:

        valid_urls = []

        for url in urls:

            total += 1

            result = check_stream(
                session,
                url
            )

            if result is True:

                alive += 1

                valid_urls.append(
                    url
                )

                print(
                    "✓ 有效：",
                    channel,
                    url
                )

            elif result is None:

                unknown += 1

                valid_urls.append(
                    url
                )

                print(
                    "? 无法验证：",
                    channel,
                    url
                )

            else:

                print(
                    "✗ 失效：",
                    channel,
                    url
                )

        final_results.append(
            (
                channel,
                valid_urls
            )
        )

    print()
    print("=" * 60)
    print("检测统计")
    print("=" * 60)

    print(
        "检测候选源：",
        total
    )

    print(
        "HTTP/HLS 有效：",
        alive
    )

    print(
        "无法验证的 RTP/组播：",
        unknown
    )

    print(
        "最终保留：",
        alive + unknown
    )

    return final_results


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
# 格式：
#
# 央视,#genre#
# CCTV1,http://xxx
# CCTV1,http://xxx
# CCTV2,http://xxx
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
            "央视,#genre#\n"
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
        "搜索频道数量：",
        len(CHANNELS)
    )

    print(
        "搜索引擎：FoodieGuide"
    )

    print(
        "不限制最终直播源数量"
    )

    print("=" * 60)

    session = requests.Session()

    session.headers.update(
        HEADERS
    )

    # =====================================================
    # 第一阶段：搜索
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

        # 稍微降低请求频率
        time.sleep(0.5)

    # =====================================================
    # 第二阶段：全局 URL 去重
    # =====================================================

    print()
    print("=" * 60)
    print("全局去重")
    print("=" * 60)

    channel_results = deduplicate(
        channel_results
    )

    candidate_total = sum(
        len(urls)
        for _, urls
        in channel_results
    )

    print(
        "去重后候选源：",
        candidate_total
    )

    # =====================================================
    # 第三阶段：检测
    # =====================================================

    channel_results = validate_streams(
        session,
        channel_results
    )

    # =====================================================
    # 最终统计
    # =====================================================

    print()
    print("=" * 60)
    print("最终结果")
    print("=" * 60)

    total = 0

    for channel, urls in channel_results:

        print(
            f"{channel}: {len(urls)} 条"
        )

        total += len(urls)

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
        "M3U8 路径：",
        M3U_FILE
    )

    print(
        "TXT 路径：",
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
