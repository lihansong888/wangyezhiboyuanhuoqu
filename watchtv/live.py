import requests
import re
import urllib3

urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)

KEYWORD = "CCTV1"

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

BASE = "https://www.foodieguide.com/iptvsearch/"


def check_page(name, response):

    print()
    print("=" * 60)
    print(name)
    print("=" * 60)

    print("HTTP：", response.status_code)
    print("最终 URL：", response.url)
    print("长度：", len(response.text))

    text = response.text.lower()

    for word in [
        "cctv1",
        "m3u8",
        "m3u",
        "xgfi",
        "gfirya",
        "resultplus",
        "chname",
        "channel1",
    ]:

        print(
            word + ":",
            "YES" if word in text else "NO"
        )

    return response.text


def request_get(session, params):

    return session.get(
        BASE,
        params=params,
        headers=HEADERS,
        timeout=30,
        verify=False,
        allow_redirects=True
    )


def request_post(session, data):

    return session.post(
        BASE,
        data=data,
        headers=HEADERS,
        timeout=30,
        verify=False,
        allow_redirects=True
    )


def main():

    print("=" * 60)
    print("FoodieGuide 搜索入口测试")
    print("=" * 60)

    print("关键词：", KEYWORD)

    session = requests.Session()

    session.headers.update(
        HEADERS
    )

    pages = []

    # =====================================================
    # 方式 1
    # =====================================================

    try:

        r = request_get(
            session,
            {
                "iptv": KEYWORD
            }
        )

        html = check_page(
            "方式 1：iptv=CCTV1",
            r
        )

        pages.append(html)

    except Exception as e:

        print()
        print("方式 1 失败：", e)


    # =====================================================
    # 方式 2
    # =====================================================

    try:

        r = request_get(
            session,
            {
                "chname": KEYWORD
            }
        )

        html = check_page(
            "方式 2：chname=CCTV1",
            r
        )

        pages.append(html)

    except Exception as e:

        print()
        print("方式 2 失败：", e)


    # =====================================================
    # 方式 3
    # =====================================================

    try:

        r = request_get(
            session,
            {
                "page": "1",
                "chname": KEYWORD,
                "l": "0"
            }
        )

        html = check_page(
            "方式 3：page=1&chname=CCTV1&l=0",
            r
        )

        pages.append(html)

    except Exception as e:

        print()
        print("方式 3 失败：", e)


    # =====================================================
    # 方式 4
    # =====================================================

    try:

        r = request_post(
            session,
            {
                "seerch": KEYWORD
            }
        )

        html = check_page(
            "方式 4：POST seerch=CCTV1",
            r
        )

        pages.append(html)

    except Exception as e:

        print()
        print("方式 4 失败：", e)


    # =====================================================
    # 合并页面
    # =====================================================

    print()
    print("=" * 60)
    print("开始寻找直播地址")
    print("=" * 60)

    all_html = "\n".join(
        pages
    )

    # =====================================================
    # 处理网页转义
    # =====================================================

    all_html = (
        all_html
        .replace("\\/", "/")
        .replace("\\:", ":")
        .replace("\\u002F", "/")
        .replace("\\x2F", "/")
        .replace("&amp;", "&")
    )

    # =====================================================
    # 提取 URL
    # =====================================================

    urls = re.findall(
        r'https?://[^\s"\'<>]+',
        all_html,
        re.I
    )

    results = []

    for url in urls:

        url = url.rstrip(
            ".,;，。；）)]}>"
        )

        lower = url.lower()

        if any(
            x in lower
            for x in [
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

                results.append(
                    url
                )

    print()
    print(
        "发现候选直播源：",
        len(results)
    )

    for i, url in enumerate(
        results,
        1
    ):

        print(
            f"{i}. {url}"
        )

    print()
    print("=" * 60)
    print("测试结束")
    print("=" * 60)


if __name__ == "__main__":

    main()
