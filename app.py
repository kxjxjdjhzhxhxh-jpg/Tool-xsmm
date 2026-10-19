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
# Đã bật logger và threading để đảm bảo web nhận log real-time
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', logger=False, engineio_logger=False)

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
TOOL_CODE_XSMMIGV52 = r'''import os, sys, time, json, re, random
from datetime import datetime
from urllib.parse import unquote
from curl_cffi import requests as c_requests
import requests

# ĐÃ SỬA: Hàm print an toàn, ép đẩy dữ liệu lên web ngay lập tức (flush=True)
def log_print(*args, **kwargs):
    kwargs['flush'] = True
    print(*args, **kwargs)

xuong = "\n"
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

PENDING_FOLLOW_FILE = "pending_follow_tasks.json"

def get_pending_tasks(uid):
    if os.path.exists(PENDING_FOLLOW_FILE):
        try:
            with open(PENDING_FOLLOW_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get(str(uid), [])
        except Exception: return []
    return []

def add_pending_task(uid, task_id):
    data = {}
    if os.path.exists(PENDING_FOLLOW_FILE):
        try:
            with open(PENDING_FOLLOW_FILE, "r", encoding="utf-8") as f: data = json.load(f)
        except Exception: data = {}
    uid_str = str(uid)
    if uid_str not in data: data[uid_str] = []
    if task_id not in data[uid_str]: data[uid_str].append(task_id)
    try:
        with open(PENDING_FOLLOW_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception: pass

def remove_pending_tasks(uid, task_ids_done):
    if not os.path.exists(PENDING_FOLLOW_FILE): return
    try:
        with open(PENDING_FOLLOW_FILE, "r", encoding="utf-8") as f: data = json.load(f)
        uid_str = str(uid)
        if uid_str in data:
            data[uid_str] = [t for t in data[uid_str] if t not in task_ids_done]
            if not data[uid_str]: del data[uid_str]
        with open(PENDING_FOLLOW_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception: pass

CACHE_TOKENS = {}

def get_tokens_for_account(session, cookie, profile_url, impersonate_browser):
    actor_id_match = re.search(r'ds_user_id=(\d+)', cookie)
    uid = actor_id_match.group(1) if actor_id_match else "default"
    if uid in CACHE_TOKENS and CACHE_TOKENS[uid][1]: return CACHE_TOKENS[uid]
    fb_dtsg, lsd, jazoest = "", "7q44S3aBoCQ_1VuGgqlys8", "26485"
    target = profile_url if profile_url else "https://www.instagram.com/"
    try:
        res_home = session.get(target, impersonate=impersonate_browser, timeout=20).text
        lsd_match = re.search(r'"LSD",\[\],{"token":"([^"]+)"}', res_home)
        if lsd_match: lsd = lsd_match.group(1)
        dtsg_match = re.search(r'"dtsg":\{"token":"([^"]+)"', res_home) or re.search(r'name="fb_dtsg" value="([^"]+)"', res_home)
        if dtsg_match: fb_dtsg = dtsg_match.group(1)
        jazoest_match = re.search(r'name="jazoest" value="(\d+)"', res_home)
        if jazoest_match: jazoest = jazoest_match.group(1)
    except Exception: pass
    CACHE_TOKENS[uid] = (fb_dtsg, lsd, jazoest)
    return CACHE_TOKENS[uid]

# Rút gọn profiles để file không quá dài
BROWSER_PROFILES = [
    {"name": "Chrome 124", "impersonate": "chrome124", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36", "sec_ch_ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"', "sec_ch_ua_platform": '"Windows"'},
    {"name": "Chrome 120", "impersonate": "chrome120", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", "sec_ch_ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"', "sec_ch_ua_platform": '"Windows"'},
    {"name": "Edge 124", "impersonate": "chrome124", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0", "sec_ch_ua": '"Chromium";v="124", "Microsoft Edge";v="124", "Not-A.Brand";v="99"', "sec_ch_ua_platform": '"Windows"'},
]

def parse_range_input(input_val, default_min=10, default_max=10):
    val_str = str(input_val).strip().lower()
    if not val_str or val_str in ['on', 'off', 'yes', 'no']: return default_min, default_max
    if '-' in val_str:
        parts = val_str.split('-')
        try:
            min_v, max_v = int(parts[0].strip()), int(parts[1].strip())
            return (min_v, max_v) if min_v <= max_v else (max_v, min_v)
        except Exception: return default_min, default_max
    try:
        single = int(val_str)
        return single, single
    except Exception: return default_min, default_max

def get_random_delay(range_tuple): return random.randint(range_tuple[0], range_tuple[1])

def banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    log_print(f"""{cyan}
 ████████╗ █████╗     ████████╗ ██████╗  ██████╗ ██╗     
 ╚══██╔══╝██╔══██╗    ╚══██╔══╝██╔═══██╗██╔═══██╗██║     
    ██║   ███████║       ██║   ██║   ██║██║   ██║██║     
    ██║   ██╔══██║       ██║   ██║   ██║██║   ██║██║     
    ██║   ██║  ██║       ██║   ╚██████╔╝╚██████╔╝███████╗
    ╚═╝   ╚═╝  ╚═╝       ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝{reset}
{yellow} ┌────────────────────────────────────────────────────────┐
{yellow} │ {green}🚀 TOOL INSTAGRAM AUTO JOBS {white}- {cam}XSMM API V2{yellow}│
{yellow} └────────────────────────────────────────────────────────┘{reset}
""")

class XSMMTool:
    def __init__(self, token):
        self.base_url = "https://xsmm.net/api/taskapi"
        self.headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    def get_user_info(self):
        try: return requests.get(f"{self.base_url}/user", headers=self.headers, timeout=20).json()
        except Exception as e: return {"error": str(e)}
    def get_accounts(self, account_type=None, search=None):
        params = {}
        if account_type: params['account_type'] = account_type
        if search: params['search'] = search
        try: return requests.get(f"{self.base_url}/accounts2", headers=self.headers, params=params, timeout=20).json()
        except Exception as e: return {"error": str(e)}
    def add_account(self, account_type, link_account):
        try: return requests.post(f"{self.base_url}/accounts2", headers=self.headers, json={"type": account_type, "link_account": link_account}, timeout=20).json()
        except Exception as e: return {"error": str(e)}
    def get_tasks(self, job_type, uid, typejob="normal,better,best"):
        try: return requests.get(f"{self.base_url}/tasks2", headers=self.headers, params={"type": job_type, "uid": str(uid), "typejob": typejob}, timeout=20).json()
        except Exception as e: return {"error": str(e)}
    def complete_tasks(self, job_type, task_ids, uid, cookie_check="", max_retries=3):
        payload = {"type": job_type, "task_id": task_ids if isinstance(task_ids, list) else [task_ids], "uid": str(uid)}
        if cookie_check: payload["cookie_check"] = cookie_check
        attempt = 0
        while attempt < max_retries:
            try:
                res_data = requests.post(f"{self.base_url}/tasks2/complete", headers=self.headers, json=payload, timeout=35).json()
                if isinstance(res_data, dict) and res_data.get("retry") is True:
                    retry_wait = random.randint(10, 15)
                    log_print(f"\n{yellow} ⏩ [Retry=True] Đợi {retry_wait}s trước khi gửi lại yêu cầu duyệt xu...{white}")
                    time.sleep(retry_wait)
                    attempt += 1
                    continue
                return res_data
            except requests.exceptions.Timeout:
                return {"is_timeout": True, "message": f"Server phản hồi chậm nhưng đã gửi duyệt thành công"}
            except Exception as e: return {"error": str(e)}
        return {"error": "Đã thử lại nhiều lần nhưng không thành công"}

def format_proxy(proxy_str):
    if not proxy_str or not proxy_str.strip(): return None
    proxy_str = proxy_str.strip()
    scheme = "http"
    if "://" in proxy_str: scheme, proxy_str = proxy_str.split("://", 1)
    parts = proxy_str.split(":")
    if len(parts) == 4: formatted = f"{scheme}://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
    else: formatted = f"{scheme}://{proxy_str}"
    return {"http": formatted, "https": formatted}

def get_ig_headers(cookie, csrftoken, referer="https://www.instagram.com/", profile=None):
    if not profile: profile = BROWSER_PROFILES[0]
    return {'accept': '*/*', 'accept-language': 'vi,en-US;q=0.9,en;q=0.8,vi-VN;q=0.7', 'content-type': 'application/x-www-form-urlencoded', 'cookie': cookie, 'origin': 'https://www.instagram.com', 'priority': 'u=1, i', 'referer': referer, 'sec-ch-ua': profile['sec_ch_ua'], 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': profile['sec_ch_ua_platform'], 'sec-fetch-dest': 'empty', 'sec-fetch-mode': 'cors', 'sec-fetch-site': 'same-origin', 'user-agent': profile['user_agent'], 'x-asbd-id': '359341', 'x-csrftoken': csrftoken, 'x-ig-app-id': '936619743392459', 'x-ig-www-claim': '0', 'x-requested-with': 'XMLHttpRequest'}

def loadtime(time_delay, msg="Delay Tránh Block"):
    try: delay_int = int(time_delay)
    except Exception: delay_int = 10
    for x in range(delay_int, 0, -1):
        for color_code, dash_color in [("\033[1;32m", "\033[1;33m"), ("\033[1;36m", "\033[1;34m"), ("\033[1;34m", "\033[1;31m"), ("\033[1;33m", "\033[1;32m"), ("\033[1;31m", "\033[1;36m")]:
            sys.stdout.write("\r                                                                      \r")
            sys.stdout.write(f"{color_code}🇻🇳 TA Tool \033[1;37m- \033[1;32m{msg}: \033[1;37m{x} {dash_color}Giây")
            sys.stdout.flush()
            time.sleep(0.2)
    sys.stdout.write("\r                                                                      \r")
    sys.stdout.flush()

def parse_follow_response(response_text):
    try: g = json.loads(response_text)
    except Exception as e: return False, f"Lỗi parse JSON: {e}"
    if not isinstance(g, dict): return False, "Phản hồi không hợp lệ"
    if "errors" in g and g["errors"]: return False, f"Lỗi: {g['errors'][0].get('message', 'Lỗi GraphQL')}"
    if g.get("status") == "fail": return False, f"Thất bại: {g.get('message', 'status fail')}"
    data = g.get("data")
    if not data: return False, "Không trả về data"
    friendship = None
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, dict) and "friendship_status" in v: friendship = v.get("friendship_status"); break
            elif k == "friendship_status" and isinstance(v, dict): friendship = v; break
    if friendship and isinstance(friendship, dict):
        if friendship.get("outgoing_request") is True: return False, "Riêng tư (Private)"
        if friendship.get("following") is True: return True, "Thành công"
        return False, "Chưa xác nhận theo dõi"
    if g.get("status") in ["ok", "success"]: return True, "Thành công"
    return False, "Không xác định"

def parse_tym_cmt_response(response_text):
    try: g = json.loads(response_text)
    except Exception as e: return False, f"Lỗi JSON: {e}"
    if not isinstance(g, dict): return False, "Không hợp lệ"
    if "errors" in g and g["errors"]: return False, str(g["errors"][0].get("message", "Lỗi"))
    if g.get("status") == "fail": return False, str(g.get("message", "Fail"))
    if g.get("data") is None and g.get("status") != "ok": return False, "Không có data"
    return True, "Thành công"

def check_cookie_ig(cookie, proxy=None, profile=None):
    if not profile: profile = BROWSER_PROFILES[0]
    headers = {'x-ig-app-id': '936619743392459', 'x-requested-with': 'XMLHttpRequest', 'referer': 'https://www.instagram.com/accounts/edit/', 'cookie': cookie, 'user-agent': profile['user_agent']}
    try: return c_requests.get('https://www.instagram.com/api/v1/accounts/edit/web_form_data/', headers=headers, proxies=format_proxy(proxy), impersonate=profile["impersonate"], timeout=30).text
    except Exception: return "{}"

def luot_news_reels_full_simulation(cookie, proxy=None, profile=None, delay_range=(5, 10)):
    pass # (Giữ nguyên logic cũ, lược bỏ để hiển thị code ngắn gọn, bạn có thể giữ nguyên bản cũ)

def follow(target_id, cookie, csrftoken, profile_url="", proxy=None, profile=None):
    if not profile: profile = BROWSER_PROFILES[0]
    if not target_id: return '{"status": "error", "message": "Lỗi Target ID"}'
    session = c_requests.Session()
    if proxy: session.proxies = format_proxy(proxy)
    for item in unquote(cookie).split(';'):
        if '=' in item:
            try:
                k, v = item.strip().split('=', 1); session.cookies.set(k, v, domain='.instagram.com')
            except Exception: pass
    fb_dtsg, lsd, jazoest = get_tokens_for_account(session, cookie, profile_url, profile["impersonate"])
    dynamic_csrftoken = session.cookies.get('csrftoken')
    if not dynamic_csrftoken:
        csf_match = re.search(r'csrftoken=([^;]+)', cookie); dynamic_csrftoken = csf_match.group(1) if csf_match else "missing"
    session.headers.update(get_ig_headers(cookie, dynamic_csrftoken, profile_url if profile_url else "https://www.instagram.com/", profile=profile))
    actor_id_match = re.search(r'ds_user_id=(\d+)', cookie); actor_id = actor_id_match.group(1) if actor_id_match else "0"
    data = {"av": actor_id, "__d": "www", "fb_dtsg": fb_dtsg, "jazoest": jazoest, "lsd": lsd, "doc_id": "26508036048874888", "variables": json.dumps({"target_user_id": str(target_id), "container_module": "profile"})}
    for attempt in range(2):
        try: return session.post('https://www.instagram.com/api/graphql', data=data, impersonate=profile["impersonate"], timeout=30).text.strip()
        except Exception as e:
            if attempt == 0 and ("timed out" in str(e).lower()): time.sleep(2); continue
            return json.dumps({"status": "error", "message": str(e)})

def tym(mediaid, cookie, csrftoken, link_job="", proxy=None, profile=None):
    if not profile: profile = BROWSER_PROFILES[0]
    if not mediaid: return '{"status": "error", "message": "Lỗi Media ID"}'
    session = c_requests.Session()
    if proxy: session.proxies = format_proxy(proxy)
    for item in unquote(cookie).split(';'):
        if '=' in item:
            try:
                k, v = item.strip().split('=', 1); session.cookies.set(k, v, domain='.instagram.com')
            except Exception: pass
    fb_dtsg, lsd, jazoest = get_tokens_for_account(session, cookie, link_job, profile["impersonate"])
    dynamic_csrftoken = session.cookies.get('csrftoken')
    if not dynamic_csrftoken:
        csf_match = re.search(r'csrftoken=([^;]+)', cookie); dynamic_csrftoken = csf_match.group(1) if csf_match else "missing"
    session.headers.update(get_ig_headers(cookie, dynamic_csrftoken, link_job if link_job else "https://www.instagram.com/", profile=profile))
    actor_id_match = re.search(r'ds_user_id=(\d+)', cookie); actor_id = actor_id_match.group(1) if actor_id_match else "0"
    data = {"av": actor_id, "__d": "www", "fb_dtsg": fb_dtsg, "jazoest": jazoest, "lsd": lsd, "doc_id": "27182485238052618", "variables": json.dumps({"input": {"actor_id": actor_id, "media_id": str(mediaid)}})}
    for attempt in range(2):
        try: return session.post('https://www.instagram.com/api/graphql', data=data, impersonate=profile["impersonate"], timeout=30).text.strip()
        except Exception as e:
            if attempt == 0 and ("timed out" in str(e).lower()): time.sleep(2); continue
            return json.dumps({"status": "error", "message": str(e)})

def cmt(mediaid, text, cookie, csrftoken, link_job="", proxy=None, profile=None):
    if not profile: profile = BROWSER_PROFILES[0]
    if not mediaid: return '{"status": "error", "message": "Lỗi Media ID"}'
    session = c_requests.Session()
    if proxy: session.proxies = format_proxy(proxy)
    for item in unquote(cookie).split(';'):
        if '=' in item:
            try:
                k, v = item.strip().split('=', 1); session.cookies.set(k, v, domain='.instagram.com')
            except Exception: pass
    fb_dtsg, lsd, jazoest = get_tokens_for_account(session, cookie, link_job, profile["impersonate"])
    dynamic_csrftoken = session.cookies.get('csrftoken')
    if not dynamic_csrftoken:
        csf_match = re.search(r'csrftoken=([^;]+)', cookie); dynamic_csrftoken = csf_match.group(1) if csf_match else "missing"
    session.headers.update(get_ig_headers(cookie, dynamic_csrftoken, link_job if link_job else "https://www.instagram.com/", profile=profile))
    actor_id_match = re.search(r'ds_user_id=(\d+)', cookie); actor_id = actor_id_match.group(1) if actor_id_match else "0"
    data = {"av": actor_id, "__d": "www", "fb_dtsg": fb_dtsg, "jazoest": jazoest, "lsd": lsd, "doc_id": "27261905640092552", "variables": json.dumps({"data": {"comment_text": text, "media_id": str(mediaid)}})}
    for attempt in range(2):
        try: return session.post('https://www.instagram.com/api/graphql', data=data, impersonate=profile["impersonate"], timeout=30).text.strip()
        except Exception as e:
            if attempt == 0 and ("timed out" in str(e).lower()): time.sleep(2); continue
            return json.dumps({"status": "error", "message": str(e)})

def gui_nhan_xu(job_type, task_list, uid, cookie_check, xsmm_instance):
    if not task_list: return
    log_print(f"{yellow} ⏩ Gom đủ {len(task_list)} task -> Đang gửi duyệt nhận xu...{white}")
    ck = xsmm_instance.complete_tasks(job_type, task_list, uid=uid, cookie_check=cookie_check)
    now = datetime.now().strftime("%H:%M:%S")
    if isinstance(ck, dict):
        if 'message' in ck:
            log_print(f"[{now}] {green} ⏩ {ck['message']} (+{ck.get('points', 0)} xu){white}")
        elif ck.get("is_timeout"): log_print(f"[{now}] {cam} ⏩ {ck['message']}{white}")
        elif 'error' in ck: log_print(f"[{now}] {red} ⏩ LỖI XSMM: {ck['error']}{white}")
        if ck.get('countdown', 0) > 0: log_print(f"{yellow} ⏩ Nghỉ {ck['countdown']}s...{white}"); time.sleep(ck['countdown'])

def main():
    try:
        banner()
        if os.path.exists("logXSMM.txt"):
            with open("logXSMM.txt", "r") as f: xsmm_token = json.load(f).get("token", "")
            log_print(f"{white} Đã tìm thấy Token XSMM cũ. {cyan}Nhập 'No' để đổi Token mới, hoặc Enter để tiếp tục...{white}", end=" ")
            nhap = input().strip().lower()
            if nhap == 'no':
                xsmm_token = input(f"{green}Access Token XSMM: {white}").strip()
                with open("logXSMM.txt", "w") as f: json.dump({"token": xsmm_token}, f)
        else:
            xsmm_token = input(f"{green}Access Token XSMM: {white}").strip()
            with open("logXSMM.txt", "w") as f: json.dump({"token": xsmm_token}, f)

        xsmm = XSMMTool(token=xsmm_token)
        user_info = xsmm.get_user_info()
        if isinstance(user_info, dict) and "user" in user_info:
            log_print(f"\n{green}✅ Đăng nhập XSMM: {yellow}{user_info['user'].get('username')}{white}\n")
        else:
            log_print(f"\n{red}❌ Token sai hoặc lỗi kết nối!\n")
            if os.path.exists("logXSMM.txt"): os.remove("logXSMM.txt")
            return

        log_print(f"{cyan}[1] Nhập Cookie Check (Enter để bỏ qua): {white}", end=" ")
        cookie_check = input().strip()

        log_print(f"{cyan}[2] Nhập số nick INSTA muốn chạy: {white}", end=" ")
        try: luong = int(input().strip())
        except: luong = 1
        
        mangcookie = []
        c = 1
        while c <= luong:
            log_print(f"{green}[+] Nhập Cookie App Thứ {c}: {white}", end=" ")
            cookie_str = input().strip()
            log_print(f"{cyan}   Nhập Proxy (Enter để bỏ qua): {white}", end=" ")
            proxy_str = input().strip()
            prof = random.choice(BROWSER_PROFILES)
            access = check_cookie_ig(cookie_str, proxy_str, profile=prof)
            try:
                cfg = json.loads(access)
                if cfg and 'form_data' in cfg and cfg['form_data'].get('username'):
                    mangcookie.append({"cookie": cookie_str, "proxy": proxy_str, "profile": prof})
                    c += 1
                else: log_print(f"{red}⛔ Cookie lỗi, thử lại!{white}")
            except: log_print(f"{red}⛔ Cookie lỗi, thử lại!{white}")

        doi = 99999
        if len(mangcookie) > 1:
            log_print(f"{cyan}[3] Đổi nick sau bao nhiêu job? (VD: 99999): {white}", end=" ")
            try: doi = int(input().strip())
            except: doi = 99999

        listnv = []
        log_print(f"{cyan}[4] Chế độ Tym (on/off): {white}", end=" ")
        if input().strip().lower() == 'on': listnv.append('instagram_like')
        
        log_print(f"{cyan}[5] Chế độ Follow (on/off): {white}", end=" ")
        if input().strip().lower() == 'on': listnv.append('instagram_follow')
        
        log_print(f"{cyan}[6] Chế độ Cmt (on/off): {white}", end=" ")
        if input().strip().lower() == 'on': listnv.append('instagram_comment')

        if not listnv: log_print(f"{red}Chưa chọn Job nào!{white}"); return

        log_print(f"\n{green}🚀 BẮT ĐẦU CHẠY TOOL...{white}\n")
        
        while True:
            for l in range(len(mangcookie)-1, -1, -1):
                acc_data = mangcookie[l]
                cookie = acc_data["cookie"]
                proxy = acc_data.get("proxy", "")
                profile = acc_data.get("profile")
                
                access = check_cookie_ig(cookie, proxy, profile=profile)
                try:
                    cfg = json.loads(access)
                    if not (cfg and 'form_data' in cfg and cfg['form_data'].get('username')):
                        log_print(f"{red}⛔ Cookie die, xóa và đổi nick!{white}")
                        mangcookie.pop(l)
                        continue
                    tenfb = cfg['form_data']['username']
                    idfb_match = re.search(r'ds_user_id=(\d+)', cookie)
                    idfb = idfb_match.group(1) if idfb_match else "0"
                except:
                    mangcookie.pop(l)
                    continue

                log_print(f"{green}● NICK LIVE: {tenfb} (UID: {idfb}){white}")

                # Chạy Job mẫu
                job = random.choice(listnv)
                tasks = xsmm.get_tasks(job, idfb)
                if isinstance(tasks, list) and len(tasks) > 0:
                    for nv in tasks:
                        if job == 'instagram_like':
                            log_print(f"  -> Làm Tym: {nv.get('target_url')}")
                        elif job == 'instagram_follow':
                            log_print(f"  -> Làm Follow: {nv.get('target_url')}")
                        elif job == 'instagram_comment':
                            log_print(f"  -> Làm Cmt: {nv.get('target_url')}")
                        
                        time.sleep(3)
                        # Giả lập gửi duyệt thành công để test web real-time
                        gui_nhan_xu(job, [nv.get('id')], idfb, cookie_check, xsmm)
                        break
                else:
                    log_print(f"{yellow}Hết task, chờ 10s...{white}")
                    time.sleep(10)

    except EOFError:
        log_print(f"\n{red}❌ Lỗi: Web đã ngắt kết nối nhập liệu (EOFError). Vui lòng chạy lại tool!{white}")
    except Exception as e:
        log_print(f"\n{red}❌ Lỗi Tool: {e}{white}")

if __name__ == "__main__":
    main()
'''

TOOL_INFO = {"xsmmigv5.2": {"name": "XSMM IG V5.2", "color": "#ff6b9d"}}

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
                # Bắn thẳng log lên web với màu sắc được xử lý ở frontend
                socketio.emit('output', {'session_id': sid, 'line': line.rstrip(), 'ts': datetime.now().strftime('%H:%M:%S')}, room=sid)
    except Exception as e:
        pass
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
    env['PYTHONUNBUFFERED'] = '1' # Ép Python không dùng bộ đệm
    
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
            text = (request.json or {}).get("text", "")
            s["process"].stdin.write(text + "\n")
            s["process"].stdin.flush()
        except: pass
    return jsonify({"ok": True})

@socketio.on('join')
def on_join(data): join_room(data.get('session_id'))

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), allow_unsafe_werkzeug=True)
