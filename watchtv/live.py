import requests
from bs4 import BeautifulSoup


def search_tonkiang(keyword):
    url = "https://tonkiang.us/"

    params = {
        "keyword": keyword,
        "l": "0"
    }

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/140.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": "https://tonkiang.us/"
    }

    print(f"正在搜索：{keyword}")
    print(f"请求地址：{url}?keyword={keyword}&l=0")

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
            print(response.text[:500])
            return []

        soup = BeautifulSoup(response.text, "html.parser")

        results = []

        # Tonkiang 的直播源位于：
        # <tba class="vnliuj"> http://xxx.m3u8 </tba>
        for item in soup.select("tba.vnliuj"):
            stream_url = item.get_text(strip=True)

            if stream_url.startswith(("http://", "https://")):
                results.append(stream_url)

        # 再从网页源码中寻找 m3u8 / m3u / ts
        import re

        urls = re.findall(
            r'https?://[^\s"\'<>]+(?:m3u8|m3u|ts)(?:\?[^\s"\'<>]*)?',
            response.text,
            re.IGNORECASE
        )

        results.extend(urls)

        # 去重
        results = list(dict.fromkeys(results))

        print()
        print(f"找到 {len(results)} 个直播源：")
        print()

        for i, stream_url in enumerate(results, 1):
            print(f"{i}. {stream_url}")

        return results

    except Exception as e:
        print("发生错误：", e)
        return []


if __name__ == "__main__":
    search_tonkiang("CCTV1")
