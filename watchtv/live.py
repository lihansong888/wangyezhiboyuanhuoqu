import requests
import re
from bs4 import BeautifulSoup

KEYWORD = "CCTV1"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
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


def main():

    session = requests.Session()
    session.headers.update(HEADERS)

    # -----------------------------------------------------
    # 方式 1
    # -----------------------------------------------------

    r = session.get(
        BASE,
        params={
            "iptv": KEYWORD
        },
        timeout=30
    )

    html1 = check_page(
        "方式 1：iptv=CCTV1",
        r
    )

    # -----------------------------------------------------
    # 方式 2
    # -----------------------------------------------------

    r = session.get(
        BASE,
        params={
            "chname": KEYWORD
        },
        timeout=30
    )

    html2 = check_page(
        "方式 2：chname=CCTV1",
        r
    )

    # -----------------------------------------------------
    # 方式 3
    # -----------------------------------------------------

    r = session.get(
        BASE,
        params={
            "page": "1",
            "chname": KEYWORD,
            "l": "0"
        },
        timeout=30
    )

    html3 = check_page(
        "方式 3：page=1&chname=CCTV1&l=0",
        r
    )

    # -----------------------------------------------------
    # 方式 4
    # -----------------------------------------------------

    r = session.post(
        BASE,
        data={
            "seerch": KEYWORD
        },
        timeout=30
    )

    html4 = check_page(
        "方式 4：POST seerch=CCTV1",
        r
    )

    # -----------------------------------------------------
    # 从所有页面寻找直播地址
    # -----------------------------------------------------

    print()
    print("=" * 60)
    print("开始寻找直播地址")
    print("=" * 60)

    all_html = (
        html1 +
        html2 +
        html3 +
        html4
    )

    # 处理网页里的转义
    all_html = (
        all_html
        .replace("\\/", "/")
        .replace("\\:", ":")
        .replace("&amp;", "&")
    )

    # 找 http/https 地址
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

        low = url.lower()

        if any(
            x in low
            for x in [
                ".m3u8",
                ".m3u",
                ".ts",
                "/rtp/",
                "/live/",
                "/stream/",
                "/channel/",
            ]
        ):

            if url not in results:
                results.append(url)

    print(
        "发现候选直播源：",
        len(results)
    )

    for i, url in enumerate(
        results,
        1
    ):
        print(
            i,
            url
        )

    print()
    print("=" * 60)
    print("测试结束")
    print("=" * 60)


if __name__ == "__main__":
    main()
