const socket = io();
const state = {};

function $(sel, root = document) { return root.querySelector(sel); }
function $$(sel, root = document) { return [...root.querySelectorAll(sel)]; }
function now() { return new Date().toLocaleTimeString('vi-VN', { hour12: false }); }
function escapeHtml(s) { return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }

// ================== HIỆU ỨNG CANVAS: SÉT + TIM + HOA ==================
(function initEffects() {
    const canvas = document.getElementById('fx-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let W, H;

    function resize() {
        W = canvas.width = window.innerWidth;
        H = canvas.height = window.innerHeight;
    }
    resize();
    window.addEventListener('resize', resize);

    // Lấy màu accent từ CSS
    let ACCENT = '#00d4ff';
    function getAccent() {
        return getComputedStyle(document.documentElement).getPropertyValue('--accent').trim() || '#00d4ff';
    }
    setInterval(() => { ACCENT = getAccent(); }, 1000);

    // ==== HOA RƠI ====
    const flowers = [];
    const FLOWER_COLORS = ['#ff6b9d', '#ffd93d', '#a78bfa', '#ff8fab', '#f9a8d4'];
    function createFlower() {
        return {
            x: Math.random() * W,
            y: -30,
            size: 8 + Math.random() * 12,
            speedY: 0.5 + Math.random() * 1,
            speedX: (Math.random() - 0.5) * 0.8,
            rot: Math.random() * Math.PI * 2,
            rotSpeed: (Math.random() - 0.5) * 0.05,
            color: FLOWER_COLORS[Math.floor(Math.random() * FLOWER_COLORS.length)],
            type: Math.random() < 0.5 ? 'flower' : 'petal'
        };
    }
    for (let i = 0; i < 15; i++) {
        const f = createFlower();
        f.y = Math.random() * H;
        flowers.push(f);
    }

    // ==== TIM RƠI ====
    const hearts = [];
    function createHeart() {
        return {
            x: Math.random() * W,
            y: -30,
            size: 8 + Math.random() * 10,
            speedY: 0.8 + Math.random() * 1.2,
            speedX: (Math.random() - 0.5) * 0.6,
            color: ['#ef4444', '#ec4899', '#f43f5e', '#fb7185', '#fda4af'][Math.floor(Math.random() * 5)],
            alpha: 0.6 + Math.random() * 0.4,
            pulse: Math.random() * Math.PI * 2
        };
    }
    for (let i = 0; i < 10; i++) {
        const h = createHeart();
        h.y = Math.random() * H;
        hearts.push(h);
    }

    // ==== TIA SÉT ====
    const lightningBolts = [];
    function createLightning() {
        const startX = Math.random() * W;
        const segments = [];
        let x = startX, y = 0;
        const endY = H * (0.3 + Math.random() * 0.4);
        while (y < endY) {
            segments.push({ x, y });
            x += (Math.random() - 0.5) * 80;
            y += 15 + Math.random() * 25;
        }
        return {
            segments,
            life: 1,
            fadeSpeed: 0.02 + Math.random() * 0.03,
            width: 1.5 + Math.random() * 2,
            branch: Math.random() < 0.3
        };
    }

    // Vẽ 1 tia sét
    function drawLightning(bolt, color) {
        if (bolt.segments.length < 2) return;
        ctx.save();
        ctx.globalAlpha = bolt.life;
        ctx.strokeStyle = color;
        ctx.lineWidth = bolt.width;
        ctx.shadowBlur = 25;
        ctx.shadowColor = color;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';

        // Glow ngoài
        ctx.beginPath();
        ctx.moveTo(bolt.segments[0].x, bolt.segments[0].y);
        for (let i = 1; i < bolt.segments.length; i++) {
            ctx.lineTo(bolt.segments[i].x, bolt.segments[i].y);
        }
        ctx.stroke();

        // Lõi trắng
        ctx.strokeStyle = 'rgba(255, 255, 255, ' + bolt.life + ')';
        ctx.lineWidth = bolt.width * 0.4;
        ctx.shadowBlur = 0;
        ctx.beginPath();
        ctx.moveTo(bolt.segments[0].x, bolt.segments[0].y);
        for (let i = 1; i < bolt.segments.length; i++) {
            ctx.lineTo(bolt.segments[i].x, bolt.segments[i].y);
        }
        ctx.stroke();

        // Nhánh
        if (bolt.branch && bolt.segments.length > 3) {
            const idx = Math.floor(bolt.segments.length / 2);
            const bp = bolt.segments[idx];
            ctx.strokeStyle = color;
            ctx.lineWidth = bolt.width * 0.6;
            ctx.shadowBlur = 20;
            ctx.shadowColor = color;
            ctx.beginPath();
            ctx.moveTo(bp.x, bp.y);
            let bx = bp.x, by = bp.y;
            for (let i = 0; i < 4; i++) {
                bx += (Math.random() - 0.5) * 60;
                by += 20 + Math.random() * 20;
                ctx.lineTo(bx, by);
            }
            ctx.stroke();
        }
        ctx.restore();
    }

    // Vẽ hoa
    function drawFlower(f) {
        ctx.save();
        ctx.translate(f.x, f.y);
        ctx.rotate(f.rot);
        ctx.globalAlpha = 0.85;
        if (f.type === 'petal') {
            // Cánh hoa đơn
            ctx.fillStyle = f.color;
            ctx.shadowBlur = 10;
            ctx.shadowColor = f.color;
            ctx.beginPath();
            ctx.ellipse(0, 0, f.size, f.size * 0.5, 0, 0, Math.PI * 2);
            ctx.fill();
        } else {
            // Hoa 5 cánh
            ctx.fillStyle = f.color;
            ctx.shadowBlur = 12;
            ctx.shadowColor = f.color;
            for (let i = 0; i < 5; i++) {
                ctx.save();
                ctx.rotate((Math.PI * 2 / 5) * i);
                ctx.beginPath();
                ctx.ellipse(0, -f.size * 0.5, f.size * 0.4, f.size * 0.7, 0, 0, Math.PI * 2);
                ctx.fill();
                ctx.restore();
            }
            // Nhụy vàng
            ctx.fillStyle = '#ffd93d';
            ctx.shadowColor = '#ffd93d';
            ctx.beginPath();
            ctx.arc(0, 0, f.size * 0.25, 0, Math.PI * 2);
            ctx.fill();
        }
        ctx.restore();
    }

    // Vẽ tim
    function drawHeart(h) {
        ctx.save();
        ctx.translate(h.x, h.y);
        const s = h.size + Math.sin(h.pulse) * 1.5;
        ctx.globalAlpha = h.alpha;
        ctx.fillStyle = h.color;
        ctx.shadowBlur = 15;
        ctx.shadowColor = h.color;
        ctx.beginPath();
        ctx.moveTo(0, s * 0.3);
        ctx.bezierCurveTo(0, 0, -s * 0.5, 0, -s * 0.5, s * 0.3);
        ctx.bezierCurveTo(-s * 0.5, s * 0.7, 0, s * 1.1, 0, s * 1.3);
        ctx.bezierCurveTo(0, s * 1.1, s * 0.5, s * 0.7, s * 0.5, s * 0.3);
        ctx.bezierCurveTo(s * 0.5, 0, 0, 0, 0, s * 0.3);
        ctx.fill();
        ctx.restore();
    }

    // Vòng lặp
    function loop() {
        ctx.clearRect(0, 0, W, H);

        // Vẽ hoa
        for (const f of flowers) {
            f.y += f.speedY;
            f.x += f.speedX + Math.sin(f.y * 0.01) * 0.3;
            f.rot += f.rotSpeed;
            if (f.y > H + 40) {
                Object.assign(f, createFlower());
            }
            drawFlower(f);
        }

        // Vẽ tim
        for (const h of hearts) {
            h.y += h.speedY;
            h.x += h.speedX + Math.sin(h.y * 0.02) * 0.4;
            h.pulse += 0.08;
            if (h.y > H + 40) {
                Object.assign(h, createHeart());
            }
            drawHeart(h);
        }

        // Vẽ sét
        for (let i = lightningBolts.length - 1; i >= 0; i--) {
            const bolt = lightningBolts[i];
            bolt.life -= bolt.fadeSpeed;
            if (bolt.life <= 0) {
                lightningBolts.splice(i, 1);
                continue;
            }
            drawLightning(bolt, ACCENT);
        }
        // Random tạo tia sét mới
        if (Math.random() < 0.01 && lightningBolts.length < 3) {
            lightningBolts.push(createLightning());
        }

        requestAnimationFrame(loop);
    }
    loop();

    // Tạo sét ngay khi bấm nút (tương tác)
    document.addEventListener('click', (e) => {
        if (e.target.closest('.btn-start') || e.target.closest('.btn-stop')) {
            for (let i = 0; i < 3; i++) {
                setTimeout(() => lightningBolts.push(createLightning()), i * 150);
            }
        }
    });
})();

// ================== COLOR PICKER ==================
(function initColorPicker() {
    const picker = document.getElementById('theme-color');
    if (!picker) return;
    const saved = localStorage.getItem('theme_accent');
    if (saved) {
        document.documentElement.style.setProperty('--accent', saved);
        picker.value = saved;
    }
    picker.addEventListener('input', (e) => {
        const color = e.target.value;
        document.documentElement.style.setProperty('--accent', color);
        localStorage.setItem('theme_accent', color);
    });
})();

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
    const form = $(`#form-${tool.replace('.', '_')}`);
    if (form) form.querySelectorAll('input, textarea, select').forEach(el => el.disabled = isRunning);
}

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

    const cookieLines = cookiesRaw.split('\n').map(l => l.trim()).filter(l => l);
    const cookies = [], proxies = [];
    for (const line of cookieLines) {
        const parts = line.split('|');
        cookies.push(parts[0].trim());
        proxies.push(parts[1] ? parts[1].trim() : '');
    }

    const seq = [];

    if (tool === 'xsmmv3.2') {
        seq.push(threads);
        seq.push(token);
        seq.push(String(cookies.length));
        for (let i = 0; i < cookies.length; i++) { seq.push(cookies[i]); seq.push(proxies[i] || ''); }
        if (cookies.length === 1) seq.push(wait); else seq.push(rotate);
        seq.push(jobLike ? 'on' : 'off'); if (jobLike) seq.push(delayTym);
        seq.push(jobFollow ? 'on' : 'off'); if (jobFollow) seq.push(delayFollow);
        seq.push(jobComment ? 'on' : 'off'); if (jobComment) seq.push(delayComment);
    } else if (tool === 'xsmmigv5.2') {
        seq.push(token);
        if (cookieCheck) { seq.push('1'); seq.push(cookieCheck); } else seq.push('0');
        seq.push(String(cookies.length));
        for (let i = 0; i < cookies.length; i++) { seq.push(cookies[i]); seq.push(proxies[i] || ''); }
        seq.push(rotate);
        seq.push(jobLike ? 'on' : 'off'); if (jobLike) { seq.push(delayTym); seq.push('3-5'); }
        seq.push(jobFollow ? 'on' : 'off'); if (jobFollow) { seq.push(delayFollow); seq.push('4-6'); seq.push('10'); }
        seq.push(jobComment ? 'on' : 'off'); if (jobComment) { seq.push(delayComment); seq.push('2-3'); }
    } else if (tool === '11223') {
        // Tool 11223 giờ: token -> cookie -> mode -> delay min/max -> coin min/max
        seq.push(token);
        seq.push(cookies[0] || '');
        seq.push(mode);
        seq.push(delayTym);
        seq.push(String(parseInt(delayTym) + 5));
        seq.push(delayCoin);
        seq.push(String(parseInt(delayCoin) + 2));
    }
    return seq.filter(s => s !== undefined && s !== null);
}

// START
$$('.btn-start').forEach(btn => {
    btn.addEventListener('click', async () => {
        const tool = btn.dataset.tool;
        const token = (getCfg(tool, 'cfg-token')?.value || '').trim();
        const cookiesRaw = (getCfg(tool, 'cfg-cookies')?.value || '').trim();

        if (!token) { alert('⚠️ Vui lòng nhập Access Token XSMM!'); return; }
        if (!cookiesRaw) { alert('⚠️ Vui lòng nhập ít nhất 1 cookie!'); return; }

        btn.disabled = true;
        try {
            const res = await fetch(`/api/start/${tool}`, { method: 'POST' });
            const data = await res.json();
            if (!data.ok) { alert('Lỗi: ' + (data.error || '')); btn.disabled = false; return; }

            state[tool] = { sessionId: data.session_id, status: 'running' };
            setStatus(tool, 'running', data.session_id);
            socket.emit('join', { session_id: data.session_id });

            const term = getTerm(tool);
            if (term) {
                term.innerHTML = '';
                appendLine(term, `▶ Bắt đầu chạy [${tool}] — Session: ${data.session_id}`);
            }

            const seq = buildInputSequence(tool);
            for (let i = 0; i < seq.length; i++) {
                await new Promise(r => setTimeout(r, 400));
                await fetch(`/api/input/${data.session_id}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: seq[i] })
                });
                if (term) {
                    const short = seq[i].length > 70 ? seq[i].substring(0, 70) + '...' : seq[i];
                    appendLine(term, `> [auto] ${short}`, now());
                }
            }
            if (term) appendLine(term, `✅ Đã gửi xong cấu hình! Tool đang chạy...`, now());
            $(`.tab-btn[data-tool="${tool}"]`).click();
        } catch (e) { alert('Lỗi kết nối: ' + e.message); btn.disabled = false; }
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
        const t = getTerm(tool); if (t) t.innerHTML = '';
        const c = getOutputCount(tool); if (c) c.textContent = '0 dòng';
        const s = state[tool];
        if (s) fetch(`/api/clear/${s.sessionId}`, { method: 'POST' });
    });
});

// SAVE
$$('.btn-save').forEach(btn => {
    btn.addEventListener('click', async () => {
        const tool = btn.dataset.tool;
        const s = state[tool];
        if (!s) { alert('Chưa có session!'); return; }
        const res = await fetch(`/api/save/${s.sessionId}`, { method: 'POST' });
        const data = await res.json();
        if (data.ok) alert('Đã lưu: ' + data.filename);
        else alert('Lỗi: ' + (data.error || ''));
    });
});

// STDIN
function sendStdin(tool) {
    const input = $(`.stdin-input[data-tool="${tool}"]`);
    if (!input) return;
    const text = input.value;
    const s = state[tool];
    if (!s || !s.sessionId) return;
    fetch(`/api/input/${s.sessionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
    });
    const term = getTerm(tool);
    if (term) appendLine(term, `> ${text}`, now());
    input.value = '';
}
$$('.btn-send').forEach(btn => btn.addEventListener('click', () => sendStdin(btn.dataset.tool)));
$$('.stdin-input').forEach(inp => inp.addEventListener('keydown', e => {
    if (e.key === 'Enter') sendStdin(inp.dataset.tool);
}));

// SOCKET
socket.on('output', data => {
    const { session_id, line, ts } = data;
    const tool = Object.keys(state).find(k => state[k].sessionId === session_id);
    if (!tool) return;
    const term = getTerm(tool);
    if (!term) return;
    appendLine(term, line, ts);
    const oc = getOutputCount(tool);
    if (oc) oc.textContent = term.children.length + ' dòng';
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

// Auto save config
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

fetch('/api/sessions').then(r => r.json()).then(list => {
    const el = $('#sessions-count'); if (el) el.textContent = list.length + ' sessions';
});
