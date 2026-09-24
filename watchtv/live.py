import requests
import re
import urllib3
from bs4 import BeautifulSoup
from urllib.parse import quote

# 忽略自签名证书警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ============================================================
# 基础配置
# ============================================================

KEYWORD = "CCTV1"

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


# ============================================================
# 提取直播地址
# ============================================================

def extract_urls(text):

    urls = []

    # 直接从源码中寻找 http/https 的直播地址
    patterns = [
        r'https?://[^\s"\'<>]+?\.m3u8(?:\?[^\s"\'<>]*)?',
        r'https?://[^\s"\'<>]+?\.m3u(?:\?[^\s"\'<>]*)?',
        r'https?://[^\s"\'<>]+?\.ts(?:\?[^\s"\'<>]*)?',
    ]

    for pattern in patterns:
        found = re.findall(pattern, text, re.IGNORECASE)

        for url in found:

            # 清理 HTML 编码
            url = url.replace("&amp;", "&")
            url = url.rstrip("),;]}")

            if url not in urls:
                urls.append(url)

    return urls


# ============================================================
# 搜索 FoodieGuide
# ============================================================

def search_foodieguide(keyword):

    url = "https://www.foodieguide.com/iptvsearch/"

    params = {
        "iptv": keyword
    }

    print("")
    print("=" * 60)
    print("正在搜索：", keyword)
    print(
        "请求地址：",
        url + "?iptv=" + quote(keyword)
    )
    print("=" * 60)

    try:

        response = requests.get(
            url,
            params=params,
            headers=HEADERS,
            timeout=30,

            # 关键：
            # FoodieGuide 当前证书存在 self-signed 问题
            # GitHub Actions 默认会拒绝该证书
            verify=False
        )

        print("HTTP状态：", response.status_code)
        print("网页长度：", len(response.text))

        if response.status_code != 200:
            print("请求失败")
            return []

        # ----------------------------------------------------
        # 方法一：直接从网页源码提取
        # ----------------------------------------------------

        urls = extract_urls(response.text)

        # ----------------------------------------------------
        # 方法二：BeautifulSoup 检查所有链接
        # ----------------------------------------------------

        soup = BeautifulSoup(response.text, "html.parser")

        for a in soup.find_all("a"):

            href = a.get("href", "")

            if not href:
                continue

            href = href.replace("&amp;", "&")

            if re.search(
                r'\.(m3u8|m3u|ts)(\?|$)',
                href,
                re.IGNORECASE
            ):

                if href not in urls:
                    urls.append(href)

        # ----------------------------------------------------
        # 去重
        # ----------------------------------------------------

        result = []

        for url in urls:

            if url not in result:
                result.append(url)

        print("")
        print("找到直播源：", len(result))
        print("")

        if result:

            for i, stream in enumerate(result, 1):

                print(f"{i}. {stream}")

        else:

            print("没有找到 m3u8 / m3u / ts 地址")

        return result

    except Exception as e:

        print("")
        print("发生错误：")
        print(e)

        return []


# ============================================================
# 主程序
# ============================================================

if __name__ == "__main__":

    results = search_foodieguide(KEYWORD)

    print("")
    print("=" * 60)
    print("搜索结束")
    print("直播源数量：", len(results))
    print("=" * 60)

    if results:

        print("")
        print("最终直播源：")

        for url in results:
            print(url)
