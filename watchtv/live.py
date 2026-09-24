import re
import os
import html as html_lib
from urllib.parse import quote

import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =========================================================
# 基本配置
# =========================================================

KEYWORD = os.environ.get("IPTV_KEYWORD", "CCTV1").strip()

TONKIANG_HOME = "https://tonkiang.us/"
TONKIANG_SEARCH = "https://tonkiang.us/?"

FOODIEGUIDE_URL = (
    "https://www.foodieguide.com/iptvsearch/?iptv="
    + quote(KEYWORD)
)

TIMEOUT = 25

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Referer": TONKIANG_HOME,
    "Upgrade-Insecure-Requests": "1",
}

try:
    import cloudscraper
except ImportError:
    cloudscraper = None


# =========================================================
# 创建 HTTP Session
# =========================================================

def make_session():

    if cloudscraper is not None:

        try:

            session = cloudscraper.create_scraper(
                browser={
                    "browser": "chrome",
                    "platform": "windows",
                    "mobile": False,
                }
            )

            session.headers.update(HEADERS)

            return session, "cloudscraper"

        except Exception as e:

            print(
                "cloudscraper 初始化失败，改用 requests：",
                e
            )

    session = requests.Session()

    session.headers.update(HEADERS)

    return session, "requests"


# =========================================================
# 清理 URL
# =========================================================

def clean_url(url):

    if not url:
        return ""

    url = html_lib.unescape(str(url))

    # 处理网页源码中的转义
    url = url.replace("\\/", "/")
    url = url.replace("\\:", ":")
    url = url.replace("\\u002F", "/")
    url = url.replace("\\x2F", "/")

    url = url.replace("&amp;", "&")

    url = url.strip().strip("\"'<>[]()")

    url = url.rstrip(
        ".,;，。；）)】]}>"
    )

    return url


# =========================================================
# 判断是否为直播地址
# =========================================================

def is_stream_url(url):

    if not url:
        return False

    url = clean_url(url)

    if not re.match(
        r"^(https?|rtsp|rtmp|udp)://",
        url,
        re.I
    ):
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
        "/live",
        "/hls/",
        "/playlist",
        "/stream",
        "/play",
        "/channel/",
        "?streamid=",
        "&streamid=",
        "livekey=",
    ]

    return any(
        x in lower
        for x in keywords
    )


# =========================================================
# 从文本提取 URL
# =========================================================

def extract_stream_urls(text):

    if not text:
        return []

    text = html_lib.unescape(
        str(text)
    )

    text = text.replace(
        "\\/",
        "/"
    )

    text = text.replace(
        "\\:",
        ":"
    )

    text = text.replace(
        "\\u002F",
        "/"
    )

    text = text.replace(
        "\\x2F",
        "/"
    )

    pattern = re.compile(
        r"""(?:(?:https?|rtsp|rtmp)://[^\s<>"'`\\]+)""",
        re.I
    )

    results = []

    for match in pattern.findall(text):

        url = clean_url(match)

        if is_stream_url(url):

            results.append(url)

    return results


# =========================================================
# 从 onclick 提取 URL
# =========================================================

def extract_urls_from_onclick(value):

    if not value:
        return []

    value = html_lib.unescape(
        str(value)
    )

    value = value.replace(
        "\\/",
        "/"
    )

    value = value.replace(
        "\\:",
        ":"
    )

    results = []

    patterns = [

        r"""['"]((?:https?|rtsp|rtmp)://[^'"]+)['"]""",

        r"""['"]((?:https?|rtsp|rtmp):\\/\\/[^'"]+)['"]""",

    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
            value,
            re.I
        )

        for item in matches:

            item = clean_url(item)

            if is_stream_url(item):

                results.append(item)

    # 没有引号包裹的情况
    results.extend(
        extract_stream_urls(value)
    )

    return results


# =========================================================
# HTML 解析
# =========================================================

def parse_streams(page_html):

    if not page_html:
        return []

    results = []

    decoded_html = html_lib.unescape(
        page_html
    )

    decoded_html = decoded_html.replace(
        "\\/",
        "/"
    )

    decoded_html = decoded_html.replace(
        "\\:",
        ":"
    )

    soup = BeautifulSoup(
        decoded_html,
        "html.parser"
    )

    # =====================================================
    # 1. Tonkiang 结果区域
    #
    # resultplus
    # gapeo
    # gfiry
    # vnliuj
    # =====================================================

    for tag in soup.find_all(True):

        class_value = tag.get(
            "class"
        )

        if class_value:

            classes = (
                class_value
                if isinstance(
                    class_value,
                    list
                )
                else str(
                    class_value
                ).split()
            )

            # 直播地址所在的 vnliuj
            if "vnliuj" in classes:

                results.extend(
                    extract_stream_urls(
                        tag.get_text(
                            " ",
                            strip=True
                        )
                    )
                )

            # 搜索结果区域
            if any(
                x in classes
                for x in [
                    "resultplus",
                    "gapeo",
                    "gfiry"
                ]
            ):

                results.extend(
                    extract_stream_urls(
                        str(tag)
                    )
                )

        # =================================================
        # 2. onclick
        # =================================================

        onclick = tag.get(
            "onclick"
        )

        if onclick:

            results.extend(
                extract_urls_from_onclick(
                    onclick
                )
            )

        # =================================================
        # 3. data-* 属性
        # =================================================

        for key, value in tag.attrs.items():

            if not str(
                key
            ).lower().startswith(
                "data-"
            ):
                continue

            if isinstance(
                value,
                str
            ):

                results.extend(
                    extract_stream_urls(
                        value
                    )
                )

    # =====================================================
    # 4. a href
    # =====================================================

    for a in soup.find_all("a"):

        href = a.get(
            "href"
        )

        if not href:
            continue

        href = clean_url(
            href
        )

        if is_stream_url(
            href
        ):

            results.append(
                href
            )

    # =====================================================
    # 5. 全页面扫描
    # =====================================================

    results.extend(
        extract_stream_urls(
            decoded_html
        )
    )

    # =====================================================
    # 6. 重点扫描搜索结果区域
    # =====================================================

    for block in soup.select(
        ".resultplus, "
        ".channel, "
        ".gapeo, "
        ".gfiry, "
        ".vnliuj"
    ):

        results.extend(
            extract_stream_urls(
                str(block)
            )
        )

    # =====================================================
    # 去重
    # =====================================================

    final_results = []

    seen = set()

    for url in results:

        url = clean_url(
            url
        )

        if not url:
            continue

        if url in seen:
            continue

        seen.add(url)

        final_results.append(
            url
        )

    return final_results


# =========================================================
# 判断 Cloudflare 验证页
# =========================================================

def is_challenge_page(text):

    if not text:
        return True

    lower = text.lower()

    challenge_words = [

        "just a moment",

        "cf-chl-",

        "challenge-platform",

        "challenges.cloudflare.com",

        "verify you are human",

        "checking your browser",

        "attention required",

        "enable javascript and cookies",

    ]

    return any(
        word in lower
        for word in challenge_words
    )


# =========================================================
# Tonkiang 搜索
# =========================================================

def fetch_tonkiang(session):

    print()
    print(
        "【1】尝试 Tonkiang 真实搜索入口"
    )

    print(
        "首页：",
        TONKIANG_HOME
    )

    # =====================================================
    # 第一步：访问首页建立 Cookie
    # =====================================================

    try:

        home = session.get(
            TONKIANG_HOME,
            headers=HEADERS,
            timeout=TIMEOUT,
            verify=True,
            allow_redirects=True
        )

        print(
            "首页 HTTP 状态：",
            home.status_code
        )

        print(
            "首页最终地址：",
            home.url
        )

        print(
            "首页长度：",
            len(home.text)
        )

        if (
            home.status_code == 200
            and not is_challenge_page(
                home.text
            )
        ):

            print(
                "Tonkiang 首页获取成功"
            )

        else:

            print(
                "Tonkiang 首页可能被验证/拦截"
            )

    except requests.RequestException as e:

        print(
            "Tonkiang 首页请求失败：",
            e
        )

    # =====================================================
    # 第二步：POST 搜索
    #
    # 网页真实表单：
    #
    # <form method="post" action="/?">
    # <input name="seerch">
    # =====================================================

    payload = {
        "seerch": KEYWORD
    }

    post_headers = dict(
        HEADERS
    )

    post_headers[
        "Origin"
    ] = "https://tonkiang.us"

    post_headers[
        "Referer"
    ] = TONKIANG_HOME

    post_headers[
        "Content-Type"
    ] = (
        "application/x-www-form-urlencoded"
    )

    print()
    print(
        "搜索方式：POST"
    )

    print(
        "搜索字段：seerch"
    )

    print(
        "搜索关键词：",
        KEYWORD
    )

    print(
        "请求地址：",
        TONKIANG_SEARCH
    )

    try:

        response = session.post(
            TONKIANG_SEARCH,
            data=payload,
            headers=post_headers,
            timeout=TIMEOUT,
            verify=True,
            allow_redirects=True
        )

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
                "Tonkiang POST HTTP 状态异常"
            )

            return None

        if is_challenge_page(
            response.text
        ):

            print(
                "Tonkiang 返回 Cloudflare/验证页面"
            )

            return None

        print(
            "Tonkiang 搜索页面获取成功"
        )

        return response.text

    except requests.RequestException as e:

        print(
            "Tonkiang POST 请求失败："
        )

        print(e)

        return None


# =========================================================
# FoodieGuide
# =========================================================

def fetch_foodieguide(session):

    print()
    print(
        "【2】切换 FoodieGuide 备用入口"
    )

    print(
        "请求地址：",
        FOODIEGUIDE_URL
    )

    try:

        response = session.get(
            FOODIEGUIDE_URL,
            headers=HEADERS,
            timeout=TIMEOUT,
            verify=False,
            allow_redirects=True
        )

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
                "FoodieGuide HTTP 状态异常"
            )

            return None

        if is_challenge_page(
            response.text
        ):

            print(
                "FoodieGuide 返回验证页面"
            )

            return None

        print(
            "FoodieGuide 页面获取成功"
        )

        return response.text

    except requests.RequestException as e:

        print(
            "FoodieGuide 请求失败：",
            e
        )

        return None


# =========================================================
# 搜索
# =========================================================

def search():

    print()
    print(
        "=" * 60
    )

    print(
        "IPTV 直播源搜索"
    )

    print(
        "=" * 60
    )

    print(
        "搜索关键词：",
        KEYWORD
    )

    print(
        "=" * 60
    )

    session, session_type = make_session()

    print(
        "HTTP 会话：",
        session_type
    )

    html = None

    source = ""

    # =====================================================
    # 第一入口：Tonkiang
    # =====================================================

    html = fetch_tonkiang(
        session
    )

    if html is not None:

        source = "tonkiang"

    # =====================================================
    # 第二入口：FoodieGuide
    # =====================================================

    if html is None:

        html = fetch_foodieguide(
            session
        )

        if html is not None:

            source = "foodieguide"

    # =====================================================
    # 两个入口都失败
    # =====================================================

    if html is None:

        print()
        print(
            "=" * 60
        )

        print(
            "搜索失败"
        )

        print(
            "=" * 60
        )

        print(
            "Tonkiang 和 FoodieGuide "
            "都无法获取有效搜索页面。"
        )

        return []

    # =====================================================
    # 开始解析
    # =====================================================

    print()

    print(
        "使用入口：",
        source
    )

    print(
        "开始解析直播源..."
    )

    print()

    streams = parse_streams(
        html
    )

    print(
        "找到直播源：",
        len(streams)
    )

    # =====================================================
    # 输出
    # =====================================================

    if streams:

        print()

        for i, url in enumerate(
            streams,
            1
        ):

            print(
                f"{i}. {url}"
            )

    else:

        print()

        print(
            "页面获取成功，但没有解析到直播源。"
        )

        print()

        print(
            "开始调试页面中的直播地址..."
        )

        debug_matches = (
            extract_stream_urls(
                html
            )
        )

        if debug_matches:

            debug_matches = list(
                dict.fromkeys(
                    debug_matches
                )
            )

            print(
                "调试扫描发现：",
                len(debug_matches),
                "个候选地址"
            )

            for item in debug_matches[:50]:

                print(
                    item
                )

        else:

            print(
                "页面中没有直接发现直播 URL。"
            )

            lower = html.lower()

            keywords = [

                "m3u8",

                "m3u",

                "resultplus",

                "channel1",

                "seerch",

                "iptv",

                "vnliuj",

                "xgfir",

            ]

            print()

            print(
                "页面关键字检查："
            )

            for keyword in keywords:

                print(
                    f"  {keyword}:",
                    "YES"
                    if keyword in lower
                    else "NO"
                )

    return streams


# =========================================================
# 保存 TXT
# =========================================================

def save_txt(streams):

    filename = (
        "live_results.txt"
    )

    try:

        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as f:

            for url in streams:

                f.write(
                    url + "\n"
                )

        print()

        print(
            "TXT 已保存：",
            filename
        )

    except Exception as e:

        print(
            "保存 TXT 失败：",
            e
        )


# =========================================================
# 保存 M3U
# =========================================================

def save_m3u(streams):

    filename = (
        "live_results.m3u"
    )

    try:

        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(
                "#EXTM3U\n"
            )

            for index, url in enumerate(
                streams,
                1
            ):

                f.write(
                    f"#EXTINF:-1,"
                    f"{KEYWORD} {index}\n"
                )

                f.write(
                    url + "\n"
                )

        print(
            "M3U 已保存：",
            filename
        )

    except Exception as e:

        print(
            "保存 M3U 失败：",
            e
        )


# =========================================================
# 主程序
# =========================================================

if __name__ == "__main__":

    streams = search()

    print()

    print(
        "=" * 60
    )

    print(
        "搜索结束"
    )

    print(
        "直播源数量：",
        len(streams)
    )

    print(
        "=" * 60
    )

    if streams:

        save_txt(
            streams
        )

        save_m3u(
            streams
        )

    print()
