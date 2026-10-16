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
    print("="*60)
    print("  XSMM TOOL V3.2 - INSTAGRAM AUTO JOBS")
    print("="*60)

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
        payload = {"type": job_type, "task_id": task_ids if isinstance(task_ids, list) else [task_ids], "uid": str(uid), "cookie_check": cookie_check}
        attempt = 0
        while attempt < max_retries:
            try:
                r = requests.post(f"{self.base_url}/tasks2/complete", headers=self.headers, json=payload, timeout=35)
                res_data = r.json()
                if isinstance(res_data, dict) and res_data.get("retry") is True:
                    time.sleep(random.randint(1, 3)); attempt += 1; continue
                return res_data
            except requests.exceptions.Timeout:
                return {"is_timeout": True, "message": "Server chậm nhưng đã gửi duyệt"}
            except Exception as e: return {"error": str(e)}
        return {"error": "Retry failed"}

useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
sec_ch_ua_120 = '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'

def format_proxy(p):
    if not p: return None
    p = p.strip()
    if not p: return None
    scheme = "http"
    if "://" in p: scheme, p = p.split("://", 1)
    parts = p.split(":")
    if len(parts) == 4:
        ip, port, user, pwd = parts
        f = f"{scheme}://{user}:{pwd}@{ip}:{port}"
    elif "@" in p:
        f = f"{scheme}://{p}"
    elif len(parts) == 2:
        f = f"{scheme}://{p}"
    else:
        f = f"{scheme}://{p}"
    return {"http": f, "https": f}

def get_ig_headers(cookie, csrftoken, referer="https://www.instagram.com/"):
    return {'accept': '*/*', 'accept-language': 'vi-VN,vi;q=0.9,en-US;q=0.6,en;q=0.5',
            'content-type': 'application/x-www-form-urlencoded', 'cookie': cookie,
            'origin': 'https://www.instagram.com', 'priority': 'u=1, i', 'referer': referer,
            'sec-ch-ua': sec_ch_ua_120, 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty', 'sec-fetch-mode': 'cors', 'sec-fetch-site': 'same-origin',
            'user-agent': useragent, 'x-asbd-id': '129477', 'x-csrftoken': csrftoken,
            'x-ig-app-id': '936619743392459', 'x-ig-www-claim': '0', 'x-requested-with': 'XMLHttpRequest'}

def check_cookie_ig(cookie, proxy=None):
    url = 'https://www.instagram.com/api/v1/accounts/edit/web_form_data/'
    headers = {'x-ig-app-id': '936619743392459', 'x-requested-with': 'XMLHttpRequest',
               'referer': 'https://www.instagram.com/accounts/edit/', 'cookie': cookie,
               'user-agent': useragent, 'sec-ch-ua': sec_ch_ua_120}
    try: return c_requests.get(url, headers=headers, proxies=format_proxy(proxy), impersonate="chrome120", timeout=30).text
    except: return "{}"

def follow(target_id, cookie, csrftoken, profile_url="", proxy=None):
    if not target_id: return '{"status": "error", "message": "Lỗi Target ID"}'
    cookie = unquote(cookie); session = c_requests.Session()
    proxies = format_proxy(proxy)
    if proxies: session.proxies = proxies
    for item in cookie.split(';'):
        if '=' in item:
            try:
                k, v = item.strip().split('=', 1); session.cookies.set(k, v, domain='.instagram.com')
            except: pass
    fb_dtsg, lsd, jazoest = "", "Jfq8VQNmkkkJufHSbEE9bf", "26328"
    try:
        res_home = session.get(profile_url or "https://www.instagram.com/", impersonate="chrome120", timeout=10).text
        m = re.search(r'"LSD",\[\],{"token":"([^"]+)"}', res_home)
        if m: lsd = m.group(1)
        m = re.search(r'"dtsg":\{"token":"([^"]+)"', res_home) or re.search(r'name="fb_dtsg" value="([^"]+)"', res_home)
        if m: fb_dtsg = m.group(1)
        m = re.search(r'name="jazoest" value="(\d+)"', res_home)
        if m: jazoest = m.group(1)
    except: pass
    dyn_csrf = session.cookies.get('csrftoken')
    if not dyn_csrf:
        m = re.search(r'csrftoken=([^;]+)', cookie); dyn_csrf = m.group(1) if m else "missing"
    session.headers.update(get_ig_headers(cookie, dyn_csrf, profile_url or "https://www.instagram.com/"))
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
    try: return session.post('https://www.instagram.com/api/graphql', data=data, impersonate="chrome120", timeout=15).text.strip()
    except Exception as e: return json.dumps({"status": "error", "message": str(e)})

def tym(mediaid, cookie, csrftoken, link_job="", proxy=None):
    if not mediaid: return '{"status": "error", "message": "Lỗi Media ID"}'
    cookie = unquote(cookie); session = c_requests.Session()
    proxies = format_proxy(proxy)
    if proxies: session.proxies = proxies
    for item in cookie.split(';'):
        if '=' in item:
            try:
                k, v = item.strip().split('=', 1); session.cookies.set(k, v, domain='.instagram.com')
            except: pass
    fb_dtsg, lsd, jazoest = "", "GyeZl-huflHZ0K5L3-pzBi", "26492"
    try:
        res_home = session.get("https://www.instagram.com/", impersonate="chrome120", timeout=10).text
        m = re.search(r'"LSD",\[\],{"token":"([^"]+)"}', res_home)
        if m: lsd = m.group(1)
        m = re.search(r'"dtsg":\{"token":"([^"]+)"', res_home) or re.search(r'name="fb_dtsg" value="([^"]+)"', res_home)
        if m: fb_dtsg = m.group(1)
        m = re.search(r'name="jazoest" value="(\d+)"', res_home)
        if m: jazoest = m.group(1)
    except: pass
    dyn_csrf = session.cookies.get('csrftoken')
    if not dyn_csrf:
        m = re.search(r'csrftoken=([^;]+)', cookie); dyn_csrf = m.group(1) if m else "missing"
    session.headers.update(get_ig_headers(cookie, dyn_csrf, link_job or "https://www.instagram.com/"))
    actor_id_match = re.search(r'ds_user_id=(\d+)', cookie)
    actor_id = actor_id_match.group(1) if actor_id_match else "0"
    tt = ""
    try:
        if link_job:
            res_get = session.get(link_job, impersonate="chrome120", timeout=10).text
            m = re.search(r'"tracking_token":"([^"]+)"', res_get)
            if m: tt = m.group(1)
    except: pass
    variables = {"input": {"actor_id": actor_id, "client_mutation_id": str(random.randint(1000000, 9999999)),
                           "container_module": "single_post", "media_id": str(mediaid)}}
    if tt: variables["input"]["tracking_token"] = tt
    data = {"av": actor_id, "__d": "www", "__user": "0", "__a": "1", "__req": "h",
            "__hs": "20702.HYP:instagram_web_pkg.2.1...0", "dpr": "1", "__ccg": "EXCELLENT",
            "__rev": "1046913831", "__comet_req": "7", "fb_dtsg": fb_dtsg, "jazoest": jazoest,
            "lsd": lsd, "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "usePolarisLikeMediaXIGLikeMutation",
            "server_timestamps": "true", "doc_id": "27182485238052618", "variables": json.dumps(variables)}
    try: return session.post('https://www.instagram.com/api/graphql', data=data, impersonate="chrome120", timeout=15).text.strip()
    except Exception as e: return json.dumps({"status": "error", "message": str(e)})

def cmt(mediaid, text, cookie, csrftoken, link_job="", proxy=None):
    if not mediaid: return '{"status": "error", "message": "Lỗi Media ID"}'
    cookie = unquote(cookie); session = c_requests.Session()
    proxies = format_proxy(proxy)
    if proxies: session.proxies = proxies
    for item in cookie.split(';'):
        if '=' in item:
            try:
                k, v = item.strip().split('=', 1); session.cookies.set(k, v, domain='.instagram.com')
            except: pass
    fb_dtsg, lsd, jazoest = "", "9zei3OjvTBQ-9YG6E0OMzm", "26312"
    try:
        res_home = session.get(link_job or "https://www.instagram.com/", impersonate="chrome120", timeout=10).text
        m = re.search(r'"LSD",\[\],{"token":"([^"]+)"}', res_home)
        if m: lsd = m.group(1)
        m = re.search(r'"dtsg":\{"token":"([^"]+)"', res_home) or re.search(r'name="fb_dtsg" value="([^"]+)"', res_home)
        if m: fb_dtsg = m.group(1)
        m = re.search(r'name="jazoest" value="(\d+)"', res_home)
        if m: jazoest = m.group(1)
    except: pass
    dyn_csrf = session.cookies.get('csrftoken')
    if not dyn_csrf:
        m = re.search(r'csrftoken=([^;]+)', cookie); dyn_csrf = m.group(1) if m else "missing"
    session.headers.update(get_ig_headers(cookie, dyn_csrf, link_job or "https://www.instagram.com/"))
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
    try: return session.post('https://www.instagram.com/api/graphql', data=data, impersonate="chrome120", timeout=15).text.strip()
    except Exception as e: return json.dumps({"status": "error", "message": str(e)})

def gui_nhan_xu(job_type, task_list, uid, cookie_check, xsmm_instance, tenfb):
    if not task_list: return
    thread_safe_print(f"[{tenfb}] Gom {len(task_list)} task -> Gửi duyệt...")
    ck = xsmm_instance.complete_tasks(job_type, task_list, uid=uid, cookie_check=cookie_check)
    now = datetime.now().strftime("%H:%M:%S")
    if isinstance(ck, dict):
        if 'message' in ck:
            pts = ck.get('points', 0)
            thread_safe_print(f"[{now}] [{tenfb}] {ck['message']} (+{pts} xu)")
        elif ck.get("is_timeout"):
            thread_safe_print(f"[{now}] [{tenfb}] {ck['message']}")
        elif 'error' in ck:
            thread_safe_print(f"[{now}] [{tenfb}] LỖI: {ck['error']}")
        if ck.get('countdown', 0) > 0:
            time.sleep(ck['countdown'])

def run_single_account(acc_data, listnv, config_delays, xsmm_token, dl, doi):
    cookie = acc_data["cookie"]; proxy = acc_data.get("proxy", "")
    xsmm_thread = XSMMTool(token=xsmm_token)
    access = check_cookie_ig(cookie, proxy)
    is_live = False; tenfb = ""; idfb = ""
    try:
        configdata = json.loads(access)
        if configdata and 'form_data' in configdata and configdata['form_data'].get('username'):
            is_live = True; tenfb = configdata['form_data']['username']
            idfb_match = re.search(r'ds_user_id=(\d+)', cookie)
            idfb = idfb_match.group(1) if idfb_match else str(configdata['form_data'].get('id', ''))
    except Exception: is_live = False
    if not is_live or not idfb:
        thread_safe_print(f"[!] Cookie lỗi - Dừng luồng")
        return
    px_display = f" | Proxy: {proxy}" if proxy else ""
    thread_safe_print(f"[+] NICK LIVE [{tenfb} | UID: {idfb}{px_display}]")
    try:
        acc_list = xsmm_thread.get_accounts(account_type="instagram", search=idfb)
        exists = False
        if isinstance(acc_list, dict) and acc_list.get("accounts"):
            for acc in acc_list["accounts"]:
                if acc and (str(acc.get("account_id")) == str(idfb) or str(acc.get("name", "")).lower() == str(tenfb).lower()):
                    exists = True; break
        if not exists:
            link_ig = f"https://www.instagram.com/{tenfb}"
            add_res = xsmm_thread.add_account("instagram", link_ig)
            if isinstance(add_res, dict) and "id" in add_res:
                thread_safe_print(f"[+] Đã thêm [{tenfb}] vào XSMM")
    except Exception as e:
        thread_safe_print(f"[!] Sync lỗi: {e}")
    max_job = 0; cache_follow = []
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
                    thread_safe_print(f"[{tenfb}] Tym: {link_job}")
                    chayfl = tym(idm, cookie, csf, link_job, proxy=proxy)
                    max_job += 1
                    try:
                        g = json.loads(chayfl)
                        if 'data' not in g and g.get('status') != 'ok': raise Exception(g.get('message', 'Block'))
                        thread_safe_print(f"[{tenfb}] TYM OK")
                        gui_nhan_xu("instagram_like", [task_id], idfb, cookie, xsmm_thread, tenfb)
                        soloitym = 0
                    except Exception as e:
                        thread_safe_print(f"[{tenfb}] TYM LỖI: {e}")
                        soloitym += 1
                    time.sleep(config_delays['tym'])
                    if soloitym > 4 or max_job >= doi: break
            else: time.sleep(dl)
        elif rand_job == 'instagram_follow':
            list_nv = xsmm_thread.get_tasks(rand_job, uid=idfb)
            if isinstance(list_nv, list) and len(list_nv) > 0:
                soloisub = 0
                temp_sess = c_requests.Session()
                proxies = format_proxy(proxy)
                if proxies: temp_sess.proxies = proxies
                temp_sess.headers.update({"User-Agent": useragent})
                for nv in list_nv:
                    task_id = nv.get('id'); target_id = nv.get('target_id', ''); link_job = nv.get('target_url', '')
                    if not target_id or not str(target_id).isdigit():
                        try:
                            res_html = temp_sess.get(link_job, impersonate="chrome120", timeout=10).text
                            m = re.search(r'"profile_id":"(\d+)"', res_html) or re.search(r'"user_id":"(\d+)"', res_html) or re.search(r'profilePage_(\d+)', res_html)
                            if m: target_id = m.group(1)
                        except: pass
                    if not target_id or not str(target_id).isdigit(): continue
                    csf_match = re.search(r'csrftoken=([^;]+)', cookie)
                    csf = csf_match.group(1) if csf_match else ""
                    thread_safe_print(f"[{tenfb}] Follow: {target_id}")
                    chay_sub = follow(target_id, cookie, csf, link_job, proxy=proxy)
                    max_job += 1
                    try:
                        g = json.loads(chay_sub)
                        if 'data' not in g and g.get('status') not in ('ok', 'success'):
                            soloisub += 1
                        else:
                            cache_follow.append(task_id); soloisub = 0
                            thread_safe_print(f"[{tenfb}] Follow {target_id} OK ({len(cache_follow)}/10)")
                            if len(cache_follow) == 10:
                                gui_nhan_xu("instagram_follow", cache_follow, idfb, cookie, xsmm_thread, tenfb)
                                cache_follow = []; break
                    except: soloisub += 1
                    time.sleep(config_delays['follow'])
                    if soloisub > 4 or max_job >= doi: break
            else: time.sleep(dl)
        elif rand_job == 'instagram_comment':
            list_nv = xsmm_thread.get_tasks(rand_job, uid=idfb)
            if isinstance(list_nv, list) and len(list_nv) > 0:
                soloicmt = 0
                temp_sess = c_requests.Session()
                proxies = format_proxy(proxy)
                if proxies: temp_sess.proxies = proxies
                temp_sess.headers.update({"User-Agent": useragent})
                for nv in list_nv:
                    task_id = nv.get('id'); idm = nv.get('target_id', ''); noidung = nv.get('comment', '❤️❤️❤️'); link_job = nv.get('target_url', '')
                    if not idm:
                        try:
                            res_html = temp_sess.get(link_job, impersonate="chrome120", timeout=10).text
                            m = re.search(r'instagram://media\?id=(\d+)', res_html) or re.search(r'"media_id":"(\d+)"', res_html)
                            if m: idm = m.group(1)
                        except: pass
                    if not idm: continue
                    csf_match = re.search(r'csrftoken=([^;]+)', cookie)
                    csf = csf_match.group(1) if csf_match else ""
                    thread_safe_print(f"[{tenfb}] CMT: {link_job}")
                    chay_cmt = cmt(idm, noidung, cookie, csf, link_job, proxy=proxy)
                    max_job += 1
                    try:
                        g = json.loads(chay_cmt)
                        if g.get('status') != 'ok' and 'data' not in g: raise Exception(g.get('message', 'Block'))
                        thread_safe_print(f"[{tenfb}] CMT OK")
                        gui_nhan_xu("instagram_comment", [task_id], idfb, cookie, xsmm_thread, tenfb)
                        soloicmt = 0
                    except Exception as e:
                        thread_safe_print(f"[{tenfb}] CMT LỖI: {e}")
                        soloicmt += 1
                    time.sleep(config_delays['comment'])
                    if soloicmt > 4 or max_job >= doi: break
            else: time.sleep(dl)
        if max_job >= doi:
            thread_safe_print(f"[{tenfb}] Nghỉ {dl}s")
            time.sleep(dl); max_job = 0

def main():
    banner()
    sys.stdout.write("Số luồng chạy song song (1-50): ")
    sys.stdout.flush()
    try:
        max_threads = int(input().strip())
        if max_threads < 1: max_threads = 1
        if max_threads > 50: max_threads = 50
    except: max_threads = 10
    print(f"OK - Sẽ chạy {max_threads} nick song song\n")

    sys.stdout.write("Access Token XSMM: ")
    sys.stdout.flush()
    xsmm_token = input().strip()

    xsmm = XSMMTool(token=xsmm_token)
    user_info = xsmm.get_user_info()
    if isinstance(user_info, dict) and "user" in user_info:
        xu = user_info["user"].get("points", 0)
        username = user_info["user"].get("username", "Unknown")
        print(f"\nXSMM: {username} ({xu} xu)\n")
    else:
        print("\nToken sai\n"); sys.exit()

    print("Nhập số nick INSTA muốn chạy: ")
    sys.stdout.flush()
    try: luong = int(input().strip())
    except: luong = 1
    mangcookie = []; thu = 1
    while len(mangcookie) < luong:
        print(f"Cookie Thứ {thu}: ")
        sys.stdout.flush()
        cookie_str = input().strip()
        print("Proxy (Enter bỏ qua): ")
        sys.stdout.flush()
        proxy_str = input().strip()
        if not cookie_str: continue
        mangcookie.append({"cookie": cookie_str, "proxy": proxy_str})
        thu += 1

    dl = 150; doi = 99999
    if len(mangcookie) == 1:
        print("Dừng bao lâu khi hết job (giây)? ")
        sys.stdout.flush()
        try: dl = int(input().strip())
        except: dl = 150
    else:
        print("Bao nhiêu job thì đổi nick? ")
        sys.stdout.flush()
        try:
            doi = int(input().strip())
            if doi < 1: doi = 99999
        except: doi = 99999

    listnv = []; config_delays = {'tym': 10, 'follow': 15, 'comment': 20}
    while True:
        print("Chế độ Tym (on/off): ")
        sys.stdout.flush()
        if input().strip().lower() == 'on':
            listnv.append('instagram_like')
            print("Delay Tym: ")
            sys.stdout.flush()
            try:
                config_delays['tym'] = int(input().strip())
                if config_delays['tym'] < 1: config_delays['tym'] = 10
            except: config_delays['tym'] = 10
        print("Chế độ Follow (on/off): ")
        sys.stdout.flush()
        if input().strip().lower() == 'on':
            listnv.append('instagram_follow')
            print("Delay Follow: ")
            sys.stdout.flush()
            try:
                config_delays['follow'] = int(input().strip())
                if config_delays['follow'] < 1: config_delays['follow'] = 15
            except: config_delays['follow'] = 15
        print("Chế độ CMT (on/off): ")
        sys.stdout.flush()
        if input().strip().lower() == 'on':
            listnv.append('instagram_comment')
            print("Delay CMT: ")
            sys.stdout.flush()
            try:
                config_delays['comment'] = int(input().strip())
                if config_delays['comment'] < 10: config_delays['comment'] = 20
            except: config_delays['comment'] = 20
        if len(listnv) == 0: print("Chọn ít nhất 1 job!")
        else: break

    banner()
    print(f"XSMM User    : {username}")
    print(f"Tổng số Nick: {len(mangcookie)}")
    print(f"Số Luồng     : {max_threads} nick song song")
    print("="*60 + "\n")

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [executor.submit(run_single_account, acc_data, listnv, config_delays, xsmm_token, dl, doi) for acc_data in mangcookie]
    print("\nHoàn thành!\n")

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
        m = re.search(r'"LSD",\[\],{"token":"([^"]+)"}', res_home)
        if m: lsd = m.group(1)
        m = re.search(r'"dtsg":\{"token":"([^"]+)"', res_home) or re.search(r'name="fb_dtsg" value="([^"]+)"', res_home)
        if m: fb_dtsg = m.group(1)
        m = re.search(r'name="jazoest" value="(\d+)"', res_home)
        if m: jazoest = m.group(1)
    except Exception: pass
    CACHE_TOKENS[uid] = (fb_dtsg, lsd, jazoest)
    return CACHE_TOKENS[uid]

BROWSER_PROFILES = [
    {"name": "Chrome 124", "impersonate": "chrome124", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36", "sec_ch_ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"', "sec_ch_ua_platform": '"Windows"'},
    {"name": "Chrome 120", "impersonate": "chrome120", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", "sec_ch_ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"', "sec_ch_ua_platform": '"Windows"'},
    {"name": "Edge 124", "impersonate": "chrome124", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0", "sec_ch_ua": '"Chromium";v="124", "Microsoft Edge";v="124", "Not-A.Brand";v="99"', "sec_ch_ua_platform": '"Windows"'},
    {"name": "Chrome 124 macOS", "impersonate": "chrome124", "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36", "sec_ch_ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"', "sec_ch_ua_platform": '"macOS"'},
    {"name": "Chrome 124 Linux", "impersonate": "chrome124", "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36", "sec_ch_ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"', "sec_ch_ua_platform": '"Linux"'},
]

def parse_range_input(v, d_min=10, d_max=10):
    v = str(v).strip()
    if not v: return d_min, d_max
    if '-' in v:
        try:
            a, b = v.split('-'); a = int(a.strip()); b = int(b.strip())
            return (a, b) if a <= b else (b, a)
        except Exception: return d_min, d_max
    try: s = int(v); return s, s
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
    return {'accept': '*/*', 'accept-language': 'vi,en-US;q=0.9,en;q=0.8,vi-VN;q=0.7',
            'content-type': 'application/x-www-form-urlencoded', 'cookie': cookie,
            'origin': 'https://www.instagram.com', 'priority': 'u=1, i', 'referer': referer,
            'sec-ch-prefers-color-scheme': 'dark', 'sec-ch-ua': profile['sec_ch_ua'],
            'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': profile['sec_ch_ua_platform'],
            'sec-fetch-dest': 'empty', 'sec-fetch-mode': 'cors', 'sec-fetch-site': 'same-origin',
            'user-agent': profile['user_agent'], 'x-asbd-id': '359341', 'x-csrftoken': csrftoken,
            'x-ig-app-id': '936619743392459', 'x-ig-www-claim': '0', 'x-requested-with': 'XMLHttpRequest'}

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
    if not target_id: return '{"status": "error"}'
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
    if not mediaid: return '{"status": "error"}'
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
    if not mediaid: return '{"status": "error"}'
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
    print(f"Gom {len(task_list)} task -> Gửi duyệt...")
    ck = xsmm.complete_tasks(job_type, task_list, uid=uid, cookie_check=cookie_check)
    now = datetime.now().strftime("%H:%M:%S")
    if isinstance(ck, dict):
        if 'message' in ck:
            print(f"[{now}] {ck['message']} (+{ck.get('points', 0)} xu)")
        elif ck.get("is_timeout"):
            print(f"[{now}] {ck['message']}")
        elif 'error' in ck:
            print(f"[{now}] LỖI: {ck['error']}")
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
            except Exception as e: return {"error": str(e)}
        return {"error": "Retry failed"}

def main():
    print("Tool XSMM IG V5.2 khởi động...")
    sys.stdout.write("Access Token XSMM: ")
    sys.stdout.flush()
    xsmm_token = input().strip()

    sys.stdout.write("Có Cookie Check riêng? [1=Có / 0=Không]: ")
    sys.stdout.flush()
    choice_ck = input().strip()
    cookie_check_global = ""
    if choice_ck == '1':
        sys.stdout.write("Dán Cookie Check Web: ")
        sys.stdout.flush()
        cookie_check_global = input().strip()

    sys.stdout.write("Số nick INSTA: ")
    sys.stdout.flush()
    try: luong = int(input().strip())
    except: luong = 1
    mangcookie = []; thu = 1
    while len(mangcookie) < luong:
        print(f"Cookie App Thứ {thu}: ")
        sys.stdout.flush()
        cookie_str = input().strip()
        print("Proxy (Enter bỏ qua): ")
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
                print("Cookie/Proxy lỗi")
        except Exception:
            print("Cookie/Proxy lỗi")

    sys.stdout.write("Sau bao nhiêu job thì đổi nick: ")
    sys.stdout.flush()
    try:
        doi = int(input().strip())
        if doi < 1: doi = 99999
    except: doi = 99999

    listnv = []
    delay_tym_range = (10, 15); delay_sub_range = (15, 20); delay_cmt_range = (20, 25)
    batch_sub_count = 10
    job_interleave_limits = {}

    sys.stdout.write("Tym (on/off): ")
    sys.stdout.flush()
    if input().strip().lower() == 'on':
        listnv.append('instagram_like')
        sys.stdout.write("Delay Tym (vd 10 hoặc 10-15): ")
        sys.stdout.flush()
        delay_tym_range = parse_range_input(input().strip(), 10, 15)
        sys.stdout.write("Số job Tym/lượt (vd 3-5): ")
        sys.stdout.flush()
        job_interleave_limits['instagram_like'] = parse_range_input(input().strip(), 3, 5)

    sys.stdout.write("Follow (on/off): ")
    sys.stdout.flush()
    if input().strip().lower() == 'on':
        listnv.append('instagram_follow')
        sys.stdout.write("Delay Follow: ")
        sys.stdout.flush()
        delay_sub_range = parse_range_input(input().strip(), 15, 20)
        sys.stdout.write("Số job Follow/lượt: ")
        sys.stdout.flush()
        job_interleave_limits['instagram_follow'] = parse_range_input(input().strip(), 4, 6)
        sys.stdout.write("Số job gom (3-12, default 10): ")
        sys.stdout.flush()
        try:
            val = int(input().strip() or "10")
            if 3 <= val <= 12: batch_sub_count = val
        except: pass

    sys.stdout.write("Comment (on/off): ")
    sys.stdout.flush()
    if input().strip().lower() == 'on':
        listnv.append('instagram_comment')
        sys.stdout.write("Delay CMT: ")
        sys.stdout.flush()
        delay_cmt_range = parse_range_input(input().strip(), 20, 25)
        sys.stdout.write("Số job CMT/lượt: ")
        sys.stdout.flush()
        job_interleave_limits['instagram_comment'] = parse_range_input(input().strip(), 2, 3)

    if len(listnv) == 0:
        print("Chưa chọn job!")
        sys.exit()

    print(f"\nChạy {len(mangcookie)} nick - jobs: {listnv}\n")

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
                print("Cookie die")
                mangcookie.pop(l)
                continue

            print(f"[+] NICK [{tenfb} | UID: {idfb}] Browser: {profile['name']}")
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
                    print(f"Đã thêm [{tenfb}]")
            except Exception: pass

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
                            print(f"[Tym] {nv.get('target_url', '')}")
                            chayfl = tym(nv.get('target_id', ''), cookie, csf, nv.get('target_url', ''), proxy=proxy, profile=profile)
                            max_job += 1; jdt += 1
                            ok, err = parse_tym_cmt_response(chayfl)
                            if ok:
                                gui_nhan_xu("instagram_like", [nv.get('id')], idfb, target_ck, xsmm); solo = 0
                            else:
                                print(f"LỖI: {err}"); solo += 1
                            time.sleep(get_random_delay(delay_tym_range))
                            if solo > 4 or jdt >= jl or max_job >= doi: break
                    else: consecutive_empty += 1
                elif ct == 'instagram_follow':
                    lv = xsmm.get_tasks(ct, uid=idfb)
                    if isinstance(lv, list) and len(lv) > 0:
                        consecutive_empty = 0; solo = 0
                        for nv in lv:
                            tid = nv.get('target_id', ''); lj = nv.get('target_url', '')
                            print(f"[Follow] {tid}")
                            if not tid or not str(tid).isdigit(): continue
                            csf_m = re.search(r'csrftoken=([^;]+)', cookie); csf = csf_m.group(1) if csf_m else ""
                            chay_sub = follow(tid, cookie, csf, lj, proxy=proxy, profile=profile)
                            max_job += 1; jdt += 1
                            ok, msg = parse_follow_response(chay_sub)
                            if ok:
                                add_pending_task(idfb, nv.get('id')); solo = 0
                                pend = get_pending_tasks(idfb)
                                print(f"Gom: {len(pend)}/{batch_sub_count}")
                            else:
                                print(f"❌ {msg}")
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
                            print(f"[CMT] {lj}")
                            if not idm: continue
                            csf_m = re.search(r'csrftoken=([^;]+)', cookie); csf = csf_m.group(1) if csf_m else ""
                            chay_cmt = cmt(idm, noidung, cookie, csf, lj, proxy=proxy, profile=profile)
                            max_job += 1; jdt += 1
                            ok, err = parse_tym_cmt_response(chay_cmt)
                            if ok:
                                gui_nhan_xu("instagram_comment", [nv.get('id')], idfb, target_ck, xsmm); solo = 0
                            else:
                                print(f"LỖI: {err}"); solo += 1
                            time.sleep(get_random_delay(delay_cmt_range))
                            if solo > 4 or jdt >= jl or max_job >= doi: break
                    else: consecutive_empty += 1

                if consecutive_empty >= len(listnv) * 2:
                    print("Hết job, chờ 30s...")
                    time.sleep(30); consecutive_empty = 0

            rem = get_pending_tasks(idfb)
            if len(rem) > 0:
                gui_nhan_xu("instagram_follow", rem, idfb, target_ck, xsmm)
                remove_pending_tasks(idfb, rem)

        if len(mangcookie) == 0:
            print("Hết cookie!"); break

if __name__ == "__main__":
    main()
'''

# ============================================================================
# ==================== TOOL 3: 11223.py (NHẬN TOKEN TỪ STDIN) ===============
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

# ⚠️ Token giờ nhận từ stdin (form web gửi vào)
XSMM_TOKEN = ""
XSMM_HEADERS = {}

def set_token(token):
    global XSMM_TOKEN, XSMM_HEADERS
    XSMM_TOKEN = token
    XSMM_HEADERS = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

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
        sc = match.group(1)
        alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'
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
        headers = {'User-Agent': 'Instagram 269.0.0.18.75 Android (28/9; 480dpi; 1080x1920; Xiaomi; Redmi Note 7; lavender; qcom; sm6150; en_US; 317822529)',
                   'Accept-Language': 'vi-VN, en-US', 'X-IG-Capabilities': '3brTvx0=',
                   'X-IG-Connection-Type': 'WIFI', 'X-IG-App-ID': '1217981644879628',
                   'X-CSRFToken': self.csrftoken, 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                   'Host': 'i.instagram.com', 'Connection': 'keep-alive', 'Accept-Encoding': 'gzip, deflate'}
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
        headers = {'authority': 'www.instagram.com', 'accept': '*/*',
                   'accept-language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
                   'content-type': 'application/x-www-form-urlencoded',
                   'origin': 'https://www.instagram.com', 'referer': 'https://www.instagram.com/',
                   'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
                   'sec-ch-ua-mobile': '?1', 'sec-ch-ua-platform': '"Android"',
                   'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
                   'x-csrftoken': self.csrftoken, 'x-ig-app-id': '1217981644879628', 'x-requested-with': 'XMLHttpRequest'}
        data = {'container_module': 'profile', 'include_follow_friction_check': 'true',
                'nav_chain': 'PolarisProfileRoot:profilePage:1:via_cold_start',
                'user_id': str(target_user_id), 'jazoest': '22613',
                'fb_dtsg': dtsg if dtsg else 'NAfw7uEKgkrIMU2uHq9loxwB_G4Ai8jtT0G9FzGOC4w'}
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
        headers = {"authority": "www.instagram.com", "accept": "*/*",
                   "accept-language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
                   "content-type": "application/x-www-form-urlencoded",
                   "origin": "https://www.instagram.com",
                   "referer": f"https://www.instagram.com/p/{target_id}/comments/",
                   "user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36",
                   "x-asbd-id": "359341", "x-csrftoken": self.csrftoken,
                   "x-fb-friendly-name": "PolarisPostCommentInputRevampedMutation",
                   "x-ig-app-id": "1217981644879628", "x-requested-with": "XMLHttpRequest"}
        variables = ('{"connections":["client:root:__PolarisPostComments__xdt_api__v1__media__' + media_id + '__comments__connection_connection(data:{},media_id:\\"' + media_id + '\\",sort_order:\\"popular\\")"],"data":{"comment_text":"' + comment_content + '","media_id":"' + media_id + '"}}')
        data = (f"av={av}&__d=www&__user=0&__a=1&__req=31&__hs=20716.HYP%3Ainstagram_web_pkg.2.1...0&dpr=3&__ccg=EXCELLENT&__rev=1047982529"
                f"&__comet_req=7&fb_dtsg={dtsg or 'NAfw7uEKgkrIMU2uHq9loxwB_G4Ai8jtT0G9FzGOC4w'}"
                "&jazoest=26096&__spin_r=1047982529&__spin_b=trunk&__spin_t=1789924702"
                "&__crn=comet.igweb.PolarisMobileAllCommentsRouteNext&fb_api_caller_class=RelayModern"
                "&fb_api_req_friendly_name=PolarisPostCommentInputRevampedMutation&server_timestamps=true"
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

    # ⚠️ BƯỚC MỚI: Nhận token từ stdin trước
    sys.stdout.write("Access Token XSMM: ")
    sys.stdout.flush()
    input_token = input().strip()
    set_token(input_token)

    ui = get_xsmm_user()
    print(f"Tài khoản: {ui.get('username')} | Xu: {ui.get('points')}")
    print("-" * 42)

    sys.stdout.write("Nhập Cookie Instagram: ")
    sys.stdout.flush()
    insta_cookie = input().strip()
    if not insta_cookie:
        print("Cookie trống!"); return

    sys.stdout.write("Chọn nhiệm vụ (1=LIKE 2=FOLLOW 3=COMMENT): ")
    sys.stdout.flush()
    choice = input().strip()
    task_type = {"1": "instagram_like", "2": "instagram_follow", "3": "instagram_comment"}.get(choice, "instagram_like")

    sys.stdout.write("Delay thao tác (min): ")
    sys.stdout.flush()
    try: dmin = int(input().strip() or 10)
    except: dmin = 10
    sys.stdout.write("Delay thao tác (max): ")
    sys.stdout.flush()
    try: dmax = int(input().strip() or 15)
    except: dmax = 15
    sys.stdout.write("Delay nhận xu (min): ")
    sys.stdout.flush()
    try: dcmin = int(input().strip() or 3)
    except: dcmin = 3
    sys.stdout.write("Delay nhận xu (max): ")
    sys.stdout.flush()
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
# ================== KHAI BÁO TOOL TRONG APP =================================
# ============================================================================
EMBEDDED_TOOLS = {
    "xsmmv3.2": {
        "name": "XSMM Tool V3.2",
        "desc": "Tool Instagram Auto Jobs - XSMM API (Multi-thread + số luồng tùy chỉnh)",
        "color": "#00d4ff",
        "filename": "xsmmv3.2.py",
        "code": TOOL_CODE_XSMMV32,
    },
    "xsmmigv5.2": {
        "name": "XSMM IG V5.2",
        "desc": "Tool Instagram Auto Jobs - XSMM API V2 (Browser Profiles + JSON Queue)",
        "color": "#ff6b9d",
        "filename": "xsmmigv5.2.py",
        "code": TOOL_CODE_XSMMIGV52,
    },
    "11223": {
        "name": "Simple IG Bot",
        "desc": "Tool đơn giản - Like / Follow / Comment với XSMM (nhận token từ form)",
        "color": "#ffd93d",
        "filename": "11223.py",
        "code": TOOL_CODE_11223,
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


@socketio.on('join')
def on_join(data):
    session_id = data.get('session_id')
    if session_id:
        join_room(session_id)
        emit('joined', {'session_id': session_id})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("=" * 60)
    print(" 🚀 TA TOOL WEB MANAGER (3 TOOLS IG)")
    print(f" 📁 Temp tools: {TEMP_TOOLS_DIR}")
    print(f" 🌐 Port: {port}")
    print(f" 📦 Tools: {list(EMBEDDED_TOOLS.keys())}")
    print("=" * 60)
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
