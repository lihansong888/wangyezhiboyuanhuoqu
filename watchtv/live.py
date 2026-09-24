import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import quote

def search_tonkiang(keyword):
    url = "https://tonkiang.us/"
    params = {
        "iptv": keyword
    }

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    print(f"\n正在搜索：{keyword}")
    print(f"请求：{url}?iptv={quote(keyword)}")

    try:
        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=20
        )

        print("HTTP状态：", response.status_code)
        print("网页长度：", len(response.text))

        if response.status_code != 200:
            print("请求失败")
            return []

        soup = BeautifulSoup(response.text, "html.parser")

        # 提取网页中所有链接
        links = []

        for a in soup.find_all("a"):
            href = a.get("href", "")

            if not href:
                continue

            if re.search(
                r'\.(m3u8|m3u|ts)(\?|$)',
                href,
                re.IGNORECASE
            ):
                links.append(href)

        # 有些直播地址不一定在 <a> 标签里，
        # 所以再从整个网页源码中提取一次
        urls = re.findall(
            r'https?://[^\s"\'<>]+(?:m3u8|m3u|ts)(?:\?[^\s"\'<>]*)?',
            response.text,
            re.IGNORECASE
        )

        links.extend(urls)

        # 去重
        result = []

        for link in links:
            link = link.replace("&amp;", "&")

            if link not in result:
                result.append(link)

        print(f"\n找到 {len(result)} 个直播源：\n")

        for i, link in enumerate(result, 1):
            print(f"{i}. {link}")

        return result

    except Exception as e:
        print("发生错误：", e)
        return []


if __name__ == "__main__":
    search_tonkiang("CCTV1")
