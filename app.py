import os
import sys
import json
import uuid
import time
import threading
import subprocess
import tempfile
import random
import string
import re
from datetime import datetime
from queue import Queue
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room
import requests
from curl_cffi import requests as c_requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ta_tool_secret_2024'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSIONS_DIR = os.path.join(BASE_DIR, "sessions")
os.makedirs(SESSIONS_DIR, exist_ok=True)
TEMP_TOOLS_DIR = os.path.join(tempfile.gettempdir(), "ta_tool_embedded")
os.makedirs(TEMP_TOOLS_DIR, exist_ok=True)

sessions = {}
sessions_lock = threading.Lock()

FB_REG_STATE = {"running": False, "total_success": 0, "total_fail": 0}
FB_REG_LOCK = threading.Lock()

# ============================================================================
# ==================== TOOL 2: xsmmigv5.2.py (FULL GỐC) ======================
# ============================================================================
TOOL_CODE_XSMMIGV52 = r'''import os
import sys
import time
import json
import re
from datetime import datetime
import random
from urllib.parse import unquote
from curl_cffi import requests as c_requests
import requests

# ================= BẢNG MÀU ANSI =================
xuong = "\n"
do = "\033[1;91m"
maufulldo = "\033[1;47;31m"
maunenhong = "\033[1;41;33m"
red = "\033[1;31m"
pink = "\033[1;35m"
green = "\033[1;32m"
yellow = "\033[1;33m"
white = "\033[0;37m"
cyan = "\033[1;36m"
blue = "\033[1;34m"
cam = "\033[38;5;208m"
gray = "\033[0;90m"
reset = "\033[0m"

# ================= QUẢN LÝ TASK_ID FOLLOW CHỜ DUYỆT BẰNG JSON =================
PENDING_FOLLOW_FILE = "pending_follow_tasks.json"

def get_pending_tasks(uid):
    if os.path.exists(PENDING_FOLLOW_FILE):
        try:
            with open(PENDING_FOLLOW_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get(str(uid), [])
        except Exception:
            return []
    return []

def add_pending_task(uid, task_id):
    data = {}
    if os.path.exists(PENDING_FOLLOW_FILE):
        try:
            with open(PENDING_FOLLOW_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    uid_str = str(uid)
    if uid_str not in data:
        data[uid_str] = []
    if task_id not in data[uid_str]:
        data[uid_str].append(task_id)
    try:
        with open(PENDING_FOLLOW_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def remove_pending_tasks(uid, task_ids_done):
    if not os.path.exists(PENDING_FOLLOW_FILE):
        return
    try:
        with open(PENDING_FOLLOW_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        uid_str = str(uid)
        if uid_str in data:
            data[uid_str] = [t for t in data[uid_str] if t not in task_ids_done]
            if not data[uid_str]:
                del data[uid_str]
        with open(PENDING_FOLLOW_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# ================= BỘ NHỚ ĐỆM TOKEN =================
CACHE_TOKENS = {}

def get_tokens_for_account(session, cookie, profile_url, impersonate_browser):
    actor_id_match = re.search(r'ds_user_id=(\d+)', cookie)
    uid = actor_id_match.group(1) if actor_id_match else "default"
    
    if uid in CACHE_TOKENS and CACHE_TOKENS[uid][1]:
        return CACHE_TOKENS[uid]

    fb_dtsg, lsd, jazoest = "", "7q44S3aBoCQ_1VuGgqlys8", "26485"
    target = profile_url if profile_url else "https://www.instagram.com/"
    try:
        res_home = session.get(target, impersonate=impersonate_browser, timeout=20).text
        lsd_match = re.search(r'"LSD",\[\],{"token":"([^"]+)"}', res_home)
        if lsd_match:
            lsd = lsd_match.group(1)
        dtsg_match = re.search(r'"dtsg":\{"token":"([^"]+)"', res_home) or re.search(r'name="fb_dtsg" value="([^"]+)"', res_home)
        if dtsg_match:
            fb_dtsg = dtsg_match.group(1)
        jazoest_match = re.search(r'name="jazoest" value="(\d+)"', res_home)
        if jazoest_match:
            jazoest = jazoest_match.group(1)
    except Exception:
        pass

    CACHE_TOKENS[uid] = (fb_dtsg, lsd, jazoest)
    return CACHE_TOKENS[uid]

# ================= POOL 25 TRÌNH DUYỆT ĐA DẠNG =================
BROWSER_PROFILES = [
    {"name": "Chrome 124 (Windows 11)", "impersonate": "chrome124",
     "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
     "sec_ch_ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"', "sec_ch_ua_platform": '"Windows"'},
    {"name": "Chrome 120 (Windows 10)", "impersonate": "chrome120",
     "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
     "sec_ch_ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"', "sec_ch_ua_platform": '"Windows"'},
    {"name": "Chrome 119 (Windows 10)", "impersonate": "chrome119",
     "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
     "sec_ch_ua": '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"', "sec_ch_ua_platform": '"Windows"'},
    {"name": "Chrome 116 (Windows 10)", "impersonate": "chrome116",
     "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
     "sec_ch_ua": '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"', "sec_ch_ua_platform": '"Windows"'},
    {"name": "Chrome 110 (Windows 10)", "impersonate": "chrome110",
     "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
     "sec_ch_ua": '"Chromium";v="110", "Not A(Brand";v="24", "Google Chrome";v="110"', "sec_ch_ua_platform": '"Windows"'},
    {"name": "Edge 124 (Windows 11)", "impersonate": "chrome124",
     "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
     "sec_ch_ua": '"Chromium";v="124", "Microsoft Edge";v="124", "Not-A.Brand";v="99"', "sec_ch_ua_platform": '"Windows"'},
    {"name": "Edge 120 (Windows 10)", "impersonate": "chrome120",
     "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
     "sec_ch_ua": '"Not_A Brand";v="8", "Chromium";v="120", "Microsoft Edge";v="120"', "sec_ch_ua_platform": '"Windows"'},
    {"name": "Edge 119 (Windows 10)", "impersonate": "chrome119",
     "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
     "sec_ch_ua": '"Microsoft Edge";v="119", "Chromium";v="119", "Not?A_Brand";v="24"', "sec_ch_ua_platform": '"Windows"'},
    {"name": "Edge 101 (Windows 10)", "impersonate": "edge101",
     "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36 Edg/101.0.1210.53",
     "sec_ch_ua": '"Not A;Brand";v="99", "Chromium";v="101", "Microsoft Edge";v="101"', "sec_ch_ua_platform": '"Windows"'},
    {"name": "Edge 99 (Windows 10)", "impersonate": "edge99",
     "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36 Edg/99.0.1150.55",
     "sec_ch_ua": '" Not A;Brand";v="99", "Chromium";v="99", "Microsoft Edge";v="99"', "sec_ch_ua_platform": '"Windows"'},
    {"name": "Chrome 124 (macOS Sonoma)", "impersonate": "chrome124",
     "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
     "sec_ch_ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"', "sec_ch_ua_platform": '"macOS"'},
    {"name": "Chrome 120 (macOS Ventura)", "impersonate": "chrome120",
     "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
     "sec_ch_ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"', "sec_ch_ua_platform": '"macOS"'},
    {"name": "Chrome 119 (macOS Monterey)", "impersonate": "chrome119",
     "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
     "sec_ch_ua": '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"', "sec_ch_ua_platform": '"macOS"'},
    {"name": "Chrome 116 (macOS Sonoma)", "impersonate": "chrome116",
     "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
     "sec_ch_ua": '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"', "sec_ch_ua_platform": '"macOS"'},
    {"name": "Chrome 110 (macOS Big Sur)", "impersonate": "chrome110",
     "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
     "sec_ch_ua": '"Chromium";v="110", "Not A(Brand";v="24", "Google Chrome";v="110"', "sec_ch_ua_platform": '"macOS"'},
    {"name": "Edge 124 (macOS Sonoma)", "impersonate": "chrome124",
     "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
     "sec_ch_ua": '"Chromium";v="124", "Microsoft Edge";v="124", "Not-A.Brand";v="99"', "sec_ch_ua_platform": '"macOS"'},
    {"name": "Edge 120 (macOS Ventura)", "impersonate": "chrome120",
     "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
     "sec_ch_ua": '"Not_A Brand";v="8", "Chromium";v="120", "Microsoft Edge";v="120"', "sec_ch_ua_platform": '"macOS"'},
    {"name": "Edge 119 (macOS Monterey)", "impersonate": "chrome119",
     "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
     "sec_ch_ua": '"Microsoft Edge";v="119", "Chromium";v="119", "Not?A_Brand";v="24"', "sec_ch_ua_platform": '"macOS"'},
    {"name": "Chrome 124 (Linux x86_64)", "impersonate": "chrome124",
     "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
     "sec_ch_ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"', "sec_ch_ua_platform": '"Linux"'},
    {"name": "Chrome 120 (Linux Ubuntu)", "impersonate": "chrome120",
     "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
     "sec_ch_ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"', "sec_ch_ua_platform": '"Linux"'},
    {"name": "Chrome 119 (Linux Debian)", "impersonate": "chrome119",
     "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
     "sec_ch_ua": '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"', "sec_ch_ua_platform": '"Linux"'},
    {"name": "Chrome 116 (Linux Fedora)", "impersonate": "chrome116",
     "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
     "sec_ch_ua": '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"', "sec_ch_ua_platform": '"Linux"'},
    {"name": "Opera 109 (Windows 10)", "impersonate": "chrome124",
     "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 OPR/109.0.0.0",
     "sec_ch_ua": '"Chromium";v="124", "Opera";v="109", "Not-A.Brand";v="99"', "sec_ch_ua_platform": '"Windows"'},
    {"name": "Opera 106 (Windows 10)", "impersonate": "chrome120",
     "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0",
     "sec_ch_ua": '"Not_A Brand";v="8", "Chromium";v="120", "Opera";v="106"', "sec_ch_ua_platform": '"Windows"'},
    {"name": "Cốc Cốc Browser (Windows 10)", "impersonate": "chrome120",
     "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.217 CocCoc/114.0.184 Safari/537.36",
     "sec_ch_ua": '"Not_A Brand";v="8", "Chromium";v="120", "CocCoc";v="114"', "sec_ch_ua_platform": '"Windows"'},
]

def parse_range_input(input_val, default_min=10, default_max=10):
    val_str = str(input_val).strip()
    if not val_str:
        return default_min, default_max
    if '-' in val_str:
        parts = val_str.split('-')
        try:
            min_v = int(parts[0].strip())
            max_v = int(parts[1].strip())
            return (min_v, max_v) if min_v <= max_v else (max_v, min_v)
        except Exception:
            return default_min, default_max
    try:
        single = int(val_str)
        return single, single
    except Exception:
        return default_min, default_max

def get_random_delay(range_tuple):
    return random.randint(range_tuple[0], range_tuple[1])

def banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"""{cyan}
 ████████╗ █████╗     ████████╗ ██████╗  ██████╗ ██╗     
 ╚══██╔══╝██╔══██╗    ╚══██╔══╝██╔═══██╗██╔═══██╗██║     
    ██║   ███████║       ██║   ██║   ██║██║   ██║██║     
    ██║   ██╔══██║       ██║   ██║   ██║██║   ██║██║     
    ██║   ██║  ██║       ██║   ╚██████╔╝╚██████╔╝███████╗
    ╚═╝   ╚═╝  ╚═╝       ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝{reset}
{yellow} ┌────────────────────────────────────────────────────────┐
{yellow} │ {green}🚀 TOOL INSTAGRAM AUTO JOBS {white}- {cam}XSMM API MULTI-THREAD V2{yellow}│
{yellow} │ {pink}📌 Bản quyền: {white}TA Tool                                  {yellow}│
{yellow} │ {cyan}☕ Donate MoMo: {green}0373607456                             {yellow}│
{yellow} └────────────────────────────────────────────────────────┘{reset}
""")

class XSMMTool:
    def __init__(self, token):
        self.base_url = "https://xsmm.net/api/taskapi"
        self.headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def get_user_info(self):
        try:
            response = requests.get(f"{self.base_url}/user", headers=self.headers, timeout=20)
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def get_accounts(self, account_type=None, search=None):
        url = f"{self.base_url}/accounts2"
        params = {}
        if account_type:
            params['account_type'] = account_type
        if search:
            params['search'] = search
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=20)
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def add_account(self, account_type, link_account):
        payload = {"type": account_type, "link_account": link_account}
        try:
            response = requests.post(f"{self.base_url}/accounts2", headers=self.headers, json=payload, timeout=20)
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def get_tasks(self, job_type, uid, typejob="normal,better,best"):
        params = {"type": job_type, "uid": str(uid), "typejob": typejob}
        try:
            response = requests.get(f"{self.base_url}/tasks2", headers=self.headers, params=params, timeout=20)
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def complete_tasks(self, job_type, task_ids, uid, cookie_check="", max_retries=3):
        payload = {
            "type": job_type,
            "task_id": task_ids if isinstance(task_ids, list) else [task_ids],
            "uid": str(uid)
        }
        if cookie_check:
            payload["cookie_check"] = cookie_check
        
        attempt = 0
        while attempt < max_retries:
            try:
                response = requests.post(f"{self.base_url}/tasks2/complete", headers=self.headers, json=payload, timeout=35)
                res_data = response.json()
                
                if isinstance(res_data, dict) and res_data.get("retry") is True:
                    retry_wait = random.randint(10, 15)
                    print(f"\n{yellow} ⏩ [Retry=True] Đợi {retry_wait}s trước khi gửi lại yêu cầu duyệt xu (lần {attempt + 1})...{white}")
                    time.sleep(retry_wait)
                    attempt += 1
                    continue
                    
                return res_data
            except requests.exceptions.Timeout:
                return {"is_timeout": True, "message": f"Server phản hồi chậm nhưng đã gửi duyệt {len(payload['task_id'])} job thành công"}
            except Exception as e:
                return {"error": str(e)}
                
        return {"error": "Đã thử lại nhiều lần nhưng không thành công"}

def format_proxy(proxy_str):
    if not proxy_str:
        return None
    proxy_str = proxy_str.strip()
    if not proxy_str:
        return None
    scheme = "http"
    if "://" in proxy_str:
        scheme, proxy_str = proxy_str.split("://", 1)
    parts = proxy_str.split(":")
    if len(parts) == 4:
        ip, port, user, pwd = parts
        formatted = f"{scheme}://{user}:{pwd}@{ip}:{port}"
    else:
        formatted = f"{scheme}://{proxy_str}"
    return {"http": formatted, "https": formatted}

def get_ig_headers(cookie, csrftoken, referer="https://www.instagram.com/", profile=None):
    if not profile:
        profile = BROWSER_PROFILES[0]
    return {
        'accept': '*/*',
        'accept-language': 'vi,en-US;q=0.9,en;q=0.8,vi-VN;q=0.7',
        'content-type': 'application/x-www-form-urlencoded',
        'cookie': cookie,
        'origin': 'https://www.instagram.com',
        'priority': 'u=1, i',
        'referer': referer,
        'sec-ch-prefers-color-scheme': 'dark',
        'sec-ch-ua': profile['sec_ch_ua'],
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': profile['sec_ch_ua_platform'],
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': profile['user_agent'],
        'x-asbd-id': '359341',
        'x-csrftoken': csrftoken,
        'x-ig-app-id': '936619743392459',
        'x-ig-www-claim': '0',
        'x-requested-with': 'XMLHttpRequest'
    }

def loadtime(time_delay, msg="Delay Tránh Block"):
    try:
        delay_int = int(time_delay)
    except Exception:
        delay_int = 10
    for x in range(delay_int, 0, -1):
        for color_code, dash_color in [
            ("\033[1;32m", "\033[1;33m"),
            ("\033[1;36m", "\033[1;34m"),
            ("\033[1;34m", "\033[1;31m"),
            ("\033[1;33m", "\033[1;32m"),
            ("\033[1;31m", "\033[1;36m")
        ]:
            sys.stdout.write("\r                                                                      \r")
            sys.stdout.write(f"{color_code}🇻🇳 TA Tool \033[1;37m- \033[1;32m{msg}: \033[1;37m{x} {dash_color}Giây")
            sys.stdout.flush()
            time.sleep(0.2)
    sys.stdout.write("\r                                                                      \r")
    sys.stdout.flush()

def parse_follow_response(response_text):
    try:
        g = json.loads(response_text)
    except Exception as e:
        return False, f"Lỗi parse JSON: {e}"

    if not isinstance(g, dict):
        return False, "Phản hồi không hợp lệ"

    if "errors" in g and g["errors"]:
        err_msg = g["errors"][0].get("message", "Lỗi GraphQL") if isinstance(g["errors"], list) else str(g["errors"])
        return False, f"Instagram báo lỗi: {err_msg}"

    if g.get("status") == "fail":
        return False, f"Instagram thất bại: {g.get('message', 'status fail')}"

    data = g.get("data")
    if not data:
        return False, "Instagram không trả về data"

    friendship = None
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, dict) and "friendship_status" in v:
                friendship = v.get("friendship_status")
                break
            elif k == "friendship_status" and isinstance(v, dict):
                friendship = v
                break

    if friendship and isinstance(friendship, dict):
        if friendship.get("outgoing_request") is True:
            return False, "Tài khoản Riêng tư (Private) - Chỉ gửi yêu cầu chờ duyệt, chưa follow thật!"
        if friendship.get("following") is True:
            return True, "Thành công"
        return False, "Instagram chưa xác nhận theo dõi (following: false)"

    if g.get("status") in ["ok", "success"]:
        return True, "Thành công"

    return False, "Không xác định được trạng thái follow"

def parse_tym_cmt_response(response_text):
    try:
        g = json.loads(response_text)
    except Exception as e:
        return False, f"Lỗi parse JSON: {e}"
    if not isinstance(g, dict):
        return False, "Phản hồi không hợp lệ"
    if "errors" in g and g["errors"]:
        err_msg = g["errors"][0].get("message", "Lỗi GraphQL") if isinstance(g["errors"], list) else str(g["errors"])
        return False, err_msg
    if g.get("status") == "fail":
        return False, g.get("message", "Instagram báo fail")
    if g.get("data") is None and g.get("status") != "ok":
        return False, "Không có data phản hồi"
    return True, "Thành công"

def check_cookie_ig(cookie, proxy=None, profile=None):
    if not profile:
        profile = BROWSER_PROFILES[0]
    url = 'https://www.instagram.com/api/v1/accounts/edit/web_form_data/'
    headers = {
        'x-ig-app-id': '936619743392459',
        'x-requested-with': 'XMLHttpRequest',
        'referer': 'https://www.instagram.com/accounts/edit/',
        'cookie': cookie,
        'user-agent': profile['user_agent'],
        'sec-ch-ua': profile['sec_ch_ua'],
        'sec-ch-ua-platform': profile['sec_ch_ua_platform']
    }
    proxies = format_proxy(proxy)
    try:
        return c_requests.get(url, headers=headers, proxies=proxies, impersonate=profile["impersonate"], timeout=30).text
    except Exception:
        return "{}"

def luot_news_reels_full_simulation(cookie, proxy=None, profile=None, delay_range=(5, 10)):
    if not profile:
        profile = BROWSER_PROFILES[0]
    session = c_requests.Session()
    proxies = format_proxy(proxy)
    if proxies:
        session.proxies = proxies
        
    for item in unquote(cookie).split(';'):
        if '=' in item:
            try:
                key, val = item.strip().split('=', 1)
                session.cookies.set(key, val, domain='.instagram.com')
            except Exception:
                pass
                
    csf_match = re.search(r'csrftoken=([^;]+)', cookie)
    csrftoken = csf_match.group(1) if csf_match else "missing"
    actor_id_match = re.search(r'ds_user_id=(\d+)', cookie)
    actor_id = actor_id_match.group(1) if actor_id_match else "0"
    
    fb_dtsg, lsd, jazoest = get_tokens_for_account(session, cookie, "https://www.instagram.com/", profile["impersonate"])
    stay_time = get_random_delay(delay_range)
    
    action_type = random.choice(["news", "reels"])
    if action_type == "news":
        print(f"\n{pink} 🌐 [Hành vi thật] Đang nạp bảng tin Newsfeed & GraphQL ({stay_time}s)...{white}")
        session.headers.update(get_ig_headers(cookie, csrftoken, "https://www.instagram.com/", profile=profile))
        session.headers.update({'x-fb-friendly-name': 'IGDBadgeCountOffMsysQuery', 'x-fb-lsd': lsd})
        payload_feed = {
            "av": actor_id, "__d": "www", "__user": "0", "__a": "1", "__req": "2",
            "dpr": "1.25", "__ccg": "EXCELLENT", "__comet_req": "7", "fb_dtsg": fb_dtsg,
            "jazoest": jazoest, "lsd": lsd, "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "IGDBadgeCountOffMsysQuery", "server_timestamps": "true",
            "variables": json.dumps({"device_id_for_iris_subscription": f"{random.randint(10000000, 99999999)}-3495-4a48-a45f-01b69ca5552b"}),
            "doc_id": "27393860900250970"
        }
        try:
            session.post("https://www.instagram.com/api/graphql", data=payload_feed, impersonate=profile["impersonate"], timeout=15)
        except Exception:
            pass
    else:
        print(f"\n{pink} 🎬 [Hành vi thật] Đang lướt xem video Reels qua GraphQL ({stay_time}s)...{white}")
        session.headers.update(get_ig_headers(cookie, csrftoken, "https://www.instagram.com/reels/", profile=profile))
        session.headers.update({'x-fb-friendly-name': 'PolarisClipsAdsPoolQuery', 'x-fb-lsd': lsd, 'x-root-field-name': 'xdt_injected_reels_units'})
        payload_reels = {
            "av": actor_id, "__d": "www", "__user": "0", "__a": "1", "__req": "1m",
            "dpr": "1.25", "__ccg": "EXCELLENT", "__comet_req": "7", "fb_dtsg": fb_dtsg,
            "jazoest": jazoest, "lsd": lsd, "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "PolarisClipsAdsPoolQuery", "server_timestamps": "true",
            "variables": json.dumps({
                "api_request": {
                    "client_view_state_media_list": [], "container_module": "reels_tab",
                    "paging_token": "{\"total_num_items\":0}", "skip_ad_insertion": False,
                    "current_time_in_seconds_since_midnight": random.randint(30000, 85000), "organic_item_ids": []
                },
                "is_ads_enabled": True, "__relay_internal__pv__PolarisShortDramaEnabledrelayprovider": True
            }),
            "doc_id": "39220144174236415"
        }
        try:
            session.post("https://www.instagram.com/graphql/query", data=payload_reels, impersonate=profile["impersonate"], timeout=15)
        except Exception:
            pass

    try:
        route_rand = random.choice(["kina.xd", "jun.0408", "instagram", "explore"])
        session.headers.update(get_ig_headers(cookie, csrftoken, "https://www.instagram.com/", profile=profile))
        session.headers.update({'x-ig-d': 'www', 'x-fb-lsd': lsd})
        payload_routes = {
            "route_urls[0]": f"/stories/{route_rand}/?r=1",
            "__d": "www", "__user": "0", "__a": "1", "__req": "3d", "dpr": "1",
            "__ccg": "EXCELLENT", "__rev": "1049835850", "fb_dtsg": fb_dtsg,
            "jazoest": jazoest, "lsd": lsd, "__comet_req": "7"
        }
        session.post("https://www.instagram.com/ajax/bulk-route-definitions/", data=payload_routes, impersonate=profile["impersonate"], timeout=10)
    except Exception:
        pass

    try:
        fake_vi = str(random.randint(3900000000000000000, 4000000000000000000))
        fake_si = f"{random.randint(100000, 999999)}a{random.randint(100, 999)}b{random.randint(10, 99)}"
        cvc_payload = {
            "d": json.dumps({
                "pps": None,
                "ps": {"m": True, "pf": 0, "s": "playing", "sa": 0},
                "si": fake_si, "so": "inline::inline", "vi": fake_vi
            }),
            "__d": "www", "__user": "0", "__a": "1", "__req": "3h", "dpr": "1",
            "__ccg": "EXCELLENT", "fb_dtsg": fb_dtsg, "jazoest": jazoest, "lsd": lsd, "__comet_req": "7"
        }
        session.post("https://www.instagram.com/video/unified_cvc/", data=cvc_payload, impersonate=profile["impersonate"], timeout=10)
    except Exception:
        pass

    try:
        session_id_rand = f"{random.randint(100000, 999999)}:{random.randint(100000, 999999)}:{random.randint(100000, 999999)}"
        telemetry_message = {
            "app_id": "936619743392459", "app_uid": actor_id, "app_ver": "1.0.0",
            "data": [{
                "extra": {
                    "reason": "autoplay", "seq_num": 1, "time": 0, "video_width": 720,
                    "m_pk": fake_vi, "playback_format": "dash"
                },
                "name": "video_started_playing", "time": time.time(), "module": "feed_timeline"
            }],
            "device_id": f"{random.randint(10000000, 99999999)}-F3E1-45ED-B368-822DCF85967A",
            "log_type": "client_event", "session_id": session_id_rand
        }
        headers_telemetry = {
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://www.instagram.com', 'referer': 'https://www.instagram.com/',
            'user-agent': profile['user_agent'], 'x-asbd-id': '359341', 'x-web-session-id': session_id_rand
        }
        session.post(
            "https://graph.instagram.com/logging_client_events",
            data={
                "access_token": "936619743392459|3cdb3f896252a1db29679cb4554db266",
                "message": json.dumps(telemetry_message)
            },
            headers=headers_telemetry,
            impersonate=profile["impersonate"],
            timeout=10
        )
    except Exception:
        pass

    loadtime(stay_time, msg="Lướt News/Reels Đầy Đủ Telemetry")
    print(f"{green} ✔ Hoàn tất ngụy trang đầy đủ phiên duyệt web thật! Tiếp tục làm việc...{white}\n")

def follow(target_id, cookie, csrftoken, profile_url="", proxy=None, profile=None):
    if not profile:
        profile = BROWSER_PROFILES[0]
    if not target_id:
        return '{"status": "error", "message": "Lỗi Target ID"}'
    cookie = unquote(cookie)
    session = c_requests.Session()
    proxies = format_proxy(proxy)
    if proxies:
        session.proxies = proxies
    for item in cookie.split(';'):
        if '=' in item:
            try:
                key, val = item.strip().split('=', 1)
                session.cookies.set(key, val, domain='.instagram.com')
            except Exception:
                pass
                
    fb_dtsg, lsd, jazoest = get_tokens_for_account(session, cookie, profile_url, profile["impersonate"])
    
    dynamic_csrftoken = session.cookies.get('csrftoken')
    if not dynamic_csrftoken:
        csf_match = re.search(r'csrftoken=([^;]+)', cookie)
        dynamic_csrftoken = csf_match.group(1) if csf_match else "missing"
    session.headers.update(get_ig_headers(cookie, dynamic_csrftoken, profile_url if profile_url else "https://www.instagram.com/", profile=profile))
    actor_id_match = re.search(r'ds_user_id=(\d+)', cookie)
    actor_id = actor_id_match.group(1) if actor_id_match else "0"
    variables = {
        "target_user_id": str(target_id),
        "container_module": "profile",
        "nav_chain": "PolarisFeedRoot:feedPage:5:topnav-link,PolarisProfileRoot:profilePage:6:unexpected"
    }
    data = {
        "av": actor_id, "__d": "www", "__user": "0", "__a": "1", "__req": "s",
        "__hs": "20702.HYP:instagram_web_pkg.2.1...0", "dpr": "1", "__ccg": "EXCELLENT",
        "__rev": "1046917461", "__comet_req": "7", "fb_dtsg": fb_dtsg, "jazoest": jazoest,
        "lsd": lsd, "fb_api_caller_class": "RelayModern", "fb_api_req_friendly_name": "usePolarisFollowMutation",
        "server_timestamps": "true", "doc_id": "26508036048874888", "variables": json.dumps(variables)
    }
    
    for attempt in range(2):
        try:
            res_gql = session.post('https://www.instagram.com/api/graphql', data=data, impersonate=profile["impersonate"], timeout=30)
            return res_gql.text.strip()
        except Exception as e:
            if attempt == 0 and ("timed out" in str(e).lower() or "curl: (28)" in str(e).lower()):
                time.sleep(2)
                continue
            return json.dumps({"status": "error", "message": str(e)})

def tym(mediaid, cookie, csrftoken, link_job="", proxy=None, profile=None):
    if not profile:
        profile = BROWSER_PROFILES[0]
    if not mediaid:
        return '{"status": "error", "message": "Lỗi Media ID"}'
    cookie = unquote(cookie)
    session = c_requests.Session()
    proxies = format_proxy(proxy)
    if proxies:
        session.proxies = proxies
    for item in cookie.split(';'):
        if '=' in item:
            try:
                key, val = item.strip().split('=', 1)
                session.cookies.set(key, val, domain='.instagram.com')
            except Exception:
                pass
                
    fb_dtsg, lsd, jazoest = get_tokens_for_account(session, cookie, link_job, profile["impersonate"])
    
    dynamic_csrftoken = session.cookies.get('csrftoken')
    if not dynamic_csrftoken:
        csf_match = re.search(r'csrftoken=([^;]+)', cookie)
        dynamic_csrftoken = csf_match.group(1) if csf_match else "missing"
    session.headers.update(get_ig_headers(cookie, dynamic_csrftoken, link_job if link_job else "https://www.instagram.com/", profile=profile))
    actor_id_match = re.search(r'ds_user_id=(\d+)', cookie)
    actor_id = actor_id_match.group(1) if actor_id_match else "0"
    
    variables = {
        "input": {
            "actor_id": actor_id, "client_mutation_id": str(random.randint(1000000, 9999999)),
            "container_module": "single_post", "media_id": str(mediaid)
        }
    }
    data = {
        "av": actor_id, "__d": "www", "__user": "0", "__a": "1", "__req": "h",
        "__hs": "20702.HYP:instagram_web_pkg.2.1...0", "dpr": "1", "__ccg": "EXCELLENT",
        "__rev": "1046913831", "__comet_req": "7", "fb_dtsg": fb_dtsg, "jazoest": jazoest,
        "lsd": lsd, "fb_api_caller_class": "RelayModern", "fb_api_req_friendly_name": "usePolarisLikeMediaXIGLikeMutation",
        "server_timestamps": "true", "doc_id": "27182485238052618", "variables": json.dumps(variables)
    }
    
    for attempt in range(2):
        try:
            res_gql = session.post('https://www.instagram.com/api/graphql', data=data, impersonate=profile["impersonate"], timeout=30)
            return res_gql.text.strip()
        except Exception as e:
            if attempt == 0 and ("timed out" in str(e).lower() or "curl: (28)" in str(e).lower()):
                time.sleep(2)
                continue
            return json.dumps({"status": "error", "message": str(e)})

def cmt(mediaid, text, cookie, csrftoken, link_job="", proxy=None, profile=None):
    if not profile:
        profile = BROWSER_PROFILES[0]
    if not mediaid:
        return '{"status": "error", "message": "Lỗi Media ID"}'
    cookie = unquote(cookie)
    session = c_requests.Session()
    proxies = format_proxy(proxy)
    if proxies:
        session.proxies = proxies
    for item in cookie.split(';'):
        if '=' in item:
            try:
                key, val = item.strip().split('=', 1)
                session.cookies.set(key, val, domain='.instagram.com')
            except Exception:
                pass
                
    fb_dtsg, lsd, jazoest = get_tokens_for_account(session, cookie, link_job, profile["impersonate"])
    
    dynamic_csrftoken = session.cookies.get('csrftoken')
    if not dynamic_csrftoken:
        csf_match = re.search(r'csrftoken=([^;]+)', cookie)
        dynamic_csrftoken = csf_match.group(1) if csf_match else "missing"
    session.headers.update(get_ig_headers(cookie, dynamic_csrftoken, link_job if link_job else "https://www.instagram.com/", profile=profile))
    actor_id_match = re.search(r'ds_user_id=(\d+)', cookie)
    actor_id = actor_id_match.group(1) if actor_id_match else "0"
    variables = {
        "connections": [f"client:root:__PolarisPostComments__xdt_api__v1__media__media_id__comments__connection_connection(data:{{}},media_id:\"{mediaid}\",sort_order:\"popular\")"],
        "data": {"comment_text": text, "media_id": str(mediaid)}
    }
    data = {
        "av": actor_id, "__d": "www", "__user": "0", "__a": "1", "__req": "10",
        "__hs": "20702.HYP:instagram_web_pkg.2.1...0", "dpr": "1", "__ccg": "EXCELLENT",
        "__rev": "1046917461", "__comet_req": "7", "fb_dtsg": fb_dtsg, "jazoest": jazoest,
        "lsd": lsd, "fb_api_caller_class": "RelayModern", "fb_api_req_friendly_name": "PolarisPostCommentInputRevampedMutation",
        "server_timestamps": "true", "doc_id": "27261905640092552", "variables": json.dumps(variables)
    }
    
    for attempt in range(2):
        try:
            res_gql = session.post('https://www.instagram.com/api/graphql', data=data, impersonate=profile["impersonate"], timeout=30)
            return res_gql.text.strip()
        except Exception as e:
            if attempt == 0 and ("timed out" in str(e).lower() or "curl: (28)" in str(e).lower()):
                time.sleep(2)
                continue
            return json.dumps({"status": "error", "message": str(e)})

def gui_nhan_xu(job_type, task_list, uid, cookie_check, xsmm_instance):
    if not task_list:
        return
    sys.stdout.write("\r                                              \r")
    print(f"{yellow} ⏩ Gom đủ {len(task_list)} task -> Đang gửi duyệt nhận xu...{white}")
    ck = xsmm_instance.complete_tasks(job_type, task_list, uid=uid, cookie_check=cookie_check)
    now = datetime.now().strftime("%H:%M:%S")
    
    if isinstance(ck, dict):
        if 'message' in ck:
            pts = ck.get('points', 0)
            succ = ck.get('success_count', len(task_list))
            print(f"[{now}] {green} ⏩ {ck['message']} (+{pts} xu | Hoàn thành: {succ}/{len(task_list)} task){white}")
        elif ck.get("is_timeout"):
            print(f"[{now}] {cam} ⏩ {ck['message']}{white}")
        elif 'error' in ck:
            print(f"[{now}] {red} ⏩ LỖI XSMM: {ck['error']}{white}")
        
        if ck.get('countdown', 0) > 0:
            print(f"{yellow} ⏩ Hệ thống yêu cầu nghỉ {ck['countdown']}s...{white}")
            time.sleep(ck['countdown'])

# ================= MAIN RUN =================
banner()

xsmm_token = ""
xu = 0
username = "Unknown"

if os.path.exists("logXSMM.txt"):
    while True:
        print(f"{white} Nhập{cam} Enter{white} để dùng token XSMM đã lưu! {xuong} Nhập{red} No{white} để nhập lại Token : ", end="")
        nhap = input().strip().lower()
        if nhap in ['', 'no']:
            break
        print(f"{red}Sai Định Dạng\n")
        
    if nhap == 'no':
        xsmm_token = input(f"{white} ⏩ {green}Access Token XSMM: ").strip()
        with open("logXSMM.txt", "w") as f:
            json.dump({"token": xsmm_token}, f)
    else:
        with open("logXSMM.txt", "r") as f:
            acc = json.load(f)
            xsmm_token = acc.get("token", "")
else:
    xsmm_token = input(f"{white} ⏩ {green}Access Token XSMM: ").strip()
    with open("logXSMM.txt", "w") as f:
        json.dump({"token": xsmm_token}, f)

xsmm = XSMMTool(token=xsmm_token)
user_info = xsmm.get_user_info()

if isinstance(user_info, dict) and "user" in user_info:
    xu = user_info["user"].get("points", 0)
    username = user_info["user"].get("username", "Unknown")
    print(f"\n{white} ✅ {green}Đăng nhập XSMM thành công: {yellow}{username}{white}\n")
else:
    print(f"\n{red} ❌ Token sai hoặc đã hết hạn\n")
    if os.path.exists("logXSMM.txt"):
        os.remove("logXSMM.txt")
    sys.exit()

cookie_check_file = "cookie_check_ig.txt"
cookie_check_global = ""

if os.path.exists(cookie_check_file):
    try:
        with open(cookie_check_file, "r", encoding="utf-8") as f:
            cookie_check_global = f.read().strip()
    except Exception:
        cookie_check_global = ""

print(f"{yellow} ┌────────────────────────────────────────────────────────┐")
print(f" │ {green}⚙  CẤU HÌNH COOKIE CHECK JOBS (WEB BROWSER / BOT)      {yellow}│")
print(f" └────────────────────────────────────────────────────────┘{reset}")

if cookie_check_global:
    ck_short = cookie_check_global[:28] + "..." if len(cookie_check_global) > 28 else cookie_check_global
    print(f"{white} Cookie Check hiện tại: {cyan}{ck_short}{white}")
    print(f" [{green}Enter{white}] Giữ nguyên và dùng tiếp")
    print(f" [{cyan}1{white}]     Thay Cookie Check Jobs mới (Trình duyệt Web)")
    print(f" [{red}0{white}]     Tắt Cookie Check riêng (Dùng chính Cookie của nick chạy)")
    print(f"{yellow} ────────────────────────────────────────────────────────{reset}")
    nhap_ck = input(f"{cam}👉 Chọn thao tác (Mặc định Enter): {white}").strip()
    if nhap_ck == '1':
        cookie_check_global = input(f"\n{white} ⏩ {green}Dán Cookie Trình Duyệt Web để Check: {white}").strip()
        with open(cookie_check_file, "w", encoding="utf-8") as f:
            f.write(cookie_check_global)
        print(f"{green} ✔ Đã cập nhật Cookie Check Jobs thành công!{white}\n")
    elif nhap_ck == '0':
        cookie_check_global = ""
        if os.path.exists(cookie_check_file):
            os.remove(cookie_check_file)
        print(f"{yellow} ⚠️ Đã tắt Cookie Check riêng! Sẽ dùng Cookie App của từng nick để check.{white}\n")
    else:
        print(f"{green} ✔ Đang dùng Cookie Check Jobs đã lưu.{white}\n")
else:
    print(f"{white} Bạn có muốn dùng {green}Cookie Trình Duyệt Web riêng{white} để Check Jobs không?")
    print(f"{gray} (Giải pháp: Làm jobs bằng Cookie App, Check jobs bằng Cookie Web bot thay thế){white}")
    nhap_them = input(f"{cam}👉 Nhập [1] để thêm Cookie Check Web, [Enter] để bỏ qua: {white}").strip()
    if nhap_them == '1':
        cookie_check_global = input(f"{white} ⏩ {green}Dán Cookie Web Browser vào đây: {white}").strip()
        if cookie_check_global:
            with open(cookie_check_file, "w", encoding="utf-8") as f:
                f.write(cookie_check_global)
            print(f"{green} ✔ Đã lưu Cookie Check Jobs thành công!{white}\n")
    else:
        print(f"{yellow} ⚠️ Sẽ dùng trực tiếp Cookie App của từng nick để gửi duyệt.{white}\n")

print(f"{yellow} ┌────────────────────────────────────────────────────────┐")
print(f" │ {green}👤 THÊM / CẬP NHẬT TRẠNG THÁI NICK THỦ CÔNG (XSMM)      {yellow}│")
print(f" └────────────────────────────────────────────────────────┘{reset}")
print(f" [{green}Enter{white}] Bỏ qua và vào luôn")
print(f" [{cyan}1{white}]     Thêm / Cập nhật lại nick bằng UID chữ (Username IG)")
print(f"{yellow} ────────────────────────────────────────────────────────{reset}")
chon_add_manual = input(f"{cam}👉 Chọn thao tác (Mặc định Enter): {white}").strip()

if chon_add_manual == '1':
    while True:
        print(f"{white} ⏩ {green}Nhập UID dạng chữ (Username IG) cần thêm/update {pink}(Enter để dừng){white}: ", end="")
        uid_chu = input().strip()
        if not uid_chu:
            break
        clean_user = uid_chu.replace("https://www.instagram.com/", "").replace("http://www.instagram.com/", "").strip("/").replace("@", "")
        if clean_user:
            link_account = f"https://www.instagram.com/{clean_user}"
            print(f"{yellow} ⏳ Đang gửi API thêm/cập nhật tài khoản [{clean_user}] lên server XSMM...{white}")
            res_add = xsmm.add_account("instagram", link_account)
            if isinstance(res_add, dict):
                if "error" in res_add:
                    print(f"{red} ❌ Server báo lỗi: {res_add['error']}{white}\n")
                elif "message" in res_add:
                    print(f"{green} ✔ Phản hồi từ XSMM: {res_add['message']}{white}\n")
                else:
                    print(f"{green} ✔ Đã thêm/cập nhật trạng thái thành công: {res_add}{white}\n")
            else:
                print(f"{green} ✔ Kết quả phản hồi: {res_add}{white}\n")
    print(f"{green} ✔ Đã hoàn tất thêm tài khoản thủ công! Tiếp tục cấu hình...{white}\n")

nhaplaicc = False
mangcookie = []

if os.path.exists("ListccXSMM.json"):
    while True:
        print(f"{white} Nhập{cam} Enter{white} để dùng list cookies đã lưu! {xuong} Nhập{red} 1{white} để nhập lại list cookie : ", end="")
        nhapcc = input().strip()
        if nhapcc in ['', '1']:
            break
        print(f"{red}Sai lựa chọn\n")
        
    if nhapcc == '':
        try:
            with open("ListccXSMM.json", "r", encoding="utf-8") as f:
                listccdaluu = json.load(f)
            for acc_item in listccdaluu:
                cc = acc_item.get("cookie", "")
                px = acc_item.get("proxy", "")
                prof = acc_item.get("profile") or random.choice(BROWSER_PROFILES)
                if not cc:
                    continue
                access = check_cookie_ig(cc, px, profile=prof)
                try:
                    configdata = json.loads(access)
                    if configdata and 'form_data' in configdata and configdata['form_data'].get('username'):
                        mangcookie.append({"cookie": cc, "proxy": px, "profile": prof})
                except Exception:
                    pass
            luong = len(mangcookie)
        except Exception:
            nhaplaicc = True
    else:
        nhaplaicc = True
elif os.path.exists("ListccXSMM.txt"):
    try:
        with open("ListccXSMM.txt", "r") as f:
            listccdaluu = f.read().splitlines()
        for cc in listccdaluu:
            if not cc:
                continue
            prof = random.choice(BROWSER_PROFILES)
            access = check_cookie_ig(cc, profile=prof)
            try:
                configdata = json.loads(access)
                if configdata and 'form_data' in configdata and configdata['form_data'].get('username'):
                    mangcookie.append({"cookie": cc, "proxy": "", "profile": prof})
            except Exception:
                pass
        luong = len(mangcookie)
        with open("ListccXSMM.json", "w", encoding="utf-8") as f:
            json.dump(mangcookie, f)
        os.remove("ListccXSMM.txt")
    except Exception:
        nhaplaicc = True
else:
    nhaplaicc = True

if nhaplaicc:
    if os.path.exists("ListccXSMM.json"):
        os.remove("ListccXSMM.json")
    if os.path.exists("ListccXSMM.txt"):
        os.remove("ListccXSMM.txt")
        
    while True:
        print(f"{white} ✏ {blue}Nhập số nick INSTA muốn chạy: ", end="")
        try:
            luong = int(input().strip())
            if 1 <= luong <= 2000:
                break
            print(f"{red}Ít nhất là 1 và nhiều nhất là 2000!\n")
        except Exception:
            print(f"{red}Nhập số hợp lệ!")

    thu = 1
    c = 1
    while c <= luong:
        print(f"{white} + {green}Nhập Cookie App Thứ {thu}:{white} ", end="")
        cookie_str = input().strip()
        print(f"{white}   {cyan}Nhập Proxy cho Nick {thu} {pink}(Enter để bỏ qua){white}: ", end="")
        proxy_str = input().strip()
        
        assigned_profile = random.choice(BROWSER_PROFILES)
        access = check_cookie_ig(cookie_str, proxy_str, profile=assigned_profile)
        try:
            configdata = json.loads(access)
            if configdata and 'form_data' in configdata and configdata['form_data'].get('username'):
                mangcookie.append({"cookie": cookie_str, "proxy": proxy_str, "profile": assigned_profile})
                with open("ListccXSMM.json", "w", encoding="utf-8") as f:
                    json.dump(mangcookie, f)
                c += 1
                thu += 1
            else:
                print(f"{white} ⛔ {red}Cookie hoặc Proxy lỗi, thử lại đi \n")
        except Exception:
            print(f"{white} ⛔ {red}Cookie hoặc Proxy lỗi, thử lại đi \n")

dl = 0
doi = 99999
if len(mangcookie) == 1:
    print(f"{white} ⏩ {blue}Hết nhiệm vụ hoặc lỗi thì dừng bao lâu? : {white}", end="")
    try:
        dl = int(input().strip())
    except Exception:
        dl = 150
else:
    while True:
        dl = 150
        print(f"{white} ⏩ {blue}Sau bao nhiêu nhiệm vụ thì đổi nick : {white}", end="")
        try:
            doi = int(input().strip())
            if doi >= 1:
                break
            print(f"{red}Lựa chọn không hợp lệ !\n")
        except Exception:
            print(f"{red}Nhập số hợp lệ!")

listnv = []
delay_tym_range = (10, 15)
delay_sub_range = (15, 20)
delay_cmt_range = (20, 25)
batch_sub_count = 10
job_interleave_limits = {}

print(f"\n{yellow} ┌────────────────────────────────────────────────────────┐")
print(f" │ {green}⚙  CẤU HÌNH NGHỈ NGƠI & LƯỚT NEWS/REELS ĐẦY ĐỦ         {yellow}│")
print(f" └────────────────────────────────────────────────────────┘{reset}")

print(f"{white} ⏩ {cyan}Nghỉ ngơi sau bao nhiêu jobs {pink}(vd: 15 hoặc 15-20, Enter để tắt): {white}", end="")
rest_jobs_input = input().strip()
rest_jobs_range = parse_range_input(rest_jobs_input, 0, 0) if rest_jobs_input else (0, 0)

if rest_jobs_range[0] > 0:
    print(f"{white} ⏩ {cyan}Thời gian nghỉ mỗi lần (giây) {pink}(vd: 60 hoặc 60-120): {white}", end="")
    rest_time_range = parse_range_input(input().strip(), 60, 90)
else:
    rest_time_range = (0, 0)

print(f"{white} ⏩ {cyan}Sau bao nhiêu jobs thì lướt News/Reels {pink}(vd: 5 hoặc 5-8, Enter để tắt): {white}", end="")
feed_jobs_input = input().strip()
feed_jobs_range = parse_range_input(feed_jobs_input, 0, 0) if feed_jobs_input else (0, 0)

if feed_jobs_range[0] > 0:
    print(f"{white} ⏩ {cyan}Thời gian lướt mỗi lần (giây) {pink}(vd: 5 hoặc 5-10): {white}", end="")
    feed_time_range = parse_range_input(input().strip(), 5, 10)
else:
    feed_time_range = (0, 0)

print(f"\n{yellow} ┌────────────────────────────────────────────────────────┐")
print(f" │ {green}⚙  CẤU HÌNH JOBS & NHẢY XEN KẼ NGẪU NHIÊN               {yellow}│")
print(f" └────────────────────────────────────────────────────────┘{reset}")

while True:
    print(f"{yellow} ⏩ {blue}Chế độ Tym trên XSMM{pink} (on/off): {white}", end="")
    chon_tym = input().strip().lower()
    if chon_tym == 'on':
        listnv.append('instagram_like')
        print(f"{yellow} ⏩ {blue}Delay Nhiệm Vụ Tym {pink}(vd: 10 hoặc 10-15): {white}", end="")
        delay_tym_range = parse_range_input(input().strip(), 10, 15)
        print(f"{yellow} ⏩ {blue}Số job Tym mỗi lượt trước khi nhảy {pink}(vd: 3 hoặc 3-5): {white}", end="")
        job_interleave_limits['instagram_like'] = parse_range_input(input().strip(), 3, 5)

    print(f"{yellow} ⏩ {blue}Chế độ Follow trên XSMM{pink} (on/off): {white}", end="")
    chon_sub = input().strip().lower()
    if chon_sub == 'on':
        listnv.append('instagram_follow')
        print(f"{yellow} ⏩ {blue}Delay Nhiệm Vụ Follow {pink}(vd: 15 hoặc 15-20): {white}", end="")
        delay_sub_range = parse_range_input(input().strip(), 15, 20)
        print(f"{yellow} ⏩ {blue}Số job Follow mỗi lượt trước khi nhảy {pink}(vd: 4 hoặc 3-6): {white}", end="")
        job_interleave_limits['instagram_follow'] = parse_range_input(input().strip(), 4, 6)
        
        while True:
            print(f"{yellow} ⏩ {blue}Số job Follow gom để nhận xu (từ 3 đến 12, mặc định 10): {white}", end="")
            nhap_batch = input().strip()
            if nhap_batch == "":
                batch_sub_count = 10
                break
            try:
                val = int(nhap_batch)
                if 3 <= val <= 12:
                    batch_sub_count = val
                    break
                print(f"{red}Vui lòng chỉ nhập trong khoảng từ 3 đến 12 !\n")
            except Exception:
                print(f"{red}Nhập số hợp lệ !\n")

    print(f"{yellow} ⏩ {blue}Chế độ Comment trên XSMM{pink} (on/off): {white}", end="")
    chon_cmt = input().strip().lower()
    if chon_cmt == 'on':
        listnv.append('instagram_comment')
        print(f"{yellow} ⏩ {blue}Delay Nhiệm Vụ Cmt {pink}(vd: 20 hoặc 20-30): {white}", end="")
        delay_cmt_range = parse_range_input(input().strip(), 20, 25)
        print(f"{yellow} ⏩ {blue}Số job Cmt mỗi lượt trước khi nhảy {pink}(vd: 2 hoặc 2-3): {white}", end="")
        job_interleave_limits['instagram_comment'] = parse_range_input(input().strip(), 2, 3)

    if len(listnv) == 0:
        print(f"{red}Chọn tối thiểu 1 loại Job !\n")
    else:
        break

banner()
status_ck = f"{green}Đang bật (Web Bot){white}" if cookie_check_global else f"{yellow}Dùng chính Cookie App{white}"

print(f"{cyan} ✅ {cam}XSMM User      : {white}{username}")
print(f"{cyan} ✅ {cam}Số Nick Chạy   : {white}{len(mangcookie)}")
print(f"{cyan} ✅ {cam}Số Dư Ban Đầu  : {green}{xu} xu")
print(f"{cyan} ✅ {cam}Cookie Check   : {status_ck}")
print(f"{cyan} ✅ {cam}Trình Duyệt    : {white}{len(BROWSER_PROFILES)} Profiles ngẫu nhiên")
if 'instagram_follow' in listnv:
    print(f"{cyan} ✅ {cam}Gom Nhận Xu    : {white}{batch_sub_count} jobs/lần (Tự động lọc nick Private)")
if rest_jobs_range[0] > 0:
    print(f"{cyan} ✅ {cam}Nghỉ Ngơi      : {white}Sau {rest_jobs_range[0]}-{rest_jobs_range[1]} jobs -> Nghỉ {rest_time_range[0]}-{rest_time_range[1]}s")
if feed_jobs_range[0] > 0:
    print(f"{cyan} ✅ {cam}Lướt News/Reels: {white}Sau {feed_jobs_range[0]}-{feed_jobs_range[1]} jobs -> Lướt {feed_time_range[0]}-{feed_time_range[1]}s (Full Telemetry)")
print(f"{yellow} ────────────────────────────────────────────────────────{reset}\n")

jobs_since_rest = 0
jobs_since_feed = 0
target_jobs_to_rest = get_random_delay(rest_jobs_range) if rest_jobs_range[0] > 0 else 999999
target_jobs_to_feed = get_random_delay(feed_jobs_range) if feed_jobs_range[0] > 0 else 999999

def check_human_behavior(cookie, proxy, profile):
    global jobs_since_rest, jobs_since_feed, target_jobs_to_rest, target_jobs_to_feed
    
    if feed_jobs_range[0] > 0 and jobs_since_feed >= target_jobs_to_feed:
        luot_news_reels_full_simulation(cookie, proxy=proxy, profile=profile, delay_range=feed_time_range)
        jobs_since_feed = 0
        target_jobs_to_feed = get_random_delay(feed_jobs_range)
        
    if rest_jobs_range[0] > 0 and jobs_since_rest >= target_jobs_to_rest:
        rest_sec = get_random_delay(rest_time_range)
        print(f"\n{cam} ☕ Đã hoàn tất {jobs_since_rest} jobs -> Nghỉ giải lao {rest_sec}s ngẫu nhiên...{white}")
        loadtime(rest_sec, msg="Nghỉ Ngơi Tránh Quét")
        jobs_since_rest = 0
        target_jobs_to_rest = get_random_delay(rest_jobs_range)

while True:
    for l in range(len(mangcookie)-1, -1, -1):
        acc_data = mangcookie[l]
        cookie = acc_data["cookie"]
        proxy = acc_data.get("proxy", "")
        profile = acc_data.get("profile") or BROWSER_PROFILES[0]
        
        target_ck_check = cookie_check_global if cookie_check_global else cookie

        access = check_cookie_ig(cookie, proxy, profile=profile)
        is_live = False
        tenfb = ""
        idfb = ""
        
        try:
            configdata = json.loads(access)
            if configdata and 'form_data' in configdata and configdata['form_data'].get('username'):
                is_live = True
                tenfb = configdata['form_data']['username']
                idfb_match = re.search(r'ds_user_id=(\d+)', cookie)
                idfb = idfb_match.group(1) if idfb_match else str(configdata['form_data'].get('id', ''))
        except Exception:
            is_live = False

        if not is_live or not idfb:
            print(f"{white} ⛔ {red}Cookie Die hoặc Proxy lỗi - ĐANG ĐỔI NICK\n")
            mangcookie.pop(l)
            with open("ListccXSMM.json", "w", encoding="utf-8") as f:
                json.dump(mangcookie, f)
            continue

        px_display = f" | Proxy: {proxy}" if proxy else " | Không Proxy"
        print(f"{green} ● NICK LIVE [{tenfb} | UID: {idfb}{px_display}] ● {cyan}Trình duyệt: {profile['name']}{white}")

        try:
            acc_list = xsmm.get_accounts(account_type="instagram", search=idfb)
            exists = False
            
            if isinstance(acc_list, dict) and acc_list.get("accounts"):
                for acc in acc_list["accounts"]:
                    if acc and (str(acc.get("account_id")) == str(idfb) or str(acc.get("name", "")).lower() == str(tenfb).lower()):
                        exists = True
                        break
                        
            if not exists:
                link_ig = f"https://www.instagram.com/{tenfb}"
                add_res = xsmm.add_account("instagram", link_ig)
                if isinstance(add_res, dict) and "id" in add_res:
                    print(f"{green} ➕ Đã thêm tài khoản [{tenfb}] vào XSMM thành công!{white}")
        except Exception as e:
            print(f"{yellow} ⚠️ Không thể đồng bộ tài khoản: {e}{white}")

        print(f"{white} Bắt đầu nhận việc cho UID: {cam}{idfb} ({tenfb}) [Chế độ nhảy xen kẽ ngẫu nhiên]")
        max_job = 0
        consecutive_empty_all = 0
        
        while max_job < doi:
            current_job_type = random.choice(listnv)
            job_limit = get_random_delay(job_interleave_limits.get(current_job_type, (3, 5)))
            jobs_done_this_turn = 0
            
            if current_job_type == 'instagram_like':
                list_nv = xsmm.get_tasks(current_job_type, uid=idfb)
                if isinstance(list_nv, dict) and "error" in list_nv:
                    print(f"{white} ❌ {red}Lỗi từ XSMM: {list_nv['error']}")
                    time.sleep(3)
                elif isinstance(list_nv, list) and len(list_nv) == 0:
                    consecutive_empty_all += 1
                elif isinstance(list_nv, list):
                    consecutive_empty_all = 0
                    soloitym = 0
                    for nv in list_nv:
                        task_id = nv.get('id')
                        idm = nv.get('target_id', '')
                        link_job = nv.get('target_url', '')
                        csf_match = re.search(r'csrftoken=([^;]+)', cookie)
                        csf = csf_match.group(1) if csf_match else ""
                        
                        print(f"{yellow} ⏩ {blue}[Tym] {white}{link_job} | MediaID: {idm}")
                        chayfl = tym(idm, cookie, csf, link_job, proxy=proxy, profile=profile)
                        max_job += 1
                        jobs_done_this_turn += 1
                        jobs_since_rest += 1
                        jobs_since_feed += 1
                        
                        is_ok, msg_err = parse_tym_cmt_response(chayfl)
                        if is_ok:
                            print(f"{green} ● TYM THÀNH CÔNG -> Đang gửi nhận xu... ● {white}")
                            gui_nhan_xu("instagram_like", [task_id], idfb, target_ck_check, xsmm)
                            soloitym = 0
                        else:
                            print(f"{red} ● TYM LỖI: {msg_err} ● {white}")
                            soloitym += 1
                            
                        current_delay = get_random_delay(delay_tym_range)
                        loadtime(current_delay, msg="Delay Random Tym")
                        check_human_behavior(cookie, proxy, profile)
                        
                        if soloitym > 4 or jobs_done_this_turn >= job_limit or max_job >= doi:
                            break

            elif current_job_type == 'instagram_follow':
                list_nv = xsmm.get_tasks(current_job_type, uid=idfb)
                if isinstance(list_nv, dict) and "error" in list_nv:
                    print(f"{white} ❌ {red}Lỗi từ XSMM: {list_nv['error']}")
                    time.sleep(3)
                elif isinstance(list_nv, list) and len(list_nv) == 0:
                    consecutive_empty_all += 1
                elif isinstance(list_nv, list):
                    consecutive_empty_all = 0
                    soloisub = 0
                    temp_sess = c_requests.Session()
                    proxies = format_proxy(proxy)
                    if proxies:
                        temp_sess.proxies = proxies
                    temp_sess.headers.update({"User-Agent": profile['user_agent']})
                    
                    for nv in list_nv:
                        task_id = nv.get('id')
                        target_id = nv.get('target_id', '')
                        link_job = nv.get('target_url', '')
                        
                        if not target_id or not str(target_id).isdigit():
                            try:
                                res_html = temp_sess.get(link_job, impersonate=profile["impersonate"], timeout=15).text
                                m = re.search(r'"profile_id":"(\d+)"', res_html)
                                if not m:
                                    m = re.search(r'"user_id":"(\d+)"', res_html)
                                if not m:
                                    m = re.search(r'profilePage_(\d+)', res_html)
                                if m:
                                    target_id = m.group(1)
                            except Exception:
                                pass

                        print(f"{yellow} ⏩ {blue}[Follow] Target ID: {white}{target_id} ({link_job})")

                        if not target_id or not str(target_id).isdigit():
                            print(f"{red} ❌ Không trích xuất được ID số, bỏ qua!")
                            continue

                        csf_match = re.search(r'csrftoken=([^;]+)', cookie)
                        csf = csf_match.group(1) if csf_match else ""

                        chay_sub = follow(target_id, cookie, csf, link_job, proxy=proxy, profile=profile)
                        max_job += 1
                        jobs_done_this_turn += 1
                        jobs_since_rest += 1
                        jobs_since_feed += 1

                        is_success, msg_result = parse_follow_response(chay_sub)
                        
                        if is_success:
                            print(f"{green} ✅ Follow ID {target_id} thành công! (Task ID: {task_id}){white}")
                            soloisub = 0
                            
                            add_pending_task(idfb, task_id)
                            pending_now = get_pending_tasks(idfb)
                            print(f"{cyan} 📋 [JSON Queue] UID {idfb} đang gom: {len(pending_now)}/{batch_sub_count} task follow{white}")
                        else:
                            print(f"{red} ❌ Follow ID {target_id} thất bại: {msg_result}{white}")
                            if "Riêng tư (Private)" in msg_result:
                                print(f"{cam} ⚠️ Đã loại bỏ task này khỏi hàng đợi để tránh rớt job khi duyệt xu!{white}")
                            else:
                                soloisub += 1

                        current_delay = get_random_delay(delay_sub_range)
                        loadtime(current_delay, msg="Delay Random Follow")
                        check_human_behavior(cookie, proxy, profile)

                        pending_tasks = get_pending_tasks(idfb)
                        if len(pending_tasks) >= batch_sub_count:
                            tasks_to_claim = pending_tasks[:batch_sub_count]
                            gui_nhan_xu("instagram_follow", tasks_to_claim, idfb, target_ck_check, xsmm)
                            remove_pending_tasks(idfb, tasks_to_claim)
                            print(f"{cyan} 🔄 Đã gửi đợt gom {len(tasks_to_claim)} task và làm sạch hàng đợi JSON!{white}")

                        if soloisub > 4 or jobs_done_this_turn >= job_limit or max_job >= doi:
                            break

            elif current_job_type == 'instagram_comment':
                list_nv = xsmm.get_tasks(current_job_type, uid=idfb)
                if isinstance(list_nv, dict) and "error" in list_nv:
                    print(f"{white} ❌ {red}Lỗi từ XSMM: {list_nv['error']}")
                    time.sleep(3)
                elif isinstance(list_nv, list) and len(list_nv) == 0:
                    consecutive_empty_all += 1
                elif isinstance(list_nv, list):
                    consecutive_empty_all = 0
                    soloicmt = 0
                    temp_sess = c_requests.Session()
                    proxies = format_proxy(proxy)
                    if proxies:
                        temp_sess.proxies = proxies
                    temp_sess.headers.update({"User-Agent": profile['user_agent']})
                    
                    for nv in list_nv:
                        task_id = nv.get('id')
                        idm = nv.get('target_id', '')
                        noidung = nv.get('comment', '❤️❤️❤️')
                        link_job = nv.get('target_url', '')
                            
                        if not idm:
                            try:
                                res_html = temp_sess.get(link_job, impersonate=profile["impersonate"], timeout=15).text
                                m = re.search(r'instagram://media\?id=(\d+)', res_html)
                                if not m:
                                    m = re.search(r'"media_id":"(\d+)"', res_html)
                                if not m:
                                    m = re.search(r'media\?id=(\d+)', res_html)
                                if m:
                                    idm = m.group(1)
                            except Exception:
                                pass

                        print(f"{yellow} ⏩ {blue}[Comment] {white}{link_job} | ND: {noidung}")
                        
                        if not idm:
                            print(f"{red} ● CMT LỖI: Không tìm thấy Media ID ● {white}")
                            soloicmt += 1
                            continue

                        csf_match = re.search(r'csrftoken=([^;]+)', cookie)
                        csf = csf_match.group(1) if csf_match else ""

                        chay_cmt = cmt(idm, noidung, cookie, csf, link_job, proxy=proxy, profile=profile)
                        max_job += 1
                        jobs_done_this_turn += 1
                        jobs_since_rest += 1
                        jobs_since_feed += 1
                        
                        is_ok, msg_err = parse_tym_cmt_response(chay_cmt)
                        if is_ok:
                            print(f"{green} ● COMMENT THÀNH CÔNG -> Đang gửi nhận xu... ● {white}")
                            gui_nhan_xu("instagram_comment", [task_id], idfb, target_ck_check, xsmm)
                            soloicmt = 0
                        else:
                            print(f"{red} ● CMT LỖI: {msg_err} ● {white}")
                            soloicmt += 1
                            
                        current_delay = get_random_delay(delay_cmt_range)
                        loadtime(current_delay, msg="Delay Random Cmt")
                        check_human_behavior(cookie, proxy, profile)
                        
                        if soloicmt > 4 or jobs_done_this_turn >= job_limit or max_job >= doi:
                            break

            if consecutive_empty_all >= len(listnv) * 2:
                print(f"{white} ❌ {yellow}Hết toàn bộ nhiệm vụ hoặc chưa tới lượt nhả job mới!")
                if len(mangcookie) == 1:
                    loadtime(dl, msg="Chờ Hết Nhiệm Vụ")
                else:
                    break

        rem_tasks = get_pending_tasks(idfb)
        if len(rem_tasks) > 0:
            print(f"\n{yellow} ⏩ Gửi duyệt nốt {len(rem_tasks)} task Follow chuẩn trong JSON trước khi đổi nick...{white}")
            gui_nhan_xu("instagram_follow", rem_tasks, idfb, target_ck_check, xsmm)
            remove_pending_tasks(idfb, rem_tasks)

    if len(mangcookie) == 1 and dl == 0:
        print(f"{pink} ⏩ {blue}Dừng Thời Gian: ", end="")
        try:
            dl = int(input().strip())
        except Exception:
            dl = 150

    if len(mangcookie) == 0:
        if os.path.exists("ListccXSMM.json"):
            os.remove("ListccXSMM.json")
        print(f"\n{pink} ⛔ {red}Tất Cả Cookie Đều Die Hoặc Proxy Lỗi\n")
        break
'''

TOOL_INFO = {"xsmmigv5.2": {"name": "XSMM IG V5.2", "color": "#ff6b9d"}}

# ============================================================================
# ==================== FB REG PAGE NÂNG CAO =================================
# ============================================================================
def fb_get_dtsg(cookie, proxies):
    try:
        r = requests.get('https://www.facebook.com/settings', headers={'cookie': cookie, 'user-agent': 'Mozilla/5.0'}, proxies=proxies, timeout=15)
        dtsg = re.search(r'name="fb_dtsg" value="(.*?)"', r.text)
        jz = re.search(r'name="jazoest" value="(.*?)"', r.text)
        if dtsg and jz: return dtsg.group(1), jz.group(1)
    except: pass
    return None, None

def fb_upload_photo(cookie, page_id, img_url, img_type, proxies):
    try: img_data = requests.get(img_url, timeout=15).content
    except: return False
    boundary = '----WebKitFormBoundary' + ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    headers = {'cookie': cookie, 'user-agent': 'Mozilla/5.0', 'content-type': f'multipart/form-data; boundary={boundary}'}
    url = f"https://www.facebook.com/api/v1/pages/{page_id}/{'picture' if img_type=='avatar' else 'cover'}/"
    field_name = "profile_pic" if img_type=='avatar' else "cover_photo"
    body = (f'--{boundary}\r\nContent-Disposition: form-data; name="{field_name}"; filename="img.jpg"\r\nContent-Type: image/jpeg\r\n\r\n').encode() + img_data + f'\r\n--{boundary}--\r\n'.encode()
    try:
        r = requests.post(url, headers=headers, data=body, proxies=proxies, timeout=30)
        return r.status_code == 200
    except: return False

def fb_invite_admin(cookie, page_id, target_uid, password, proxies):
    fb_dtsg, jazoest = fb_get_dtsg(cookie, proxies)
    if not fb_dtsg: return False
    actor_m = re.search(r'c_user=(\d+)', cookie); actor_id = actor_m.group(1) if actor_m else ""
    
    headers = {'cookie': cookie, 'user-agent': 'Mozilla/5.0', 'content-type': 'application/x-www-form-urlencoded', 'origin': 'https://www.facebook.com'}
    payload = {
        'fb_dtsg': fb_dtsg, 'jazoest': jazoest,
        'variables': json.dumps({"input": {"actor_id": actor_id, "profile_id": page_id, "target_user_id": target_uid, "task_ids": [1, 2, 3, 4, 5], "password": password}}),
        'doc_id': '5278783472212933'
    }
    try:
        r = requests.post("https://www.facebook.com/api/graphql/", headers=headers, data=payload, proxies=proxies, timeout=20)
        return 'errors' not in r.json()
    except: return False

def fb_reg_worker(idx, cookie, page_name, cat, proxy, avt, cover, target_uid, pwd, result_list):
    res = {"idx": idx, "uid": "", "page_id": "", "page_name": page_name, "status": "Đang xử lý...", "ok": False}
    try:
        m = re.search(r'c_user=(\d+)', cookie); res["uid"] = m.group(1) if m else ""
        proxies = {"http": proxy, "https": proxy} if proxy else None
        fb_dtsg, jazoest = fb_get_dtsg(cookie, proxies)
        if not fb_dtsg: res["status"] = "Cookie die"; result_list.append(res); return
        
        headers = {'cookie': cookie, 'user-agent': 'Mozilla/5.0', 'content-type': 'application/x-www-form-urlencoded'}
        payload = {'fb_dtsg': fb_dtsg, 'jazoest': jazoest, 'variables': json.dumps({"input": {"actor_id": res["uid"], "name": page_name, "category_id": cat, "creation_source": "comet"}}), 'doc_id': '5814795813638014'}
        r = requests.post("https://www.facebook.com/api/graphql/", headers=headers, data=payload, proxies=proxies, timeout=25)
        pid_match = re.search(r'"page_id":"(\d+)"', json.dumps(r.json().get('data', {})))
        if not pid_match: res["status"] = "Lỗi tạo Page"; result_list.append(res); return
        
        res["page_id"] = pid_match.group(1)
        if avt: fb_upload_photo(cookie, res["page_id"], avt, 'avatar', proxies)
        if cover: fb_upload_photo(cookie, res["page_id"], cover, 'cover', proxies)
        if target_uid and pwd: fb_invite_admin(cookie, res["page_id"], target_uid, pwd, proxies)
        
        res["status"] = "OK + QTV"; res["ok"] = True
        result_list.append(res)
    except Exception as e:
        res["status"] = "Lỗi"; result_list.append(res)

def run_fb_reg(tasks, threads):
    FB_REG_STATE["running"] = True; FB_REG_STATE["total_success"] = 0; FB_REG_STATE["total_fail"] = 0
    q = Queue(); [q.put((i+1, t['cookie'], t['page_name'], '2200', t.get('proxy',''), t.get('avatar',''), t.get('cover',''), t.get('target_uid',''), t.get('pwd',''))) for i, t in enumerate(tasks)]
    def worker():
        while True:
            try: task = q.get_nowait()
            except: break
            try:
                rl = []
                fb_reg_worker(*task, rl)
                if rl:
                    res = rl[0]
                    with FB_REG_LOCK:
                        if res["ok"]: FB_REG_STATE["total_success"] += 1
                        else: FB_REG_STATE["total_fail"] += 1
                        socketio.emit('fb_reg_update', {"result": res, "stats": {"success": FB_REG_STATE["total_success"], "fail": FB_REG_STATE["total_fail"]}})
            except: pass
            finally: q.task_done()
    ts = [threading.Thread(target=worker, daemon=True) for _ in range(threads)]
    for t in ts: t.start()
    for t in ts: t.join()
    FB_REG_STATE["running"] = False
    socketio.emit('fb_reg_done', {"success": FB_REG_STATE["total_success"], "fail": FB_REG_STATE["total_fail"]})

@app.route('/api/fb_reg_start', methods=['POST'])
def api_fb_reg_start():
    data = request.json or {}
    if not data.get('tasks'): return jsonify({"ok": False})
    threading.Thread(target=run_fb_reg, args=(data['tasks'], int(data.get('threads', 10))), daemon=True).start()
    return jsonify({"ok": True})

# ============================================================================
# ==================== ROUTES CƠ BẢN =========================================
# ============================================================================
def ensure_tool_file(k):
    f = os.path.join(TEMP_TOOLS_DIR, "xsmmigv5.2.py")
    if os.path.exists(f):
        try: os.remove(f)
        except: pass
    with open(f, "w", encoding="utf-8") as fw:
        fw.write(TOOL_CODE_XSMMIGV52)
    return f

def read_process_output(sid, process):
    try:
        for line in iter(process.stdout.readline, ''):
            if line == '' and process.poll() is not None: break
            if line:
                socketio.emit('output', {'session_id': sid, 'line': line.rstrip(), 'ts': datetime.now().strftime('%H:%M:%S')}, room=sid)
    except: pass
    finally:
        process.wait()
        socketio.emit('status', {'session_id': sid, 'status': 'stopped'}, room=sid)

@app.route('/')
def index(): return render_template('index.html', tools=TOOL_INFO)

@app.route('/api/start/<k>', methods=['POST'])
def api_start(k):
    sid = str(uuid.uuid4())[:8]; f = ensure_tool_file(k)
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PYTHONUNBUFFERED'] = '1'
    p = subprocess.Popen(
        [sys.executable, '-u', f],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=TEMP_TOOLS_DIR,
        bufsize=1,
        universal_newlines=True,
        encoding='utf-8',
        errors='replace',
        env=env
    )
    with sessions_lock: sessions[sid] = {"tool": k, "process": p}
    threading.Thread(target=read_process_output, args=(sid, p), daemon=True).start()
    return jsonify({"ok": True, "session_id": sid})

@app.route('/api/stop/<sid>', methods=['POST'])
def api_stop(sid):
    s = sessions.get(sid)
    if s:
        try:
            p = s["process"]
            p.terminate()
            try: p.wait(timeout=2)
            except subprocess.TimeoutExpired: p.kill()
            socketio.emit('status', {'session_id': sid, 'status': 'stopped'}, room=sid)
            return jsonify({"ok": True})
        except: return jsonify({"ok": False}), 500
    return jsonify({"ok": False}), 404

@app.route('/api/input/<sid>', methods=['POST'])
def api_input(sid):
    s = sessions.get(sid)
    if s:
        try:
            s["process"].stdin.write((request.json or {}).get("text", "") + "\n")
            s["process"].stdin.flush()
        except: pass
    return jsonify({"ok": True})

@socketio.on('join')
def on_join(data): join_room(data.get('session_id'))

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), allow_unsafe_werkzeug=True)
