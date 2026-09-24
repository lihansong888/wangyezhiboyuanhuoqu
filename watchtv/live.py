import requests
from bs4 import BeautifulSoup


def search_tonkiang(keyword):
    url = "https://tonkiang.us/?"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/140.0.0.0 Safari/537.36"
        ),
        "Referer": "https://tonkiang.us/",
    }

    data = {
        "seerch": keyword
    }

    print(f"\n正在搜索：{keyword}")
    print("请求方式：POST")
    print("请求地址：", url)

    try:
        response = requests.post(
            url,
            data=data,
            headers=headers,
            timeout=30
        )

        print("HTTP状态：", response.status_code)
        print("网页长度：", len(response.text))

        if response.status_code != 200:
            print("请求失败")
            return []

        soup = BeautifulSoup(response.text, "html.parser")

        results = []

        # Tonkiang 搜索结果：
        # <div class="resultplus">
        #     <div class="channel1">
        #         ...
        #         <td class="nl">直播地址</td>
        #     </div>
        # </div>

        for item in soup.select("div.resultplus"):
            channel = item.select_one("div.channel1")
            if not channel:
                continue

            # 找到直播地址
            for td in item.select("td.nl"):
                text = td.get_text(strip=True)

                if not text:
                    continue

                if (
                    text.startswith("http://")
                    or text.startswith("https://")
                ):
                    results.append(text)

        # 去重
        results = list(dict.fromkeys(results))

        print(f"\n找到 {len(results)} 个直播源：\n")

        for index, stream_url in enumerate(results, 1):
            print(f"{index}. {stream_url}")

        return results

    except Exception as e:
        print("\n发生错误：")
        print(e)
        return []


if __name__ == "__main__":
    search_tonkiang("CCTV1")
