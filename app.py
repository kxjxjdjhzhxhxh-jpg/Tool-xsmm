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

TEMP_TOOLS_DIR = os.path.join(tempfile.gettempdir(), "ta_tool_embedded")
os.makedirs(TEMP_TOOLS_DIR, exist_ok=True)

# ============================================================================
# ==================== TOOL 1: xsmmv3.2.py (CÓ SỐ LUỒNG) ====================
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

xuong = "\n"
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
        try:
            return requests.get(f"{self.base_url}/user", headers=self.headers, timeout=20).json()
        except Exception as e:
            return {"error": str(e)}
    def get_accounts(self, account_type=None, search=None):
        params = {}
        if account_type: params['account_type'] = account_type
        if search: params['search'] = search
        try:
            return requests.get(f"{self.base_url}/accounts2", headers=self.headers, params=params, timeout=20).json()
        except Exception as e:
            return {"error": str(e)}
    def add_account(self, account_type, link_account):
        try:
            return requests.post(f"{self.base_url}/accounts2", headers=self.headers, json={"type": account_type, "link_account": link_account}, timeout=20).json()
        except Exception as e:
            return {"error": str(e)}
    def get_tasks(self, job_type, uid, typejob="normal,better,best"):
        params = {"type": job_type, "uid": str(uid), "typejob": typejob}
        try:
            return requests.get(f"{self.base_url}/tasks2", headers=self.headers, params=params, timeout=20).json()
        except Exception as e:
            return {"error": str(e)}
    def complete_tasks(self, job_type, task_ids, uid, cookie_check="", max_retries=3):
        payload = {
            "type": job_type,
            "task_id": task_ids if isinstance(task_ids, list) else [task_ids],
            "uid": str(uid),
            "cookie_check": cookie_check
        }
        attempt = 0
        while attempt < max_retries:
            try:
                response = requests.post(f"{self.base_url}/tasks2/complete", headers=self.headers, json=payload, timeout=35)
                res_data = response.json()
                if isinstance(res_data, dict) and res_data.get("retry") is True:
                    retry_wait = random.randint(1, 3)
                    thread_safe_print(f"\n{yellow} ⏩ [Retry=True] Đợi {retry_wait}s...{white}")
                    time.sleep(retry_wait)
                    attempt += 1
                    continue
                return res_data
            except requests.exceptions.Timeout:
                return {"is_timeout": True, "message": f"Server phản hồi chậm..."}
            except Exception as e:
                return {"error": str(e)}
        return {"error": "Đã thử lại nhiều lần"}

useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
sec_ch_ua_120 = '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'

def format_proxy(proxy_str):
    if not proxy_str: return None
    proxy_str = proxy_str.strip()
    if not proxy_str: return None
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

def get_ig_headers(cookie, csrftoken, referer="https://www.instagram.com/"):
    return {
        'accept': '*/*', 'accept-language': 'vi-VN,vi;q=0.9,en-US;q=0.6,en;q=0.5',
        'content-type': 'application/x-www-form-urlencoded', 'cookie': cookie,
        'origin': 'https://www.instagram.com', 'priority': 'u=1, i', 'referer': referer,
        'sec-ch-ua': sec_ch_ua_120, 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty', 'sec-fetch-mode': 'cors', 'sec-fetch-site': 'same-origin',
        'user-agent': useragent, 'x-asbd-id': '129477', 'x-csrftoken': csrftoken,
        'x-ig-app-id': '936619743392459', 'x-ig-www-claim': '0', 'x-requested-with': 'XMLHttpRequest'
    }

def check_cookie_ig(cookie, proxy=None):
    url = 'https://www.instagram.com/api/v1/accounts/edit/web_form_data/'
    headers = {
        'x-ig-app-id': '936619743392459', 'x-requested-with': 'XMLHttpRequest',
        'referer': 'https://www.instagram.com/accounts/edit/', 'cookie': cookie,
        'user-agent': useragent, 'sec-ch-ua': sec_ch_ua_120
    }
    proxies = format_proxy(proxy)
    try:
        return c_requests.get(url, headers=headers, proxies=proxies, impersonate="chrome120", timeout=30).text
    except:
        return "{}"

def follow(target_id, cookie, csrftoken, profile_url="", proxy=None):
    if not target_id: return '{"status": "error", "message": "Lỗi Target ID"}'
    cookie = unquote(cookie)
    session = c_requests.Session()
    proxies = format_proxy(proxy)
    if proxies: session.proxies = proxies
    for item in cookie.split(';'):
        if '=' in item:
            try:
                key, val = item.strip().split('=', 1)
                session.cookies.set(key, val, domain='.instagram.com')
            except: pass
    fb_dtsg, lsd, jazoest = "", "Jfq8VQNmkkkJufHSbEE9bf", "26328"
    try:
        res_home = session.get(profile_url if profile_url else "https://www.instagram.com/", impersonate="chrome120", timeout=10).text
        lsd_match = re.search(r'"LSD",\[\],{"token":"([^"]+)"}', res_home)
        if lsd_match: lsd = lsd_match.group(1)
        dtsg_match = re.search(r'"dtsg":\{"token":"([^"]+)"', res_home) or re.search(r'name="fb_dtsg" value="([^"]+)"', res_home)
        if dtsg_match: fb_dtsg = dtsg_match.group(1)
        jazoest_match = re.search(r'name="jazoest" value="(\d+)"', res_home)
        if jazoest_match: jazoest = jazoest_match.group(1)
    except: pass
    dynamic_csrftoken = session.cookies.get('csrftoken')
    if not dynamic_csrftoken:
        csf_match = re.search(r'csrftoken=([^;]+)', cookie)
        dynamic_csrftoken = csf_match.group(1) if csf_match else "missing"
    session.headers.update(get_ig_headers(cookie, dynamic_csrftoken, profile_url if profile_url else "https://www.instagram.com/"))
    actor_id_match = re.search(r'ds_user_id=(\d+)', cookie)
    actor_id = actor_id_match.group(1) if actor_id_match else "0"
    variables = {"target_user_id": str(target_id), "container_module": "profile",
                 "nav_chain": "PolarisFeedRoot:feedPage:5:topnav-link,PolarisProfileRoot:profilePage:6:unexpected"}
    data = {
        "av": actor_id, "__d": "www", "__user": "0", "__a": "1", "__req": "s",
        "__hs": "20702.HYP:instagram_web_pkg.2.1...0", "dpr": "1", "__ccg": "EXCELLENT",
        "__rev": "1046917461", "__comet_req": "7", "fb_dtsg": fb_dtsg, "jazoest": jazoest,
        "lsd": lsd, "fb_api_caller_class": "RelayModern",
        "fb_api_req_friendly_name": "usePolarisFollowMutation",
        "server_timestamps": "true", "doc_id": "26508036048874888", "variables": json.dumps(variables)
    }
    try:
        return session.post('https://www.instagram.com/api/graphql', data=data, impersonate="chrome120", timeout=15).text.strip()
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

def tym(mediaid, cookie, csrftoken, link_job="", proxy=None):
    if not mediaid: return '{"status": "error", "message": "Lỗi Media ID"}'
    cookie = unquote(cookie)
    session = c_requests.Session()
    proxies = format_proxy(proxy)
    if proxies: session.proxies = proxies
    for item in cookie.split(';'):
        if '=' in item:
            try:
                key, val = item.strip().split('=', 1)
                session.cookies.set(key, val, domain='.instagram.com')
            except: pass
    fb_dtsg, lsd, jazoest = "", "GyeZl-huflHZ0K5L3-pzBi", "26492"
    try:
        res_home = session.get("https://www.instagram.com/", impersonate="chrome120", timeout=10).text
        lsd_match = re.search(r'"LSD",\[\],{"token":"([^"]+)"}', res_home)
        if lsd_match: lsd = lsd_match.group(1)
        dtsg_match = re.search(r'"dtsg":\{"token":"([^"]+)"', res_home) or re.search(r'name="fb_dtsg" value="([^"]+)"', res_home)
        if dtsg_match: fb_dtsg = dtsg_match.group(1)
        jazoest_match = re.search(r'name="jazoest" value="(\d+)"', res_home)
        if jazoest_match: jazoest = jazoest_match.group(1)
    except: pass
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
            if tt_match: tracking_token = tt_match.group(1)
    except: pass
    variables = {"input": {"actor_id": actor_id, "client_mutation_id": str(random.randint(1000000, 9999999)),
                           "container_module": "single_post", "media_id": str(mediaid)}}
    if tracking_token: variables["input"]["tracking_token"] = tracking_token
    data = {
        "av": actor_id, "__d": "www", "__user": "0", "__a": "1", "__req": "h",
        "__hs": "20702.HYP:instagram_web_pkg.2.1...0", "dpr": "1", "__ccg": "EXCELLENT",
        "__rev": "1046913831", "__comet_req": "7", "fb_dtsg": fb_dtsg, "jazoest": jazoest,
        "lsd": lsd, "fb_api_caller_class": "RelayModern",
        "fb_api_req_friendly_name": "usePolarisLikeMediaXIGLikeMutation",
        "server_timestamps": "true", "doc_id": "27182485238052618", "variables": json.dumps(variables)
    }
    try:
        return session.post('https://www.instagram.com/api/graphql', data=data, impersonate="chrome120", timeout=15).text.strip()
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

def cmt(mediaid, text, cookie, csrftoken, link_job="", proxy=None):
    if not mediaid: return '{"status": "error", "message": "Lỗi Media ID"}'
    cookie = unquote(cookie)
    session = c_requests.Session()
    proxies = format_proxy(proxy)
    if proxies: session.proxies = proxies
    for item in cookie.split(';'):
        if '=' in item:
            try:
                key, val = item.strip().split('=', 1)
                session.cookies.set(key, val, domain='.instagram.com')
            except: pass
    fb_dtsg, lsd, jazoest = "", "9zei3OjvTBQ-9YG6E0OMzm", "26312"
    try:
        res_home = session.get(link_job if link_job else "https://www.instagram.com/", impersonate="chrome120", timeout=10).text
        lsd_match = re.search(r'"LSD",\[\],{"token":"([^"]+)"}', res_home)
        if lsd_match: lsd = lsd_match.group(1)
        dtsg_match = re.search(r'"dtsg":\{"token":"([^"]+)"', res_home) or re.search(r'name="fb_dtsg" value="([^"]+)"', res_home)
        if dtsg_match: fb_dtsg = dtsg_match.group(1)
        jazoest_match = re.search(r'name="jazoest" value="(\d+)"', res_home)
        if jazoest_match: jazoest = jazoest_match.group(1)
    except: pass
    dynamic_csrftoken = session.cookies.get('csrftoken')
    if not dynamic_csrftoken:
        csf_match = re.search(r'csrftoken=([^;]+)', cookie)
        dynamic_csrftoken = csf_match.group(1) if csf_match else "missing"
    session.headers.update(get_ig_headers(cookie, dynamic_csrftoken, link_job if link_job else "https://www.instagram.com/"))
    actor_id_match = re.search(r'ds_user_id=(\d+)', cookie)
    actor_id = actor_id_match.group(1) if actor_id_match else "0"
    variables = {
        "connections": [f'client:root:__PolarisPostComments__xdt_api__v1__media__media_id__comments__connection_connection(data:{{}},media_id:"{mediaid}",sort_order:"popular")'],
        "data": {"comment_text": text, "media_id": str(mediaid)}
    }
    data = {
        "av": actor_id, "__d": "www", "__user": "0", "__a": "1", "__req": "10",
        "__hs": "20702.HYP:instagram_web_pkg.2.1...0", "dpr": "1", "__ccg": "EXCELLENT",
        "__rev": "1046917461", "__comet_req": "7", "fb_dtsg": fb_dtsg, "jazoest": jazoest,
        "lsd": lsd, "fb_api_caller_class": "RelayModern",
        "fb_api_req_friendly_name": "PolarisPostCommentInputRevampedMutation",
        "server_timestamps": "true", "doc_id": "27261905640092552", "variables": json.dumps(variables)
    }
    try:
        return session.post('https://www.instagram.com/api/graphql', data=data, impersonate="chrome120", timeout=15).text.strip()
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

def gui_nhan_xu(job_type, task_list, uid, cookie_check, xsmm_instance, tenfb):
    if not task_list: return
    thread_safe_print(f"{yellow} ⏩ [{tenfb}] Gom đủ {len(task_list)} task -> Gửi duyệt...{white}")
    ck = xsmm_instance.complete_tasks(job_type, task_list, uid=uid, cookie_check=cookie_check)
    now = datetime.now().strftime("%H:%M:%S")
    if isinstance(ck, dict):
        if 'message' in ck:
            pts = ck.get('points', 0)
            thread_safe_print(f"[{now}] {green} ⏩ [{tenfb}] {ck['message']} (+{pts} xu){white}")
        elif ck.get("is_timeout"):
            thread_safe_print(f"[{now}] {cam} ⏩ [{tenfb}] {ck['message']}{white}")
        elif 'error' in ck:
            thread_safe_print(f"[{now}] {red} ⏩ [{tenfb}] LỖI: {ck['error']}{white}")
        if ck.get('countdown', 0) > 0:
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
    except Exception: is_live = False
    if not is_live or not idfb:
        thread_safe_print(f"{white} ⛔ {red}Cookie lỗi/Proxy die - Dừng luồng!{white}")
        return
    px_display = f" | Proxy: {proxy}" if proxy else " | Không Proxy"
    thread_safe_print(f"{green} ● NICK LIVE [{tenfb} | UID: {idfb}{px_display}] Bắt đầu... ● {white}")
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
                thread_safe_print(f"{green} ➕ Đã thêm [{tenfb}] vào XSMM!{white}")
    except Exception as e:
        thread_safe_print(f"{yellow} ⚠️ [{tenfb}] Sync lỗi: {e}{white}")
    max_job = 0
    cache_follow = []
    while True:
        rand_job = random.choice(listnv)
        if rand_job == 'instagram_like':
            list_nv = xsmm_thread.get_tasks(rand_job, uid=idfb)
            if isinstance(list_nv, list) and len(list_nv) > 0:
                soloitym = 0
                for nv in list_nv:
                    task_id = nv.get('id'); idm = nv.get('target_id', ''); link_job = nv.get('target_url', '')
                    csf_match = re.search(r'csrftoken=([^;]+)', cookie)
                    csf = csf_match.group(1) if csf_match else ""
                    thread_safe_print(f"{yellow} ⏩ [{tenfb}] Tym: {white}{link_job}")
                    chayfl = tym(idm, cookie, csf, link_job, proxy=proxy)
                    max_job += 1
                    try:
                        g = json.loads(chayfl)
                        if 'data' not in g and g.get('status') != 'ok': raise Exception(g.get('message', 'Block'))
                        thread_safe_print(f"{green} ● [{tenfb}] TYM OK -> Gửi xu ● {white}")
                        gui_nhan_xu("instagram_like", [task_id], idfb, cookie, xsmm_thread, tenfb)
                        soloitym = 0
                    except Exception as e:
                        thread_safe_print(f"{red} ● [{tenfb}] TYM LỖI: {e} ● {white}")
                        soloitym += 1
                    time.sleep(config_delays['tym'])
                    if soloitym > 4 or max_job >= doi: break
            else:
                time.sleep(dl)
        elif rand_job == 'instagram_follow':
            list_nv = xsmm_thread.get_tasks(rand_job, uid=idfb)
            if isinstance(list_nv, list) and len(list_nv) > 0:
                soloisub = 0
                for nv in list_nv:
                    task_id = nv.get('id'); target_id = nv.get('target_id', ''); link_job = nv.get('target_url', '')
                    if not target_id or not str(target_id).isdigit():
                        try:
                            temp_sess = c_requests.Session()
                            proxies = format_proxy(proxy)
                            if proxies: temp_sess.proxies = proxies
                            temp_sess.headers.update({"User-Agent": useragent})
                            res_html = temp_sess.get(link_job, impersonate="chrome120", timeout=10).text
                            m = re.search(r'"profile_id":"(\d+)"', res_html) or re.search(r'"user_id":"(\d+)"', res_html) or re.search(r'profilePage_(\d+)', res_html)
                            if m: target_id = m.group(1)
                        except: pass
                    if not target_id or not str(target_id).isdigit(): continue
                    csf_match = re.search(r'csrftoken=([^;]+)', cookie)
                    csf = csf_match.group(1) if csf_match else ""
                    thread_safe_print(f"{yellow} ⏩ [{tenfb}] Follow: {white}{target_id}")
                    chay_sub = follow(target_id, cookie, csf, link_job, proxy=proxy)
                    max_job += 1
                    try:
                        g = json.loads(chay_sub)
                        if 'data' not in g and g.get('status') != 'ok' and g.get('status') != 'success':
                            soloisub += 1
                        else:
                            cache_follow.append(task_id); soloisub = 0
                            thread_safe_print(f"{green} ✅ [{tenfb}] Follow {target_id} -> Gom ({len(cache_follow)}/10){white}")
                            if len(cache_follow) == 10:
                                gui_nhan_xu("instagram_follow", cache_follow, idfb, cookie, xsmm_thread, tenfb)
                                cache_follow = []; break
                    except: soloisub += 1
                    time.sleep(config_delays['follow'])
                    if soloisub > 4 or max_job >= doi: break
            else:
                time.sleep(dl)
        elif rand_job == 'instagram_comment':
            list_nv = xsmm_thread.get_tasks(rand_job, uid=idfb)
            if isinstance(list_nv, list) and len(list_nv) > 0:
                soloicmt = 0
                for nv in list_nv:
                    task_id = nv.get('id'); idm = nv.get('target_id', ''); noidung = nv.get('comment', '❤️❤️❤️'); link_job = nv.get('target_url', '')
                    if not idm:
                        try:
                            temp_sess = c_requests.Session()
                            proxies = format_proxy(proxy)
                            if proxies: temp_sess.proxies = proxies
                            res_html = temp_sess.get(link_job, impersonate="chrome120", timeout=10).text
                            m = re.search(r'instagram://media\?id=(\d+)', res_html) or re.search(r'"media_id":"(\d+)"', res_html)
                            if m: idm = m.group(1)
                        except: pass
                    if not idm: continue
                    csf_match = re.search(r'csrftoken=([^;]+)', cookie)
                    csf = csf_match.group(1) if csf_match else ""
                    thread_safe_print(f"{yellow} ⏩ [{tenfb}] CMT: {white}{link_job}")
                    chay_cmt = cmt(idm, noidung, cookie, csf, link_job, proxy=proxy)
                    max_job += 1
                    try:
                        g = json.loads(chay_cmt)
                        if g.get('status') != 'ok' and 'data' not in g: raise Exception(g.get('message', 'Block'))
                        thread_safe_print(f"{green} ● [{tenfb}] CMT OK -> Gửi xu ● {white}")
                        gui_nhan_xu("instagram_comment", [task_id], idfb, cookie, xsmm_thread, tenfb)
                        soloicmt = 0
                    except Exception as e:
                        thread_safe_print(f"{red} ● [{tenfb}] CMT LỖI: {e} ● {white}")
                        soloicmt += 1
                    time.sleep(config_delays['comment'])
                    if soloicmt > 4 or max_job >= doi: break
            else:
                time.sleep(dl)
        if max_job >= doi:
            thread_safe_print(f"{cyan} ⏩ [{tenfb}] Đủ job. Nghỉ {dl}s...{white}")
            time.sleep(dl)
            max_job = 0

def main():
    banner()
    xsmm_token = ""
    xu = 0
    username = "Unknown"

    sys.stdout.write(f"{white} ⏩ {green}Số luồng chạy song song (1-50): {white}")
    sys.stdout.flush()
    try:
        max_threads = int(input().strip())
        if max_threads < 1: max_threads = 1
        if max_threads > 50: max_threads = 50
    except: max_threads = 10
    print(f"{green} ✅ Sẽ chạy tối đa {max_threads} nick song song{white}\n")

    sys.stdout.write(f"{white} ⏩ {green}Access Token XSMM: {white}")
    sys.stdout.flush()
    xsmm_token = input().strip()
    try:
        with open("logXSMM.txt", "w") as f: json.dump({"token": xsmm_token}, f)
    except: pass

    xsmm = XSMMTool(token=xsmm_token)
    user_info = xsmm.get_user_info()
    if isinstance(user_info, dict) and "user" in user_info:
        xu = user_info["user"].get("points", 0)
        username = user_info["user"].get("username", "Unknown")
        print(f"\n{white} ✅ {green}Đăng nhập XSMM: {yellow}{username}{white} ({xu} xu)\n")
    else:
        print(f"\n{red} ❌ Token sai\n"); sys.exit()

    print(f"{white} ✏ {blue}Nhập số nick INSTA: {white}")
    sys.stdout.flush()
    try: luong = int(input().strip())
    except: luong = 1
    mangcookie = []
    thu = 1
    while len(mangcookie) < luong:
        print(f"{white} + {green}Cookie Thứ {thu}:{white} ")
        sys.stdout.flush()
        cookie_str = input().strip()
        print(f"{white}   {cyan}Proxy (Enter bỏ qua){white}: ")
        sys.stdout.flush()
        proxy_str = input().strip()
        if not cookie_str: continue
        mangcookie.append({"cookie": cookie_str, "proxy": proxy_str})
        thu += 1

    dl = 150
    doi = 99999
    if len(mangcookie) == 1:
        print(f"{white} ⏩ {blue}Dừng bao lâu khi hết job? (giây): {white}")
        sys.stdout.flush()
        try: dl = int(input().strip())
        except: dl = 150
    else:
        print(f"{white} ⏩ {blue}Bao nhiêu job thì đổi nick: {white}")
        sys.stdout.flush()
        try:
            doi = int(input().strip())
            if doi < 1: doi = 99999
        except: doi = 99999

    listnv = []
    config_delays = {'tym': 10, 'follow': 15, 'comment': 20}
    while True:
        print(f"{yellow} ⏩ {blue}Chế độ Tym (on/off): {white}")
        sys.stdout.flush()
        if input().strip().lower() == 'on':
            listnv.append('instagram_like')
            print(f"{yellow} ⏩ Delay Tym: {white}")
            sys.stdout.flush()
            try:
                config_delays['tym'] = int(input().strip())
                if config_delays['tym'] < 1: config_delays['tym'] = 10
            except: config_delays['tym'] = 10
        print(f"{yellow} ⏩ {blue}Chế độ Follow (on/off): {white}")
        sys.stdout.flush()
        if input().strip().lower() == 'on':
            listnv.append('instagram_follow')
            print(f"{yellow} ⏩ Delay Follow: {white}")
            sys.stdout.flush()
            try:
                config_delays['follow'] = int(input().strip())
                if config_delays['follow'] < 1: config_delays['follow'] = 15
            except: config_delays['follow'] = 15
        print(f"{yellow} ⏩ {blue}Chế độ CMT (on/off): {white}")
        sys.stdout.flush()
        if input().strip().lower() == 'on':
            listnv.append('instagram_comment')
            print(f"{yellow} ⏩ Delay CMT: {white}")
            sys.stdout.flush()
            try:
                config_delays['comment'] = int(input().strip())
                if config_delays['comment'] < 10: config_delays['comment'] = 20
            except: config_delays['comment'] = 20
        if len(listnv) == 0:
            print(f"{red}Chọn ít nhất 1 job!\n")
        else: break

    banner()
    print(f"{cyan} ✅ XSMM User    : {white}{username}")
    print(f"{cyan} ✅ Tổng số Nick: {white}{len(mangcookie)}")
    print(f"{cyan} ✅ Số Luồng     : {green}Tối đa {max_threads} Nick song song{white}")
    print(f"{yellow} ┌────────────────────────────────────────────┐{reset}\n")

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [executor.submit(run_single_account, acc_data, listnv, config_delays, xsmm_token, dl, doi) for acc_data in mangcookie]
    print(f"\n{pink} ⛔ {red}Hoàn thành!\n")

if __name__ == "__main__":
    main()
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

red = "\033[1;31m"; pink = "\033[1;35m"; green = "\033[1;32m"
yellow = "\033[1;33m"; white = "\033[0;37m"; cyan = "\033[1;36m"
blue = "\033[1;34m"; cam = "\033[38;5;208m"; reset = "\033[0m"

PENDING_FOLLOW_FILE = "pending_follow_tasks.json"

def get_pending_tasks(uid):
    if os.path.exists(PENDING_FOLLOW_FILE):
        try:
            with open(PENDING_FOLLOW_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get(str(uid), [])
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
    try:
        res_home = session.get(profile_url or "https://www.instagram.com/", impersonate=impersonate_browser, timeout=20).text
        lsd_match = re.search(r'"LSD",\[\],{"token":"([^"]+)"}', res_home)
        if lsd_match: lsd = lsd_match.group(1)
        dtsg_match = re.search(r'"dtsg":\{"token":"([^"]+)"', res_home) or re.search(r'name="fb_dtsg" value="([^"]+)"', res_home)
        if dtsg_match: fb_dtsg = dtsg_match.group(1)
        jazoest_match = re.search(r'name="jazoest" value="(\d+)"', res_home)
        if jazoest_match: jazoest = jazoest_match.group(1)
    except Exception: pass
    CACHE_TOKENS[uid] = (fb_dtsg, lsd, jazoest)
    return CACHE_TOKENS[uid]

BROWSER_PROFILES = [
    {"name": "Chrome 124", "impersonate": "chrome124", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36", "sec_ch_ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"', "sec_ch_ua_platform": '"Windows"'},
    {"name": "Chrome 120", "impersonate": "chrome120", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", "sec_ch_ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"', "sec_ch_ua_platform": '"Windows"'},
    {"name": "Edge 124", "impersonate": "chrome124", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0", "sec_ch_ua": '"Chromium";v="124", "Microsoft Edge";v="124"', "sec_ch_ua_platform": '"Windows"'},
]

def parse_range_input(v, d_min=10, d_max=10):
    v = str(v).strip()
    if not v: return d_min, d_max
    if '-' in v:
        try:
            a, b = v.split('-'); a=int(a.strip()); b=int(b.strip())
            return (a,b) if a<=b else (b,a)
        except Exception: return d_min, d_max
    try: s=int(v); return s,s
    except Exception: return d_min, d_max

def get_random_delay(r): return random.randint(r[0], r[1])

def format_proxy(p):
    if not p: return None
    p = p.strip()
    if not p: return None
    scheme = "http"
    if "://" in p: scheme, p = p.split("://", 1)
    parts = p.split(":")
    if len(parts) == 4:
        ip, port, user, pwd = parts
        return {"http": f"{scheme}://{user}:{pwd}@{ip}:{port}", "https": f"{scheme}://{user}:{pwd}@{ip}:{port}"}
    return {"http": f"{scheme}://{p}", "https": f"{scheme}://{p}"}

def get_ig_headers(cookie, csrftoken, referer="https://www.instagram.com/", profile=None):
    if not profile: profile = BROWSER_PROFILES[0]
    return {
        'accept': '*/*', 'accept-language': 'vi,en-US;q=0.9,en;q=0.8,vi-VN;q=0.7',
        'content-type': 'application/x-www-form-urlencoded', 'cookie': cookie,
        'origin': 'https://www.instagram.com', 'priority': 'u=1, i', 'referer': referer,
        'sec-ch-prefers-color-scheme': 'dark', 'sec-ch-ua': profile['sec_ch_ua'],
        'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': profile['sec_ch_ua_platform'],
        'sec-fetch-dest': 'empty', 'sec-fetch-mode': 'cors', 'sec-fetch-site': 'same-origin',
        'user-agent': profile['user_agent'], 'x-asbd-id': '359341', 'x-csrftoken': csrftoken,
        'x-ig-app-id': '936619743392459', 'x-ig-www-claim': '0', 'x-requested-with': 'XMLHttpRequest'
    }

def parse_follow_response(text):
    try: g = json.loads(text)
    except Exception as e: return False, f"Lỗi parse JSON: {e}"
    if not isinstance(g, dict): return False, "Invalid"
    if "errors" in g and g["errors"]:
        return False, g["errors"][0].get("message", "Lỗi GraphQL") if isinstance(g["errors"], list) else str(g["errors"])
    if g.get("status") == "fail": return False, g.get("message", "fail")
    data = g.get("data")
    if not data: return False, "No data"
    friendship = None
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, dict) and "friendship_status" in v:
                friendship = v.get("friendship_status"); break
            elif k == "friendship_status" and isinstance(v, dict):
                friendship = v; break
    if friendship and isinstance(friendship, dict):
        if friendship.get("outgoing_request") is True:
            return False, "Private - Chỉ gửi yêu cầu"
        if friendship.get("following") is True: return True, "OK"
        return False, "Chưa follow"
    if g.get("status") in ["ok", "success"]: return True, "OK"
    return False, "Unknown"

def parse_tym_cmt_response(text):
    try: g = json.loads(text)
    except Exception as e: return False, f"Lỗi parse: {e}"
    if not isinstance(g, dict): return False, "Invalid"
    if "errors" in g and g["errors"]:
        return False, g["errors"][0].get("message", "Lỗi") if isinstance(g["errors"], list) else str(g["errors"])
    if g.get("status") == "fail": return False, g.get("message", "fail")
    if g.get("data") is None and g.get("status") != "ok": return False, "No data"
    return True, "OK"

def check_cookie_ig(cookie, proxy=None, profile=None):
    if not profile: profile = BROWSER_PROFILES[0]
    url = 'https://www.instagram.com/api/v1/accounts/edit/web_form_data/'
    headers = {'x-ig-app-id': '936619743392459', 'x-requested-with': 'XMLHttpRequest',
               'referer': 'https://www.instagram.com/accounts/edit/', 'cookie': cookie,
               'user-agent': profile['user_agent'], 'sec-ch-ua': profile['sec_ch_ua'],
               'sec-ch-ua-platform': profile['sec_ch_ua_platform']}
    try:
        return c_requests.get(url, headers=headers, proxies=format_proxy(proxy), impersonate=profile["impersonate"], timeout=30).text
    except Exception: return "{}"

def follow(target_id, cookie, csrftoken, profile_url="", proxy=None, profile=None):
    if not profile: profile = BROWSER_PROFILES[0]
    if not target_id: return '{"status": "error", "message": "No target"}'
    cookie = unquote(cookie)
    session = c_requests.Session()
    proxies = format_proxy(proxy)
    if proxies: session.proxies = proxies
    for item in cookie.split(';'):
        if '=' in item:
            try:
                k, v = item.strip().split('=', 1); session.cookies.set(k, v, domain='.instagram.com')
            except Exception: pass
    fb_dtsg, lsd, jazoest = get_tokens_for_account(session, cookie, profile_url, profile["impersonate"])
    dyn_csrf = session.cookies.get('csrftoken')
    if not dyn_csrf:
        m = re.search(r'csrftoken=([^;]+)', cookie); dyn_csrf = m.group(1) if m else "missing"
    session.headers.update(get_ig_headers(cookie, dyn_csrf, profile_url or "https://www.instagram.com/", profile=profile))
    actor_id_match = re.search(r'ds_user_id=(\d+)', cookie)
    actor_id = actor_id_match.group(1) if actor_id_match else "0"
    variables = {"target_user_id": str(target_id), "container_module": "profile",
                 "nav_chain": "PolarisFeedRoot:feedPage:5:topnav-link,PolarisProfileRoot:profilePage:6:unexpected"}
    data = {"av": actor_id, "__d": "www", "__user": "0", "__a": "1", "__req": "s",
            "__hs": "20702.HYP:instagram_web_pkg.2.1...0", "dpr": "1", "__ccg": "EXCELLENT",
            "__rev": "1046917461", "__comet_req": "7", "fb_dtsg": fb_dtsg, "jazoest": jazoest,
            "lsd": lsd, "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "usePolarisFollowMutation",
            "server_timestamps": "true", "doc_id": "26508036048874888", "variables": json.dumps(variables)}
    for attempt in range(2):
        try:
            return session.post('https://www.instagram.com/api/graphql', data=data, impersonate=profile["impersonate"], timeout=30).text.strip()
        except Exception as e:
            if attempt == 0 and ("timed out" in str(e).lower() or "curl: (28)" in str(e).lower()):
                time.sleep(2); continue
            return json.dumps({"status": "error", "message": str(e)})

def tym(mediaid, cookie, csrftoken, link_job="", proxy=None, profile=None):
    if not profile: profile = BROWSER_PROFILES[0]
    if not mediaid: return '{"status": "error", "message": "No media"}'
    cookie = unquote(cookie)
    session = c_requests.Session()
    proxies = format_proxy(proxy)
    if proxies: session.proxies = proxies
    for item in cookie.split(';'):
        if '=' in item:
            try:
                k, v = item.strip().split('=', 1); session.cookies.set(k, v, domain='.instagram.com')
            except Exception: pass
    fb_dtsg, lsd, jazoest = get_tokens_for_account(session, cookie, link_job, profile["impersonate"])
    dyn_csrf = session.cookies.get('csrftoken')
    if not dyn_csrf:
        m = re.search(r'csrftoken=([^;]+)', cookie); dyn_csrf = m.group(1) if m else "missing"
    session.headers.update(get_ig_headers(cookie, dyn_csrf, link_job or "https://www.instagram.com/", profile=profile))
    actor_id_match = re.search(r'ds_user_id=(\d+)', cookie)
    actor_id = actor_id_match.group(1) if actor_id_match else "0"
    variables = {"input": {"actor_id": actor_id, "client_mutation_id": str(random.randint(1000000, 9999999)),
                           "container_module": "single_post", "media_id": str(mediaid)}}
    data = {"av": actor_id, "__d": "www", "__user": "0", "__a": "1", "__req": "h",
            "__hs": "20702.HYP:instagram_web_pkg.2.1...0", "dpr": "1", "__ccg": "EXCELLENT",
            "__rev": "1046913831", "__comet_req": "7", "fb_dtsg": fb_dtsg, "jazoest": jazoest,
            "lsd": lsd, "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "usePolarisLikeMediaXIGLikeMutation",
            "server_timestamps": "true", "doc_id": "27182485238052618", "variables": json.dumps(variables)}
    for attempt in range(2):
        try:
            return session.post('https://www.instagram.com/api/graphql', data=data, impersonate=profile["impersonate"], timeout=30).text.strip()
        except Exception as e:
            if attempt == 0 and ("timed out" in str(e).lower() or "curl: (28)" in str(e).lower()):
                time.sleep(2); continue
            return json.dumps({"status": "error", "message": str(e)})

def cmt(mediaid, text, cookie, csrftoken, link_job="", proxy=None, profile=None):
    if not profile: profile = BROWSER_PROFILES[0]
    if not mediaid: return '{"status": "error", "message": "No media"}'
    cookie = unquote(cookie)
    session = c_requests.Session()
    proxies = format_proxy(proxy)
    if proxies: session.proxies = proxies
    for item in cookie.split(';'):
        if '=' in item:
            try:
                k, v = item.strip().split('=', 1); session.cookies.set(k, v, domain='.instagram.com')
            except Exception: pass
    fb_dtsg, lsd, jazoest = get_tokens_for_account(session, cookie, link_job, profile["impersonate"])
    dyn_csrf = session.cookies.get('csrftoken')
    if not dyn_csrf:
        m = re.search(r'csrftoken=([^;]+)', cookie); dyn_csrf = m.group(1) if m else "missing"
    session.headers.update(get_ig_headers(cookie, dyn_csrf, link_job or "https://www.instagram.com/", profile=profile))
    actor_id_match = re.search(r'ds_user_id=(\d+)', cookie)
    actor_id = actor_id_match.group(1) if actor_id_match else "0"
    variables = {"connections": [f'client:root:__PolarisPostComments__xdt_api__v1__media__media_id__comments__connection_connection(data:{{}},media_id:"{mediaid}",sort_order:"popular")'],
                 "data": {"comment_text": text, "media_id": str(mediaid)}}
    data = {"av": actor_id, "__d": "www", "__user": "0", "__a": "1", "__req": "10",
            "__hs": "20702.HYP:instagram_web_pkg.2.1...0", "dpr": "1", "__ccg": "EXCELLENT",
            "__rev": "1046917461", "__comet_req": "7", "fb_dtsg": fb_dtsg, "jazoest": jazoest,
            "lsd": lsd, "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "PolarisPostCommentInputRevampedMutation",
            "server_timestamps": "true", "doc_id": "27261905640092552", "variables": json.dumps(variables)}
    for attempt in range(2):
        try:
            return session.post('https://www.instagram.com/api/graphql', data=data, impersonate=profile["impersonate"], timeout=30).text.strip()
        except Exception as e:
            if attempt == 0 and ("timed out" in str(e).lower() or "curl: (28)" in str(e).lower()):
                time.sleep(2); continue
            return json.dumps({"status": "error", "message": str(e)})

def gui_nhan_xu(job_type, task_list, uid, cookie_check, xsmm):
    if not task_list: return
    print(f"{yellow} ⏩ Gom {len(task_list)} task -> Gửi duyệt...{white}")
    ck = xsmm.complete_tasks(job_type, task_list, uid=uid, cookie_check=cookie_check)
    now = datetime.now().strftime("%H:%M:%S")
    if isinstance(ck, dict):
        if 'message' in ck:
            print(f"[{now}] {green} ⏩ {ck['message']} (+{ck.get('points', 0)} xu){white}")
        elif ck.get("is_timeout"):
            print(f"[{now}] {cam} ⏩ {ck['message']}{white}")
        elif 'error' in ck:
            print(f"[{now}] {red} ⏩ LỖI: {ck['error']}{white}")
        if ck.get('countdown', 0) > 0:
            time.sleep(ck['countdown'])

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
                r = requests.post(f"{self.base_url}/tasks2/complete", headers=self.headers, json=payload, timeout=35)
                res_data = r.json()
                if isinstance(res_data, dict) and res_data.get("retry") is True:
                    time.sleep(random.randint(10, 15)); attempt += 1; continue
                return res_data
            except requests.exceptions.Timeout:
                return {"is_timeout": True, "message": f"Timeout nhưng đã gửi {len(payload['task_id'])} job"}
            except Exception as e:
                return {"error": str(e)}
        return {"error": "Retry failed"}

def main():
    print(f"{cyan}🚀 Tool XSMM IG V5.2 khởi động...{reset}")
    print(f"{white} ⏩ {green}Access Token XSMM: {white}")
    sys.stdout.flush()
    xsmm_token = input().strip()

    print(f"{white} 📋 {cyan}Có Cookie Check riêng? [1=Có / 0=Không] {white}")
    sys.stdout.flush()
    choice_ck = input().strip()
    cookie_check_global = ""
    if choice_ck == '1':
        print(f"{white} ⏩ {green}Dán Cookie Check Web: {white}")
        sys.stdout.flush()
        cookie_check_global = input().strip()

    print(f"{white} ✏ {blue}Số nick INSTA: {white}")
    sys.stdout.flush()
    try: luong = int(input().strip())
    except: luong = 1
    mangcookie = []
    thu = 1
    while len(mangcookie) < luong:
        print(f"{white} + {green}Cookie App Thứ {thu}:{white} ")
        sys.stdout.flush()
        cookie_str = input().strip()
        print(f"{white}   {cyan}Proxy (Enter bỏ qua){white}: ")
        sys.stdout.flush()
        proxy_str = input().strip()
        if not cookie_str: continue
        prof = random.choice(BROWSER_PROFILES)
        access = check_cookie_ig(cookie_str, proxy_str, profile=prof)
        try:
            cfg = json.loads(access)
            if cfg and 'form_data' in cfg and cfg['form_data'].get('username'):
                mangcookie.append({"cookie": cookie_str, "proxy": proxy_str, "profile": prof})
                thu += 1
            else:
                print(f"{white} ⛔ {red}Cookie/Proxy lỗi\n")
        except Exception:
            print(f"{white} ⛔ {red}Cookie/Proxy lỗi\n")

    print(f"{white} ⏩ {blue}Sau bao nhiêu job thì đổi nick: {white}")
    sys.stdout.flush()
    try:
        doi = int(input().strip())
        if doi < 1: doi = 99999
    except: doi = 99999

    listnv = []
    delay_tym_range = (10, 15); delay_sub_range = (15, 20); delay_cmt_range = (20, 25)
    batch_sub_count = 10
    job_interleave_limits = {}

    print(f"{white} ⏩ {blue}Tym (on/off): {white}")
    sys.stdout.flush()
    if input().strip().lower() == 'on':
        listnv.append('instagram_like')
        print(f"{white} ⏩ Delay Tym: {white}"); sys.stdout.flush()
        delay_tym_range = parse_range_input(input().strip(), 10, 15)
        print(f"{white} ⏩ Số job Tym/lượt: {white}"); sys.stdout.flush()
        job_interleave_limits['instagram_like'] = parse_range_input(input().strip(), 3, 5)

    print(f"{white} ⏩ {blue}Follow (on/off): {white}")
    sys.stdout.flush()
    if input().strip().lower() == 'on':
        listnv.append('instagram_follow')
        print(f"{white} ⏩ Delay Follow: {white}"); sys.stdout.flush()
        delay_sub_range = parse_range_input(input().strip(), 15, 20)
        print(f"{white} ⏩ Số job Follow/lượt: {white}"); sys.stdout.flush()
        job_interleave_limits['instagram_follow'] = parse_range_input(input().strip(), 4, 6)
        print(f"{white} ⏩ Số job gom (3-12, default 10): {white}"); sys.stdout.flush()
        try:
            val = int(input().strip() or "10")
            if 3 <= val <= 12: batch_sub_count = val
        except: pass

    print(f"{white} ⏩ {blue}Comment (on/off): {white}")
    sys.stdout.flush()
    if input().strip().lower() == 'on':
        listnv.append('instagram_comment')
        print(f"{white} ⏩ Delay CMT: {white}"); sys.stdout.flush()
        delay_cmt_range = parse_range_input(input().strip(), 20, 25)
        print(f"{white} ⏩ Số job CMT/lượt: {white}"); sys.stdout.flush()
        job_interleave_limits['instagram_comment'] = parse_range_input(input().strip(), 2, 3)

    if len(listnv) == 0:
        print(f"{red}Chưa chọn job!\n"); sys.exit()

    print(f"\n{cyan}✅ Chạy {len(mangcookie)} nick - jobs: {listnv}{reset}\n")

    while True:
        for l in range(len(mangcookie)-1, -1, -1):
            acc_data = mangcookie[l]
            cookie = acc_data["cookie"]; proxy = acc_data.get("proxy", "")
            profile = acc_data.get("profile") or BROWSER_PROFILES[0]
            target_ck = cookie_check_global if cookie_check_global else cookie
            access = check_cookie_ig(cookie, proxy, profile=profile)
            is_live = False; tenfb = ""; idfb = ""
            try:
                cfg = json.loads(access)
                if cfg and 'form_data' in cfg and cfg['form_data'].get('username'):
                    is_live = True; tenfb = cfg['form_data']['username']
                    m = re.search(r'ds_user_id=(\d+)', cookie)
                    idfb = m.group(1) if m else str(cfg['form_data'].get('id', ''))
            except Exception: is_live = False
            if not is_live or not idfb:
                print(f"{white} ⛔ {red}Cookie die\n"); mangcookie.pop(l); continue

            print(f"{green} ● NICK [{tenfb} | UID: {idfb}] {cyan}Browser: {profile['name']}{white}")
            xsmm = XSMMTool(token=xsmm_token)
            try:
                acc_list = xsmm.get_accounts(account_type="instagram", search=idfb)
                exists = False
                if isinstance(acc_list, dict) and acc_list.get("accounts"):
                    for acc in acc_list["accounts"]:
                        if acc and (str(acc.get("account_id")) == str(idfb) or str(acc.get("name", "")).lower() == str(tenfb).lower()):
                            exists = True; break
                if not exists:
                    xsmm.add_account("instagram", f"https://www.instagram.com/{tenfb}")
                    print(f"{green} ➕ Đã thêm [{tenfb}]{white}")
            except Exception as e: pass

            max_job = 0; consecutive_empty = 0
            while max_job < doi:
                ct = random.choice(listnv)
                jl = get_random_delay(job_interleave_limits.get(ct, (3, 5)))
                jdt = 0
                if ct == 'instagram_like':
                    lv = xsmm.get_tasks(ct, uid=idfb)
                    if isinstance(lv, list) and len(lv) > 0:
                        consecutive_empty = 0; solo = 0
                        for nv in lv:
                            csf_m = re.search(r'csrftoken=([^;]+)', cookie); csf = csf_m.group(1) if csf_m else ""
                            print(f"{yellow} ⏩ [Tym]{white} {nv.get('target_url', '')}")
                            chayfl = tym(nv.get('target_id', ''), cookie, csf, nv.get('target_url', ''), proxy=proxy, profile=profile)
                            max_job += 1; jdt += 1
                            ok, err = parse_tym_cmt_response(chayfl)
                            if ok:
                                gui_nhan_xu("instagram_like", [nv.get('id')], idfb, target_ck, xsmm); solo = 0
                            else:
                                print(f"{red} ● LỖI: {err}{white}"); solo += 1
                            time.sleep(get_random_delay(delay_tym_range))
                            if solo > 4 or jdt >= jl or max_job >= doi: break
                    else: consecutive_empty += 1
                elif ct == 'instagram_follow':
                    lv = xsmm.get_tasks(ct, uid=idfb)
                    if isinstance(lv, list) and len(lv) > 0:
                        consecutive_empty = 0; solo = 0
                        for nv in lv:
                            tid = nv.get('target_id', ''); lj = nv.get('target_url', '')
                            print(f"{yellow} ⏩ [Follow]{white} {tid}")
                            if not tid or not str(tid).isdigit(): continue
                            csf_m = re.search(r'csrftoken=([^;]+)', cookie); csf = csf_m.group(1) if csf_m else ""
                            chay_sub = follow(tid, cookie, csf, lj, proxy=proxy, profile=profile)
                            max_job += 1; jdt += 1
                            ok, msg = parse_follow_response(chay_sub)
                            if ok:
                                add_pending_task(idfb, nv.get('id')); solo = 0
                                pend = get_pending_tasks(idfb)
                                print(f"{cyan} 📋 Gom: {len(pend)}/{batch_sub_count}{white}")
                            else:
                                print(f"{red} ❌ {msg}{white}")
                                if "Private" not in msg: solo += 1
                            time.sleep(get_random_delay(delay_sub_range))
                            pend = get_pending_tasks(idfb)
                            if len(pend) >= batch_sub_count:
                                tc = pend[:batch_sub_count]
                                gui_nhan_xu("instagram_follow", tc, idfb, target_ck, xsmm)
                                remove_pending_tasks(idfb, tc)
                            if solo > 4 or jdt >= jl or max_job >= doi: break
                    else: consecutive_empty += 1
                elif ct == 'instagram_comment':
                    lv = xsmm.get_tasks(ct, uid=idfb)
                    if isinstance(lv, list) and len(lv) > 0:
                        consecutive_empty = 0; solo = 0
                        for nv in lv:
                            idm = nv.get('target_id', ''); noidung = nv.get('comment', '❤️❤️❤️'); lj = nv.get('target_url', '')
                            print(f"{yellow} ⏩ [CMT]{white} {lj}")
                            if not idm: continue
                            csf_m = re.search(r'csrftoken=([^;]+)', cookie); csf = csf_m.group(1) if csf_m else ""
                            chay_cmt = cmt(idm, noidung, cookie, csf, lj, proxy=proxy, profile=profile)
                            max_job += 1; jdt += 1
                            ok, err = parse_tym_cmt_response(chay_cmt)
                            if ok:
                                gui_nhan_xu("instagram_comment", [nv.get('id')], idfb, target_ck, xsmm); solo = 0
                            else:
                                print(f"{red} ● LỖI: {err}{white}"); solo += 1
                            time.sleep(get_random_delay(delay_cmt_range))
                            if solo > 4 or jdt >= jl or max_job >= doi: break
                    else: consecutive_empty += 1

                if consecutive_empty >= len(listnv) * 2:
                    print(f"{white} ❌ {yellow}Hết job, chờ 30s...")
                    time.sleep(30); consecutive_empty = 0

            rem = get_pending_tasks(idfb)
            if len(rem) > 0:
                gui_nhan_xu("instagram_follow", rem, idfb, target_ck, xsmm)
                remove_pending_tasks(idfb, rem)

        if len(mangcookie) == 0:
            print(f"\n{pink} ⛔ {red}Hết cookie!{white}"); break

if __name__ == "__main__":
    main()
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

def handle_sigint(sig, frame): os._exit(0)
signal.signal(signal.SIGINT, handle_sigint)

XSMM_TOKEN = "thêm token vo đây"
XSMM_HEADERS = {"Authorization": f"Bearer {XSMM_TOKEN}", "Content-Type": "application/json"}

def parse_cookie_string(cookie_str):
    cookies = {}
    cookie_str = cookie_str.strip().rstrip(',')
    for item in cookie_str.split(';'):
        if '=' in item:
            parts = item.strip().split('=', 1)
            if len(parts) == 2:
                cookies[parts[0].strip()] = parts[1].strip()
    return cookies

def get_media_id(input_str):
    input_str = str(input_str).strip()
    match = re.search(r'/p/([A-Za-z0-9_-]+)', input_str) or re.search(r'/reel/([A-Za-z0-9_-]+)', input_str)
    if match:
        sc = match.group(1); alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'
        mid = 0
        for ch in sc: mid = (mid * 64) + alphabet.index(ch)
        return str(mid)
    return input_str

class INSTAGRAM():
    def __init__(self, cookies_str):
        self.cookies_dict = parse_cookie_string(cookies_str)
        self.csrftoken = self.cookies_dict.get('csrftoken', '')

    def GETINFO(self):
        try:
            headers = {'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                       'accept-language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
                       'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'}
            response = requests.get("https://www.instagram.com/", headers=headers, cookies=self.cookies_dict).text
            m = re.search(r'"viewerId":"(\d+)"', response)
            if not m:
                m2 = re.findall(r'userID":.*?,', response)
                userID1 = m2[0].split(':"')[1].split('",')[0] if m2 else None
            else: userID1 = m.group(1)
            um = re.search(r'"username":"([^"]+)"', response)
            ig_username = um.group(1) if um else userID1
            dm = re.search(r'"dtsg":\s*\{"token":"([^"]+)"', response)
            fb_dtsg = dm.group(1) if dm else ""
            return userID1, fb_dtsg, "", ig_username
        except Exception: return False, False, False, False

    def LIKE(self, av, dtsg, post_id, cookies, link, lsd_token):
        media_id = get_media_id(link if link else post_id)
        headers = {'User-Agent': 'Instagram 269.0.0.18.75 Android', 'X-IG-App-ID': '1217981644879628',
                   'X-CSRFToken': self.csrftoken, 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        try:
            r = requests.post(f"https://i.instagram.com/api/v1/media/{media_id}/like/", cookies=self.cookies_dict,
                              headers=headers, data={'module_name': 'feed_timeline', 'media_id': media_id})
            if r.status_code == 200:
                try:
                    if r.json().get('status') == 'ok': return True
                except:
                    if "ok" in r.text.lower(): return True
            return False
        except Exception: return False

    def FOLLOW(self, dtsg, target_user_id):
        url = f"https://www.instagram.com/api/v1/friendships/create/{target_user_id}/"
        headers = {'accept': '*/*', 'content-type': 'application/x-www-form-urlencoded',
                   'origin': 'https://www.instagram.com', 'referer': 'https://www.instagram.com/',
                   'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 Chrome/139.0.0.0 Mobile Safari/537.36',
                   'x-csrftoken': self.csrftoken, 'x-ig-app-id': '1217981644879628', 'x-requested-with': 'XMLHttpRequest'}
        data = {'container_module': 'profile', 'user_id': str(target_user_id), 'jazoest': '22613',
                'fb_dtsg': dtsg or 'NAfw7uEKgkrIMU2uHq9loxwB_G4Ai8jtT0G9FzGOC4w'}
        try:
            r = requests.post(url, cookies=self.cookies_dict, headers=headers, data=data)
            if r.status_code == 200:
                try:
                    j = r.json()
                    if j.get('status') == 'ok' or j.get('friendship_status', {}).get('following') == True: return True
                except:
                    if "ok" in r.text.lower(): return True
            return False
        except Exception: return False

    def COMMENT(self, av, dtsg, target_id, target_url, comment_content):
        url = "https://www.instagram.com/api/graphql"
        media_id = get_media_id(target_url if target_url else target_id)
        headers = {"accept": "*/*", "content-type": "application/x-www-form-urlencoded",
                   "origin": "https://www.instagram.com", "user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 Chrome/139.0.0.0 Mobile Safari/537.36",
                   "x-csrftoken": self.csrftoken, "x-ig-app-id": "1217981644879628", "x-requested-with": "XMLHttpRequest"}
        variables = ('{"connections":["client:root:__PolarisPostComments__xdt_api__v1__media__' + media_id + '__comments__connection_connection(data:{},media_id:\\"' + media_id + '\\",sort_order:\\"popular\\")"],"data":{"comment_text":"' + comment_content + '","media_id":"' + media_id + '"}}')
        data = (f"av={av}&__d=www&__user=0&__a=1&__req=31&__hs=20716.HYP%3Ainstagram_web_pkg&dpr=3&__ccg=EXCELLENT"
                f"&fb_dtsg={dtsg or 'NAfw7uEKgkrIMU2uHq9loxwB_G4Ai8jtT0G9FzGOC4w'}&jazoest=26096"
                "&fb_api_caller_class=RelayModern&fb_api_req_friendly_name=PolarisPostCommentInputRevampedMutation&server_timestamps=true"
                f"&variables={urllib.parse.quote(variables)}&doc_id=27261905640092552")
        try:
            r = requests.post(url, headers=headers, data=data)
            if r.status_code == 200:
                try:
                    j = r.json()
                    if "data" in j or j.get("status") == "ok": return True
                except:
                    if "ok" in r.text.lower(): return True
            return False
        except Exception: return False

def get_xsmm_user():
    try: return requests.get("https://xsmm.net/api/taskapi/user", headers=XSMM_HEADERS).json().get("user", {})
    except: return {}

def get_instagram_accounts(search_uid=""):
    try:
        url = "https://xsmm.net/api/taskapi/accounts2?account_type=instagram"
        if search_uid: url += f"&search={search_uid}"
        res = requests.get(url, headers=XSMM_HEADERS).json()
        return res.get("accounts", []) if isinstance(res, dict) else []
    except: return []

def sync_and_get_xsmm_id(ig_username, fallback_av):
    try:
        requests.post("https://xsmm.net/api/taskapi/accounts2", headers=XSMM_HEADERS,
                      json={"type": "instagram", "link_account": f"https://www.instagram.com/{ig_username}"})
    except: pass
    for acc in get_instagram_accounts(search_uid=fallback_av):
        if isinstance(acc, dict):
            if str(acc.get("account_id")) == str(fallback_av) or ig_username.lower() in str(acc.get("link_account", "")).lower():
                return acc.get("account_id") or acc.get("id")
    for acc in get_instagram_accounts():
        if isinstance(acc, dict):
            if str(acc.get("account_id")) == str(fallback_av) or ig_username.lower() in str(acc.get("link_account", "")).lower():
                return acc.get("account_id") or acc.get("id")
    return fallback_av

def get_tasks(task_type, uid):
    try:
        res = requests.get(f"https://xsmm.net/api/taskapi/tasks2?type={task_type}&uid={uid}&typejob=normal", headers=XSMM_HEADERS).json()
        return res if isinstance(res, list) else []
    except: return []

def complete_tasks(task_type, uid, task_ids, cookie_check):
    try:
        res = requests.post("https://xsmm.net/api/taskapi/tasks2/complete", headers=XSMM_HEADERS,
                            json={"type": task_type, "task_id": task_ids, "uid": str(uid), "cookie_check": cookie_check}).json()
        return res if isinstance(res, dict) else {}
    except: return {}

def main():
    print("==========================================")
    print("   AUTO INSTAGRAM TASK - XSMM.NET         ")
    print("==========================================")
    ui = get_xsmm_user()
    print(f"Tài khoản: {ui.get('username')} | Xu: {ui.get('points')}")
    print("-" * 42)

    print("Nhập Cookie Instagram:")
    sys.stdout.flush()
    insta_cookie = input().strip()
    if not insta_cookie:
        print("Cookie trống!"); return

    print("Chọn nhiệm vụ (1/2/3): 1=LIKE 2=FOLLOW 3=COMMENT")
    sys.stdout.flush()
    choice = input().strip()
    task_type = {"1": "instagram_like", "2": "instagram_follow", "3": "instagram_comment"}.get(choice, "instagram_like")

    print("Delay thao tác (min):"); sys.stdout.flush()
    try: dmin = int(input().strip() or 10)
    except: dmin = 10
    print("Delay thao tác (max):"); sys.stdout.flush()
    try: dmax = int(input().strip() or 15)
    except: dmax = 15
    print("Delay nhận xu (min):"); sys.stdout.flush()
    try: dcmin = int(input().strip() or 3)
    except: dcmin = 3
    print("Delay nhận xu (max):"); sys.stdout.flush()
    try: dcmax = int(input().strip() or 5)
    except: dcmax = 5

    print("\nĐang check cookie...")
    ig = INSTAGRAM(insta_cookie)
    info = ig.GETINFO()
    if info == False: print("Cookie die!"); return
    av, fb_dtsg, _, ig_username = info
    if not av: print("Không có UID!"); return
    print(f"[+] OK - Username: {ig_username} - AV: {av}")
    xsmm_uid = sync_and_get_xsmm_id(ig_username, av)
    print(f"[+] XSMM UID: {xsmm_uid}")
    print(f"\nBắt đầu quét [{task_type}]...")

    total = 0; cache = []
    while True:
        tasks = get_tasks(task_type, xsmm_uid)
        if not tasks:
            print("[-] Không có job. Chờ 10s..."); time.sleep(10); continue
        print(f"[+] {len(tasks)} job.")
        for i, task in enumerate(tasks, 1):
            tid = task.get("id"); target_id = task.get("target_id"); target_url = task.get("target_url")
            cmt_content = task.get("msg") or task.get("comment") or "Tuyệt vời!"
            idorlink = task.get("idorlink") or target_url or target_id or "?"
            print(f"-> [{i}/{len(tasks)}]: {idorlink}")
            is_done = False
            if task_type == "instagram_like": is_done = ig.LIKE(av, fb_dtsg, target_id, insta_cookie, target_url, "")
            elif task_type == "instagram_follow": is_done = ig.FOLLOW(fb_dtsg, target_id if target_id else get_media_id(idorlink))
            elif task_type == "instagram_comment": is_done = ig.COMMENT(av, fb_dtsg, target_id, target_url, cmt_content)

            if is_done:
                print("   [+] OK"); total += 1
                if task_type in ["instagram_like", "instagram_comment"]:
                    res = complete_tasks(task_type, xsmm_uid, [tid], insta_cookie)
                    print(f"   [>>] Nhận xu: {res}")
                    time.sleep(random.randint(dcmin, dcmax))
                elif task_type == "instagram_follow":
                    cache.append(tid); print(f"   [>>] Cache: {len(cache)}/12")
                    if len(cache) >= 12:
                        res = complete_tasks(task_type, xsmm_uid, cache, insta_cookie)
                        print(f"   [>>] Nhận xu: {res}")
                        cache = []; time.sleep(random.randint(dcmin, dcmax))
                if total % 5 == 0:
                    r = random.randint(20, 30); print(f"[*] Nghỉ {r}s..."); time.sleep(r)
            else: print("   [-] Fail")
            d = random.randint(dmin, dmax); time.sleep(d)
        print("--- Đợt tiếp theo ---"); time.sleep(5)

if __name__ == "__main__":
    main()
'''
# ============================================================================
# ==================== TOOL 4: autoaddfb (userscript) =======================
# ============================================================================
TOOL_CODE_AUTOADDFB = r'''// ==UserScript==
// @name         Facebook Friends Suite – CEO Edition
// @namespace    http://tampermonkey.net/
// @version      4.0-CEO
// @description  Premium Auto Friend/Unfriend Tool – Chuyên nghiệp, tối ưu, responsive, thương hiệu VNDEVCODE.COM
// @author       Trần Hào Dev | VNDEVCODE
// @match        *://*.facebook.com/*
// @match        *://facebook.com/*
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    let running = false;
    let done = 0;
    let limit = 50;
    let delay = 800;
    let speedMode = 'normal';
    let startTime = 0;
    let errorCount = 0;
    let successCount = 0;

    const sleep = ms => new Promise(res => setTimeout(res, ms));

    const style = document.createElement('style');
    style.textContent = `
        @import url('https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,300..700&display=swap');
        #vnd-tool {
            position: fixed; bottom: 28px; right: 28px; z-index: 999999;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            width: 340px; max-width: calc(100vw - 56px);
            background: #0b0e1a; border-radius: 24px; padding: 0;
            box-shadow: 0 24px 80px rgba(0,0,0,0.8), 0 0 0 1px rgba(255,215,0,0.12);
            color: #f0f0f0; transition: all 0.4s cubic-bezier(0.22, 1, 0.36, 1);
            border: 1px solid rgba(255,215,0,0.08);
            backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
            overflow: hidden; user-select: none; letter-spacing: 0.01em;
        }
        #vnd-tool::before { content: ''; position: absolute; inset: 0;
            background: radial-gradient(ellipse at 20% 20%, rgba(255,215,0,0.04), transparent 60%),
                        radial-gradient(ellipse at 80% 80%, rgba(0,200,180,0.02), transparent 50%);
            pointer-events: none; }
        #vnd-tool * { box-sizing: border-box; }
        .vnd-header { position: relative; padding: 16px 20px 12px;
            background: linear-gradient(135deg, rgba(255,215,0,0.06), transparent 60%);
            border-bottom: 1px solid rgba(255,215,0,0.06); display: flex; align-items: center; gap: 12px; }
        .vnd-brand { display: flex; align-items: center; gap: 10px; flex: 1; }
        .vnd-logo { width: 36px; height: 36px; background: linear-gradient(135deg, #f7b731, #f5a623);
            border-radius: 10px; display: flex; align-items: center; justify-content: center;
            font-size: 16px; font-weight: 800; color: #0b0e1a;
            box-shadow: 0 4px 16px rgba(247, 183, 49, 0.25); flex-shrink: 0; }
        .vnd-title { font-size: 17px; font-weight: 700; letter-spacing: -0.3px;
            background: linear-gradient(90deg, #f7b731, #f5a623); -webkit-background-clip: text;
            -webkit-text-fill-color: transparent; background-clip: text; }
        .vnd-sub { font-size: 9px; font-weight: 600; letter-spacing: 1.2px; text-transform: uppercase;
            color: rgba(255,255,255,0.25); margin-top: 1px; }
        .vnd-badge { background: rgba(255,215,0,0.12); border: 1px solid rgba(255,215,0,0.15);
            color: #f7b731; font-size: 8px; font-weight: 700; padding: 2px 10px; border-radius: 20px;
            letter-spacing: 0.8px; text-transform: uppercase; flex-shrink: 0; }
        .vnd-toggle { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.06);
            color: rgba(255,255,255,0.3); width: 28px; height: 28px; border-radius: 8px; cursor: pointer;
            font-size: 16px; display: flex; align-items: center; justify-content: center;
            transition: 0.2s; flex-shrink: 0; }
        .vnd-toggle:hover { background: rgba(255,255,255,0.08); color: #fff; }
        .vnd-body { padding: 16px 20px 20px; position: relative; }
        .vnd-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 16px; }
        .vnd-stat { background: rgba(255,255,255,0.03); border-radius: 14px; padding: 10px 6px;
            text-align: center; border: 1px solid rgba(255,255,255,0.04); transition: 0.2s; }
        .vnd-stat:hover { background: rgba(255,255,255,0.05); }
        .vnd-stat-value { font-size: 22px; font-weight: 700; letter-spacing: -0.5px; display: block; line-height: 1.2; }
        .vnd-stat-value.gold { color: #f7b731; }
        .vnd-stat-value.green { color: #4ade80; }
        .vnd-stat-value.red { color: #f87171; }
        .vnd-stat-label { font-size: 9px; color: rgba(255,255,255,0.3); font-weight: 600;
            text-transform: uppercase; letter-spacing: 0.8px; margin-top: 4px; display: block; }
        .vnd-controls { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; }
        .vnd-input-group { flex: 1; min-width: 80px; background: rgba(255,255,255,0.04);
            border-radius: 12px; padding: 4px 10px 4px 12px; display: flex; align-items: center; gap: 6px;
            border: 1px solid rgba(255,255,255,0.06); }
        .vnd-input-group .vnd-label { font-size: 11px; color: rgba(255,255,255,0.3); font-weight: 600; }
        .vnd-input-group input { background: transparent; border: none; color: #fff; font-weight: 600;
            font-size: 14px; width: 50px; text-align: center; outline: none; padding: 4px 0; }
        .vnd-speed { display: flex; gap: 4px; background: rgba(255,255,255,0.04); border-radius: 12px;
            padding: 3px; border: 1px solid rgba(255,255,255,0.06); }
        .vnd-speed-btn { padding: 4px 12px; border: none; border-radius: 8px; font-size: 10px;
            font-weight: 700; text-transform: uppercase; cursor: pointer; transition: 0.2s;
            color: rgba(255,255,255,0.3); background: transparent; letter-spacing: 0.5px; }
        .vnd-speed-btn.active { background: linear-gradient(135deg, #f7b731, #f5a623);
            color: #0b0e1a; box-shadow: 0 2px 12px rgba(247, 183, 49, 0.2); }
        .vnd-buttons { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 14px; }
        .vnd-btn { padding: 10px 6px; border: none; border-radius: 14px; font-weight: 700;
            font-size: 13px; cursor: pointer; transition: all 0.25s; display: flex;
            align-items: center; justify-content: center; gap: 6px; color: #fff; position: relative; overflow: hidden; }
        .vnd-btn-add { background: linear-gradient(135deg, #0ea5e9, #06b6d4);
            box-shadow: 0 4px 16px rgba(6, 182, 212, 0.2); }
        .vnd-btn-add:hover:not(:disabled) { transform: translateY(-2px); }
        .vnd-btn-cancel { background: linear-gradient(135deg, #f43f5e, #e11d48);
            box-shadow: 0 4px 16px rgba(225, 29, 72, 0.2); }
        .vnd-btn-cancel:hover:not(:disabled) { transform: translateY(-2px); }
        .vnd-btn-stop { grid-column: 1 / -1; background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.08); color: rgba(255,255,255,0.5); }
        .vnd-btn:disabled { opacity: 0.35; cursor: not-allowed; }
        .vnd-progress { background: rgba(255,255,255,0.05); border-radius: 20px; height: 3px;
            overflow: hidden; margin-bottom: 12px; }
        .vnd-progress .vnd-bar { height: 100%; width: 0%; background: linear-gradient(90deg, #f7b731, #f5a623);
            border-radius: 20px; transition: width 0.3s ease; }
        .vnd-status { display: flex; justify-content: space-between; align-items: center;
            font-size: 12px; flex-wrap: wrap; gap: 4px; }
        .vnd-status-left { display: flex; align-items: center; gap: 8px; }
        .vnd-dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; }
        .vnd-dot.idle { background: #4b5563; }
        .vnd-dot.running { background: #4ade80; box-shadow: 0 0 12px rgba(74, 222, 128, 0.4);
            animation: pulse 0.8s ease-in-out infinite; }
        .vnd-dot.done { background: #f7b731; }
        .vnd-dot.error { background: #f87171; }
        @keyframes pulse { 0%, 100% { transform: scale(1); opacity: 1; } 50% { transform: scale(1.6); opacity: 0.5; } }
        .vnd-status-text { color: rgba(255,255,255,0.55); font-weight: 500; }
        .vnd-status-text strong { color: #fff; font-weight: 600; }
        .vnd-footer { text-align: center; font-size: 9px; color: rgba(255,255,255,0.12);
            letter-spacing: 1px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.04); margin-top: 4px; }
        .vnd-footer a { color: rgba(255,215,0,0.4); text-decoration: none; }
        #vnd-trigger { position: fixed; bottom: 28px; right: 28px; z-index: 999998;
            width: 52px; height: 52px; border-radius: 50%;
            background: linear-gradient(135deg, #f7b731, #f5a623); border: none;
            color: #0b0e1a; font-size: 24px; cursor: pointer;
            box-shadow: 0 8px 32px rgba(247, 183, 49, 0.35);
            transition: all 0.3s; display: none; align-items: center; justify-content: center;
            font-weight: 900; }
        #vnd-trigger:hover { transform: scale(1.08) rotate(8deg); }
        #vnd-trigger.show { display: flex; }
        @media (max-width: 640px) {
            #vnd-tool { bottom: 16px; right: 16px; left: 16px; width: auto; max-width: none; border-radius: 20px; }
        }
        #vnd-tool.hidden { transform: translateY(calc(100% + 50px)) scale(0.96); opacity: 0; pointer-events: none; }
        #vnd-tool:not(.hidden) { transform: translateY(0) scale(1); opacity: 1; }
    `;
    document.head.appendChild(style);

    const container = document.createElement('div');
    container.id = 'vnd-tool';
    container.innerHTML = `
        <div class="vnd-header">
            <div class="vnd-brand">
                <div class="vnd-logo">V</div>
                <div>
                    <div class="vnd-title">AUTO KB Facebook</div>
                    <div class="vnd-sub">VNDEVCODE.COM</div>
                </div>
            </div>
            <span class="vnd-badge">Milk</span>
            <button class="vnd-toggle" id="vnd-toggle" title="Thu gọn">−</button>
        </div>
        <div class="vnd-body">
            <div class="vnd-stats">
                <div class="vnd-stat"><span class="vnd-stat-value gold" id="vnd-done">0</span><span class="vnd-stat-label">Đã xử lý</span></div>
                <div class="vnd-stat"><span class="vnd-stat-value green" id="vnd-success">0</span><span class="vnd-stat-label">Thành công</span></div>
                <div class="vnd-stat"><span class="vnd-stat-value red" id="vnd-errors">0</span><span class="vnd-stat-label">Lỗi</span></div>
            </div>
            <div class="vnd-controls">
                <div class="vnd-input-group">
                    <span class="vnd-label">🎯</span>
                    <input type="number" id="vnd-limit" value="50" min="1" max="999">
                </div>
                <div class="vnd-speed" id="vnd-speed-group">
                    <button class="vnd-speed-btn" data-speed="fast">⚡ Nhanh</button>
                    <button class="vnd-speed-btn active" data-speed="normal">● Vừa</button>
                    <button class="vnd-speed-btn" data-speed="slow">🐢 Chậm</button>
                </div>
            </div>
            <div class="vnd-buttons">
                <button class="vnd-btn vnd-btn-add" id="vnd-add">➕ Thêm bạn</button>
                <button class="vnd-btn vnd-btn-cancel" id="vnd-cancel">✖ Hủy lời mời</button>
                <button class="vnd-btn vnd-btn-stop" id="vnd-stop">⏹ Dừng tất cả</button>
            </div>
            <div class="vnd-progress"><div class="vnd-bar" id="vnd-progress-bar"></div></div>
            <div class="vnd-status">
                <div class="vnd-status-left">
                    <span class="vnd-dot idle" id="vnd-dot"></span>
                    <span class="vnd-status-text" id="vnd-status-text">💤 Sẵn sàng</span>
                </div>
                <div class="vnd-status-right">
                    <span class="vnd-done" id="vnd-count-done">0</span> / <span class="vnd-total" id="vnd-count-total">0</span>
                </div>
            </div>
            <div class="vnd-footer">
                <a href="https://vndevcode.com" target="_blank">VNDEVCODE.COM</a>  •  v4.0
            </div>
        </div>
    `;
    document.body.appendChild(container);

    const trigger = document.createElement('button');
    trigger.id = 'vnd-trigger';
    trigger.textContent = '⚡';
    document.body.appendChild(trigger);

    const $ = id => document.getElementById(id);
    const doneEl = $('vnd-done'); const successEl = $('vnd-success'); const errorsEl = $('vnd-errors');
    const limitInput = $('vnd-limit'); const progressBar = $('vnd-progress-bar');
    const dotEl = $('vnd-dot'); const statusText = $('vnd-status-text');
    const countDone = $('vnd-count-done'); const countTotal = $('vnd-count-total');
    const btnAdd = $('vnd-add'); const btnCancel = $('vnd-cancel'); const btnStop = $('vnd-stop');
    const toggleBtn = $('vnd-toggle'); const speedBtns = document.querySelectorAll('.vnd-speed-btn');

    function updateUI(d, t, s, e, msg, dot) {
        doneEl.textContent = d || 0; successEl.textContent = s || 0; errorsEl.textContent = e || 0;
        countDone.textContent = d || 0; countTotal.textContent = t || 0;
        statusText.innerHTML = msg || '💤 Sẵn sàng';
        dotEl.className = 'vnd-dot ' + (dot || 'idle');
        if (t && t > 0) progressBar.style.width = Math.min(100, (d / t) * 100) + '%';
        else progressBar.style.width = '0%';
    }
    function setRunning(state) {
        running = state; btnAdd.disabled = state; btnCancel.disabled = state;
        if (state) updateUI(done, limit, successCount, errorCount, '⏳ Đang chạy...', 'running');
    }

    let visible = true;
    toggleBtn.addEventListener('click', () => {
        visible = !visible; container.classList.toggle('hidden', !visible);
        trigger.classList.toggle('show', !visible); toggleBtn.textContent = visible ? '−' : '+';
    });
    trigger.addEventListener('click', () => {
        visible = true; container.classList.remove('hidden'); trigger.classList.remove('show');
        toggleBtn.textContent = '−';
    });

    speedBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            speedBtns.forEach(b => b.classList.remove('active')); btn.classList.add('active');
            speedMode = btn.dataset.speed;
            delay = speedMode === 'fast' ? 400 : speedMode === 'normal' ? 800 : 1200;
        });
    });

    function getButtons(mode) {
        const all = document.querySelectorAll('div[role="button"], span, div, button');
        const addT = ['Thêm bạn bè', 'Add friend', 'Kết bạn', 'Add Friend'];
        const cancelT = ['Hủy', 'Hủy lời mời', 'Cancel', 'Cancel Request', 'Gỡ', 'Hủy yêu cầu'];
        const res = [];
        for (const el of all) {
            const text = el.innerText?.trim() || '';
            if (!text) continue;
            if (mode === 'add' && addT.includes(text)) res.push(el);
            else if (mode === 'cancel' && cancelT.includes(text)) res.push(el);
        }
        return res;
    }

    async function startProcess(mode) {
        if (running) return;
        done = 0; successCount = 0; errorCount = 0;
        limit = parseInt(limitInput.value) || 50; startTime = Date.now();
        setRunning(true);
        updateUI(done, limit, successCount, errorCount, `🔍 Tìm nút ${mode === 'add' ? 'Thêm' : 'Hủy'}...`, 'running');
        let emptyScroll = 0;
        while (running && done < limit) {
            const btns = getButtons(mode);
            if (btns.length === 0) {
                emptyScroll++;
                if (emptyScroll > 3) { window.scrollBy(0, window.innerHeight * 1.8); await sleep(1500); emptyScroll = 0; continue; }
                window.scrollBy(0, window.innerHeight); await sleep(1000); continue;
            }
            emptyScroll = 0;
            for (const btn of btns) {
                if (!running || done >= limit) break;
                try {
                    if (btn.offsetParent === null) continue;
                    btn.scrollIntoView({ block: 'center', behavior: 'auto' }); await sleep(80);
                    btn.click(); done++; successCount++;
                    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
                    updateUI(done, limit, successCount, errorCount, `${mode === 'add' ? '➕' : '✖'} ${done}/${limit} (${elapsed}s)`, 'running');
                    const variance = delay * 0.3;
                    await sleep(Math.max(200, delay + (Math.random() * variance * 2 - variance)));
                } catch (e) { errorCount++; await sleep(300); }
            }
            window.scrollBy(0, 400); await sleep(500);
        }
        setRunning(false);
        if (done >= limit) updateUI(done, limit, successCount, errorCount, `🎉 HOÀN THÀNH! ${done}/${limit}`, 'done');
        else updateUI(done, limit, successCount, errorCount, `⏹ Đã dừng. ${done}/${limit}`, 'idle');
    }

    btnAdd.addEventListener('click', () => startProcess('add'));
    btnCancel.addEventListener('click', () => startProcess('cancel'));
    btnStop.addEventListener('click', () => {
        if (running) { setRunning(false); updateUI(done, limit, successCount, errorCount, '⏹ Dừng bởi user', 'idle'); }
    });

    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.shiftKey && e.key === 'F') {
            e.preventDefault(); visible = !visible; container.classList.toggle('hidden', !visible);
            trigger.classList.toggle('show', !visible); toggleBtn.textContent = visible ? '−' : '+';
        }
        if (e.ctrlKey && e.shiftKey && e.key === 'S') { e.preventDefault(); if (!running) btnAdd.click(); }
    });

    updateUI(0, 0, 0, 0, '💤 Sẵn sàng', 'idle'); setRunning(false);
    console.log('%c🚀 VNDEVCODE CEO Suite loaded!', 'color: #f7b731; font-size: 20px; font-weight: 900;');
})();
'''


# ============================================================================
# ==================== TOOL 5: login.py (FB CAA + 2FA) ======================
# ============================================================================
TOOL_CODE_LOGIN = r'''# -*- coding: utf-8 -*-
"""
⚡ CYBER FB NATIVE CAA LOGIN & TOKEN EXTRACTOR ENGINE ⚡
Đăng nhập Facebook chuẩn giao thức Bloks CAA & Native 2FA Resolver.
Định dạng nạp: uid|pass|2fa|cookie
"""
import sys, os, time, uuid, json, base64, random, string, struct, re, hashlib, argparse
from curl_cffi import requests

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization

try:
    import pyotp
    HAS_PYOTP = True
except ImportError:
    HAS_PYOTP = False

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        try: _s.reconfigure(encoding="utf-8")
        except Exception: pass

TOKEN_TYPES = {
    1: {"name": "EAAAAU (Facebook for Android - Katana)", "prefix": "EAAAAU",
        "app_id": "350685531728", "app_secret": "62f8ce9f74b12f84c123cc23437a4a32",
        "auth_header": "OAuth 350685531728|62f8ce9f74b12f84c123cc23437a4a32", "desc": "Token Katana Android"},
    2: {"name": "EAAAAAY (Facebook for iPhone - iOS)", "prefix": "EAAAAAY",
        "app_id": "6628568379", "app_secret": "c1e620fa708a1d5696fb991c1bde5662",
        "auth_header": "OAuth 6628568379|c1e620fa708a1d5696fb991c1bde5662", "desc": "Token iOS"},
    3: {"name": "EAAD6V (Facebook Messenger for Android)", "prefix": "EAAD6V",
        "app_id": "275254692598279", "app_secret": "585aec5b4c27376758abb7ffcb9db2af",
        "auth_header": "OAuth 275254692598279|585aec5b4c27376758abb7ffcb9db2af", "desc": "Token Messenger"}
}

DEFAULT_UA = "[FBAN/FB4A;FBAV/543.0.0.55.73;FBBV/846638243;FBDM/{density=3.0,width=1080,height=1920};FBLC/en_US;FBRV/0;FBCR/HT-Mobile;FBMF/Sony;FBBD/Sony;FBPN/com.facebook.katana;FBDV/LT30a;FBSV/10;FBOP/1;FBCA/x86_64:arm64-v8a;] RestSharp/113.1.0.0"

def log(msg, color=None):
    t = time.strftime("%H:%M:%S")
    print(f"[{t}] {msg}")

def luu_file(filename, line):
    try:
        with open(filename, "a", encoding="utf-8") as f:
            f.write(line.strip() + "\n")
    except Exception: pass

_RE_MID = re.compile(r'(?:datr|mid)=([0-9a-zA-Z\._\-]{15,35})')
def lay_machine_id_tu_cookie(cookie_str):
    if not cookie_str: return ""
    m = _RE_MID.search(cookie_str)
    return m.group(1).rstrip("=") if m else ""

def sinh_ma_otp_2fa(ma_2fa):
    if not ma_2fa: return ""
    clean = re.sub(r'[^A-Za-z0-9]', '', str(ma_2fa)).strip()
    if len(clean) == 6 and clean.isdigit(): return clean
    if len(clean) >= 16 and HAS_PYOTP:
        try: return pyotp.TOTP(clean).now()
        except Exception: pass
    return ""

def fb_sign_payload(data, app_secret):
    raw = "".join(f"{k}={data[k]}" for k in sorted(data) if k != "sig")
    return hashlib.md5((raw + app_secret).encode("utf-8")).hexdigest()

def encrypt_password_fb4a(password, pub_pem, key_id, timestamp=None):
    if timestamp is None: timestamp = int(time.time())
    aes_key = os.urandom(32); iv = os.urandom(12)
    rsa_pub = serialization.load_pem_public_key(pub_pem.encode('utf-8'))
    enc_aes_key = rsa_pub.encrypt(aes_key, padding.PKCS1v15())
    aesgcm = AESGCM(aes_key)
    aad = str(timestamp).encode('utf-8')
    enc_data = aesgcm.encrypt(iv, password.encode('utf-8'), aad)
    ciphertext = enc_data[:-16]; tag = enc_data[-16:]
    payload = bytearray()
    payload.append(1); payload.append(key_id & 0xFF); payload.extend(iv)
    payload.extend(struct.pack('<H', len(enc_aes_key)))
    payload.extend(enc_aes_key); payload.extend(tag); payload.extend(ciphertext)
    return f"#PWD_FB4A:2:{timestamp}:{base64.b64encode(payload).decode('ascii')}"

class FacebookLoginClient:
    def __init__(self, proxy=None, user_agent=DEFAULT_UA):
        self.proxy = self._norm(proxy); self.user_agent = user_agent
        self.cached_public_key = None; self.cached_key_id = None; self.cached_key_expires = 0
        self.session = requests.Session(impersonate="chrome120")
        if self.proxy: self.session.proxies = {"http": self.proxy, "https": self.proxy}

    def _norm(self, p):
        if not p: return ""
        raw = p.strip()
        if "://" not in raw:
            parts = raw.split(":")
            if len(parts) == 4: return f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
            elif len(parts) == 2: return f"http://{parts[0]}:{parts[1]}"
            return f"http://{raw}"
        return raw

    def fetch_pwd_key(self, device_id=None):
        now = time.time()
        if self.cached_public_key and now < self.cached_key_expires:
            return self.cached_public_key, self.cached_key_id
        if not device_id: device_id = str(uuid.uuid4())
        url = "https://graph.facebook.com/pwd_key_fetch"
        data = {"device_id": device_id, "version": "2", "flow": "CONTROLLER_INITIALIZATION",
                "locale": "en_US", "client_country_code": "US", "method": "GET",
                "fb_api_req_friendly_name": "pwdKeyFetch", "fb_api_caller_class": "Fb4aAuthHandler",
                "access_token": "350685531728|62f8ce9f74b12f84c123cc23437a4a32"}
        headers = {"User-Agent": self.user_agent, "Authorization": "OAuth null",
                   "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
                   "Host": "graph.facebook.com"}
        try:
            r = self.session.post(url, data=data, headers=headers, timeout=12)
            if r.status_code == 200:
                resp = r.json(); pub = resp.get("public_key"); kid = resp.get("key_id", 42)
                ttl = resp.get("seconds_to_live", 3600)
                if pub:
                    self.cached_public_key = pub; self.cached_key_id = kid
                    self.cached_key_expires = now + ttl - 60
                    return pub, kid
        except Exception: pass
        fallback = ("-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA3u8G+AIiUThPGp+dMt3i\n"
                    "OgLmJRm+0i3/V3HSE/ihZYokegGaybIlUOY/Gi23rYLae86dSVPlEmNzBoGSAnvd\n"
                    "MXwRrnkJl6W2ByV1itjADjaZ+FHjIjdKDzlWGqz/m3jkK4PgbbM/9c+bYAn7lpIc\n"
                    "j6PggpoazNQ3r4PwcMNCX0l/Rci4GvedI6wzmp8ED9H/ptB37LdvBE1rpSK0xxfX\n"
                    "BI/yo3PL29g1zElDF6D/oiGfu4GTcimyidIJAiRf5N9QOW7i3aSCiN0lwWh5Qq5/\n"
                    "Gv6k+UE5MRYRUONZl6pDIpuO0cz4v5bbZGtTIOJm7elpWqqILPrY2QRNacl7nSFa\n"
                    "4wIDAQAB\n-----END PUBLIC KEY-----\n")
        return fallback, 42

    def solve_2fa_native(self, username, password, token_type, otp_code, machine_id=""):
        conf = TOKEN_TYPES.get(token_type, TOKEN_TYPES[1])
        dev_id = str(uuid.uuid4()); fam_dev_id = str(uuid.uuid4())
        twofa_data = {"format": "json", "method": "auth.login", "email": username, "password": password,
                      "credentials_type": "two_factor", "twofactor_code": str(otp_code).strip(),
                      "access_token": f"{conf['app_id']}|{conf['app_secret']}", "api_key": conf["app_id"],
                      "device_id": dev_id, "family_device_id": fam_dev_id,
                      "generate_session_cookies": "1", "generate_machine_id": "1",
                      "locale": "vi_VN", "client_country_code": "VN",
                      "error_detail_type": "button_with_disabled"}
        if machine_id: twofa_data["machine_id"] = machine_id
        twofa_data["sig"] = fb_sign_payload(twofa_data, conf["app_secret"])
        headers = {"User-Agent": self.user_agent, "X-Fb-Connection-Type": "WIFI",
                   "Content-Type": "application/x-www-form-urlencoded"}
        for ep in ["https://b-api.facebook.com/method/auth.login", "https://graph.facebook.com/auth/login"]:
            try:
                r = self.session.post(ep, data=twofa_data, headers=headers, timeout=15)
                j = r.json()
                if "access_token" in j:
                    cookies_list = j.get("session_cookies", [])
                    c_dict = {ck["name"]: ck["value"] for ck in cookies_list if isinstance(ck, dict) and "name" in ck and "value" in ck}
                    order = ['c_user', 'xs', 'fr', 'datr', 'i_user', 'sb']
                    c_parts = [f"{k}={c_dict[k]}" for k in order if k in c_dict]
                    for k, v in c_dict.items():
                        if k not in order: c_parts.append(f"{k}={v}")
                    return {"success": True, "access_token": j["access_token"], "token_type": conf["name"],
                            "token_prefix": j["access_token"][:10],
                            "uid": str(j.get("uid") or c_dict.get("c_user") or username),
                            "cookies_str": "; ".join(c_parts), "cookies_dict": c_dict, "error": None}
                elif "error_msg" in j or "error" in j:
                    err = j.get("error_msg") or j.get("error", {}).get("message")
                    return {"success": False, "error": f"Lỗi 2FA: {err}", "access_token": None, "uid": username, "cookies_str": ""}
            except Exception: continue
        return {"success": False, "error": "Xác thực 2FA thất bại", "access_token": None, "uid": username, "cookies_str": ""}

    def login(self, username, password, token_type=1, ma_2fa="", cookie=""):
        conf = TOKEN_TYPES.get(token_type, TOKEN_TYPES[1])
        device_id = str(uuid.uuid4()); waterfall_id = str(uuid.uuid4()); now_ts = int(time.time())
        machine_id = lay_machine_id_tu_cookie(cookie)
        if machine_id: log(f"    [*] Machine ID: {machine_id}")
        otp_code = sinh_ma_otp_2fa(ma_2fa)
        if otp_code: log(f"    [*] OTP 6 số: {otp_code}")

        pub_pem, key_id = self.fetch_pwd_key(device_id=device_id)
        enc_pwd = encrypt_password_fb4a(password=password, pub_pem=pub_pem, key_id=key_id, timestamp=now_ts)

        client_input_params = {
            "aac": json.dumps({"aac_init_timestamp": now_ts, "aacjid": str(uuid.uuid4()),
                               "aaccs": base64.b64encode(os.urandom(32)).decode('ascii')}),
            "sim_phones": [], "aymh_accounts": [], "network_bssid": None,
            "secure_family_device_id": str(uuid.uuid4()),
            "attestation_result": {"keyHash": "", "data": "", "signature": ""},
            "has_granted_read_contacts_permissions": 0, "auth_secure_device_id": "null",
            "has_whatsapp_installed": 0, "password": enc_pwd, "sso_token_map_json_string": "",
            "block_store_machine_id": None, "cloud_trust_token": None, "event_flow": "login_manual",
            "password_contains_non_ascii": "false", "sim_serials": [], "client_known_key_hash": "",
            "sso_accounts_auth_data": [], "encrypted_msisdn": "",
            "has_granted_read_phone_permissions": 0, "app_manager_id": "null",
            "should_show_nested_nta_from_aymh": 1, "device_id": device_id,
            "zero_balance_state": "init", "login_attempt_count": 1, "machine_id": machine_id,
            "flash_call_permission_status": {"READ_PHONE_STATE": "PERMANENTLY_DENIED",
                                             "READ_CALL_LOG": "DENIED", "ANSWER_PHONE_CALLS": "DENIED"},
            "accounts_list": [], "gms_incoming_call_retriever_eligibility": "not_eligible",
            "family_device_id": device_id, "fb_ig_device_id": [], "device_emails": [],
            "try_num": 1, "lois_settings": {"lois_token": ""}, "event_step": "home_page",
            "headers_infra_flow_id": "", "openid_tokens": {}, "contact_point": username
        }
        if otp_code:
            client_input_params["two_factor_code"] = otp_code
            client_input_params["verification_code"] = otp_code

        server_params = {
            "should_trigger_override_login_2fa_action": 0, "is_vanilla_password_page_empty_password": 0,
            "is_from_logged_out": 0, "should_trigger_override_login_success_action": 0,
            "login_credential_type": "none", "server_login_source": "login", "waterfall_id": waterfall_id,
            "two_step_login_type": "two_step_login" if otp_code else "one_step_login",
            "login_source": "Login", "is_platform_login": 0, "pw_encryption_try_count": 1,
            "login_entry_point": "logged_out", "INTERNAL__latency_qpl_marker_id": 36707139,
            "is_from_aymh": 1, "offline_experiment_group": "caa_iteration_v6_perf_fb_2",
            "is_from_landing_page": 0, "left_nav_button_action": "BACK",
            "password_text_input_id": "4vmmea:105", "is_from_empty_password": 0,
            "is_from_msplit_fallback": 0, "ar_event_source": "login_home_page",
            "username_text_input_id": "4vmmea:104", "layered_homepage_experiment_group": None,
            "device_id": device_id, "login_surface": "login_home",
            "INTERNAL__latency_qpl_instance_id": int(time.time() * 10000),
            "reg_flow_source": "aymh_single_profile_native_integration_point",
            "is_caa_perf_enabled": 1, "credential_type": "password",
            "is_from_password_entry_page": 0, "caller": "gslr", "family_device_id": device_id,
            "is_from_assistive_id": 0, "access_flow_version": "pre_mt_behavior",
            "is_from_logged_in_switcher": 0
        }
        inner_obj = {"client_input_params": client_input_params, "server_params": server_params}
        params_wrapper = {"params": json.dumps(inner_obj)}
        variables = {"params": {"params": json.dumps(params_wrapper),
                                "bloks_versioning_id": "3eaf51d9e775c6dd164f226b640410d412bf13172692f4fd10d71ff0c9a9317a",
                                "app_id": "com.bloks.www.bloks.caa.login.async.send_login_request"},
                     "scale": "3",
                     "nt_context": {"using_white_navbar": True,
                                    "styles_id": "02864d999fe8454ffd17b9c8e8df2abe",
                                    "pixel_ratio": 3, "is_push_on": True,
                                    "theme_params": [{"value": [], "design_system_name": "FDS"}],
                                    "bloks_version": "3eaf51d9e775c6dd164f226b640410d412bf13172692f4fd10d71ff0c9a9317a"}}
        form_data = {"method": "post", "pretty": "false", "format": "json", "server_timestamps": "true",
                     "locale": "en_US", "purpose": "fetch",
                     "fb_api_req_friendly_name": "FbBloksActionRootQuery-com.bloks.www.bloks.caa.login.async.send_login_request",
                     "fb_api_caller_class": "graphservice",
                     "client_doc_id": "11994080429434958920198826852",
                     "fb_api_client_context": json.dumps({"is_background": False}),
                     "variables": json.dumps(variables),
                     "fb_api_analytics_tags": json.dumps(["GraphServices"]),
                     "client_trace_id": str(uuid.uuid4())}
        headers = {"X-Fb-Connection-Type": "WIFI", "X-Fb-Http-Engine": "Tigon/Liger",
                   "X-Fb-Client-Ip": "True", "X-Fb-Server-Cluster": "True",
                   "X-Tigon-Is-Retry": "False", "User-Agent": self.user_agent,
                   "X-Fb-Device-Group": "3003", "X-Graphql-Request-Purpose": "fetch",
                   "X-Fb-Privacy-Context": "3643298472347298", "X-Graphql-Client-Library": "graphservice",
                   "X-Fb-Net-Hni": "45201", "X-Fb-Sim-Hni": "45201",
                   "Authorization": conf["auth_header"],
                   "Accept": "application/json, text/json, text/x-json, text/javascript, application/xml, text/xml",
                   "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
                   "Host": "b-graph.facebook.com"}
        try:
            r = self.session.post("https://b-graph.facebook.com/graphql", data=form_data, headers=headers, timeout=20)
            raw_text = r.text
        except Exception as e:
            return {"success": False, "error": f"Lỗi mạng: {e}", "access_token": None, "uid": username, "cookies_str": ""}

        clean_text = re.sub(r'\\+', '', raw_text)
        tokens = [t for t in set(re.findall(r'(EAA[A-Za-z0-9]+)', clean_text)) if len(t) > 60]
        token = tokens[0] if tokens else None

        cookie_pairs = re.findall(r'name":"([^"]+)","value":"([^"]+)"', clean_text)
        cookies_dict = {}
        for name, val in cookie_pairs:
            if name in ('c_user', 'xs', 'fr', 'datr', 'i_user', 'sb'):
                cookies_dict[name] = val
        order = ['c_user', 'xs', 'fr', 'datr', 'i_user']
        c_parts = [f"{k}={cookies_dict[k]}" for k in order if k in cookies_dict]
        for k, v in cookies_dict.items():
            if k not in order: c_parts.append(f"{k}={v}")
        cookies_str = "; ".join(c_parts)
        uid = cookies_dict.get('c_user') or username

        if token:
            return {"success": True, "access_token": token, "token_type": conf["name"],
                    "token_prefix": token[:10], "uid": uid, "cookies_str": cookies_str,
                    "cookies_dict": cookies_dict, "error": None}

        is_2fa = any(k in clean_text.lower() for k in ("two_step", "login_2fa", "code_entry", "accountrecoverycodeentry"))
        if is_2fa:
            log("    [!] Tài khoản yêu cầu 2FA!")
            if not otp_code:
                print("👉 Nhập mã OTP 6 số (hoặc Secret Key 2FA):")
                sys.stdout.flush()
                prompt_2fa = input().strip()
                otp_code = sinh_ma_otp_2fa(prompt_2fa)
            if otp_code:
                log(f"    [*] Gửi OTP ({otp_code})...")
                return self.solve_2fa_native(username=username, password=password, token_type=token_type, otp_code=otp_code, machine_id=machine_id)
            else:
                return {"success": False, "error": "Yêu cầu 2FA nhưng thiếu OTP/Secret", "access_token": None, "uid": username, "cookies_str": ""}

        err_msg = "Đăng nhập thất bại"
        if "checkpoint" in clean_text.lower(): err_msg = "CHECKPOINT (282/956)"
        elif "incorrect" in clean_text.lower(): err_msg = "SAI MẬT KHẨU"
        else:
            m_err = re.search(r'error_message":"([^"]+)"', clean_text) or re.search(r'description":"([^"]+)"', clean_text)
            if m_err: err_msg = m_err.group(1)
        return {"success": False, "error": err_msg, "access_token": None, "uid": uid, "cookies_str": cookies_str}

def parse_acc_input(line):
    parts = line.split("|")
    uid = parts[0].strip() if len(parts) > 0 else ""
    pwd = parts[1].strip() if len(parts) > 1 else ""
    ma_2fa = parts[2].strip() if len(parts) > 2 else ""
    cookie = "|".join(parts[3:]).strip() if len(parts) > 3 else ""
    return uid, pwd, ma_2fa, cookie

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--type", type=int, choices=[1, 2, 3])
    parser.add_argument("-a", "--acc", type=str)
    args = parser.parse_args()

    print("=== ⚡ CYBER FB CAA LOGIN & 2FA TOKEN EXTRACTOR ⚡ ===")
    print("Định dạng: uid|pass|2fa|cookie")
    print("─────────────────────────────────────────────")

    token_type = args.type
    if not token_type:
        print("👉 CHỌN DẠNG TOKEN:")
        print("   [1] EAAAAU  : Android (Katana)")
        print("   [2] EAAAAAY : iPhone (iOS)")
        print("   [3] EAAD6V  : Messenger")
        sys.stdout.flush()
        t_inp = input("👉 Lựa chọn [1/2/3, default 1]: ").strip()
        if t_inp in ("2", "ios", "iphone"): token_type = 2
        elif t_inp in ("3", "msgr", "messenger"): token_type = 3
        else: token_type = 1

    log(f"[*] Token: {TOKEN_TYPES[token_type]['name']}")
    client = FacebookLoginClient()

    raw_input = args.acc
    if not raw_input:
        sys.stdout.flush()
        raw_input = input("👉 Nhập acc (uid|pass|2fa|cookie): ").strip()

    if not raw_input:
        log("[-] Chưa nhập acc!"); return

    uid, pwd, ma_2fa, cookie = parse_acc_input(raw_input)
    if not uid or not pwd:
        log("[-] Thiếu uid hoặc pass!"); return

    print("=" * 65)
    log(f"🚀 ĐĂNG NHẬP: {uid}")

    res = client.login(username=uid, password=pwd, token_type=token_type, ma_2fa=ma_2fa, cookie=cookie)

    if res["success"]:
        token = res["access_token"]; cookies_str = res["cookies_str"]; acc_uid = res["uid"]
        print("=" * 65)
        print(f"🎉 ĐĂNG NHẬP THÀNH CÔNG!")
        print(f"   UID:          {acc_uid}")
        print(f"   Dạng Token:   {res['token_type']}")
        print(f"   Access Token: {token}")
        print(f"   Cookies:      {cookies_str}")
        print("=" * 65)
        luu_file("token_output.txt", f"{acc_uid}|{pwd}|{token}|{cookies_str}")
        luu_file("token_only.txt", token)
        log("🎉 Đã lưu vào token_output.txt")
    else:
        log(f"[-] THẤT BẠI: {res['error']}")
        luu_file("login_failed.txt", f"{uid}|{pwd}|{res['error']}")

if __name__ == "__main__":
    main()
'''
# ============================================================================
# ==================== TOOL 6: chuyenpage.py ================================
# ============================================================================
TOOL_CODE_CHUYENPAGE = r'''import sys
import requests
import json
import re
import uuid
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.dont_write_bytecode = True
print_lock = threading.Lock()

def safe_print(text):
    with print_lock:
        if not text.startswith('\033['):
            text = f"\033[1m{text}\033[0m"
        print(text)

def log_system(msg): safe_print(f"[Hệ Thống] | {msg}")
def log_info(uid, msg): safe_print(f"[{uid}] | {msg}")

FB4A_UA = '[FBAN/FB4A;FBAV/542.0.0.46.151;FBBV/840338789;FBDM/{density=0.75,width=300,height=540};FBLC/vi_VN;FBRV/0;FBCR/MobiFone;FBMF/MTool-Max;FBBD/MTool-Max;FBPN/com.facebook.katana;FBDV/MTool-Max;FBSV/9;FBOP/1;FBCA/x86_64:arm64-v8a;]'

def get_user_info(access_token):
    try:
        r = requests.get("https://graph.facebook.com/me", params={"access_token": access_token, "fields": "id,name"}, timeout=10)
        d = r.json()
        if "id" in d: return d["id"], d.get("name", "")
        return None, None
    except Exception as e:
        safe_print(f"[Lỗi user info] {e}")
        return None, None

def _fb_fetch_profile_info(token, profile_id):
    variables = {'profile_switcher_connection_first': 300, 'additional_profile_picture_size': 80,
                 'profileID': str(profile_id), 'main_profile_picture_size': 80, 'scale': '2',
                 'nt_context': {'using_white_navbar': True, 'styles_id': '588d028b36bed0e1889e09b60e0f9aea',
                                'pixel_ratio': 2, 'is_push_on': True,
                                'theme_params': [{'value': [], 'design_system_name': 'FDS'}],
                                'bloks_version': '338f8ead5977a2c41eba3e92584dcf1d132e8b7928f1f5796662ec064023047d'},
                 'overflow_recent_searches_filter_ids': [],
                 'use_native_entrypoint_for_stars_on_reels': True}
    payload = {'method': 'post', 'pretty': 'false', 'format': 'json', 'server_timestamps': 'true',
               'locale': 'vi_VN', 'client_doc_id': '116912609015732060545213902280',
               'variables': json.dumps(variables)}
    headers = {'User-Agent': FB4A_UA, 'Accept-Encoding': 'gzip', 'authorization': f'OAuth {token}'}
    try:
        return requests.post('https://b-graph.facebook.com/graphql', data=payload, headers=headers, timeout=15).json()
    except: return None

def _fb_get_profile_switcher_map(token, source_uid):
    log_system("Đang lấy UID Page từ Profile Switcher...")
    gql = _fb_fetch_profile_info(token, source_uid)
    if not gql: return []
    result = []
    try:
        edges = gql.get('data', {}).get('user', {}).get('profile_switcher_eligible_profiles', {}).get('edges', [])
        for edge in edges:
            node = edge.get('node', {}); profile = node.get('profile', {})
            tp = node.get('session_info', {}).get('access_token', '')
            pid = str(profile.get('id', ''))
            if not pid or pid == str(source_uid) or not tp: continue
            result.append({'profile_id': pid, 'name': profile.get('name', ''), 'access_token': tp})
    except: pass
    return result

def _fb_match_page_to_profile(page, ps_map):
    pid = str(page.get('id', '')); pname = page.get('name', '').strip().lower()
    for p in ps_map:
        if p['name'].strip().lower() == pname: return p['profile_id'], p.get('access_token', '')
        if p['profile_id'] == pid: return p['profile_id'], p.get('access_token', '')
    return None, None

def get_page_tokens(access_token, user_uid=None):
    try:
        r = requests.get("https://graph.facebook.com/me/accounts",
                         params={"access_token": access_token, "fields": "id,name,access_token"}, timeout=15)
        data = r.json()
        if "data" in data:
            ps_map = _fb_get_profile_switcher_map(access_token, user_uid) if user_uid else []
            pages = []
            for page in data["data"]:
                pid = page.get("id"); pt = page.get("access_token"); pname = page.get("name", "")
                if pid and pt:
                    profile_uid, _ = _fb_match_page_to_profile(page, ps_map)
                    pages.append({'uid': profile_uid if profile_uid else pid, 'token': pt,
                                  'name': pname, 'id': pid})
            return pages
        else:
            safe_print(f"[Lỗi page] {data.get('error', {}).get('message', 'Unknown')}")
            return []
    except Exception as e:
        safe_print(f"[Lỗi page] {e}"); return []

def build_headers(token):
    return {"User-Agent": FB4A_UA, "authorization": f"OAuth {token}",
            "x-fb-sim-hni": "45201", "x-fb-net-hni": "45201",
            "x-graphql-client-library": "graphservice", "x-tigon-is-retry": "False",
            "x-graphql-request-purpose": "fetch", "x-fb-device-group": "2789",
            "Accept-Encoding": "identity", "x-zero-eh": "error",
            "x-fb-connection-type": "WIFI", "x-fb-http-engine": "Tigon/Liger",
            "x-fb-client-ip": "True", "x-fb-server-cluster": "True",
            "Content-Type": "application/x-www-form-urlencoded"}

def send_invitation(source_token, source_password, page_uid, target_uid):
    log_info("SOURCE", f"Gửi lời mời page {page_uid} cho {target_uid}...")
    payload_url = (f"/nt/profile/admin_management/permissions_reauth?"
                   f"admin_id={target_uid}"
                   "&admin_rows_container_id=%5B%228bxxoh%3A2%22%2Cnull%5D"
                   "&admin_type=full_access"
                   "&entry_point_screen_id=%5B%227o2xil%3A5%22%2Cnull%5D"
                   f"&profile_id={page_uid}"
                   "&state_ids%5Bauthenticated%5D=8csr9g%3A0"
                   "&state_ids%5Bauthentication_attempted%5D=8csr9g%3A1"
                   "&state_ids%5Bshow_entry_point_saving_spinner%5D=8bxxoh%3A0"
                   "&state_ids%5Bshow_saving_spinner%5D=8csr9g%3A3"
                   "&state_ids%5Bads%5D=8clnk7%3A2"
                   "&state_ids%5Bcontent%5D=8clnk7%3A3"
                   "&state_ids%5Binsights%5D=8clnk7%3A4"
                   "&state_ids%5Bmessages%5D=8clnk7%3A5"
                   "&state_ids%5Bmoderate%5D=8clnk7%3A6")
    client_data = {"sensitive_string_value": f'[["password","{source_password}"]]'}
    nt_context = {"using_white_navbar": True, "styles_id": "55d2af294359fa6bbdb8e045ff01fc5e",
                  "pixel_ratio": 1.5, "is_push_on": True, "theme_params": [],
                  "bloks_version": "cb6ac324faea83da28649a4d5046c3a4f0486cb987f8ab769765e316b075a76c"}
    params_obj = {"nt_context": nt_context, "payload": payload_url, "client_data": client_data}
    variables = {"params": json.dumps(params_obj),
                 "bloks_versioning_id": "cb6ac324faea83da28649a4d5046c3a4f0486cb987f8ab769765e316b075a76c",
                 "app_id": "com.bloks.www.bloks.caa.admin_management.permissions_reauth",
                 "scale": 1, "nt_context": nt_context}
    data = {"method": "post", "pretty": "false", "format": "json", "server_timestamps": "true",
            "locale": "vi_VN", "purpose": "fetch",
            "fb_api_req_friendly_name": "FbBloksActionRootQuery-com.bloks.www.bloks.caa.admin_management.permissions_reauth",
            "fb_api_caller_class": "graphservice",
            "client_doc_id": "30749539927629244093798192451",
            "variables": json.dumps(variables),
            "fb_api_analytics_tags": '["GraphServices"]',
            "client_trace_id": str(uuid.uuid4())}
    try:
        r = requests.post("https://b-graph.facebook.com/graphql", headers=build_headers(source_token), data=data, timeout=30)
        r.raise_for_status(); return r.json()
    except Exception as e: return {"error": str(e)}

def accept_invitation(target_token, invitation_id):
    log_info("TARGET", f"Chấp nhận lời mời (id={invitation_id})...")
    payload_url = f"/nt/profile/admin_management/accept_invitation?invitation_id={invitation_id}"
    nt_context = {"using_white_navbar": True, "styles_id": "55d2af294359fa6bbdb8e045ff01fc5e",
                  "pixel_ratio": 1.5, "is_push_on": True, "theme_params": [],
                  "bloks_version": "cb6ac324faea83da28649a4d5046c3a4f0486cb987f8ab769765e316b075a76c"}
    params_obj = {"nt_context": nt_context, "payload": payload_url}
    variables = {"params": json.dumps(params_obj),
                 "bloks_versioning_id": "cb6ac324faea83da28649a4d5046c3a4f0486cb987f8ab769765e316b075a76c",
                 "app_id": "com.bloks.www.bloks.caa.admin_management.accept_invitation",
                 "scale": 1, "nt_context": nt_context}
    data = {"method": "post", "pretty": "false", "format": "json", "server_timestamps": "true",
            "locale": "vi_VN", "purpose": "fetch",
            "fb_api_req_friendly_name": "FbBloksActionRootQuery-com.bloks.www.bloks.caa.admin_management.accept_invitation",
            "fb_api_caller_class": "graphservice",
            "client_doc_id": "11994080423986492941384902285",
            "variables": json.dumps(variables),
            "fb_api_analytics_tags": '["GraphServices"]',
            "client_trace_id": str(uuid.uuid4())}
    try:
        r = requests.post("https://b-graph.facebook.com/graphql", headers=build_headers(target_token), data=data, timeout=30)
        r.raise_for_status(); return r.json()
    except Exception as e: return {"error": str(e)}

def extract_invitation_id(response):
    text = json.dumps(response)
    for pattern in [r'"invitation_id":"([^"]+)"', r'"id":"([^"]+)"', r'"confirmation_code":"([^"]+)"']:
        m = re.search(pattern, text)
        if m: return m.group(1)
    return None

def transfer_page(source_token, source_password, page_uid, target_token):
    target_uid, _ = get_user_info(target_token)
    if not target_uid: return False, "Không lấy được UID target"
    resp1 = send_invitation(source_token, source_password, page_uid, target_uid)
    if "error" in resp1: return False, f"Lỗi gửi mời: {resp1['error']}"
    if resp1.get("errors"): return False, f"Lỗi server: {resp1['errors']}"
    inv_id = extract_invitation_id(resp1)
    if not inv_id: return False, "Không có invitation_id"
    resp2 = accept_invitation(target_token, inv_id)
    if "error" in resp2: return False, f"Lỗi chấp nhận: {resp2['error']}"
    if resp2.get("errors"): return False, f"Lỗi server accept: {resp2['errors']}"
    return True, "Thành công"

def main():
    safe_print("\n" + "="*50)
    safe_print("    TOOL CHUYỂN PAGE FACEBOOK")
    safe_print("="*50)

    sys.stdout.flush()
    source_token = input("Nhập token tài khoản nguồn: ").strip()
    if not source_token: log_system("Token trống"); return

    source_uid, source_name = get_user_info(source_token)
    if not source_uid: log_system("Token nguồn sai"); return
    log_info(source_uid, f"Đăng nhập OK: {source_name}")

    log_system("Quét page...")
    pages = get_page_tokens(source_token, source_uid)
    if not pages: log_system("Không có page"); return

    safe_print("\nDanh sách page:")
    for idx, p in enumerate(pages, 1):
        safe_print(f"{idx}. UID={p['uid']} | Tên={p['name'][:30]} | ID={p['id']}")

    sys.stdout.flush()
    choice = input("\nChọn page (cách nhau bởi dấu phẩy/space): ").strip()
    if not choice: log_system("Không chọn"); return

    indices = []
    for part in re.split(r'[,\s]+', choice):
        if part.isdigit():
            idx = int(part)
            if 1 <= idx <= len(pages): indices.append(idx - 1)
    if not indices: log_system("Không page hợp lệ"); return

    sys.stdout.flush()
    source_password = input("Mật khẩu tài khoản nguồn: ").strip()
    if not source_password: log_system("Mật khẩu trống"); return

    sys.stdout.flush()
    target_token = input("Token tài khoản đích: ").strip()
    if not target_token: log_system("Token đích trống"); return

    target_uid, target_name = get_user_info(target_token)
    if not target_uid: log_system("Token đích sai"); return
    log_info(target_uid, f"Đăng nhập OK: {target_name}")

    safe_print(f"\nSẽ chuyển {len(indices)} page sang {target_name} ({target_uid})")
    sys.stdout.flush()
    if input("Tiếp tục? (y/n): ").strip().lower() != 'y':
        log_system("Hủy"); return

    success = 0; fail = 0
    for idx in indices:
        page = pages[idx]
        log_system(f"Xử lý page {page['name']} ({page['uid']})...")
        ok, msg = transfer_page(source_token, source_password, page['uid'], target_token)
        if ok:
            success += 1
            log_info("KẾT QUẢ", f"✅ {page['name']} - OK")
        else:
            fail += 1
            log_info("KẾT QUẢ", f"❌ {page['name']} - {msg}")

    safe_print("\n" + "="*50)
    safe_print(f"Tổng: {len(indices)} | OK: {success} | Fail: {fail}")
    safe_print("="*50)

if __name__ == "__main__":
    main()
'''


# ============================================================================
# ==================== TOOL 7: bon.py (Decompiler) ==========================
# ============================================================================
TOOL_CODE_BON = r'''import base64
import marshal
import dis

_data = b'4wAAAAAAAAAAAAAAAAUAAAAAAAAA854CAACXAGQAZAFsAFoAZABkAWwBWgFkAGQBbAJaAmQAZAFsA1oDZABkAWwEWgRkAGQBbAVaBWQAZAFsBloGZABkAWwHWgdkAGQBbAhaCGQAZAFsCVoJZABkAmwDbQpaCgEAZABkA2wLbQtaC20MWgwBAGQAZARsDW0OWg4BAGQAZAVsD20QWhABAAkAZABkBmwRbRJaEgEAZABkB2wHbRNaEwEAZABkCGwUbRVaFW0WWhYBAGQAZAFsF1oXAgBlAWo4AAAAAAAAAAAAAAAAAAAAAAAAAgBlAmo6AAAAAAAAAAAAAAAAAAAAAAAAZAyrAQAAAAAAAKsBAAAAAAAAWh5kDYQAWh9kDoQAWiBkD1ohZBBaImQRWiNkElokZBNaJWQUWiZkFVonZBZaKGQXhABaKWQYhABaKmQZhABaK2QahABaLGQbhABaLWQchABaLmQdhABaL2QehABaMGQfhABaMWQghABaMmUzZCFrKAAAcgcCAGUyqwAAAAAAAAABAAkACQACAGU0AgBlB2pqAAAAAAAAAAAAAAAAAAAAAAAAZCKrAQAAAAAAAGpsAAAAAAAAAAAAAAAAAAAAAAAAqwEAAAAAAAABAIwkIwBlGCQAckABAAIAZQJqMgAAAAAAAAAAAAAAAAAAAAAAAGQJqwEAAAAAAAABAAIAZQJqMgAAAAAAAAAAAAAAAAAAAAAAAGQKqwEAAAAAAAABAAIAZRpkC6sBAAAAAAAAAQACAGUJajYAAAAAAAAAAAAAAAAAAAAAAACrAAAAAAAAAAEAWQCMy3cAeANZAHcBIwBlNyQAchwBAAIAZRpkI6sBAAAAAAAAAQACAGUJajYAAAAAAAAAAAAAAAAAAAAAAACrAAAAAAAAAAEAWQCMaXcAeANZAHcBKSTpAAAAAE4pAdoFc2xlZXApAtoIZGF0ZXRpbWXaCXRpbWVkZWx0YSkB2g1CZWF1dGlmdWxTb3VwKQHaElRocmVhZFBvb2xFeGVjdXRvcikB2gVGYWtlcikB2gdzZXNzaW9uKQLaBEZvcmXaBVN0eWxlei9waXAgaW5zdGFsbCBmYWtlciByZXF1ZXN0cyBjb2xvcmFtYSBiczQgcHlzdHlsZXodcGlwMyBpbnN0YWxsIHJlcXVlc3RzIHB5c29ja3N1HwAAAF9fVnVpIEzDsm5nIENo4bqheSBM4bqhaSBUb29sX1/pIAAAAGMBAAAAAAAAAAAAAAAEAAAAAwAAAPNkAAAAlwB0AQAAAAAAAAAAagIAAAAAAAAAAAAAAAAAAAAAAAB8AGoFAAAAAAAAAAAAAAAAAAAAAAAAqwAAAAAAAACrAQAAAAAAAGoHAAAAAAAAAAAAAAAAAAAAAAAAqwAAAAAAAABTAKkBTikE2gZiYXNlNjTaCWI2NGVuY29kZdoGZW5jb2Rl2gZkZWNvZGUpAdoEZGF0YXMBAAAAIPoKYm9uX2dvYy5wedoMZW5jcnlwdF9kYXRhchUAAAAgAAAAcyIAAACAANwLEdcLG9ELG5hEn0uZS5tN0wsq1wsx0Qsx0wsz0AQz8wAAAABjAQAAAAAAAAAAAAAABAAAAAMAAADzZAAAAJcAdAEAAAAAAAAAAGoCAAAAAAAAAAAAAAAAAAAAAAAAfABqBQAAAAAAAAAAAAAAAAAAAAAAAKsAAAAAAAAAqwEAAAAAAABqBwAAAAAAAAAAAAAAAAAAAAAAAKsAAAAAAAAAUwByDgAAACkEcg8AAADaCWI2NGRlY29kZXIRAAAAchIAAAApAdoOZW5jcnlwdGVkX2RhdGFzAQAAACByFAAAANoMZGVjcnlwdF9kYXRhchoAAAAjAAAAcyUAAACAANwLEdcLG9ELG5hO1xwx0Rwx0xwz0ws01ws70Qs70ws90AQ9chYAAAB6BxtbMTszNm16BxtbMTszMW16BxtbMTszMm16BxtbMTszM216BxtbMTszNG16BxtbMTszNW16BxtbMTszOW16BBtbMG1jAAAAAAAAAAAAAAAABAAAAAMAAADz4AAAAJcAdAEAAAAAAAAAAGoCAAAAAAAAAAAAAAAAAAAAAAAAdAAAAAAAAAAAAGoEAAAAAAAAAAAAAAAAAAAAAAAAZAFrKAAAcgJkAm4BZAOrAQAAAAAAAAEAdAcAAAAAAAAAAHQIAAAAAAAAAABkBHoAAAB0CgAAAAAAAAAAegAAAKsBAAAAAAAAAQB0BwAAAAAAAAAAdAwAAAAAAAAAAGQFegAAAHQKAAAAAAAAAAB6AAAAqwEAAAAAAAABAHQHAAAAAAAAAAB0DgAAAAAAAAAAZAZ6AAAAqwEAAAAAAAABAHkAKQdO2gJudNoDY2xz2gVjbGVhcnXNAQAACuKWiOKWiOKWiOKWiOKWiOKWiOKVl+KWkeKWkeKWiOKWiOKWiOKWiOKWiOKVl+KWkeKWiOKWiOKWiOKVl+KWkeKWkeKWiOKWiOKVlwrilojilojilZTilZDilZDilojilojilZfilojilojilZTilZDilZDilojilojilZfilojilojilojilojilZfilpHilojilojilZEK4paI4paI4paI4paI4paI4paI4pWm4pWd4paI4paI4pWR4paR4paR4paI4paI4pWR4paI4paI4pWU4paI4paI4pWX4paI4paI4pWRCuKWiOKWiOKVlOKVkOKVkOKWiOKWiOKVl+KWiOKWiOKVkeKWkeKWkeKWiOKWiOKVkeKWiOKWiOKVkeKVmuKWiOKWiOKWiOKWiOKVkQrilojilojilojilojilojilojilabilZ3ilZrilojilojilojilojilojilZTilZ3ilojilojilZHilpHilZrilojilojilojilZEK4pWa4pWQ4pWQ4pWQ4pWQ4pWQ4pWd4paR4paR4pWa4pWQ4pWQ4pWQ4pWQ4pWd4paR4pWa4pWQ4pWd4paR4paR4pWa4pWQ4pWQ4pWdCiAgICB6HlRvb2wgQnk6IExBTkggQUsgfCBWZXJzaW9uIDEuMHotPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09KQjaAm9z2gZzeXN0ZW3aBG5hbWXaBXByaW502gR2YW5n2gNlbmTaA2x1Y9oFdHJhbmepAHIWAAAAchQAAADaBmJhbm5lcigAAAAxAAAAc1oAAACAANwEBodJgUmUcpd3kXegJJJ/iWWoR9QENNwECYwk8AAHEgjxAAcLCPQOAAsO8Q8HCw70AAcFD/QQAAUKjCPQEDDRCjC0M9EKNtQEN9wECYwlkCjRChrVBBtyFgAAAGMAAAAAAAAAAAAAAAUAAAADAAAA86QAAACXAAkAdAEAAAAAAAAAAGoCAAAAAAAAAAAAAAAAAAAAAAAAZAGrAQAAAAAAAH0AfABqBQAAAAAAAAAAAAAAAAAAAAAAAKsAAAAAAAAAfQF8AWQCGQAAAH0CfAJTACMAdAYAAAAAAAAAACQAcgR9A3QJAAAAAAAAAABkA3wDmwCdAqsBAAAAAAAAAQBZAGQAfQN+A3kAZAB9A34DdwF3AHgDWQB3ASkETnohaHR0cHM6Ly9hcGkuaXBpZnkub3JnP2Zvcm1hdD1qc29u2gJpcCEAAABM4buXaSBraGkgbOG6pXkgxJHhu4NhIGNo4buJIElQOiApBdoIcmVxdWVzdHPaA2dldNoEanNvbo5JRXhjZXB0aW9uciIAAAApBNoIcmVzcG9uc2XaB2lwX2RhdGHaCmlwX2FkZHJlc3PaAWVzBAAAACAgICByFAAAANoOZ2V0X2lwX2FkZHJlc3NyMwAAAD4AAABzUwAAAIAA8AIHBRTcExuXPJE80CBD0xNEiAjYEhqXLZEtky+IB9gVGlwSWZ5IENsaWVudCBJUCBDaGVja2VyIFRvb2w6IP//2g'

def main():
    print("=== BON DECOMPILER ===")
    try:
        code_obj = marshal.loads(base64.b64decode(_data))
        print("[+] Giải mã thành công!")

        print("\n=== CONSTANTS ===")
        for const in code_obj.co_consts:
            if isinstance(const, str):
                print(const[:200])

        print("\n=== NAMES ===")
        for name in code_obj.co_names:
            print(name)

        print("\n=== VARNAMES ===")
        for var in code_obj.co_varnames:
            print(var)

        with open('bon_decompiled.pyc', 'wb') as f:
            f.write(base64.b64decode(_data))

        try:
            exec(code_obj, globals())
            print("\n=== FUNCTIONS DEFINED ===")
            for name, obj in list(globals().items()):
                if callable(obj) and not name.startswith('_'):
                    print(f"- {name}")
        except Exception as e:
            print(f"[!] Không thể exec: {e}")

    except Exception as e:
        print(f"Lỗi: {e}")

if __name__ == "__main__":
    main()
'''


# ============================================================================
# ================== KHAI BÁO TOOL TRONG APP =================================
# ============================================================================
EMBEDDED_TOOLS = {
    "xsmmv3.2": {
        "name": "XSMM Tool V3.2",
        "desc": "Tool Instagram Auto Jobs - XSMM API (Multi-thread + số luồng tùy chỉnh)",
        "color": "#00d4ff",
        "filename": "xsmmv3.2.py",
        "code": TOOL_CODE_XSMMV32,
        "type": "python",
    },
    "xsmmigv5.2": {
        "name": "XSMM IG V5.2",
        "desc": "Tool Instagram Auto Jobs - XSMM API V2 (Browser Profiles + JSON Queue)",
        "color": "#ff6b9d",
        "filename": "xsmmigv5.2.py",
        "code": TOOL_CODE_XSMMIGV52,
        "type": "python",
    },
    "11223": {
        "name": "Simple IG Bot",
        "desc": "Tool đơn giản - Like / Follow / Comment với XSMM",
        "color": "#ffd93d",
        "filename": "11223.py",
        "code": TOOL_CODE_11223,
        "type": "python",
    },
    "autoaddfb": {
        "name": "Auto FB Friends",
        "desc": "Userscript Tampermonkey - Auto Add/Unfriend Facebook Friends (CEO Edition)",
        "color": "#4267B2",
        "filename": "autoaddfb.user.js",
        "code": TOOL_CODE_AUTOADDFB,
        "type": "userscript",
    },
    "login": {
        "name": "FB CAA Login + 2FA",
        "desc": "Đăng nhập Facebook chuẩn Bloks CAA - Tự động giải 2FA - Lấy Token EAAAAU/EAAAAAY/EAAD6V",
        "color": "#1877F2",
        "filename": "login.py",
        "code": TOOL_CODE_LOGIN,
        "type": "python",
    },
    "chuyenpage": {
        "name": "Chuyển Page FB",
        "desc": "Chuyển quyền quản trị Page Facebook từ tài khoản nguồn sang tài khoản đích",
        "color": "#8b5cf6",
        "filename": "chuyenpage.py",
        "code": TOOL_CODE_CHUYENPAGE,
        "type": "python",
    },
    "bon": {
        "name": "Bon Decompiler",
        "desc": "Giải mã file .py đã bị mã hóa bằng marshal + base64",
        "color": "#f97316",
        "filename": "bon.py",
        "code": TOOL_CODE_BON,
        "type": "python",
    },
}


def ensure_tool_file(tool_key):
    if tool_key not in EMBEDDED_TOOLS:
        return None, f"Tool không hợp lệ: {tool_key}"
    info = EMBEDDED_TOOLS[tool_key]
    filepath = os.path.join(TEMP_TOOLS_DIR, info["filename"])
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(info["code"])
        return filepath, None
    except Exception as e:
        return None, f"Không thể tạo file tool: {e}"


sessions = {}
sessions_lock = threading.Lock()

TOOL_INFO = {k: {"name": v["name"], "desc": v["desc"], "color": v["color"], "type": v.get("type", "python")}
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


@app.route('/api/download/<tool_key>')
def api_download(tool_key):
    """Tải file tool (cho userscript autoaddfb)"""
    if tool_key not in EMBEDDED_TOOLS:
        return jsonify({"ok": False, "error": "Tool không hợp lệ"}), 404
    info = EMBEDDED_TOOLS[tool_key]
    filepath, err = ensure_tool_file(tool_key)
    if err:
        return jsonify({"ok": False, "error": err}), 500
    from flask import send_file
    return send_file(filepath, as_attachment=True, download_name=info["filename"])


@socketio.on('join')
def on_join(data):
    session_id = data.get('session_id')
    if session_id:
        join_room(session_id)
        emit('joined', {'session_id': session_id})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("=" * 60)
    print(" 🚀 TA TOOL WEB MANAGER (7 TOOLS)")
    print(f" 📁 Temp tools: {TEMP_TOOLS_DIR}")
    print(f" 🌐 Port: {port}")
    print(f" 📦 Tools: {list(EMBEDDED_TOOLS.keys())}")
    print("=" * 60)
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
