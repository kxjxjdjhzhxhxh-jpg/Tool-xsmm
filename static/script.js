const socket = io();
const state = {};

function $(sel, root = document) { return root.querySelector(sel); }
function $$(sel, root = document) { return [...root.querySelectorAll(sel)]; }

function now() {
    return new Date().toLocaleTimeString('vi-VN', { hour12: false });
}

function escapeHtml(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

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

setInterval(() => {
    $('#clock').textContent = now();
}, 1000);

// Tab switch
$$('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tool = btn.dataset.tool;
        $$('.tab-btn').forEach(b => b.classList.toggle('active', b === btn));
        $$('.tool-panel').forEach(p => p.classList.toggle('active', p.dataset.tool === tool));
    });
});
$$('.tab-btn')[0]?.click();

function getPanel(tool) { return $(`.tool-panel[data-tool="${tool}"]`); }
function getTerm(tool) { return $(`#term-${tool}`); }
function getStatusBadge(tool) { return $(`.session-info[data-tool="${tool}"] .status-badge`); }
function getSessionIdEl(tool) { return $(`.session-info[data-tool="${tool}"] .session-id`); }
function getOutputCount(tool) { return $(`.session-info[data-tool="${tool}"] .output-count`); }
function getBtn(tool, cls) { return $(`.btn-${cls}[data-tool="${tool}"]`); }

function setStatus(tool, status, sessionId = null) {
    const badge = getStatusBadge(tool);
    if (!badge) return;
    badge.className = 'status-badge ' + (status === 'running' ? 'running' : status === 'stopped' ? 'stopped' : 'idle');
    badge.textContent = status === 'running' ? '● RUNNING' : status === 'stopped' ? '● STOPPED' : '● IDLE';

    if (sessionId !== null) {
        getSessionIdEl(tool).textContent = sessionId ? `Session: ${sessionId}` : '';
    }

    const isRunning = status === 'running';
    getBtn(tool, 'start').disabled = isRunning;
    getBtn(tool, 'stop').disabled = !isRunning;
    getBtn(tool, 'clear').disabled = false;
    getBtn(tool, 'save').disabled = false;

    const stdin = $(`.stdin-input[data-tool="${tool}"]`);
    const sendBtn = $(`.btn-send[data-tool="${tool}"]`);
    if (stdin) stdin.disabled = !isRunning;
    if (sendBtn) sendBtn.disabled = !isRunning;
}

// START
$$('.btn-start').forEach(btn => {
    btn.addEventListener('click', async () => {
        const tool = btn.dataset.tool;
        btn.disabled = true;
        try {
            const res = await fetch(`/api/start/${tool}`, { method: 'POST' });
            const data = await res.json();
            if (!data.ok) {
                alert('Lỗi: ' + (data.error || 'Không rõ'));
                btn.disabled = false;
                return;
            }
            state[tool] = { sessionId: data.session_id, status: 'running' };
            setStatus(tool, 'running', data.session_id);
            socket.emit('join', { session_id: data.session_id });
            const term = getTerm(tool);
            term.innerHTML = '';
            appendLine(term, `▶ Bắt đầu chạy tool [${tool}] — Session: ${data.session_id}`);
            // Auto switch tab
            $(`.tab-btn[data-tool="${tool}"]`).click();
        } catch (e) {
            alert('Lỗi kết nối: ' + e.message);
            btn.disabled = false;
        }
    });
});

// STOP
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

// CLEAR
$$('.btn-clear').forEach(btn => {
    btn.addEventListener('click', () => {
        const tool = btn.dataset.tool;
        getTerm(tool).innerHTML = '';
        getOutputCount(tool).textContent = '0 dòng';
        const s = state[tool];
        if (s) fetch(`/api/clear/${s.sessionId}`, { method: 'POST' });
    });
});

// SAVE
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

// STDIN
function sendStdin(tool) {
    const input = $(`.stdin-input[data-tool="${tool}"]`);
    const text = input.value;
    const s = state[tool];
    if (!s || !s.sessionId) return;
    fetch(`/api/input/${s.sessionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
    }).then(r => r.json()).then(data => {
        if (!data.ok) console.error('Lỗi gửi input:', data.error);
    });
    const term = getTerm(tool);
    appendLine(term, `> ${text}`, now());
    input.value = '';
}

$$('.btn-send').forEach(btn => {
    btn.addEventListener('click', () => sendStdin(btn.dataset.tool));
});
$$('.stdin-input').forEach(inp => {
    inp.addEventListener('keydown', e => {
        if (e.key === 'Enter') sendStdin(inp.dataset.tool);
    });
});

// SOCKET
socket.on('connect', () => console.log('[SOCKET] connected:', socket.id));
socket.on('disconnect', () => console.log('[SOCKET] disconnected'));

socket.on('output', data => {
    const { session_id, line, ts } = data;
    const tool = Object.keys(state).find(k => state[k].sessionId === session_id);
    if (!tool) return;
    const term = getTerm(tool);
    if (!term) return;
    appendLine(term, line, ts);
    const count = term.children.length;
    getOutputCount(tool).textContent = count + ' dòng';
});

socket.on('status', data => {
    const { session_id, status, message, return_code } = data;
    const tool = Object.keys(state).find(k => state[k].sessionId === session_id);
    if (!tool) return;
    if (status === 'stopped') {
        state[tool].status = 'stopped';
        setStatus(tool, 'stopped');
        const term = getTerm(tool);
        appendLine(term, `■ ${message || 'Đã dừng'} (exit: ${return_code ?? '?'})`);
    }
});

socket.on('cleared', data => {
    const { session_id } = data;
    const tool = Object.keys(state).find(k => state[k].sessionId === session_id);
    if (tool) getTerm(tool).innerHTML = '';
});

fetch('/api/sessions').then(r => r.json()).then(list => {
    $('#sessions-count').textContent = list.length + ' sessions';
});
