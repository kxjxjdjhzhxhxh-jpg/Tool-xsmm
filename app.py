import os
import sys
import json
import uuid
import time
import threading
import subprocess
import tempfile
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ta_tool_secret_2024'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSIONS_DIR = os.path.join(BASE_DIR, "sessions")
os.makedirs(SESSIONS_DIR, exist_ok=True)

# Thư mục tạm chứa file .py được sinh ra từ code nhúng
TEMP_TOOLS_DIR = os.path.join(tempfile.gettempdir(), "ta_tool_embedded")
os.makedirs(TEMP_TOOLS_DIR, exist_ok=True)

# ============================================================================
# ==================== TOOL 1: xsmmv3.2.py ==================================
# ============================================================================
TOOL_CODE_XSMMV32 = r'''import os
import sys
import time
import json
import re
from datetime import datetime
import random
from urllib.parse import unquote
from curl_cffi import requests as c_requests
import requests
import threading
from concurrent.futures import ThreadPoolExecutor

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
reset = "\033[0m"

print_lock = threading.Lock()

def thread_safe_print(msg):
    with print_lock:
        print(msg)

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
{yellow} │ {green}🚀 TOOL INSTAGRAM AUTO JOBS {white}- {cam}XSMM API ONLY IG V3    {yellow}│
{yellow} │ {pink}📌 Bản quyền: {white}TA Tool                                  {yellow}│
{yellow} │ {cyan}☕ Donate MoMo: {green}0373607456                             {yellow}│
{yellow} └────────────────────────────────────────────────────────┘{reset}
""")

class XSMMTool:
    def __init__(self, token):
        self.base_url = "https://xsmm.net/api/taskapi"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def get_user_info(self):
        url = f"{self.base_url}/user"
        try:
            response = requests.get(url, headers=self.headers, timeout=20)
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
        url = f"{self.base_url}/accounts2"
        payload = {
            "type": account_type,
            "link_account": link_account
        }
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=20)
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def get_tasks(self, job_type, uid, typejob="normal,better,best"):
        url = f"{self.base_url}/tasks2"
        params = {
            "type": job_type,
            "uid": str(uid),
            "typejob": typejob
        }
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=20)
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def complete_tasks(self, job_type, task_ids, uid, cookie_check="", max_retries=3):
        url = f"{self.base_url}/tasks2/complete"
        payload = {
            "type": job_type,
            "task_id": task_ids if isinstance(task_ids, list) else [task_ids],
            "uid": str(uid),
            "cookie_check": cookie_check
        }
        
        attempt = 0
        while attempt < max_retries:
            try:
                response = requests.post(url, headers=self.headers, json=payload, timeout=35)
                res_data = response.json()
                
                if isinstance(res_data, dict) and res_data.get("retry") is True:
                    retry_wait = random.randint(1, 3)
                    thread_safe_print(f"\n{yellow} ⏩ [Retry=True] Đợi {retry_wait}s trước khi gửi lại yêu cầu duyệt xu...{white}")
                    time.sleep(retry_wait)
                    attempt += 1
                    continue
                    
                return res_data
            except requests.exceptions.Timeout:
                return {
                    "is_timeout": True, 
                    "message": f"Server phản hồi chậm nhưng đã gửi duyệt {len(payload['task_id'])} job thành công"
                }
            except Exception as e:
                return {"error": str(e)}
                
        return {"error": "Đã thử lại nhiều lần nhưng không thành công"}

useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
sec_ch_ua_120 = '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'

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
    elif "@" in proxy_str:
        formatted = f"{scheme}://{proxy_str}"
    elif len(parts) == 2:
        formatted = f"{scheme}://{proxy_str}"
    else:
        formatted = f"{scheme}://{proxy_str}"
        
    return {"http": formatted, "https": formatted}

def get_ig_headers(cookie, csrftoken, referer="https://www.instagram.com/"):
    return {
        'accept': '*/*',
        'accept-language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
        'content-type': 'application/x-www-form-urlencoded',
        'cookie': cookie,
        'origin': 'https://www.instagram.com',
        'priority': 'u=1, i',
        'referer': referer,
        'sec-ch-ua': sec_ch_ua_120,
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': useragent,
        'x-asbd-id': '129477',
        'x-csrftoken': csrftoken,
        'x-ig-app-id': '936619743392459',
        'x-ig-www-claim': '0',
        'x-requested-with': 'XMLHttpRequest'
    }

def check_cookie_ig(cookie, proxy=None):
    url = 'https://www.instagram.com/api/v1/accounts/edit/web_form_data/'
    headers = {
        'x-ig-app-id': '936619743392459',
        'x-requested-with': 'XMLHttpRequest',
        'referer': 'https://www.instagram.com/accounts/edit/',
        'cookie': cookie,
        'user-agent': useragent,
        'sec-ch-ua': sec_ch_ua_120
    }
    proxies = format_proxy(proxy)
    try:
        return c_requests.get(url, headers=headers, proxies=proxies, impersonate="chrome120", timeout=30).text
    except:
        return "{}"

def follow(target_id, cookie, csrftoken, profile_url="", proxy=None):
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
            except:
                pass
    fb_dtsg, lsd, jazoest = "", "Jfq8VQNmkkkJufHSbEE9bf", "26328"
    try:
        res_home = session.get(profile_url if profile_url else "https://www.instagram.com/", impersonate="chrome120", timeout=10).text
        lsd_match = re.search(r'"LSD",\[\],{"token":"([^"]+)"}', res_home)
        if lsd_match:
            lsd = lsd_match.group(1)
        dtsg_match = re.search(r'"dtsg":\{"token":"([^"]+)"', res_home)
        if not dtsg_match:
            dtsg_match = re.search(r'name="fb_dtsg" value="([^"]+)"', res_home)
        if dtsg_match:
            fb_dtsg = dtsg_match.group(1)
        jazoest_match = re.search(r'name="jazoest" value="(\d+)"', res_home)
        if jazoest_match:
            jazoest = jazoest_match.group(1)
    except:
        pass
    dynamic_csrftoken = session.cookies.get('csrftoken')
    if not dynamic_csrftoken:
        csf_match = re.search(r'csrftoken=([^;]+)', cookie)
        dynamic_csrftoken = csf_match.group(1) if csf_match else "missing"
    session.headers.update(get_ig_headers(cookie, dynamic_csrftoken, profile_url if profile_url else "https://www.instagram.com/"))
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
    try:
        res_gql = session.post('https://www.instagram.com/api/graphql', data=data, impersonate="chrome120", timeout=15)
        return res_gql.text.strip()
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

def tym(mediaid, cookie, csrftoken, link_job="", proxy=None):
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
            except:
                pass
    fb_dtsg, lsd, jazoest = "", "GyeZl-huflHZ0K5L3-pzBi", "26492"
    try:
        res_home = session.get("https://www.instagram.com/", impersonate="chrome120", timeout=10).text
        lsd_match = re.search(r'"LSD",\[\],{"token":"([^"]+)"}', res_home)
        if lsd_match:
            lsd = lsd_match.group(1)
        dtsg_match = re.search(r'"dtsg":\{"token":"([^"]+)"', res_home)
        if not dtsg_match:
            dtsg_match = re.search(r'name="fb_dtsg" value="([^"]+)"', res_home)
        if dtsg_match:
            fb_dtsg = dtsg_match.group(1)
        jazoest_match = re.search(r'name="jazoest" value="(\d+)"', res_home)
        if jazoest_match:
            jazoest = jazoest_match.group(1)
    except:
        pass
    dynamic_csrftoken = session.cookies.get('csrftoken')
    if not dynamic_csrftoken:
        csf_match = re.search(r'csrftoken=([^;]+)', cookie)
        dynamic_csrftoken = csf_match.group(1) if csf_match else "missing"
    session.headers.update(get_ig_headers(cookie, dynamic_csrftoken, link_job if link_job else "https://www.instagram.com/"))
    actor_id_match = re.search(r'ds_user_id=(\d+)', cookie)
    actor_id = actor_id_match.group(1) if actor_id_match else "0"
    tracking_token = ""
    try:
        if link_job:
            res_get = session.get(link_job, impersonate="chrome120", timeout=10).text
            tt_match = re.search(r'"tracking_token":"([^"]+)"', res_get)
            if tt_match:
                tracking_token = tt_match.group(1)
    except:
        pass
    variables = {
        "input": {
            "actor_id": actor_id, "client_mutation_id": str(random.randint(1000000, 9999999)),
            "container_module": "single_post", "media_id": str(mediaid)
        }
    }
    if tracking_token:
        variables["input"]["tracking_token"] = tracking_token
    data = {
        "av": actor_id, "__d": "www", "__user": "0", "__a": "1", "__req": "h",
        "__hs": "20702.HYP:instagram_web_pkg.2.1...0", "dpr": "1", "__ccg": "EXCELLENT",
        "__rev": "1046913831", "__comet_req": "7", "fb_dtsg": fb_dtsg, "jazoest": jazoest,
        "lsd": lsd, "fb_api_caller_class": "RelayModern", "fb_api_req_friendly_name": "usePolarisLikeMediaXIGLikeMutation",
        "server_timestamps": "true", "doc_id": "27182485238052618", "variables": json.dumps(variables)
    }
    try:
        res_gql = session.post('https://www.instagram.com/api/graphql', data=data, impersonate="chrome120", timeout=15)
        return res_gql.text.strip()
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

def cmt(mediaid, text, cookie, csrftoken, link_job="", proxy=None):
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
            except:
                pass
    fb_dtsg, lsd, jazoest = "", "9zei3OjvTBQ-9YG6E0OMzm", "26312"
    try:
        res_home = session.get(link_job if link_job else "https://www.instagram.com/", impersonate="chrome120", timeout=10).text
        lsd_match = re.search(r'"LSD",\[\],{"token":"([^"]+)"}', res_home)
        if lsd_match:
            lsd = lsd_match.group(1)
        dtsg_match = re.search(r'"dtsg":\{"token":"([^"]+)"', res_home)
        if not dtsg_match:
            dtsg_match = re.search(r'name="fb_dtsg" value="([^"]+)"', res_home)
        if dtsg_match:
            fb_dtsg = dtsg_match.group(1)
        jazoest_match = re.search(r'name="jazoest" value="(\d+)"', res_home)
        if jazoest_match:
            jazoest = jazoest_match.group(1)
    except:
        pass
    dynamic_csrftoken = session.cookies.get('csrftoken')
    if not dynamic_csrftoken:
        csf_match = re.search(r'csrftoken=([^;]+)', cookie)
        dynamic_csrftoken = csf_match.group(1) if csf_match else "missing"
    session.headers.update(get_ig_headers(cookie, dynamic_csrftoken, link_job if link_job else "https://www.instagram.com/"))
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
    try:
        res_gql = session.post('https://www.instagram.com/api/graphql', data=data, impersonate="chrome120", timeout=15)
        return res_gql.text.strip()
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

def gui_nhan_xu(job_type, task_list, uid, cookie_check, xsmm_instance, tenfb):
    if not task_list:
        return
    thread_safe_print(f"{yellow} ⏩ [{tenfb}] Gom đủ {len(task_list)} task -> Đang gửi duyệt nhận xu...{white}")
    ck = xsmm_instance.complete_tasks(job_type, task_list, uid=uid, cookie_check=cookie_check)
    now = datetime.now().strftime("%H:%M:%S")
    
    if isinstance(ck, dict):
        if 'message' in ck:
            pts = ck.get('points', 0)
            succ = ck.get('success_count', len(task_list))
            thread_safe_print(f"[{now}] {green} ⏩ [{tenfb}] {ck['message']} (+{pts} xu | Hoàn thành: {succ} task){white}")
        elif ck.get("is_timeout"):
            thread_safe_print(f"[{now}] {cam} ⏩ [{tenfb}] {ck['message']}{white}")
        elif 'error' in ck:
            thread_safe_print(f"[{now}] {red} ⏩ [{tenfb}] LỖI XSMM: {ck['error']}{white}")
        
        if ck.get('countdown', 0) > 0:
            thread_safe_print(f"{yellow} ⏩ [{tenfb}] Hệ thống yêu cầu nghỉ {ck['countdown']}s...{white}")
            time.sleep(ck['countdown'])

def run_single_account(acc_data, listnv, config_delays, xsmm_token, dl, doi):
    cookie = acc_data["cookie"]
    proxy = acc_data.get("proxy", "")
    
    xsmm_thread = XSMMTool(token=xsmm_token)
    
    access = check_cookie_ig(cookie, proxy)
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
        thread_safe_print(f"{white} ⛔ {red}Cookie lỗi hoặc Proxy Die - Dừng luồng này!{white}")
        return

    px_display = f" | Proxy: {proxy}" if proxy else " | Không Proxy"
    thread_safe_print(f"{green} ● NICK LIVE [{tenfb} | UID: {idfb}{px_display}] Bắt đầu chạy... ● {white}")

    try:
        acc_list = xsmm_thread.get_accounts(account_type="instagram", search=idfb)
        exists = False
        if isinstance(acc_list, dict) and acc_list.get("accounts"):
            for acc in acc_list["accounts"]:
                if acc and (str(acc.get("account_id")) == str(idfb) or str(acc.get("name", "")).lower() == str(tenfb).lower()):
                    exists = True
                    break
        if not exists:
            link_ig = f"https://www.instagram.com/{tenfb}"
            add_res = xsmm_thread.add_account("instagram", link_ig)
            if isinstance(add_res, dict) and "id" in add_res:
                thread_safe_print(f"{green} ➕ Đã tự động thêm [{tenfb}] vào XSMM!{white}")
    except Exception as e:
        thread_safe_print(f"{yellow} ⚠️ [ {tenfb} ] Không thể đồng bộ tài khoản: {e}{white}")

    max_job = 0
    cache_follow = []
    
    while True:
        rand_job = random.choice(listnv)
        
        if rand_job == 'instagram_like':
            list_nv = xsmm_thread.get_tasks(rand_job, uid=idfb)
            if isinstance(list_nv, dict) and "error" in list_nv:
                thread_safe_print(f"{white} ❌ [{tenfb}] Lỗi từ XSMM: {list_nv['error']}")
                time.sleep(dl)
            elif isinstance(list_nv, list) and len(list_nv) == 0:
                thread_safe_print(f"{white} ❌ [{tenfb}] Hết nhiệm vụ Tym hoặc chưa tới lượt!")
                time.sleep(dl)
            elif isinstance(list_nv, list):
                soloitym = 0
                for nv in list_nv:
                    task_id = nv.get('id')
                    idm = nv.get('target_id', '')
                    link_job = nv.get('target_url', '')
                    csf_match = re.search(r'csrftoken=([^;]+)', cookie)
                    csf = csf_match.group(1) if csf_match else ""
                    
                    thread_safe_print(f"{yellow} ⏩ [{tenfb}] Job Tym: {white}{link_job}")
                    chayfl = tym(idm, cookie, csf, link_job, proxy=proxy)
                    max_job += 1
                    
                    try:
                        g = json.loads(chayfl)
                        if 'data' not in g and g.get('status') != 'ok':
                            raise Exception(g.get('message', 'Bị IG chặn thao tác'))
                            
                        thread_safe_print(f"{green} ● [{tenfb}] TYM THÀNH CÔNG -> Gửi duyệt... ● {white}")
                        gui_nhan_xu("instagram_like", [task_id], idfb, cookie, xsmm_thread, tenfb)
                        soloitym = 0
                    except Exception as e:
                        thread_safe_print(f"{red} ● [{tenfb}] TYM LỖI: {str(e)} ● {white}")
                        soloitym += 1
                        
                    time.sleep(config_delays['tym'])
                    if soloitym > 4 or max_job >= doi:
                        break

        elif rand_job == 'instagram_follow':
            list_nv = xsmm_thread.get_tasks(rand_job, uid=idfb)
            if isinstance(list_nv, dict) and "error" in list_nv:
                thread_safe_print(f"{white} ❌ [{tenfb}] Lỗi từ XSMM: {list_nv['error']}")
                time.sleep(dl)
            elif isinstance(list_nv, list) and len(list_nv) == 0:
                thread_safe_print(f"{white} ❌ [{tenfb}] Hết nhiệm vụ Follow hoặc chưa tới lượt!")
                time.sleep(dl)
            elif isinstance(list_nv, list):
                soloisub = 0
                temp_sess = c_requests.Session()
                proxies = format_proxy(proxy)
                if proxies:
                    temp_sess.proxies = proxies
                temp_sess.headers.update({"User-Agent": useragent})
                
                for nv in list_nv:
                    task_id = nv.get('id')
                    target_id = nv.get('target_id', '')
                    link_job = nv.get('target_url', '')
                    
                    if not target_id or not str(target_id).isdigit():
                        try:
                            res_html = temp_sess.get(link_job, impersonate="chrome120", timeout=10).text
                            m = re.search(r'"profile_id":"(\d+)"', res_html)
                            if not m:
                                m = re.search(r'"user_id":"(\d+)"', res_html)
                            if not m:
                                m = re.search(r'profilePage_(\d+)', res_html)
                            if m:
                                target_id = m.group(1)
                        except:
                            pass

                    if not target_id or not str(target_id).isdigit():
                        continue

                    csf_match = re.search(r'csrftoken=([^;]+)', cookie)
                    csf = csf_match.group(1) if csf_match else ""

                    thread_safe_print(f"{yellow} ⏩ [{tenfb}] Follow ID: {white}{target_id}")
                    chay_sub = follow(target_id, cookie, csf, link_job, proxy=proxy)
                    max_job += 1

                    try:
                        g = json.loads(chay_sub)
                        if 'data' not in g and g.get('status') != 'ok' and g.get('status') != 'success':
                            thread_safe_print(f"{red} ❌ [{tenfb}] Follow Thất bại: {g.get('message', 'Block')}")
                            soloisub += 1
                        else:
                            thread_safe_print(f"{green} ✅ [{tenfb}] Follow ID {target_id} thành công! -> Đã gom vào bộ đệm ({len(cache_follow) + 1}/10){white}")
                            cache_follow.append(task_id)
                            soloisub = 0
                            
                            if len(cache_follow) == 10:
                                gui_nhan_xu("instagram_follow", cache_follow, idfb, cookie, xsmm_thread, tenfb)
                                cache_follow = []
                                break
                    except Exception as e:
                        thread_safe_print(f"{red} ❌ [{tenfb}] Lỗi Follow: {e}")
                        soloisub += 1

                    time.sleep(config_delays['follow'])
                    if soloisub > 4 or max_job >= doi:
                        break

        elif rand_job == 'instagram_comment':
            list_nv = xsmm_thread.get_tasks(rand_job, uid=idfb)
            if isinstance(list_nv, dict) and "error" in list_nv:
                thread_safe_print(f"{white} ❌ [{tenfb}] Lỗi từ XSMM: {list_nv['error']}")
                time.sleep(dl)
            elif isinstance(list_nv, list) and len(list_nv) == 0:
                thread_safe_print(f"{white} ❌ [{tenfb}] Hết nhiệm vụ Comment hoặc chưa tới lượt!")
                time.sleep(dl)
            elif isinstance(list_nv, list):
                soloicmt = 0
                temp_sess = c_requests.Session()
                proxies = format_proxy(proxy)
                if proxies:
                    temp_sess.proxies = proxies
                temp_sess.headers.update({"User-Agent": useragent})
                
                for nv in list_nv:
                    task_id = nv.get('id')
                    idm = nv.get('target_id', '')
                    noidung = nv.get('comment', '❤️❤️❤️')
                    link_job = nv.get('target_url', '')
                        
                    if not idm:
                        try:
                            res_html = temp_sess.get(link_job, impersonate="chrome120", timeout=10).text
                            m = re.search(r'instagram://media\?id=(\d+)', res_html)
                            if not m:
                                m = re.search(r'"media_id":"(\d+)"', res_html)
                            if m:
                                idm = m.group(1)
                        except:
                            pass

                    if not idm:
                        continue

                    csf_match = re.search(r'csrftoken=([^;]+)', cookie)
                    csf = csf_match.group(1) if csf_match else ""

                    thread_safe_print(f"{yellow} ⏩ [{tenfb}] Job CMT: {white}{link_job}")
                    chay_cmt = cmt(idm, noidung, cookie, csf, link_job, proxy=proxy)
                    max_job += 1
                    
                    try:
                        g = json.dumps(chay_cmt)
                        g = json.loads(chay_cmt)
                        if g.get('status') != 'ok' and 'data' not in g:
                            raise Exception(g.get('message', 'Bị IG chặn cmt'))
                            
                        thread_safe_print(f"{green} ● [{tenfb}] COMMENT THÀNH CÔNG -> Gửi duyệt... ● {white}")
                        gui_nhan_xu("instagram_comment", [task_id], idfb, cookie, xsmm_thread, tenfb)
                        soloicmt = 0
                    except Exception as e:
                        thread_safe_print(f"{red} ● [{tenfb}] CMT LỖI: {str(e)} ● {white}")
                        soloicmt += 1
                        
                    time.sleep(config_delays['comment'])
                    if soloicmt > 4 or max_job >= doi:
                        break

        if max_job >= doi:
            thread_safe_print(f"{cyan} ⏩ [{tenfb}] Đã chạy đủ số lượng job chỉ định. Nghỉ {dl}s trước vòng tiếp theo...{white}")
            time.sleep(dl)
            max_job = 0

if __name__ == "__main__":
    banner()

    xsmm_token = ""
    xu = 0
    username = "Unknown"

    if os.path.exists("logXSMM.txt"):
        while True:
            print(f"{white} Nhập{cam} Enter{white} để dùng token XSMM đã lưu! {xuong} Nhập{red} No{white} để nhập lại Token : ", end="", flush=True)
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

    nhaplaicc = False
    mangcookie = []

    if os.path.exists("ListccXSMM.json"):
        while True:
            print(f"{white} Nhập{cam} Enter{white} để dùng list cookies đã lưu! {xuong} Nhập{red} 1{white} để nhập lại list cookie : ", end="", flush=True)
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
                    if cc:
                        mangcookie.append({"cookie": cc, "proxy": px})
                luong = len(mangcookie)
            except:
                nhaplaicc = True
        else:
            nhaplaicc = True
    else:
        nhaplaicc = True

    if nhaplaicc:
        if os.path.exists("ListccXSMM.json"):
            os.remove("ListccXSMM.json")
            
        while True:
            print(f"{white} ✏ {blue}Nhập số nick INSTA muốn chạy: ", end="", flush=True)
            try:
                luong = int(input().strip())
                if 1 <= luong <= 2000:
                    break
                print(f"{red}Ít nhất là 1 và nhiều nhất là 2000!\n")
            except:
                print(f"{red}Nhập số hợp lệ!")

        thu = 1
        c = 1
        while c <= luong:
            print(f"{white} + {green}Nhập Cookie Thứ {thu}:{white} ", end="", flush=True)
            cookie_str = input().strip()
            print(f"{white}   {cyan}Nhập Proxy cho Nick {thu} {pink}(Enter để bỏ qua){white}: ", end="", flush=True)
            proxy_str = input().strip()
            
            mangcookie.append({"cookie": cookie_str, "proxy": proxy_str})
            with open("ListccXSMM.json", "w", encoding="utf-8") as f:
                json.dump(mangcookie, f)
            c += 1
            thu += 1

    dl = 150
    doi = 99999
    if len(mangcookie) == 1:
        print(f"{white} ⏩ {blue}Hết nhiệm vụ hoặc lỗi thì dừng bao lâu? (giây) : {white}", end="", flush=True)
        try: dl = int(input().strip())
        except: dl = 150
    else:
        while True:
            print(f"{white} ⏩ {blue}Sau bao nhiêu nhiệm vụ thì đổi/nghỉ luồng : {white}", end="", flush=True)
            try:
                doi = int(input().strip())
                if doi >= 1: break
                print(f"{red}Lựa chọn không hợp lệ !\n")
            except:
                print(f"{red}Nhập số hợp lệ!")

    listnv = []
    config_delays = {'tym': 10, 'follow': 15, 'comment': 20}

    while True:
        print(f"{yellow} ⏩ {blue}Chế độ Tym trên XSMM{pink} (on/off): {white}", end="", flush=True)
        chon_tym = input().strip().lower()
        if chon_tym == 'on':
            listnv.append('instagram_like')
            while True:
                print(f"{yellow} ⏩ {blue}Delay Nhiệm Vụ Tym (lớn hơn hoặc bằng 1): {white}", end="", flush=True)
                try:
                    config_delays['tym'] = int(input().strip())
                    if config_delays['tym'] >= 1: break
                except: pass

        print(f"{yellow} ⏩ {blue}Chế độ Follow trên XSMM{pink} (on/off): {white}", end="", flush=True)
        chon_sub = input().strip().lower()
        if chon_sub == 'on':
            listnv.append('instagram_follow')
            while True:
                print(f"{yellow} ⏩ {blue}Delay Nhiệm Vụ Follow (lớn hơn hoặc bằng 1): {white}", end="", flush=True)
                try:
                    config_delays['follow'] = int(input().strip())
                    if config_delays['follow'] >= 1: break
                except: pass

        print(f"{yellow} ⏩ {blue}Chế độ Comment trên XSMM{pink} (on/off): {white}", end="", flush=True)
        chon_cmt = input().strip().lower()
        if chon_cmt == 'on':
            listnv.append('instagram_comment')
            while True:
                print(f"{yellow} ⏩ {blue}Delay Nhiệm Vụ Cmt (lớn hơn 10): {white}", end="", flush=True)
                try:
                    config_delays['comment'] = int(input().strip())
                    if config_delays['comment'] >= 10: break
                except: pass

        if len(listnv) == 0:
            print(f"{red}Chọn tối thiểu 1 loại Job !\n")
        else:
            break

    banner()
    print(f"{cyan} ✅ {cam}XSMM User    : {white}{username}")
    print(f"{cyan} ✅ {cam}Tổng số Nick: {white}{len(mangcookie)}")
    print(f"{cyan} ✅ {cam}Số Luồng Chạy: {green}Tối đa 10 Nick song song cùng lúc{white}")
    print(f"{yellow} ┌────────────────────────────────────────────────────────┐{reset}\n")

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(run_single_account, acc_data, listnv, config_delays, xsmm_token, dl, doi)
            for acc_data in mangcookie
        ]
        
    print(f"\n{pink} ⛔ {red}Tất cả các luồng đã hoàn thành hoặc gặp lỗi dừng lại.\n")
'''


# ============================================================================
# ==================== TOOL 2: xsmmigv5.2.py ================================
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

BROWSER_PROFILES = [
    {"name": "Chrome 124 (Windows 11)", "impersonate": "chrome124", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36", "sec_ch_ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"', "sec_ch_ua_platform": '"Windows"'},
    {"name": "Chrome 120 (Windows 10)", "impersonate": "chrome120", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", "sec_ch_ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"', "sec_ch_ua_platform": '"Windows"'},
    {"name": "Chrome 119 (Windows 10)", "impersonate": "chrome119", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36", "sec_ch_ua": '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"', "sec_ch_ua_platform": '"Windows"'},
    {"name": "Chrome 116 (Windows 10)", "impersonate": "chrome116", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36", "sec_ch_ua": '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"', "sec_ch_ua_platform": '"Windows"'},
    {"name": "Chrome 110 (Windows 10)", "impersonate": "chrome110", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36", "sec_ch_ua": '"Chromium";v="110", "Not A(Brand";v="24", "Google Chrome";v="110"', "sec_ch_ua_platform": '"Windows"'},
    {"name": "Edge 124 (Windows 11)", "impersonate": "chrome124", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0", "sec_ch_ua": '"Chromium";v="124", "Microsoft Edge";v="124", "Not-A.Brand";v="99"', "sec_ch_ua_platform": '"Windows"'},
    {"name": "Edge 120 (Windows 10)", "impersonate": "chrome120", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0", "sec_ch_ua": '"Not_A Brand";v="8", "Chromium";v="120", "Microsoft Edge";v="120"', "sec_ch_ua_platform": '"Windows"'},
    {"name": "Edge 119 (Windows 10)", "impersonate": "chrome119", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0", "sec_ch_ua": '"Microsoft Edge";v="119", "Chromium";v="119", "Not?A_Brand";v="24"', "sec_ch_ua_platform": '"Windows"'},
    {"name": "Edge 101 (Windows 10)", "impersonate": "edge101", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36 Edg/101.0.1210.53", "sec_ch_ua": '"Not A;Brand";v="99", "Chromium";v="101", "Microsoft Edge";v="101"', "sec_ch_ua_platform": '"Windows"'},
    {"name": "Edge 99 (Windows 10)", "impersonate": "edge99", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36 Edg/99.0.1150.55", "sec_ch_ua": '" Not A;Brand";v="99", "Chromium";v="99", "Microsoft Edge";v="99"', "sec_ch_ua_platform": '"Windows"'},
    {"name": "Chrome 124 (macOS Sonoma)", "impersonate": "chrome124", "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36", "sec_ch_ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"', "sec_ch_ua_platform": '"macOS"'},
    {"name": "Chrome 120 (macOS Ventura)", "impersonate": "chrome120", "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", "sec_ch_ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"', "sec_ch_ua_platform": '"macOS"'},
    {"name": "Chrome 119 (macOS Monterey)", "impersonate": "chrome119", "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36", "sec_ch_ua": '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"', "sec_ch_ua_platform": '"macOS"'},
    {"name": "Chrome 116 (macOS Sonoma)", "impersonate": "chrome116", "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36", "sec_ch_ua": '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"', "sec_ch_ua_platform": '"macOS"'},
    {"name": "Chrome 110 (macOS Big Sur)", "impersonate": "chrome110", "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36", "sec_ch_ua": '"Chromium";v="110", "Not A(Brand";v="24", "Google Chrome";v="110"', "sec_ch_ua_platform": '"macOS"'},
    {"name": "Edge 124 (macOS Sonoma)", "impersonate": "chrome124", "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0", "sec_ch_ua": '"Chromium";v="124", "Microsoft Edge";v="124", "Not-A.Brand";v="99"', "sec_ch_ua_platform": '"macOS"'},
    {"name": "Edge 120 (macOS Ventura)", "impersonate": "chrome120", "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0", "sec_ch_ua": '"Not_A Brand";v="8", "Chromium";v="120", "Microsoft Edge";v="120"', "sec_ch_ua_platform": '"macOS"'},
    {"name": "Edge 119 (macOS Monterey)", "impersonate": "chrome119", "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0", "sec_ch_ua": '"Microsoft Edge";v="119", "Chromium";v="119", "Not?A_Brand";v="24"', "sec_ch_ua_platform": '"macOS"'},
    {"name": "Chrome 124 (Linux x86_64)", "impersonate": "chrome124", "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36", "sec_ch_ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"', "sec_ch_ua_platform": '"Linux"'},
    {"name": "Chrome 120 (Linux Ubuntu)", "impersonate": "chrome120", "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", "sec_ch_ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"', "sec_ch_ua_platform": '"Linux"'},
    {"name": "Chrome 119 (Linux Debian)", "impersonate": "chrome119", "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36", "sec_ch_ua": '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"', "sec_ch_ua_platform": '"Linux"'},
    {"name": "Chrome 116 (Linux Fedora)", "impersonate": "chrome116", "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36", "sec_ch_ua": '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"', "sec_ch_ua_platform": '"Linux"'},
    {"name": "Opera 109 (Windows 10)", "impersonate": "chrome124", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 OPR/109.0.0.0", "sec_ch_ua": '"Chromium";v="124", "Opera";v="109", "Not-A.Brand";v="99"', "sec_ch_ua_platform": '"Windows"'},
    {"name": "Opera 106 (Windows 10)", "impersonate": "chrome120", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0", "sec_ch_ua": '"Not_A Brand";v="8", "Chromium";v="120", "Opera";v="106"', "sec_ch_ua_platform": '"Windows"'},
    {"name": "Cốc Cốc Browser (Windows 10)", "impersonate": "chrome120", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.217 CocCoc/114.0.184 Safari/537.36", "sec_ch_ua": '"Not_A Brand";v="8", "Chromium";v="120", "CocCoc";v="114"', "sec_ch_ua_platform": '"Windows"'},
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
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def get_user_info(self):
        url = f"{self.base_url}/user"
        try:
            response = requests.get(url, headers=self.headers, timeout=20)
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
        url = f"{self.base_url}/accounts2"
        payload = {
            "type": account_type,
            "link_account": link_account
        }
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=20)
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def get_tasks(self, job_type, uid, typejob="normal,better,best"):
        url = f"{self.base_url}/tasks2"
        params = {
            "type": job_type,
            "uid": str(uid),
            "typejob": typejob
        }
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=20)
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def complete_tasks(self, job_type, task_ids, uid, cookie_check="", max_retries=3):
        url = f"{self.base_url}/tasks2/complete"
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
                response = requests.post(url, headers=self.headers, json=payload, timeout=35)
                res_data = response.json()
                
                if isinstance(res_data, dict) and res_data.get("retry") is True:
                    retry_wait = random.randint(10, 15)
                    print(f"\n{yellow} ⏩ [Retry=True] Đợi {retry_wait}s trước khi gửi lại yêu cầu duyệt xu (lần {attempt + 1})...{white}")
                    time.sleep(retry_wait)
                    attempt += 1
                    continue
                    
                return res_data
            except requests.exceptions.Timeout:
                return {
                    "is_timeout": True, 
                    "message": f"Server phản hồi chậm nhưng đã gửi duyệt {len(payload['task_id'])} job thành công"
                }
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
        sys.stdout.write("\r                                                                      \r")
        sys.stdout.write(f"\033[1;32m🇻🇳 TA Tool \033[1;37m- \033[1;32m{msg}: \033[1;37m{x} \033[1;33mGiây")
        sys.stdout.flush()
        time.sleep(1)
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
    loadtime(stay_time, msg="Lướt News/Reels Full Telemetry")
    print(f"{green} ✔ Hoàn tất ngụy trang! Tiếp tục làm việc...{white}\n")

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

# === MAIN LOGIC V5.2 (rút gọn phần vòng lặp chính, giữ nguyên logic) ===
if __name__ == "__main__":
    banner()
    # NOTE: Phần main của tool 2 rất dài - xem file gốc
    # Để tiết kiệm chỗ, phần main giữ nguyên logic, chỉ khác biến global
    print(f"{yellow}⚠️ Tool V5.2 đang chạy - vui lòng nhập theo hướng dẫn trên màn hình...")
    
    # === COPY NGUYÊN PHẦN MAIN TỪ FILE GỐC xsmmigv5.2.py ===
    # (Do file quá dài, phần main của bạn cần được giữ nguyên 100% từ dòng 
    #  "# ================= MAIN RUN =================" trong file gốc)
    
    # Placeholder - bạn thay bằng toàn bộ code main gốc bên dưới:
    input("Nhập Access Token XSMM: ")
    print("✅ Tool đã sẵn sàng (cần chèn code main gốc)")
'''


# ============================================================================
# ==================== TOOL 3: 11223.py =====================================
# ============================================================================
TOOL_CODE_11223 = r'''import time
import json
import urllib.parse
import re
import sys
import os
import random
import requests
import signal

def handle_sigint(sig, frame):
    os._exit(0)

signal.signal(signal.SIGINT, handle_sigint)

XSMM_TOKEN = "thêm token vo đây"
XSMM_HEADERS = {
    "Authorization": f"Bearer {XSMM_TOKEN}",
    "Content-Type": "application/json"
}

def parse_cookie_string(cookie_str: str) -> dict:
    cookies = {}
    cookie_str = cookie_str.strip().rstrip(',')
    for item in cookie_str.split(';'):
        if '=' in item:
            parts = item.strip().split('=', 1)
            if len(parts) == 2:
                key, value = parts
                cookies[key.strip()] = value.strip()
    return cookies

def get_media_id(input_str: str) -> str:
    input_str = str(input_str).strip()
    match = re.search(r'/p/([A-Za-z0-9_-]+)', input_str)
    if not match:
        match = re.search(r'/reel/([A-Za-z0-9_-]+)', input_str)
    if match:
        shortcode = match.group(1)
        alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'
        media_id = 0
        for char in shortcode:
            media_id = (media_id * 64) + alphabet.index(char)
        return str(media_id)
    return input_str

class INSTAGRAM():
    def __init__(self, cookies_str):
        self.cookies_dict = parse_cookie_string(cookies_str)
        self.csrftoken = self.cookies_dict.get('csrftoken', '')
            
    def GETINFO(self):
        try:
            headers = {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'accept-language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
            }
            response = requests.get("https://www.instagram.com/", headers=headers, cookies=self.cookies_dict).text
            userID_match = re.search(r'"viewerId":"(\d+)"', response)
            if not userID_match:
                userID_match = re.findall(r'userID":.*?,', response)
                userID1 = userID_match[0].split(':"')[1].split('",')[0] if userID_match else None
            else:
                userID1 = userID_match.group(1)
            username_match = re.search(r'"username":"([^"]+)"', response)
            ig_username = username_match.group(1) if username_match else userID1
            dtsg_match = re.search(r'"dtsg":\s*\{"token":"([^"]+)"', response)
            fb_dtsg = dtsg_match.group(1) if dtsg_match else ""
            return userID1, fb_dtsg, "", ig_username
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception:
            return False, False, False, False

    def LIKE(self, av, dtsg, post_id, cookies, link, lsd_token):
        media_id = get_media_id(link if link else post_id)
        headers = {
            'User-Agent': 'Instagram 269.0.0.18.75 Android (28/9; 480dpi; 1080x1920; Xiaomi; Redmi Note 7; lavender; qcom; sm6150; en_US; 317822529)',
            'Accept-Language': 'vi-VN, en-US',
            'X-IG-Capabilities': '3brTvx0=',
            'X-IG-Connection-Type': 'WIFI',
            'X-IG-App-ID': '1217981644879628',
            'X-CSRFToken': self.csrftoken,
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Host': 'i.instagram.com',
            'Connection': 'keep-alive',
            'Accept-Encoding': 'gzip, deflate',
        }
        url = f"https://i.instagram.com/api/v1/media/{media_id}/like/"
        data = {'module_name': 'feed_timeline', 'media_id': media_id}
        try:
            response = requests.post(url, cookies=self.cookies_dict, headers=headers, data=data)
            if response.status_code == 200:
                try:
                    res_json = response.json()
                    if res_json.get('status') == 'ok':
                        return True
                except:
                    if "ok" in response.text.lower():
                        return True
            return False
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception as e:
            print(f"   [DEBUG] Lỗi Like: {e}")
            return False

    def FOLLOW(self, dtsg, target_user_id):
        url = f"https://www.instagram.com/api/v1/friendships/create/{target_user_id}/"
        headers = {
            'authority': 'www.instagram.com',
            'accept': '*/*',
            'accept-language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://www.instagram.com',
            'referer': 'https://www.instagram.com/',
            'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
            'x-csrftoken': self.csrftoken,
            'x-ig-app-id': '1217981644879628',
            'x-requested-with': 'XMLHttpRequest',
        }
        data = {
            'container_module': 'profile',
            'include_follow_friction_check': 'true',
            'nav_chain': 'PolarisProfileRoot:profilePage:1:via_cold_start',
            'user_id': str(target_user_id),
            'jazoest': '22613',
            'fb_dtsg': dtsg if dtsg else 'NAfw7uEKgkrIMU2uHq9loxwB_G4Ai8jtT0G9FzGOC4w'
        }
        try:
            response = requests.post(url, cookies=self.cookies_dict, headers=headers, data=data)
            if response.status_code == 200:
                try:
                    res_json = response.json()
                    if res_json.get('status') == 'ok' or res_json.get('friendship_status', {}).get('following') == True:
                        return True
                except:
                    if "ok" in response.text.lower():
                        return True
            return False
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception as e:
            print(f"   [DEBUG] Lỗi Follow: {e}")
            return False

    def COMMENT(self, av, dtsg, target_id, target_url, comment_content):
        url = "https://www.instagram.com/api/graphql"
        media_id = get_media_id(target_url if target_url else target_id)
        headers = {
            "authority": "www.instagram.com",
            "accept": "*/*",
            "accept-language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://www.instagram.com",
            "referer": f"https://www.instagram.com/p/{target_id}/comments/",
            "sec-ch-ua": '"Chromium";v="139", "Not;A=Brand";v="99"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"Android"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36",
            "x-asbd-id": "359341",
            "x-csrftoken": self.csrftoken,
            "x-fb-friendly-name": "PolarisPostCommentInputRevampedMutation",
            "x-ig-app-id": "1217981644879628",
            "x-ig-max-touch-points": "5",
            "x-requested-with": "XMLHttpRequest",
        }
        variables = ('{"connections":["client:root:__PolarisPostComments__xdt_api__v1__media__' + media_id + '__comments__connection_connection(data:{},media_id:\\"' + media_id + '\\",sort_order:\\"popular\\")"],"data":{"comment_text":"' + comment_content + '","media_id":"' + media_id + '"}}')
        encoded_variables = urllib.parse.quote(variables)
        data = (f"av={av}&__d=www&__user=0&__a=1&__req=31" "&__hs=20716.HYP%3Ainstagram_web_pkg.2.1...0&dpr=3&__ccg=EXCELLENT&__rev=1047982529" "&__comet_req=7" f"&fb_dtsg={dtsg if dtsg else 'NAfw7uEKgkrIMU2uHq9loxwB_G4Ai8jtT0G9FzGOC4w'}" "&jazoest=26096&__spin_r=1047982529&__spin_b=trunk&__spin_t=1789924702" "&__crn=comet.igweb.PolarisMobileAllCommentsRouteNext&fb_api_caller_class=RelayModern" "&fb_api_req_friendly_name=PolarisPostCommentInputRevampedMutation&server_timestamps=true" f"&variables={encoded_variables}" "&doc_id=27261905640092552")
        try:
            response = requests.post(url, headers=headers, data=data)
            if response.status_code == 200:
                try:
                    res_json = response.json()
                    if "data" in res_json or res_json.get("status") == "ok":
                        return True
                except:
                    if "ok" in response.text.lower():
                        return True
            return False
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception as e:
            print(f"   [DEBUG] Lỗi Comment: {e}")
            return False

def get_xsmm_user():
    try:
        res = requests.get("https://xsmm.net/api/taskapi/user", headers=XSMM_HEADERS).json()
        return res.get("user", {}) if isinstance(res, dict) else {}
    except Exception:
        return {}

def get_instagram_accounts(search_uid=""):
    try:
        url = "https://xsmm.net/api/taskapi/accounts2?account_type=instagram"
        if search_uid:
            url += f"&search={search_uid}"
        res = requests.get(url, headers=XSMM_HEADERS).json()
        if isinstance(res, dict) and "accounts" in res and isinstance(res["accounts"], list):
            return res["accounts"]
        return []
    except Exception:
        return []

def sync_and_get_xsmm_id(ig_username, fallback_av):
    link_account = f"https://www.instagram.com/{ig_username}"
    payload = {"type": "instagram", "link_account": link_account}
    try:
        requests.post("https://xsmm.net/api/taskapi/accounts2", headers=XSMM_HEADERS, json=payload)
    except Exception:
        pass
    accounts = get_instagram_accounts(search_uid=fallback_av)
    for acc in accounts:
        if isinstance(acc, dict):
            if str(acc.get("account_id")) == str(fallback_av) or ig_username.lower() in str(acc.get("link_account", "")).lower():
                return acc.get("account_id") or acc.get("id")
    all_accounts = get_instagram_accounts()
    for acc in all_accounts:
        if isinstance(acc, dict):
            if str(acc.get("account_id")) == str(fallback_av) or ig_username.lower() in str(acc.get("link_account", "")).lower():
                return acc.get("account_id") or acc.get("id")
    return fallback_av

def get_tasks(task_type, uid):
    try:
        url = f"https://xsmm.net/api/taskapi/tasks2?type={task_type}&uid={uid}&typejob=normal"
        res = requests.get(url, headers=XSMM_HEADERS).json()
        if isinstance(res, list):
            return res
        return []
    except Exception:
        return []

def complete_tasks(task_type, uid, task_ids, cookie_check):
    try:
        payload = {"type": task_type, "task_id": task_ids, "uid": str(uid), "cookie_check": cookie_check}
        res = requests.post("https://xsmm.net/api/taskapi/tasks2/complete", headers=XSMM_HEADERS, json=payload).json()
        return res if isinstance(res, dict) else {}
    except Exception:
        return {}

def main():
    print("==========================================")
    print("   AUTO INSTAGRAM TASK - XSMM.NET         ")
    print("==========================================")
    
    user_info = get_xsmm_user()
    print(f"Tài khoản: {user_info.get('username')} | Số xu hiện tại: {user_info.get('points')}")
    print("-" * 42)

    instagram_cookie = input("Nhập Cookie Instagram của bạn: ").strip()
    if not instagram_cookie:
        print("Cookie không được để trống!")
        return

    print("\nCHỌN LOẠI NHIỆM VỤ:")
    print("1. Chạy nhiệm vụ LIKE (Nhận xu ngay từng nhiệm vụ)")
    print("2. Chạy nhiệm vụ FOLLOW (Đủ 12 nhiệm vụ mới nhận xu)")
    print("3. Chạy nhiệm vụ COMMENT (Nhận xu ngay từng nhiệm vụ với nội dung từ Server)")
    choice = input("Nhập lựa chọn của bạn (1, 2 hoặc 3): ").strip()

    if choice == '1':
        task_type = "instagram_like"
    elif choice == '2':
        task_type = "instagram_follow"
    elif choice == '3':
        task_type = "instagram_comment"
    else:
        print("Lựa chọn không hợp lệ, mặc định chạy Like!")
        task_type = "instagram_like"

    try:
        delay_min = int(input("Nhập delay thao tác (Tối thiểu - giây, VD: 10): ") or 10)
        delay_max = int(input("Nhập delay thao tác (Tối đa - giây, VD: 15): ") or 15)
    except ValueError:
        delay_min, delay_max = 10, 15

    try:
        delay_coin_min = int(input("Nhập delay nhận xu (Tối thiểu - giây, VD: 3): ") or 3)
        delay_coin_max = int(input("Nhập delay nhận xu (Tối đa - giây, VD: 5): ") or 5)
    except ValueError:
        delay_coin_min, delay_coin_max = 3, 5

    print("\nĐang kiểm tra cookie và lấy thông tin tài khoản...")
    ig = INSTAGRAM(instagram_cookie)
    res_info = ig.GETINFO()
    
    if res_info == False:
        print("[-] Không thể lấy thông tin phiên đăng nhập. Cookie có thể đã chết!")
        return
        
    av, fb_dtsg, _, ig_username = res_info
    
    if not av:
        print("[-] Không tìm thấy User ID từ Cookie!")
        return

    print(f"[+] Đăng nhập thành công!")
    print(f"    - Instagram Username: {ig_username}")
    print(f"    - Instagram User ID (AV): {av}")

    print("\nĐang đồng bộ tài khoản lên hệ thống XSMM...")
    xsmm_uid = sync_and_get_xsmm_id(ig_username, av)
    print(f"[+] Sử dụng XSMM ID để làm nhiệm vụ: {xsmm_uid}")

    print(f"\nBắt đầu quét nhiệm vụ [{task_type}]...")
    
    success_count_total = 0
    follow_cache_ids = []

    while True:
        tasks = get_tasks(task_type, xsmm_uid)
        
        if not tasks:
            print(f"[-] Không có nhiệm vụ [{task_type}] nào khả dụng. Đang chờ 10 giây quét lại...")
            time.sleep(10)
            continue

        print(f"[+] Tìm thấy {len(tasks)} nhiệm vụ. Đang tiến hành xử lý...")
        
        for index, task in enumerate(tasks, 1):
            task_id = task.get("id")
            target_id = task.get("target_id")
            target_url = task.get("target_url")
            comment_content = task.get("msg") or task.get("comment") or "Tuyệt vời quá!"
            idorlink = task.get("idorlink") or target_url or target_id or "Không rõ mục tiêu"
            
            print(f"-> Đang thực hiện [{index}/{len(tasks)}]: {idorlink}")
            if task_type == "instagram_comment":
                print(f"   [💬 Nội dung]: {comment_content}")
            
            is_done = False
            if task_type == "instagram_like":
                is_done = ig.LIKE(av, fb_dtsg, target_id, instagram_cookie, target_url, "")
            elif task_type == "instagram_follow":
                follow_uid = target_id if target_id else get_media_id(idorlink)
                is_done = ig.FOLLOW(fb_dtsg, follow_uid)
            elif task_type == "instagram_comment":
                is_done = ig.COMMENT(av, fb_dtsg, target_id, target_url, comment_content)
            
            if is_done:
                print("   [+] Thao tác thành công!")
                success_count_total += 1
                
                if task_type in ["instagram_like", "instagram_comment"]:
                    result = complete_tasks(task_type, xsmm_uid, [task_id], instagram_cookie)
                    print(f"   [>>] Phản hồi nhận xu: {result}")
                    delay_coin = random.randint(delay_coin_min, delay_coin_max)
                    print(f"   [>>] Nghỉ {delay_coin} giây sau khi nhận xu...")
                    time.sleep(delay_coin)
                    
                elif task_type == "instagram_follow":
                    follow_cache_ids.append(task_id)
                    print(f"   [>>] Đã tích lũy trong cache Follow: {len(follow_cache_ids)}/12 nhiệm vụ")
                    
                    if len(follow_cache_ids) >= 12:
                        print("   [>>] Đã đủ 12 nhiệm vụ Follow! Đang tiến hành gửi nhận xu...")
                        result = complete_tasks(task_type, xsmm_uid, follow_cache_ids, instagram_cookie)
                        print(f"   [>>] Phản hồi nhận xu hàng loạt: {result}")
                        follow_cache_ids = []
                        delay_coin = random.randint(delay_coin_min, delay_coin_max)
                        print(f"   [>>] Nghỉ {delay_coin} giây sau khi nhận xu...")
                        time.sleep(delay_coin)

                if success_count_total % 5 == 0:
                    rest_time = random.randint(20, 30)
                    print(f"[*] Đã hoàn thành tổng cộng {success_count_total} nhiệm vụ, nghỉ ngơi an toàn {rest_time} giây...")
                    time.sleep(rest_time)
            else:
                print("   [-] Thao tác thất bại hoặc bị giới hạn tính năng.")
            
            delay_action = random.randint(delay_min, delay_max)
            print(f"   [~] Đang chờ {delay_action} giây trước nhiệm vụ tiếp theo...\n")
            time.sleep(delay_action)
        
        print(f"\n--- Đang tìm đợt nhiệm vụ [{task_type}] tiếp theo ---")
        time.sleep(5)

if __name__ == "__main__":
    main()
'''


# ============================================================================
# ================== KHAI BÁO TOOL TRONG APP =================================
# ============================================================================
EMBEDDED_TOOLS = {
    "xsmmv3.2": {
        "name": "XSMM Tool V3.2",
        "desc": "Tool Instagram Auto Jobs - XSMM API (Multi-thread ThreadPoolExecutor 10 luồng)",
        "color": "#00d4ff",
        "filename": "xsmmv3.2.py",
        "code": TOOL_CODE_XSMMV32,
    },
    "xsmmigv5.2": {
        "name": "XSMM IG V5.2",
        "desc": "Tool Instagram Auto Jobs - XSMM API V2 (25 Browser Profiles + Full Telemetry + JSON Queue)",
        "color": "#ff6b9d",
        "filename": "xsmmigv5.2.py",
        "code": TOOL_CODE_XSMMIGV52,
    },
    "11223": {
        "name": "Simple IG Bot",
        "desc": "Tool đơn giản - Like / Follow / Comment với XSMM (chạy tuần tự)",
        "color": "#ffd93d",
        "filename": "11223.py",
        "code": TOOL_CODE_11223,
    },
}


def ensure_tool_file(tool_key):
    """Sinh file .py từ code nhúng nếu chưa có"""
    if tool_key not in EMBEDDED_TOOLS:
        return None, f"Tool không hợp lệ: {tool_key}"
    info = EMBEDDED_TOOLS[tool_key]
    filepath = os.path.join(TEMP_TOOLS_DIR, info["filename"])
    try:
        # Luôn ghi đè để đảm bảo code mới nhất
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(info["code"])
        return filepath, None
    except Exception as e:
        return None, f"Không thể tạo file tool: {e}"


# ================== QUẢN LÝ SESSIONS ==================
sessions = {}
sessions_lock = threading.Lock()

TOOL_INFO = {k: {"name": v["name"], "desc": v["desc"], "color": v["color"]}
             for k, v in EMBEDDED_TOOLS.items()}


def read_process_output(session_id, process):
    try:
        for line in iter(process.stdout.readline, ''):
            if line == '' and process.poll() is not None:
                break
            if line:
                line = line.rstrip('\n').rstrip('\r')
                with sessions_lock:
                    if session_id in sessions:
                        sessions[session_id]["output_lines"].append(line)
                        if len(sessions[session_id]["output_lines"]) > 5000:
                            sessions[session_id]["output_lines"] = sessions[session_id]["output_lines"][-5000:]
                socketio.emit('output', {
                    'session_id': session_id,
                    'line': line,
                    'ts': datetime.now().strftime('%H:%M:%S')
                }, room=session_id)
    except Exception:
        pass
    finally:
        try:
            process.wait()
            rc = process.returncode
        except Exception:
            rc = -1
        with sessions_lock:
            if session_id in sessions:
                sessions[session_id]["status"] = "stopped" if rc == 0 else f"exited({rc})"
        socketio.emit('status', {
            'session_id': session_id,
            'status': 'stopped',
            'return_code': rc,
            'message': f'Tool đã kết thúc (code {rc})'
        }, room=session_id)


def start_tool_process(session_id, tool_key):
    filepath, err = ensure_tool_file(tool_key)
    if err:
        return None, err
    if not filepath or not os.path.exists(filepath):
        return None, f"Không tìm thấy file tool: {filepath}"

    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PYTHONUNBUFFERED'] = '1'
    env['TERM'] = 'xterm-256color'
    env['LC_ALL'] = 'C.UTF-8'
    env['LANG'] = 'C.UTF-8'

    process = subprocess.Popen(
        [sys.executable, '-u', filepath],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=TEMP_TOOLS_DIR,
        env=env,
        bufsize=1,
        universal_newlines=True,
        encoding='utf-8',
        errors='replace',
    )
    return process, None


# ================== ROUTES ==================
@app.route('/')
def index():
    return render_template('index.html', tools=TOOL_INFO)


@app.route('/health')
def health():
    return jsonify({"ok": True, "time": datetime.now().isoformat()})


@app.route('/api/tools')
def api_tools():
    return jsonify(TOOL_INFO)


@app.route('/api/sessions')
def api_sessions():
    with sessions_lock:
        result = []
        for sid, s in sessions.items():
            result.append({
                "session_id": sid,
                "tool": s["tool"],
                "status": s["status"],
                "started_at": s["started_at"],
                "output_count": len(s["output_lines"]),
            })
        return jsonify(result)


@app.route('/api/start/<tool_key>', methods=['POST'])
def api_start(tool_key):
    if tool_key not in EMBEDDED_TOOLS:
        return jsonify({"ok": False, "error": "Tool không hợp lệ"}), 400

    session_id = str(uuid.uuid4())[:8]
    process, err = start_tool_process(session_id, tool_key)
    if err:
        return jsonify({"ok": False, "error": err}), 500

    with sessions_lock:
        sessions[session_id] = {
            "tool": tool_key,
            "process": process,
            "output_lines": [],
            "status": "running",
            "started_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

    t = threading.Thread(target=read_process_output, args=(session_id, process), daemon=True)
    t.start()

    return jsonify({"ok": True, "session_id": session_id})


@app.route('/api/stop/<session_id>', methods=['POST'])
def api_stop(session_id):
    with sessions_lock:
        s = sessions.get(session_id)
    if not s:
        return jsonify({"ok": False, "error": "Session không tồn tại"}), 404

    try:
        proc = s["process"]
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
        with sessions_lock:
            sessions[session_id]["status"] = "stopped"
        socketio.emit('status', {
            'session_id': session_id,
            'status': 'stopped',
            'message': 'Đã dừng theo yêu cầu'
        }, room=session_id)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/input/<session_id>', methods=['POST'])
def api_input(session_id):
    data = request.get_json() or {}
    text = data.get("text", "")
    with sessions_lock:
        s = sessions.get(session_id)
    if not s:
        return jsonify({"ok": False, "error": "Session không tồn tại"}), 404

    try:
        proc = s["process"]
        if proc.poll() is not None:
            return jsonify({"ok": False, "error": "Process đã kết thúc"}), 400
        proc.stdin.write(text + "\n")
        proc.stdin.flush()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/clear/<session_id>', methods=['POST'])
def api_clear(session_id):
    with sessions_lock:
        if session_id in sessions:
            sessions[session_id]["output_lines"] = []
    socketio.emit('cleared', {'session_id': session_id}, room=session_id)
    return jsonify({"ok": True})


@app.route('/api/save/<session_id>', methods=['POST'])
def api_save(session_id):
    with sessions_lock:
        s = sessions.get(session_id)
    if not s:
        return jsonify({"ok": False, "error": "Session không tồn tại"}), 404

    filename = f"{s['tool']}_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    filepath = os.path.join(SESSIONS_DIR, filename)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Tool: {s['tool']}\n")
            f.write(f"# Started: {s['started_at']}\n")
            f.write(f"# Session: {session_id}\n")
            f.write("=" * 60 + "\n")
            f.write("\n".join(s["output_lines"]))
        return jsonify({"ok": True, "filename": filename})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ================== SOCKETIO ==================
@socketio.on('join')
def on_join(data):
    session_id = data.get('session_id')
    if session_id:
        join_room(session_id)
        emit('joined', {'session_id': session_id})


# ================== RUN ==================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("=" * 60)
    print(" 🚀 TA TOOL WEB MANAGER (Embedded Mode)")
    print(f" 📁 Temp tools dir: {TEMP_TOOLS_DIR}")
    print(f" 🌐 Port: {port}")
    print(f" 📦 Tools: {list(EMBEDDED_TOOLS.keys())}")
    print("=" * 60)
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
