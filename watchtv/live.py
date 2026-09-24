import re
import os
import html as html_lib
from urllib.parse import quote, urljoin
import requests
import urllib3
from bs4 import BeautifulSoup
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# =========================================================
# 基本配置
# =========================================================
KEYWORD = os.environ.get("IPTV_KEYWORD", "CCTV1").strip()
# Tonkiang 的真实搜索表单：
# <form method="post" action="/?">
#     <input name="seerch" ...>
#
# 注意：这里不能只用以前的 GET ?iptv=CCTV1。
TONKIANG_HOME = "https://tonkiang.us/"
TONKIANG_SEARCH = "https://tonkiang.us/?"
# 备用搜索入口
FOODIEGUIDE_URL = (    
"https://www.foodieguide.com/iptvsearch/?iptv="    
+ quote(KEYWORD)
)
TIMEOUT = 25
HEADERS = {    
"User-Agent": (        
"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "        
"AppleWebKit/537.36 (KHTML, like Gecko) "        
"Chrome/131.0.0.0 Safari/537.36"    
),    
"Accept": (        
"text/html,application/xhtml+xml,application/xml;"        
"q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"    
),    
"Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",    
"Cache-Control": "no-cache",    
"Pragma": "no-cache",    
"Referer": TONKIANG_HOME,    
"Upgrade-Insecure-Requests": "1",
}
# =========================================================
# 可选 cloudscraper
#
# 如果 GitHub Actions 被 Cloudflare 拦截，而 workflow 中安装了
# cloudscraper，就优先尝试它；没有安装也不会报错。
# =========================================================
try:    
import cloudscraper
except ImportError:    
cloudscraper = None

def make_session():    
if cloudscraper is not None:        
try:            
session = cloudscraper.create_scraper(                
browser={                    
"browser": "chrome",                    
"platform": "windows",                    
"mobile": False,                
}            
)            
session.headers.update(HEADERS)            
return session, "cloudscraper"        
except Exception as e:            
print("cloudscraper 初始化失败，改用 requests：", e)
    session = requests.Session()    
session.headers.update(HEADERS)    
return session, "requests"

# =========================================================
# 判断是不是直播地址
# =========================================================
    print()
