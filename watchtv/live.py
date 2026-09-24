import requests
import re
import urllib3
from bs4 import BeautifulSoup
from urllib.parse import quote

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


KEYWORD = "CCTV1"

URL = "https://www.foodieguide.com/iptvsearch/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://www.foodieguide.com/",
}


def clean_url(url):

    if not url:
        return None

    url = url.replace("&amp;", "&")
    url = url.replace("\\/", "/")

    # 去掉 HTML / JS 常见尾部字符
    url = url.strip()
    url = url.rstrip("'\"),;]} >")

    if not url.startswith(("http://", "https://")):
        return None

    return url


def is_stream_url(url):

    if not url:
        return False

    return bool(
        re.search(
            r'\.(m3u8|m3u|ts)(?:\?|$)',
            url,
            re.IGNORECASE
        )
    )


def extract_streams(html):

    results = []

    def add(url):

        url = clean_url(url)

        if not url:
            return

        if is_stream_url(url):

            if url not in results:
                results.append(url)

    # ========================================================
    # 1. 直接搜索网页源码中的直播地址
    # ========================================================

    patterns = [

        # http://xxx.m3u8
        r'https?://[^\'"\s<>]+?\.m3u8(?:\?[^\'"\s<>]*)?',

        # http://xxx.m3u
        r'https?://[^\'"\s<>]+?\.m3u(?:\?[^\'"\s<>]*)?',

        # http://xxx.ts
        r'https?://[^\'"\s<>]+?\.ts(?:\?[^\'"\s<>]*)?',
    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
            html,
            re.IGNORECASE
        )

        for url in matches:
            add(url)


    # ========================================================
    # 2. 解析 onclick
    #
    # FoodieGuide 页面实际上大量使用：
    #
    # onclick="yaergl('http://xxx/live/cctv1.m3u8')"
    #
    # ========================================================

    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.find_all(True):

        onclick = tag.get("onclick", "")

        if onclick:

            matches = re.findall(
                r'https?://[^\'"\s<>]+',
                onclick,
                re.IGNORECASE
            )

            for url in matches:
                add(url)


    # ========================================================
    # 3. 检查所有 href
    # ========================================================

    for tag in soup.find_all("a"):

        href = tag.get("href", "")

        add(href)


    # ========================================================
    # 4. 检查网页所有纯文本
    # ========================================================

    text = soup.get_text(" ", strip=True)

    matches = re.findall(
        r'https?://[^\'"\s<>]+',
        text,
        re.IGNORECASE
    )

    for url in matches:
        add(url)


    return results


def search_foodieguide(keyword):

    params = {
        "iptv": keyword
    }

    print("")
    print("=" * 60)
    print("正在搜索：", keyword)
    print(
        "请求地址：",
        URL + "?iptv=" + quote(keyword)
    )
    print("=" * 60)

    try:

        response = requests.get(
            URL,
            params=params,
            headers=HEADERS,
            timeout=30,
            verify=False
        )

        print("HTTP状态：", response.status_code)
        print("网页长度：", len(response.text))

        if response.status_code != 200:

            print("请求失败")
            return []

        # ====================================================
        # 提取直播源
        # ====================================================

        results = extract_streams(response.text)

        print("")
        print("找到直播源：", len(results))
        print("")

        if results:

            for i, url in enumerate(results, 1):

                print(f"{i}. {url}")

        else:

            print("没有找到直播源")

            # =================================================
            # 为了下一步排查，把关键 HTML 打印出来
            # =================================================

            print("")
            print("正在检查网页中的 m3u8 相关内容...")

            for line in response.text.splitlines():

                if (
                    "m3u8" in line.lower()
                    or "m3u" in line.lower()
                    or "yaergl" in line.lower()
                ):

                    print(line[:1000])

        return results

    except Exception as e:

        print("")
        print("网络请求错误：")
        print(e)

        return []


if __name__ == "__main__":

    results = search_foodieguide(KEYWORD)

    print("")
    print("=" * 60)
    print("搜索结束")
    print("直播源数量：", len(results))
    print("=" * 60)
