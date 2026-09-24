import requests
import re
import urllib3
import json
from urllib.parse import quote

urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)

# =========================================================
# 配置
# =========================================================

CHANNEL_FILE = "watchtv/channels.json"

BASE_URL = "https://www.foodieguide.com/iptvsearch/"

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

TIMEOUT = 30


# =========================================================
# 提取直播源
# =========================================================

def extract_urls(html):

    if not html:
        return []

    # 处理网页中的转义
    html = html.replace("\\/", "/")
    html = html.replace("\\:", ":")
    html = html.replace("\\u002F", "/")
    html = html.replace("\\x2F", "/")
    html = html.replace("&amp;", "&")

    results = []

    # -----------------------------------------------------
    # 第一种：直接寻找完整 URL
    # -----------------------------------------------------

    urls = re.findall(
        r'https?://[^\s"\'<>\\]+',
        html,
        re.IGNORECASE
    )

    for url in urls:

        url = url.strip()
        url = url.rstrip(
            ".,;，。；）)]}>"
        )

        lower = url.lower()

        if any(
            key in lower
            for key in [
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
                results.append(url)

    # -----------------------------------------------------
    # 第二种：处理网页中可能没有完整协议的情况
    # -----------------------------------------------------

    escaped_urls = re.findall(
        r'https?\\?://[^\s"\'<>]+',
        html,
        re.IGNORECASE
    )

    for url in escaped_urls:

        url = (
            url
            .replace("\\/", "/")
            .replace("\\:", ":")
        )

        url = url.rstrip(
            ".,;，。；）)]}>"
        )

        lower = url.lower()

        if any(
            key in lower
            for key in [
                ".m3u8",
                ".m3u",
                ".ts",
                ".flv",
                "/rtp/",
                "/live/",
                "/stream/",
                "/channel/"
            ]
        ):

            if url not in results:
                results.append(url)

    return results


# =========================================================
# 搜索 FoodieGuide
# =========================================================

def search_foodieguide(keyword):

    session = requests.Session()

    session.headers.update(
        HEADERS
    )

    print()
    print("=" * 60)
    print("FoodieGuide IPTV 搜索")
    print("=" * 60)

    print(
        "搜索关键词：",
        keyword
    )

    # =====================================================
    # 方式一
    # 已验证可以返回搜索结果
    # =====================================================

    url = BASE_URL

    params = {
        "chname": keyword
    }

    print()
    print(
        "请求入口：",
        BASE_URL + "?chname=" + quote(keyword)
    )

    try:

        response = session.get(
            url,
            params=params,
            headers=HEADERS,
            timeout=TIMEOUT,
            verify=False,
            allow_redirects=True
        )

    except Exception as e:

        print()
        print(
            "请求失败：",
            e
        )

        return []

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
            "FoodieGuide 请求失败"
        )

        return []

    # =====================================================
    # 解析
    # =====================================================

    print()
    print(
        "开始解析直播源..."
    )

    streams = extract_urls(
        response.text
    )

    # =====================================================
    # 如果第一页没有源
    # 再尝试 page=1&chname=频道&l=0
    # =====================================================

    if not streams:

        print(
            "主入口没有直接找到直播源。"
        )

        print(
            "尝试第二入口..."
        )

        params = {
            "page": "1",
            "chname": keyword,
            "l": "0"
        }

        try:

            response = session.get(
                url,
                params=params,
                headers=HEADERS,
                timeout=TIMEOUT,
                verify=False,
                allow_redirects=True
            )

            print(
                "第二入口 HTTP：",
                response.status_code
            )

            print(
                "第二入口最终地址：",
                response.url
            )

            print(
                "第二入口网页长度：",
                len(response.text)
            )

            if response.status_code == 200:

                streams = extract_urls(
                    response.text
                )

        except Exception as e:

            print(
                "第二入口请求失败：",
                e
            )

    # =====================================================
    # 当前频道内部去重
    # =====================================================

    unique = []

    seen = set()

    for stream in streams:

        stream = stream.strip()

        if not stream:
            continue

        if stream in seen:
            continue

        seen.add(stream)

        unique.append(stream)

    # =====================================================
    # 输出
    # =====================================================

    print()
    print("=" * 60)

    print(
        "找到直播源：",
        len(unique)
    )

    print("=" * 60)

    for index, stream in enumerate(
        unique,
        1
    ):

        print(
            f"{index}. {stream}"
        )

    return unique


# =========================================================
# 保存 M3U
# =========================================================

def save_m3u(all_results):

    filename = "live_results.m3u"

    try:

        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(
                "#EXTM3U\n"
            )

            for keyword, streams in all_results:

                for index, stream in enumerate(
                    streams,
                    1
                ):

                    file.write(
                        f"#EXTINF:-1,{keyword} {index}\n"
                    )

                    file.write(
                        stream + "\n"
                    )

        print()
        print(
            "M3U 文件已生成：",
            filename
        )

    except Exception as e:

        print(
            "M3U 保存失败：",
            e
        )


# =========================================================
# 保存 TXT
# =========================================================

def save_txt(all_results):

    filename = "live_results.txt"

    try:

        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as file:

            for keyword, streams in all_results:

                for stream in streams:

                    file.write(
                        f"{keyword},{stream}\n"
                    )

        print(
            "TXT 文件已生成：",
            filename
        )

    except Exception as e:

        print(
            "TXT 保存失败：",
            e
        )


# =========================================================
# 主程序
# =========================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("直播源批量搜索")
    print("=" * 60)

    # =====================================================
    # 读取频道列表
    # =====================================================

    try:

        with open(
            CHANNEL_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            channels = json.load(file)

    except Exception as e:

        print()
        print(
            "读取频道列表失败：",
            e
        )

        raise SystemExit(1)

    if not isinstance(channels, list):

        print()
        print(
            "频道列表格式错误：必须是 JSON 数组"
        )

        raise SystemExit(1)

    print(
        "频道数量：",
        len(channels)
    )

    # =====================================================
    # 批量搜索
    # =====================================================

    all_results = []

    # 总地址去重
    # 同一个地址如果被不同频道搜索到，
    # 暂时保留第一次出现的频道归属。

    global_seen = set()

    for keyword in channels:

        keyword = str(keyword).strip()

        if not keyword:
            continue

        streams = search_foodieguide(
            keyword
        )

        if not streams:

            print()
            print(
                f"{keyword}：没有找到直播源"
            )

            continue

        # -------------------------------------------------
        # 按「频道 + 地址」整理
        # -------------------------------------------------

        channel_results = []

        for stream in streams:

            stream = stream.strip()

            if not stream:
                continue

            # 相同频道 + 相同地址不重复
            key = (
                keyword,
                stream
            )

            if key in global_seen:
                continue

            global_seen.add(key)

            channel_results.append(
                stream
            )

        if channel_results:

            all_results.append(
                (
                    keyword,
                    channel_results
                )
            )

    # =====================================================
    # 保存
    # =====================================================

    if all_results:

        save_m3u(
            all_results
        )

        save_txt(
            all_results
        )

    else:

        print()
        print(
            "所有频道都没有找到直播源。"
        )

    # =====================================================
    # 统计
    # =====================================================

    total_streams = sum(
        len(streams)
        for keyword, streams in all_results
    )

    print()
    print("=" * 60)
    print("搜索完成")
    print("=" * 60)

    print(
        "成功获取频道：",
        len(all_results)
    )

    print(
        "直播源总数：",
        total_streams
    )

    print("=" * 60)
