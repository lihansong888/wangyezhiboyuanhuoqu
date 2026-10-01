```python
import os
import re
import html
import time
import requests
import urllib3

urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)

# =========================================================
# 配置
# =========================================================

OUTPUT_M3U = "live.m3u8"
OUTPUT_TXT = "live.txt"

FOODIE_URL = "https://www.foodieguide.com/iptvsearch/"
TONKIANG_BASE = "https://tonkiang.us/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

TIMEOUT = 20


# =========================================================
# 港澳台频道
# 暂时不加入 CCTV
# =========================================================

CHANNELS = [

    # -----------------------------------------------------
    # 香港
    # -----------------------------------------------------

    "凤凰中文",
    "凤凰资讯",

    "翡翠台",
    "明珠台",
    "J2",
    "TVB Plus",
    "无线新闻台",

    "ViuTV",
    "ViuTV6",
    "ViuTVsix",

    "香港开电视",
    "HOY TV",
    "HOY资讯台",
    "HOY国际财经台",

    "港台电视31",
    "港台电视32",
    "港台电视33",

    "靖天电影",
    "靖天综合台",
    "靖天资讯台",
    "靖天日本台",

    # -----------------------------------------------------
    # 台湾
    # -----------------------------------------------------

    "台视",
    "台视新闻台",

    "中视",
    "中视新闻台",

    "华视",
    "华视新闻资讯台",

    "民视",
    "民视新闻台",

    "公视",
    "公视台语台",

    "三立台湾台",
    "三立都会台",
    "三立新闻台",
    "三立财经新闻台",

    "东森新闻台",
    "东森财经新闻台",
    "东森综合台",
    "东森戏剧台",
    "东森电影台",

    "TVBS",
    "TVBS新闻台",

    "中天新闻",
    "中天综合",
    "中天娱乐",

    "年代新闻",
    "年代MUCH",

    "八大第一台",
    "八大综合台",
    "八大戏剧台",
    "八大娱乐台",

    "纬来综合台",
    "纬来体育台",
    "纬来日本台",
    "纬来电影台",
    "纬来育乐台",

    "非凡新闻台",
    "非凡商业台",

    "龙华戏剧",
    "龙华电影",
    "龙华经典",

    # -----------------------------------------------------
    # 澳门
    # -----------------------------------------------------

    "澳视澳门",
    "澳视葡文",
    "澳门综艺",
    "澳门资讯",
    "TDM澳门",
]


# =========================================================
# 频道别名
# =========================================================

CHANNEL_ALIASES = {

    # 香港
    "凤凰中文": [
        "凤凰中文",
        "凤凰卫视中文台",
        "凤凰卫视",
        "凤凰中文台",
    ],

    "凤凰资讯": [
        "凤凰资讯",
        "凤凰资讯台",
        "凤凰卫视资讯台",
    ],

    "翡翠台": [
        "翡翠台",
        "TVB翡翠台",
        "TVB",
        "翡翠",
    ],

    "明珠台": [
        "明珠台",
        "TVB明珠台",
        "Pearl",
    ],

    "J2": [
        "J2",
        "TVB J2",
    ],

    "TVB Plus": [
        "TVB Plus",
        "TVBPlus",
    ],

    "无线新闻台": [
        "无线新闻台",
        "TVB新闻台",
        "TVB新闻",
    ],

    "ViuTV": [
        "ViuTV",
        "Viu TV",
    ],

    "ViuTV6": [
        "ViuTV6",
        "ViuTV 6",
    ],

    "ViuTVsix": [
        "ViuTVsix",
        "ViuTV six",
    ],

    "香港开电视": [
        "香港开电视",
        "开电视",
        "HOY TV",
    ],

    "HOY TV": [
        "HOY TV",
        "HOY",
        "香港开电视",
    ],

    "HOY资讯台": [
        "HOY资讯台",
        "HOY资讯",
        "HOY News",
    ],

    "HOY国际财经台": [
        "HOY国际财经台",
        "HOY国际财经",
    ],

    "港台电视31": [
        "港台电视31",
        "RTHK 31",
        "RTHK31",
    ],

    "港台电视32": [
        "港台电视32",
        "RTHK 32",
        "RTHK32",
    ],

    "港台电视33": [
        "港台电视33",
        "RTHK 33",
        "RTHK33",
    ],

    "靖天电影": [
        "靖天电影",
        "靖天影院",
        "靖天影城",
    ],

    "靖天综合台": [
        "靖天综合台",
        "靖天综合",
    ],

    "靖天资讯台": [
        "靖天资讯台",
        "靖天资讯",
    ],

    "靖天日本台": [
        "靖天日本台",
        "靖天日本",
    ],

    # 台湾
    "台视": [
        "台视",
        "台灣電視",
        "臺灣電視",
        "TTV",
    ],

    "台视新闻台": [
        "台视新闻台",
        "台視新聞",
        "TTV新闻",
    ],

    "中视": [
        "中视",
        "中視",
        "CTV",
    ],

    "中视新闻台": [
        "中视新闻台",
        "中視新聞",
        "CTV新闻",
    ],

    "华视": [
        "华视",
        "華視",
        "CTS",
    ],

    "华视新闻资讯台": [
        "华视新闻资讯台",
        "華視新聞資訊台",
        "CTS新闻",
    ],

    "民视": [
        "民视",
        "民視",
        "FTV",
    ],

    "民视新闻台": [
        "民视新闻台",
        "民視新聞台",
        "FTV新闻",
    ],

    "公视": [
        "公视",
        "公視",
        "PTS",
    ],

    "公视台语台": [
        "公视台语台",
        "公視台語台",
        "PTS台语",
    ],

    "三立台湾台": [
        "三立台湾台",
        "三立台灣台",
        "三立台湾",
    ],

    "三立都会台": [
        "三立都会台",
        "三立都會台",
        "三立都会",
    ],

    "三立新闻台": [
        "三立新闻台",
        "三立新聞台",
        "SET新闻",
    ],

    "三立财经新闻台": [
        "三立财经新闻台",
        "三立財經新聞台",
    ],

    "东森新闻台": [
        "东森新闻台",
        "東森新聞台",
        "ETTV新闻",
    ],

    "东森财经新闻台": [
        "东森财经新闻台",
        "東森財經新聞台",
    ],

    "东森综合台": [
        "东森综合台",
        "東森綜合台",
    ],

    "东森戏剧台": [
        "东森戏剧台",
        "東森戲劇台",
    ],

    "东森电影台": [
        "东森电影台",
        "東森電影台",
    ],

    "TVBS": [
        "TVBS",
        "TVBS频道",
    ],

    "TVBS新闻台": [
        "TVBS新闻台",
        "TVBS新聞台",
        "TVBS新闻",
    ],

    "中天新闻": [
        "中天新闻",
        "中天新聞",
        "CTi新闻",
    ],

    "中天综合": [
        "中天综合",
        "中天綜合",
    ],

    "中天娱乐": [
        "中天娱乐",
        "中天娛樂",
    ],

    "年代新闻": [
        "年代新闻",
        "年代新聞",
        "ERA新闻",
    ],

    "年代MUCH": [
        "年代MUCH",
        "年代MUCH台",
        "MUCH",
    ],

    "八大第一台": [
        "八大第一台",
        "八大第一",
    ],

    "八大综合台": [
        "八大综合台",
        "八大綜合台",
    ],

    "八大戏剧台": [
        "八大戏剧台",
        "八大戲劇台",
    ],

    "八大娱乐台": [
        "八大娱乐台",
        "八大娛樂台",
    ],

    "纬来综合台": [
        "纬来综合台",
        "緯來綜合台",
    ],

    "纬来体育台": [
        "纬来体育台",
        "緯來體育台",
        "纬来体育",
    ],

    "纬来日本台": [
        "纬来日本台",
        "緯來日本台",
    ],

    "纬来电影台": [
        "纬来电影台",
        "緯來電影台",
    ],

    "纬来育乐台": [
        "纬来育乐台",
        "緯來育樂台",
    ],

    "非凡新闻台": [
        "非凡新闻台",
        "非凡新聞台",
        "非凡新闻",
    ],

    "非凡商业台": [
        "非凡商业台",
        "非凡商業台",
    ],

    "龙华戏剧": [
        "龙华戏剧",
        "龍華戲劇",
    ],

    "龙华电影": [
        "龙华电影",
        "龍華電影",
    ],

    "龙华经典": [
        "龙华经典",
        "龍華經典",
    ],

    # 澳门
    "澳视澳门": [
        "澳视澳门",
        "澳視澳門",
        "TDM中文",
    ],

    "澳视葡文": [
        "澳视葡文",
        "澳視葡文",
        "TDM葡文",
    ],

    "澳门综艺": [
        "澳门综艺",
        "澳門綜藝",
    ],

    "澳门资讯": [
        "澳门资讯",
        "澳門資訊",
    ],

    "TDM澳门": [
        "TDM澳门",
        "TDM澳門",
        "澳门广播电视",
    ],
}


# =========================================================
# Tonkiang 五类源
# =========================================================

TONKIANG_ENDPOINTS = [
    ("普通源", "index.php"),
    ("酒店源", "iptvhotelx.php"),
    ("组播源", "iptvmulticast.php"),
    ("秒开源", "mqlive.php"),
    ("代理源", "iptvproxy.php"),
]


# =========================================================
# URL 清洗
# =========================================================

def clean_url(url):
    if not url:
        return ""

    url = html.unescape(url)

    url = (
        url.replace("\\/", "/")
        .replace("\\u0026", "&")
        .replace("&amp;", "&")
    )

    url = url.strip()
    url = url.strip("\"'<>[](){}")

    # 去掉 URL 末尾常见干扰符号
    url = url.rstrip(".,;\"'<>)]}")

    return url


# =========================================================
# 判断是否为候选直播源
# =========================================================

def is_candidate_url(url):
    if not url:
        return False

    url = url.strip()

    low = url.lower()

    # -----------------------------------------------------
    # HTTP / HTTPS
    # -----------------------------------------------------

    if low.startswith("http://") or low.startswith("https://"):

        keywords = [
            ".m3u8",
            ".m3u",
            ".ts",
            ".flv",
            ".mp4",
            "/live/",
            "/hls/",
            "/rtp/",
            "/rtmp/",
            "/tsfile/",
            "/stream/",
            "/channel/",
            "/playlist/",
            "/play/",
            "/video/",
            "m3u8?",
            "m3u?",
            "live?",
        ]

        return any(x in low for x in keywords)

    # -----------------------------------------------------
    # 组播
    # -----------------------------------------------------

    if low.startswith("rtp://"):
        return True

    if low.startswith("udp://"):
        return True

    if low.startswith("igmp://"):
        return True

    return False


# =========================================================
# 提取 URL
# =========================================================

def extract_urls(text):

    if not text:
        return []

    text = html.unescape(text)

    results = []

    # -----------------------------------------------------
    # HTTP / HTTPS
    # -----------------------------------------------------

    http_pattern = re.compile(
        r'https?://[^\s"\'<>\\]+',
        re.I
    )

    for match in http_pattern.findall(text):
        url = clean_url(match)

        if is_candidate_url(url):
            results.append(url)

    # -----------------------------------------------------
    # 组播 RTP / UDP / IGMP
    #
    # 例如：
    # rtp://239.0.0.1:8000
    # udp://239.0.0.1:1234
    # igmp://239.0.0.1:5000
    # -----------------------------------------------------

    multicast_pattern = re.compile(
        r'(?:rtp|udp|igmp)://'
        r'(?:\d{1,3}\.){3}\d{1,3}'
        r':\d{1,6}'
        r'(?:[/?][^\s"\'<>\\]*)?',
        re.I
    )

    for match in multicast_pattern.findall(text):
        url = clean_url(match)

        if is_candidate_url(url):
            results.append(url)

    # -----------------------------------------------------
    # 再检查带引号的 URL
    # -----------------------------------------------------

    quoted_pattern = re.compile(
        r'["\']((?:https?|rtp|udp|igmp)://[^"\']+)["\']',
        re.I
    )

    for match in quoted_pattern.findall(text):
        url = clean_url(match)

        if is_candidate_url(url):
            results.append(url)

    return unique_urls(results)


# =========================================================
# URL 去重
# =========================================================

def unique_urls(urls):

    seen = set()
    result = []

    for url in urls:

        url = clean_url(url)

        if not url:
            continue

        key = url.lower()

        if key in seen:
            continue

        seen.add(key)
        result.append(url)

    return result


# =========================================================
# FoodieGuide 搜索
# =========================================================

def foodie_search_keyword(session, keyword):

    all_urls = []

    print(f"    [FoodieGuide] 搜索：{keyword}")

    # -----------------------------------------------------
    # 方法 1
    # -----------------------------------------------------

    try:
        url = FOODIE_URL + "?chname=" + requests.utils.quote(keyword)

        r = session.get(
            url,
            headers=HEADERS,
            timeout=TIMEOUT,
            verify=False
        )

        if r.status_code == 200:
            urls = extract_urls(r.text)

            print(
                f"      chname -> {len(urls)}"
            )

            all_urls.extend(urls)

    except Exception as e:
        print(
            f"      chname 错误：{e}"
        )

    # -----------------------------------------------------
    # 方法 2
    # -----------------------------------------------------

    try:
        url = FOODIE_URL + "?iptv=" + requests.utils.quote(keyword)

        r = session.get(
            url,
            headers=HEADERS,
            timeout=TIMEOUT,
            verify=False
        )

        if r.status_code == 200:
            urls = extract_urls(r.text)

            print(
                f"      iptv -> {len(urls)}"
            )

            all_urls.extend(urls)

    except Exception as e:
        print(
            f"      iptv 错误：{e}"
        )

    # -----------------------------------------------------
    # 方法 3
    # -----------------------------------------------------

    try:
        url = (
            FOODIE_URL
            + "?page=1&chname="
            + requests.utils.quote(keyword)
            + "&l=0"
        )

        r = session.get(
            url,
            headers=HEADERS,
            timeout=TIMEOUT,
            verify=False
        )

        if r.status_code == 200:
            urls = extract_urls(r.text)

            print(
                f"      page -> {len(urls)}"
            )

            all_urls.extend(urls)

    except Exception as e:
        print(
            f"      page 错误：{e}"
        )

    # -----------------------------------------------------
    # 方法 4 POST
    # -----------------------------------------------------

    try:
        r = session.post(
            FOODIE_URL,
            data={
                "seerch": keyword
            },
            headers=HEADERS,
            timeout=TIMEOUT,
            verify=False
        )

        if r.status_code == 200:
            urls = extract_urls(r.text)

            print(
                f"      POST -> {len(urls)}"
            )

            all_urls.extend(urls)

    except Exception as e:
        print(
            f"      POST 错误：{e}"
        )

    return unique_urls(all_urls)


# =========================================================
# Tonkiang 单个分类搜索
# =========================================================

def tonkiang_search_endpoint(
    session,
    endpoint,
    keyword,
    source_type
):

    all_urls = []

    base_url = TONKIANG_BASE + endpoint

    print(
        f"    [Tonkiang/{source_type}] 搜索：{keyword}"
    )

    # -----------------------------------------------------
    # GET iptv
    # -----------------------------------------------------

    try:

        url = (
            base_url
            + "?iptv="
            + requests.utils.quote(keyword)
        )

        r = session.get(
            url,
            headers=HEADERS,
            timeout=TIMEOUT,
            verify=False
        )

        if r.status_code == 200:

            urls = extract_urls(r.text)

            print(
                f"      iptv -> {len(urls)}"
            )

            all_urls.extend(urls)

    except Exception as e:

        print(
            f"      iptv 错误：{e}"
        )

    # -----------------------------------------------------
    # GET chname
    # -----------------------------------------------------

    try:

        url = (
            base_url
            + "?chname="
            + requests.utils.quote(keyword)
        )

        r = session.get(
            url,
            headers=HEADERS,
            timeout=TIMEOUT,
            verify=False
        )

        if r.status_code == 200:

            urls = extract_urls(r.text)

            print(
                f"      chname -> {len(urls)}"
            )

            all_urls.extend(urls)

    except Exception as e:

        print(
            f"      chname 错误：{e}"
        )

    # -----------------------------------------------------
    # POST
    # -----------------------------------------------------

    try:

        r = session.post(
            base_url,
            data={
                "seerch": keyword
            },
            headers=HEADERS,
            timeout=TIMEOUT,
            verify=False
        )

        if r.status_code == 200:

            urls = extract_urls(r.text)

            print(
                f"      POST -> {len(urls)}"
            )

            all_urls.extend(urls)

    except Exception as e:

        print(
            f"      POST 错误：{e}"
        )

    return unique_urls(all_urls)


# =========================================================
# Tonkiang 五类源搜索
# =========================================================

def tonkiang_search(session, keyword):

    all_urls = []

    for source_type, endpoint in TONKIANG_ENDPOINTS:

        urls = tonkiang_search_endpoint(
            session,
            endpoint,
            keyword,
            source_type
        )

        all_urls.extend(urls)

        # 稍微降低请求频率
        time.sleep(0.3)

    return unique_urls(all_urls)


# =========================================================
# 搜索一个频道
# =========================================================

def search_channel(session, channel):

    print()
    print("=" * 60)
    print(f"开始搜索频道：{channel}")
    print("=" * 60)

    aliases = CHANNEL_ALIASES.get(
        channel,
        [channel]
    )

    all_urls = []

    for keyword in aliases:

        print()
        print(
            f"  >>> 搜索关键词：{keyword}"
        )

        # -------------------------------------------------
        # FoodieGuide
        # -------------------------------------------------

        foodie_urls = foodie_search_keyword(
            session,
            keyword
        )

        all_urls.extend(foodie_urls)

        # -------------------------------------------------
        # Tonkiang
        # -------------------------------------------------

        tonkiang_urls = tonkiang_search(
            session,
            keyword
        )

        all_urls.extend(tonkiang_urls)

        time.sleep(0.5)

    all_urls = unique_urls(all_urls)

    print()
    print(
        f"频道【{channel}】最终找到："
        f"{len(all_urls)} 个源"
    )

    return all_urls


# =========================================================
# 全局去重
# =========================================================

def deduplicate(results):

    seen = set()

    final_results = {}

    for channel, urls in results.items():

        final_results[channel] = []

        for url in urls:

            key = url.lower()

            if key in seen:
                continue

            seen.add(key)

            final_results[channel].append(url)

    return final_results


# =========================================================
# 保存 M3U
# =========================================================

def save_m3u8(results):

    count = 0

    with open(
        OUTPUT_M3U,
        "w",
        encoding="utf-8"
    ) as f:

        f.write("#EXTM3U\n")

        for channel, urls in results.items():

            for url in urls:

                f.write(
                    f'#EXTINF:-1 '
                    f'tvg-name="{channel}" '
                    f'group-title="港澳台直播",'
                    f'{channel}\n'
                )

                f.write(
                    url + "\n"
                )

                count += 1

    return count


# =========================================================
# 保存 TXT
# =========================================================

def save_txt(results):

    count = 0

    with open(
        OUTPUT_TXT,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            "港澳台直播,#genre#\n"
        )

        for channel, urls in results.items():

            for url in urls:

                f.write(
                    f"{channel},{url}\n"
                )

                count += 1

    return count


# =========================================================
# 主程序
# =========================================================

def main():

    print()
    print("=" * 70)
    print("       港澳台 IPTV 直播源搜索引擎")
    print("=" * 70)
    print()

    print(
        f"搜索频道数量：{len(CHANNELS)}"
    )

    print(
        "搜索引擎：FoodieGuide + Tonkiang"
    )

    print()
    print("Tonkiang 搜索类别：")

    for source_type, endpoint in TONKIANG_ENDPOINTS:

        print(
            f"  - {source_type} -> {endpoint}"
        )

    print()

    print(
        "支持提取："
        "HTTP / HTTPS / RTP / UDP / IGMP"
    )

    print()

    print(
        "不进行播放检测"
    )

    print(
        "不进行测速"
    )

    print(
        "不限制最终源数量"
    )

    print()

    session = requests.Session()

    results = {}

    # =====================================================
    # 搜索所有频道
    # =====================================================

    for index, channel in enumerate(
        CHANNELS,
        start=1
    ):

        print()
        print(
            f"######## "
            f"{index}/{len(CHANNELS)} "
            f"########"
        )

        urls = search_channel(
            session,
            channel
        )

        results[channel] = urls

    # =====================================================
    # 全局去重
    # =====================================================

    print()
    print("=" * 70)
    print("开始全局去重")
    print("=" * 70)

    results = deduplicate(results)

    # =====================================================
    # 统计
    # =====================================================

    total = 0

    print()

    for channel, urls in results.items():

        print(
            f"{channel:<20} "
            f"{len(urls)}"
        )

        total += len(urls)

    print()
    print(
        f"最终频道数量：{len(results)}"
    )

    print(
        f"最终直播源数量：{total}"
    )

    # =====================================================
    # 保存
    # =====================================================

    print()
    print("=" * 70)
    print("开始生成文件")
    print("=" * 70)

    m3u_count = save_m3u8(
        results
    )

    txt_count = save_txt(
        results
    )

    print()
    print(
        f"M3U 文件：{OUTPUT_M3U}"
    )

    print(
        f"M3U 源数量：{m3u_count}"
    )

    print()
    print(
        f"TXT 文件：{OUTPUT_TXT}"
    )

    print(
        f"TXT 源数量：{txt_count}"
    )

    # =====================================================
    # 文件检查
    # =====================================================

    print()

    if os.path.exists(OUTPUT_M3U):

        size = os.path.getsize(
            OUTPUT_M3U
        )

        print(
            f"✓ {OUTPUT_M3U} 已生成 "
            f"({size} bytes)"
        )

    else:

        print(
            f"✗ {OUTPUT_M3U} 生成失败"
        )

    if os.path.exists(OUTPUT_TXT):

        size = os.path.getsize(
            OUTPUT_TXT
        )

        print(
            f"✓ {OUTPUT_TXT} 已生成 "
            f"({size} bytes)"
        )

    else:

        print(
            f"✗ {OUTPUT_TXT} 生成失败"
        )

    print()
    print("=" * 70)
    print("搜索完成")
    print("=" * 70)


# =========================================================
# 入口
# =========================================================

if __name__ == "__main__":
    main()
```
