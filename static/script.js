const socket = io();
const state = {};

function $(sel, root = document) { return root.querySelector(sel); }
function $$(sel, root = document) { return [...root.querySelectorAll(sel)]; }
function now() { return new Date().toLocaleTimeString('vi-VN', { hour12: false }); }
function escapeHtml(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }

// ================== HIỆU ỨNG TRONG PANEL ==================
function createEffectForPanel(canvas) {
    if (!canvas) return null;
    const ctx = canvas.getContext('2d');
    let W = 0, H = 0;
    let ACTIVE = false;

    function resize() {
        const rect = canvas.getBoundingClientRect();
        W = canvas.width = Math.max(1, rect.width);
        H = canvas.height = Math.max(1, rect.height);
    }
    const ro = new ResizeObserver(resize);
    ro.observe(canvas);
    setTimeout(resize, 100);

    let ACCENT = '#ec4899';
    function getAccent() {
        const panel = canvas.closest('.tool-panel');
        const c = panel ? getComputedStyle(panel).getPropertyValue('--panel-color').trim() : '#ec4899';
        return c || '#ec4899';
    }

    const flowers = [];
    const FLOWER_COLORS = ['#ff6b9d', '#ffd93d', '#a78bfa', '#ff8fab', '#f9a8d4'];
    function newFlower() {
        return { x: Math.random() * W, y: -20, size: 6 + Math.random() * 8,
            speedY: 0.4 + Math.random() * 0.8, speedX: (Math.random() - 0.5) * 0.6,
            rot: Math.random() * Math.PI * 2, rotSpeed: (Math.random() - 0.5) * 0.05,
            color: FLOWER_COLORS[Math.floor(Math.random() * FLOWER_COLORS.length)],
            type: Math.random() < 0.5 ? 'flower' : 'petal' };
    }
    for (let i = 0; i < 8; i++) { const f = newFlower(); f.y = Math.random() * H; flowers.push(f); }

    const hearts = [];
    function newHeart() {
        return { x: Math.random() * W, y: -20, size: 6 + Math.random() * 7,
            speedY: 0.6 + Math.random() * 1, speedX: (Math.random() - 0.5) * 0.5,
            color: ['#ef4444', '#ec4899', '#f43f5e', '#fb7185'][Math.floor(Math.random() * 4)],
            alpha: 0.6 + Math.random() * 0.4, pulse: Math.random() * Math.PI * 2 };
    }
    for (let i = 0; i < 6; i++) { const h = newHeart(); h.y = Math.random() * H; hearts.push(h); }

    const bolts = [];
    function newBolt() {
        const sx = Math.random() * W; const segs = [];
        let x = sx, y = 0; const endY = H * (0.4 + Math.random() * 0.5);
        while (y < endY) { segs.push({ x, y }); x += (Math.random() - 0.5) * 60; y += 10 + Math.random() * 20; }
        return { segments: segs, life: 1, fadeSpeed: 0.03 + Math.random() * 0.02, width: 1 + Math.random() * 1.5 };
    }
    function triggerLightning() { for (let i = 0; i < 3; i++) setTimeout(() => bolts.push(newBolt()), i * 120); }

    function drawLightning(bolt, color) {
        if (bolt.segments.length < 2) return;
        ctx.save();
        ctx.globalAlpha = bolt.life;
        ctx.strokeStyle = color;
        ctx.lineWidth = bolt.width;
        ctx.shadowBlur = 15;
        ctx.shadowColor = color;
        ctx.lineCap = 'round'; ctx.lineJoin = 'round';
        ctx.beginPath();
        ctx.moveTo(bolt.segments[0].x, bolt.segments[0].y);
        for (let i = 1; i < bolt.segments.length; i++) ctx.lineTo(bolt.segments[i].x, bolt.segments[i].y);
        ctx.stroke();
        ctx.strokeStyle = 'rgba(255,255,255,' + bolt.life + ')';
        ctx.lineWidth = bolt.width * 0.4; ctx.shadowBlur = 0;
        ctx.beginPath();
        ctx.moveTo(bolt.segments[0].x, bolt.segments[0].y);
        for (let i = 1; i < bolt.segments.length; i++) ctx.lineTo(bolt.segments[i].x, bolt.segments[i].y);
        ctx.stroke();
        ctx.restore();
    }

    function drawFlower(f) {
        ctx.save(); ctx.translate(f.x, f.y); ctx.rotate(f.rot);
        ctx.globalAlpha = 0.85; ctx.fillStyle = f.color;
        ctx.shadowBlur = 8; ctx.shadowColor = f.color;
        if (f.type === 'petal') {
            ctx.beginPath(); ctx.ellipse(0, 0, f.size, f.size * 0.5, 0, 0, Math.PI * 2); ctx.fill();
        } else {
            for (let i = 0; i < 5; i++) {
                ctx.save(); ctx.rotate((Math.PI * 2 / 5) * i);
                ctx.beginPath(); ctx.ellipse(0, -f.size * 0.5, f.size * 0.4, f.size * 0.7, 0, 0, Math.PI * 2); ctx.fill();
                ctx.restore();
            }
            ctx.fillStyle = '#ffd93d';
            ctx.beginPath(); ctx.arc(0, 0, f.size * 0.25, 0, Math.PI * 2); ctx.fill();
        }
        ctx.restore();
    }

    function drawHeart(h) {
        ctx.save(); ctx.translate(h.x, h.y);
        const s = h.size + Math.sin(h.pulse) * 1.2;
        ctx.globalAlpha = h.alpha; ctx.fillStyle = h.color;
        ctx.shadowBlur = 10; ctx.shadowColor = h.color;
        ctx.beginPath();
        ctx.moveTo(0, s * 0.3);
        ctx.bezierCurveTo(0, 0, -s * 0.5, 0, -s * 0.5, s * 0.3);
        ctx.bezierCurveTo(-s * 0.5, s * 0.7, 0, s * 1.1, 0, s * 1.3);
        ctx.bezierCurveTo(0, s * 1.1, s * 0.5, s * 0.7, s * 0.5, s * 0.3);
        ctx.bezierCurveTo(s * 0.5, 0, 0, 0, 0, s * 0.3);
        ctx.fill(); ctx.restore();
    }

    function loop() {
        ctx.clearRect(0, 0, W, H);
        if (ACTIVE && W > 0 && H > 0) {
            ACCENT = getAccent();
            for (const f of flowers) {
                f.y += f.speedY; f.x += f.speedX + Math.sin(f.y * 0.02) * 0.3; f.rot += f.rotSpeed;
                if (f.y > H + 30) Object.assign(f, newFlower());
                drawFlower(f);
            }
            for (const h of hearts) {
                h.y += h.speedY; h.x += h.speedX + Math.sin(h.y * 0.02) * 0.3; h.pulse += 0.08;
                if (h.y > H + 30) Object.assign(h, newHeart());
                drawHeart(h);
            }
            for (let i = bolts.length - 1; i >= 0; i--) {
                bolts[i].life -= bolts[i].fadeSpeed;
                if (bolts[i].life <= 0) { bolts.splice(i, 1); continue; }
                drawLightning(bolts[i], ACCENT);
            }
            if (Math.random() < 0.02 && bolts.length < 2) bolts.push(newBolt());
        }
        requestAnimationFrame(loop);
    }
    loop();

    return {
        start: () => { ACTIVE = true; canvas.classList.add('active'); resize(); triggerLightning(); },
        stop: () => { ACTIVE = false; canvas.classList.remove('active'); bolts.length = 0; ctx.clearRect(0, 0, W, H); }
    };
}

const fxInstances = {};
$$('.tool-panel').forEach(panel => {
    const tool = panel.dataset.tool;
    const cForm = panel.querySelector('.fx-canvas-form');
    const cTerm = panel.querySelector('.fx-canvas-term');
    fxInstances[tool] = { form: createEffectForPanel(cForm), term: createEffectForPanel(cTerm) };
});

function fxStart(tool) { const fx = fxInstances[tool]; if (fx) { if (fx.form) fx.form.start(); if (fx.term) fx.term.start(); } }
function fxStop(tool) { const fx = fxInstances[tool]; if (fx) { if (fx.form) fx.form.stop(); if (fx.term) fx.term.stop(); } }

(function initColorPicker() {
    const picker = document.getElementById('theme-color');
    if (!picker) return;
    const saved = localStorage.getItem('theme_accent');
    if (saved) { document.documentElement.style.setProperty('--accent', saved); picker.value = saved; }
    picker.addEventListener('input', (e) => {
        document.documentElement.style.setProperty('--accent', e.target.value);
        localStorage.setItem('theme_accent', e.target.value);
    });
})();

function classifyLine(line) {
    if (/\b(traceback|exception|error|lỗi|die|fail|thất bại)\b/i.test(line)) return 'err';
    if (/\b(warn|cảnh báo|retry|timeout|chậm)\b/i.test(line)) return 'warn';
    if (/\b(success|thành công|✔|✅|ok|done|hoàn thành)\b/i.test(line)) return 'ok';
    if (/\b(info|đang|bắt đầu|nick|job|task)\b/i.test(line)) return 'info';
    return '';
}

function appendLine(termEl, line, ts = null) {
    if (!termEl) return;
    const div = document.createElement('div');
    div.className = 'term-line ' + classifyLine(line);
    div.innerHTML = `<span class="ts">[${ts || now()}]</span>${escapeHtml(line)}`;
    termEl.appendChild(div);
    termEl.scrollTop = termEl.scrollHeight;
}

setInterval(() => { const el = $('#clock'); if (el) el.textContent = now(); }, 1000);

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
    const sb = getBtn(tool, 'start'); if (sb) sb.disabled = isRunning;
    const stb = getBtn(tool, 'stop'); if (stb) stb.disabled = !isRunning;
    const cb = getBtn(tool, 'clear'); if (cb) cb.disabled = false;
    const svb = getBtn(tool, 'save'); if (svb) svb.disabled = false;
    const stdin = $(`.stdin-input[data-tool="${tool}"]`);
    const sendBtn = $(`.btn-send[data-tool="${tool}"]`);
    if (stdin) stdin.disabled = !isRunning;
    if (sendBtn) sendBtn.disabled = !isRunning;
    const form = $(`#form-${tool.replace('.', '_')}`);
    if (form) form.querySelectorAll('input, textarea, select').forEach(el => el.disabled = isRunning);
}

// ================== BUILD INPUT SEQUENCE (3 tool IG) ==================
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

    const lines = cookiesRaw.split('\n').map(s => s.trim()).filter(Boolean);
    const cookies = [], proxies = [];
    for (const line of lines) {
        const parts = line.split('|');
        cookies.push(parts[0].trim());
        proxies.push(parts[1] ? parts[1].trim() : '');
    }

    const seq = [];
    if (tool === 'xsmmv3.2') {
        seq.push(threads); seq.push(token); seq.push(String(cookies.length));
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
        seq.push(jobLike ? 'on' : 'off'); if (jobLike) seq.push(delayTym);
        seq.push(jobFollow ? 'on' : 'off'); if (jobFollow) seq.push(delayFollow);
        seq.push(jobComment ? 'on' : 'off'); if (jobComment) seq.push(delayComment);
    } else if (tool === '11223') {
        seq.push(token); seq.push(cookies[0] || ''); seq.push(mode);
        seq.push(delayTym); seq.push(String(parseInt(delayTym) + 5));
        seq.push(delayCoin); seq.push(String(parseInt(delayCoin) + 2));
    }
    return seq.filter(s => s !== undefined && s !== null);
}

// ================== START 3 TOOL IG ==================
$$('.btn-start[data-tool]').forEach(btn => {
    if (btn.id && (btn.id === 'btn_fb_reg' || btn.id === 'btn_fb_chuyen')) return;
    btn.addEventListener('click', async () => {
        const tool = btn.dataset.tool;
        if (!tool || !['xsmmv3.2', 'xsmmigv5.2', '11223'].includes(tool)) return;

        const token = (getCfg(tool, 'cfg-token')?.value || '').trim();
        const cookiesRaw = (getCfg(tool, 'cfg-cookies')?.value || '').trim();
        if (!token) { alert('⚠️ Nhập Access Token XSMM!'); return; }
        if (!cookiesRaw) { alert('⚠️ Nhập ít nhất 1 cookie!'); return; }

        btn.disabled = true;
        try {
            const res = await fetch(`/api/start/${tool}`, { method: 'POST' });
            const data = await res.json();
            if (!data.ok) { alert('Lỗi: ' + (data.error || '')); btn.disabled = false; return; }

            state[tool] = { sessionId: data.session_id, status: 'running' };
            setStatus(tool, 'running', data.session_id);
            socket.emit('join', { session_id: data.session_id });
            fxStart(tool);

            const term = getTerm(tool);
            if (term) { term.innerHTML = ''; appendLine(term, `▶ Bắt đầu [${tool}] — Session: ${data.session_id}`); }

            await new Promise(r => setTimeout(r, 3000));
            const seq = buildInputSequence(tool);
            for (let i = 0; i < seq.length; i++) {
                await new Promise(r => setTimeout(r, 300));
                await fetch(`/api/input/${data.session_id}`, {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: seq[i] })
                });
                if (term) {
                    const short = seq[i].length > 70 ? seq[i].substring(0, 70) + '...' : seq[i];
                    appendLine(term, `> [auto] ${short}`, now());
                }
            }
            $(`.tab-btn[data-tool="${tool}"]`).click();
        } catch (e) { alert('Lỗi: ' + e.message); btn.disabled = false; }
    });
});

// ================== STOP ==================
$$('.btn-stop').forEach(btn => {
    btn.addEventListener('click', async () => {
        const tool = btn.dataset.tool;
        const s = state[tool]; if (!s) return;
        if (!confirm('Dừng tool?')) return;
        await fetch(`/api/stop/${s.sessionId}`, { method: 'POST' });
        setStatus(tool, 'stopped');
        fxStop(tool);
    });
});

$$('.btn-clear').forEach(btn => {
    btn.addEventListener('click', () => {
        const tool = btn.dataset.tool;
        const t = getTerm(tool); if (t) t.innerHTML = '';
        const c = getOutputCount(tool); if (c) c.textContent = '0 dòng';
        const s = state[tool]; if (s) fetch(`/api/clear/${s.sessionId}`, { method: 'POST' });
    });
});

$$('.btn-save').forEach(btn => {
    btn.addEventListener('click', async () => {
        const tool = btn.dataset.tool; const s = state[tool];
        if (!s) { alert('Chưa có session!'); return; }
        const res = await fetch(`/api/save/${s.sessionId}`, { method: 'POST' });
        const data = await res.json();
        if (data.ok) alert('Đã lưu: ' + data.filename); else alert('Lỗi: ' + (data.error || ''));
    });
});

function sendStdin(tool) {
    const input = $(`.stdin-input[data-tool="${tool}"]`); if (!input) return;
    const text = input.value; const s = state[tool]; if (!s || !s.sessionId) return;
    fetch(`/api/input/${s.sessionId}`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
    });
    const term = getTerm(tool); if (term) appendLine(term, `> ${text}`, now());
    input.value = '';
}
$$('.btn-send').forEach(btn => btn.addEventListener('click', () => sendStdin(btn.dataset.tool)));
$$('.stdin-input').forEach(inp => inp.addEventListener('keydown', e => {
    if (e.key === 'Enter') sendStdin(inp.dataset.tool);
}));

// ================== FB TOOL: REG PAGE ==================
const btnFbReg = document.getElementById('btn_fb_reg');
if (btnFbReg) {
    btnFbReg.addEventListener('click', async () => {
        const cookie = document.getElementById('fb_reg_cookie').value.trim();
        const name = document.getElementById('fb_reg_name').value.trim();
        const cat = document.getElementById('fb_reg_category')?.value.trim() || document.getElementById('fb_reg_cat').value.trim();
        const term = document.getElementById('term-fb_regpage');

        if (!cookie || !name) { alert('⚠️ Nhập Cookie và Tên Page!'); return; }

        btnFbReg.disabled = true;
        fxStart('fb_regpage');
        if (term) { term.innerHTML = ''; appendLine(term, `▶ Bắt đầu tạo Page: ${name}`); }

        try {
            const res = await fetch('/api/fb/regpage', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ cookie, page_name: name, category_id: cat })
            });
            const data = await res.json();
            if (data.ok) {
                appendLine(term, `✅ ${data.message}`, now());
                alert('✅ ' + data.message);
            } else {
                appendLine(term, `❌ ${data.message}`, now());
                alert('❌ ' + data.message);
            }
        } catch (e) {
            if (term) appendLine(term, `❌ Lỗi: ${e.message}`, now());
            alert('Lỗi: ' + e.message);
        }
        btnFbReg.disabled = false;
        setTimeout(() => fxStop('fb_regpage'), 2000);
    });
}

// ================== FB TOOL: CHUYỂN PAGE ==================
const btnFbChuyen = document.getElementById('btn_fb_chuyen');
if (btnFbChuyen) {
    btnFbChuyen.addEventListener('click', async () => {
        const cookie = document.getElementById('fb_chuyen_cookie').value.trim();
        const password = document.getElementById('fb_chuyen_pass').value.trim();
        const pageId = document.getElementById('fb_chuyen_pageid').value.trim();
        const uid = document.getElementById('fb_chuyen_uid').value.trim();
        const term = document.getElementById('term-fb_chuyenpage');

        if (!cookie || !pageId || !uid) { alert('⚠️ Nhập Cookie / Page ID / UID nhận!'); return; }

        btnFbChuyen.disabled = true;
        fxStart('fb_chuyenpage');
        if (term) { term.innerHTML = ''; appendLine(term, `▶ Chuyển Page ${pageId} → UID ${uid}`); }

        try {
            const res = await fetch('/api/fb/chuyenpage', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ cookie, password, page_id: pageId, uid_nhan: uid })
            });
            const data = await res.json();
            if (data.ok) {
                appendLine(term, `✅ ${data.message}`, now());
                alert('✅ ' + data.message);
            } else {
                appendLine(term, `❌ ${data.message}`, now());
                alert('❌ ' + data.message);
            }
        } catch (e) {
            if (term) appendLine(term, `❌ Lỗi: ${e.message}`, now());
            alert('Lỗi: ' + e.message);
        }
        btnFbChuyen.disabled = false;
        setTimeout(() => fxStop('fb_chuyenpage'), 2000);
    });
}

// ================== SOCKET ==================
socket.on('output', data => {
    const { session_id, line, ts } = data;
    const tool = Object.keys(state).find(k => state[k].sessionId === session_id);
    if (!tool) return;
    const term = getTerm(tool); if (!term) return;
    appendLine(term, line, ts);
    const oc = getOutputCount(tool); if (oc) oc.textContent = term.children.length + ' dòng';
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
        fxStop(tool);
    }
});

socket.on('cleared', data => {
    const tool = Object.keys(state).find(k => state[k].sessionId === data.session_id);
    if (tool) { const t = getTerm(tool); if (t) t.innerHTML = ''; }
});

// ================== AUTO SAVE CONFIG ==================
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
