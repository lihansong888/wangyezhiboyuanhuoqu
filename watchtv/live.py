import requests
import re
from bs4 import BeautifulSoup


def search_foodieguide(keyword):
    url = "https://www.foodieguide.com/iptvsearch/"

    params = {
        "iptv": keyword
    }

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/140.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,"
            "application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
        ),
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": "https://www.foodieguide.com/iptvsearch/"
    }

    print(f"正在搜索：{keyword}")
    print(f"请求地址：{url}?iptv={keyword}")

    try:
        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=30
        )

        print("HTTP状态：", response.status_code)
        print("网页长度：", len(response.text))

        if response.status_code != 200:
            print("请求失败")
            print(response.text[:1000])
            return []

        soup = BeautifulSoup(response.text, "html.parser")

        results = []

        # 从网页中的所有文字和属性里寻找直播地址
        for tag in soup.find_all(True):

            # 检查标签文字
            text = tag.get_text(" ", strip=True)

            if text:
                urls = re.findall(
                    r'https?://[^\s"\'<>]+'
                    r'(?:m3u8|m3u|ts)'
                    r'(?:\?[^\s"\'<>]*)?',
                    text,
                    re.IGNORECASE
                )

                results.extend(urls)

            # 检查 href
            href = tag.get("href")

            if href:
                urls = re.findall(
                    r'https?://[^\s"\'<>]+'
                    r'(?:m3u8|m3u|ts)'
                    r'(?:\?[^\s"\'<>]*)?',
                    href,
                    re.IGNORECASE
                )

                results.extend(urls)

            # 检查 data-* 属性
            for value in tag.attrs.values():

                if isinstance(value, list):
                    value = " ".join(value)

                if not isinstance(value, str):
                    continue

                urls = re.findall(
                    r'https?://[^\s"\'<>]+'
                    r'(?:m3u8|m3u|ts)'
                    r'(?:\?[^\s"\'<>]*)?',
                    value,
                    re.IGNORECASE
                )

                results.extend(urls)

        # 最后直接扫描整个 HTML
        urls = re.findall(
            r'https?://[^\s"\'<>]+'
            r'(?:m3u8|m3u|ts)'
            r'(?:\?[^\s"\'<>]*)?',
            response.text,
            re.IGNORECASE
        )

        results.extend(urls)

        # 清理 HTML 编码
        results = [
            url.replace("&amp;", "&")
            for url in results
        ]

        # 去重
        results = list(dict.fromkeys(results))

        print()
        print(f"找到 {len(results)} 个直播源：")
        print()

        for i, stream_url in enumerate(results, 1):
            print(f"{i}. {stream_url}")

        return results

    except requests.exceptions.Timeout:
        print("请求超时")
        return []

    except requests.exceptions.RequestException as e:
        print("网络请求错误：")
        print(e)
        return []

    except Exception as e:
        print("程序发生错误：")
        print(e)
        return []


if __name__ == "__main__":
    search_foodieguide("CCTV1")
