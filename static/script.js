const socket = io();
const state = {};

function $(sel, root = document) { return root.querySelector(sel); }
function $$(sel, root = document) { return [...root.querySelectorAll(sel)]; }
function now() { return new Date().toLocaleTimeString('vi-VN', { hour12: false }); }
function escapeHtml(s) { return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }

function classifyLine(line) {
    if (/\b(traceback|exception|error|lỗi|die|fail|thất bại)\b/i.test(line)) return 'err';
    if (/\b(warn|cảnh báo|retry|timeout|chậm)\b/i.test(line)) return 'warn';
    if (/\b(success|thành công|✔|✅|ok|done)\b/i.test(line)) return 'ok';
    if (/\b(info|đang|bắt đầu|nick live|nick|job|task)\b/i.test(line)) return 'info';
    return '';
}

function appendLine(termEl, line, ts = null) {
    const div = document.createElement('div');
    div.className = 'term-line ' + classifyLine(line);
    const time = ts || now();
    div.innerHTML = `<span class="ts">[${time}]</span>${escapeHtml(line)}`;
    termEl.appendChild(div);
    termEl.scrollTop = termEl.scrollHeight;
}

setInterval(() => { const el = $('#clock'); if (el) el.textContent = now(); }, 1000);

// Tab switch
$$('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tool = btn.dataset.tool;
        $$('.tab-btn').forEach(b => b.classList.toggle('active', b === btn));
        $$('.tool-panel').forEach(p => p.classList.toggle('active', p.dataset.tool === tool));
    });
});
$$('.tab-btn')[0]?.click();

// Helpers
function getPanel(tool) { return $(`.tool-panel[data-tool="${tool}"]`); }
function getTerm(tool) { const p = getPanel(tool); return p ? p.querySelector('.terminal') : null; }
function getStatusBadge(tool) { return $(`.session-info[data-tool="${tool}"] .status-badge`); }
function getSessionIdEl(tool) { return $(`.session-info[data-tool="${tool}"] .session-id`); }
function getOutputCount(tool) { return $(`.session-info[data-tool="${tool}"] .output-count`); }
function getBtn(tool, cls) { return $(`.btn-${cls}[data-tool="${tool}"]`); }
function getCfg(tool, cls) { const p = getPanel(tool); return p ? p.querySelector('.' + cls) : null; }

function setStatus(tool, status, sessionId = null) {
    const badge = getStatusBadge(tool);
    if (!badge) return;
    badge.className = 'status-badge ' + (status === 'running' ? 'running' : status === 'stopped' ? 'stopped' : 'idle');
    badge.textContent = status === 'running' ? '● RUNNING' : status === 'stopped' ? '● STOPPED' : '● IDLE';
    if (sessionId !== null) getSessionIdEl(tool).textContent = sessionId ? `Session: ${sessionId}` : '';

    const isRunning = status === 'running';
    getBtn(tool, 'start').disabled = isRunning;
    getBtn(tool, 'stop').disabled = !isRunning;
    getBtn(tool, 'clear').disabled = false;
    getBtn(tool, 'save').disabled = false;

    const stdin = $(`.stdin-input[data-tool="${tool}"]`);
    const sendBtn = $(`.btn-send[data-tool="${tool}"]`);
    if (stdin) stdin.disabled = !isRunning;
    if (sendBtn) sendBtn.disabled = !isRunning;

    // Vô hiệu hóa form khi đang chạy
    const form = $(`#form-${tool.replace('.', '_')}`);
    if (form) form.querySelectorAll('input, textarea, select').forEach(el => el.disabled = isRunning);
}

// ================== BUILD INPUT SEQUENCE ==================
function buildInputSequence(tool) {
    const token = (getCfg(tool, 'cfg-token')?.value || '').trim();
    const cookiesRaw = (getCfg(tool, 'cfg-cookies')?.value || '').trim();
    const cookieCheck = (getCfg(tool, 'cfg-cookiecheck')?.value || '').trim();
    const delayTym = getCfg(tool, 'cfg-delay-tym')?.value || '10';
    const delayFollow = getCfg(tool, 'cfg-delay-follow')?.value || '15';
    const delayComment = getCfg(tool, 'cfg-delay-comment')?.value || '20';
    const threads = getCfg(tool, 'cfg-threads')?.value || '10';
    const rotate = getCfg(tool, 'cfg-rotate')?.value || '99999';
    const wait = getCfg(tool, 'cfg-wait')?.value || '150';
    const jobLike = getCfg(tool, 'cfg-job-like')?.checked;
    const jobFollow = getCfg(tool, 'cfg-job-follow')?.checked;
    const jobComment = getCfg(tool, 'cfg-job-comment')?.checked;
    const mode = getCfg(tool, 'cfg-mode')?.value || '1';
    const delayCoin = getCfg(tool, 'cfg-delaycoin')?.value || '3';

    // Parse cookie list
    const cookieLines = cookiesRaw.split('\n').map(l => l.trim()).filter(l => l);
    const cookies = [];
    const proxies = [];
    for (const line of cookieLines) {
        const parts = line.split('|');
        cookies.push(parts[0].trim());
        proxies.push(parts[1] ? parts[1].trim() : '');
    }

    const seq = []; // mỗi phần tử là 1 chuỗi gửi vào stdin

    if (tool === 'xsmmv3.2' || tool === 'xsmmigv5.2') {
        // 1. Token XSMM (nếu có file log cũ sẽ hỏi Enter/No — ta luôn gửi 'no' để dùng token mới)
        // Tool sẽ check "logXSMM.txt" tồn tại — trong môi trường mới không có => hỏi thẳng token
        seq.push(token);

        // 2. Cookie Check (chỉ V5.2)
        if (tool === 'xsmmigv5.2') {
            if (cookieCheck) {
                // Chọn [1] để thay cookie check mới
                seq.push('1');
                seq.push(cookieCheck);
            } else {
                // Chọn [0] để tắt cookie check riêng
                seq.push('0');
            }
        }

        // 3. Số nick muốn chạy
        seq.push(String(cookies.length));

        // 4. Nhập từng cookie + proxy
        for (let i = 0; i < cookies.length; i++) {
            seq.push(cookies[i]);
            seq.push(proxies[i] || '');
        }

        // 5. Delay / rotate / wait
        if (cookies.length === 1) {
            seq.push(wait); // Hỏi "dừng bao lâu?"
        } else {
            seq.push(rotate); // Hỏi "sau bao nhiêu job thì đổi nick"
        }

        // 6. Chọn jobs: on/off
        seq.push(jobLike ? 'on' : 'off');
        if (jobLike) seq.push(delayTym);

        seq.push(jobFollow ? 'on' : 'off');
        if (jobFollow) {
            seq.push(delayFollow);
            if (tool === 'xsmmigv5.2') seq.push('10'); // số job gom follow
        }

        seq.push(jobComment ? 'on' : 'off');
        if (jobComment) seq.push(delayComment);

    } else if (tool === '11223') {
        // Tool 3: đơn giản
        seq.push(cookies[0] || '');
        seq.push(mode);
        seq.push(delayTym);        // delay thao tác min
        seq.push(String(parseInt(delayTym) + 5)); // delay thao tác max
        seq.push(delayCoin);       // delay nhận xu min
        seq.push(String(parseInt(delayCoin) + 2)); // delay nhận xu max
    }

    return seq.filter(s => s !== undefined && s !== null);
}

// ================== START ==================
$$('.btn-start').forEach(btn => {
    btn.addEventListener('click', async () => {
        const tool = btn.dataset.tool;

        // Validate
        const token = (getCfg(tool, 'cfg-token')?.value || '').trim();
        const cookiesRaw = (getCfg(tool, 'cfg-cookies')?.value || '').trim();

        if (tool !== '11223') {
            if (!token) { alert('⚠️ Vui lòng nhập Access Token XSMM!'); return; }
            if (!cookiesRaw) { alert('⚠️ Vui lòng nhập ít nhất 1 cookie IG/FB!'); return; }
        } else {
            if (!cookiesRaw) { alert('⚠️ Vui lòng nhập Cookie Instagram!'); return; }
            // Tool 3 hard-code token trong file, không hỏi
        }

        btn.disabled = true;
        try {
            const res = await fetch(`/api/start/${tool}`, { method: 'POST' });
            const data = await res.json();
            if (!data.ok) { alert('Lỗi: ' + (data.error || 'Không rõ')); btn.disabled = false; return; }

            state[tool] = { sessionId: data.session_id, status: 'running' };
            setStatus(tool, 'running', data.session_id);
            socket.emit('join', { session_id: data.session_id });

            const term = getTerm(tool);
            if (term) {
                term.innerHTML = '';
                appendLine(term, `▶ Bắt đầu chạy tool [${tool}] — Session: ${data.session_id}`);
                appendLine(term, `📝 Đang tự động gửi ${buildInputSequence(tool).length} dòng cấu hình vào stdin...`);
            }

            // Gửi tuần tự từng input với delay nhỏ để tool kịp đọc
            const seq = buildInputSequence(tool);
            for (let i = 0; i < seq.length; i++) {
                await new Promise(r => setTimeout(r, 350));
                await fetch(`/api/input/${data.session_id}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: seq[i] })
                });
                if (term) appendLine(term, `> [auto] ${seq[i].length > 80 ? seq[i].substring(0, 80) + '...' : seq[i]}`, now());
            }
            if (term) appendLine(term, `✅ Đã gửi xong cấu hình. Tool bắt đầu chạy...`, now());

            $(`.tab-btn[data-tool="${tool}"]`).click();
        } catch (e) {
            alert('Lỗi kết nối: ' + e.message);
            btn.disabled = false;
        }
    });
});

// ================== STOP ==================
$$('.btn-stop').forEach(btn => {
    btn.addEventListener('click', async () => {
        const tool = btn.dataset.tool;
        const s = state[tool];
        if (!s) return;
        if (!confirm('Dừng tool này?')) return;
        await fetch(`/api/stop/${s.sessionId}`, { method: 'POST' });
        setStatus(tool, 'stopped');
    });
});

// ================== CLEAR ==================
$$('.btn-clear').forEach(btn => {
    btn.addEventListener('click', () => {
        const tool = btn.dataset.tool;
        const t = getTerm(tool); if (t) t.innerHTML = '';
        const c = getOutputCount(tool); if (c) c.textContent = '0 dòng';
        const s = state[tool];
        if (s) fetch(`/api/clear/${s.sessionId}`, { method: 'POST' });
    });
});

// ================== SAVE ==================
$$('.btn-save').forEach(btn => {
    btn.addEventListener('click', async () => {
        const tool = btn.dataset.tool;
        const s = state[tool];
        if (!s) { alert('Chưa có session để lưu!'); return; }
        const res = await fetch(`/api/save/${s.sessionId}`, { method: 'POST' });
        const data = await res.json();
        if (data.ok) alert('Đã lưu log: ' + data.filename);
        else alert('Lỗi: ' + (data.error || ''));
    });
});

// ================== STDIN (nhập tay khi cần) ==================
function sendStdin(tool) {
    const input = $(`.stdin-input[data-tool="${tool}"]`); if (!input) return;
    const text = input.value;
    const s = state[tool]; if (!s || !s.sessionId) return;
    fetch(`/api/input/${s.sessionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
    }).then(r => r.json()).then(data => {
        if (!data.ok) console.error('Lỗi gửi input:', data.error);
    });
    const term = getTerm(tool); if (term) appendLine(term, `> ${text}`, now());
    input.value = '';
}
$$('.btn-send').forEach(btn => btn.addEventListener('click', () => sendStdin(btn.dataset.tool)));
$$('.stdin-input').forEach(inp => inp.addEventListener('keydown', e => {
    if (e.key === 'Enter') sendStdin(inp.dataset.tool);
}));

// ================== SOCKET ==================
socket.on('connect', () => console.log('[SOCKET] connected:', socket.id));
socket.on('disconnect', () => console.log('[SOCKET] disconnected'));

socket.on('output', data => {
    const { session_id, line, ts } = data;
    const tool = Object.keys(state).find(k => state[k].sessionId === session_id);
    if (!tool) return;
    const term = getTerm(tool); if (!term) return;
    appendLine(term, line, ts);
    const outCount = getOutputCount(tool);
    if (outCount) outCount.textContent = term.children.length + ' dòng';
});

socket.on('status', data => {
    const { session_id, status, message, return_code } = data;
    const tool = Object.keys(state).find(k => state[k].sessionId === session_id);
    if (!tool) return;
    if (status === 'stopped') {
        state[tool].status = 'stopped';
        setStatus(tool, 'stopped');
        const term = getTerm(tool);
        if (term) appendLine(term, `■ ${message || 'Đã dừng'} (exit: ${return_code ?? '?'})`);
    }
});

socket.on('cleared', data => {
    const tool = Object.keys(state).find(k => state[k].sessionId === data.session_id);
    if (tool) { const t = getTerm(tool); if (t) t.innerHTML = ''; }
});

fetch('/api/sessions').then(r => r.json()).then(list => {
    const el = $('#sessions-count'); if (el) el.textContent = list.length + ' sessions';
});

// ================== LƯU CẤU HÌNH VÀO localStorage ==================
const CFG_FIELDS = ['cfg-token', 'cfg-cookies', 'cfg-cookiecheck', 'cfg-delay-tym', 'cfg-delay-follow',
                    'cfg-delay-comment', 'cfg-threads', 'cfg-rotate', 'cfg-wait', 'cfg-delaycoin'];

CFG_FIELDS.forEach(cls => {
    $$('.' + cls).forEach(input => {
        const tool = input.closest('.tool-panel')?.dataset.tool;
        if (!tool) return;
        const key = `ta_cfg_${tool}_${cls}`;
        const saved = localStorage.getItem(key);
        if (saved !== null && input.type !== 'checkbox') input.value = saved;
        input.addEventListener('input', () => localStorage.setItem(key, input.value));
    });
});

// Checkbox jobs
['cfg-job-like', 'cfg-job-follow', 'cfg-job-comment'].forEach(cls => {
    $$('.' + cls).forEach(cb => {
        const tool = cb.closest('.tool-panel')?.dataset.tool;
        if (!tool) return;
        const key = `ta_cfg_${tool}_${cls}`;
        const saved = localStorage.getItem(key);
        if (saved !== null) cb.checked = saved === 'true';
        cb.addEventListener('change', () => localStorage.setItem(key, cb.checked));
    });
});
