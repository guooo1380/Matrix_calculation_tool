/* ═══════════════════════════════════════════════════
   矩阵计算工具 — app.js
   ═══════════════════════════════════════════════════ */

// ── 运算配置 ────────────────────────────────────────

const OPS = {
    transpose: {
        name: '转置矩阵',
        dims: [['m', '行数'], ['n', '列数']],
        matrices: d => [{ label: '矩阵', rows: d.m, cols: d.n }],
    },
    inverse: {
        name: '逆矩阵',
        dims: [['n', '阶数']],
        matrices: d => [{ label: '矩阵', rows: d.n, cols: d.n }],
    },
    determinant: {
        name: '行列式',
        dims: [['n', '阶数']],
        matrices: d => [{ label: '矩阵', rows: d.n, cols: d.n }],
    },
    multiply: {
        name: '矩阵乘法',
        dims: [['m', 'A 行数'], ['n', 'A 列 / B 行'], ['p', 'B 列数']],
        matrices: d => [
            { label: '矩阵 A', rows: d.m, cols: d.n },
            { label: '矩阵 B', rows: d.n, cols: d.p },
        ],
    },
    standard: {
        name: '等价标准形',
        dims: [['m', '行数'], ['n', '列数']],
        matrices: d => [{ label: '矩阵', rows: d.m, cols: d.n }],
    },
};

// ── 矩阵运算 ────────────────────────────────────────

function transpose(m) {
    const rows = m.length, cols = m[0].length;
    const out = [];
    for (let j = 0; j < cols; j++) {
        out[j] = [];
        for (let i = 0; i < rows; i++) out[j][i] = m[i][j];
    }
    return out;
}

function inverse(matrix) {
    const n = matrix.length;
    const aug = matrix.map((row, i) => {
        const r = row.map(Number);
        for (let k = 0; k < n; k++) r.push(i === k ? 1 : 0);
        return r;
    });
    for (let col = 0; col < n; col++) {
        let maxRow = col;
        for (let row = col + 1; row < n; row++)
            if (Math.abs(aug[row][col]) > Math.abs(aug[maxRow][col])) maxRow = row;
        if (Math.abs(aug[maxRow][col]) < 1e-12) return null;
        [aug[col], aug[maxRow]] = [aug[maxRow], aug[col]];
        const pivot = aug[col][col];
        aug[col] = aug[col].map(v => v / pivot);
        for (let row = 0; row < n; row++) {
            if (row === col) continue;
            const f = aug[row][col];
            aug[row] = aug[row].map((v, k) => v - f * aug[col][k]);
        }
    }
    return aug.map(r => r.slice(n));
}

function determinant(matrix) {
    const n = matrix.length;
    if (n === 1) return matrix[0][0];
    if (n === 2) return matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0];
    let det = 0;
    for (let j = 0; j < n; j++) {
        const minor = [];
        for (let i = 1; i < n; i++)
            minor.push(matrix[i].filter((_, k) => k !== j));
        det += Math.pow(-1, j) * matrix[0][j] * determinant(minor);
    }
    return det;
}

function multiply(a, b) {
    const m = a.length, n = a[0].length, p = b[0].length;
    const out = [];
    for (let i = 0; i < m; i++) {
        out[i] = [];
        for (let j = 0; j < p; j++) {
            let s = 0;
            for (let k = 0; k < n; k++) s += a[i][k] * b[k][j];
            out[i][j] = s;
        }
    }
    return out;
}

function equivalentStandardForm(matrix) {
    const m = matrix.length, n = matrix[0].length;
    const a = matrix.map(r => r.map(Number));
    let rank = 0;
    for (let k = 0; k < Math.min(m, n); k++) {
        let bestR = k, bestC = k, bestVal = Math.abs(a[k][k]);
        for (let i = k; i < m; i++)
            for (let j = k; j < n; j++)
                if (Math.abs(a[i][j]) > bestVal) { bestR = i; bestC = j; bestVal = Math.abs(a[i][j]); }
        if (bestVal < 1e-12) break;
        [a[k], a[bestR]] = [a[bestR], a[k]];
        for (const row of a) { const t = row[k]; row[k] = row[bestC]; row[bestC] = t; }
        const pivot = a[k][k];
        a[k] = a[k].map(v => v / pivot);
        for (let i = 0; i < m; i++) {
            if (i !== k && Math.abs(a[i][k]) > 1e-12) {
                const f = a[i][k];
                a[i] = a[i].map((v, j) => v - f * a[k][j]);
            }
        }
        for (let j = 0; j < n; j++) {
            if (j !== k && Math.abs(a[k][j]) > 1e-12) {
                const f = a[k][j];
                for (let i = 0; i < m; i++) a[i][j] -= f * a[i][k];
            }
        }
        rank++;
    }
    const std = [];
    for (let i = 0; i < m; i++) {
        std[i] = [];
        for (let j = 0; j < n; j++) std[i][j] = (i === j && i < rank) ? 1 : 0;
    }
    return { std, rank };
}

function fmtVal(v) {
    if (typeof v !== 'number') return String(v);
    if (Math.abs(v - Math.round(v)) < 1e-9) return String(Math.round(v));
    return parseFloat(v.toFixed(4)).toString();
}

function fmtDet(v) {
    if (Math.abs(v - Math.round(v)) < 1e-9) return String(Math.round(v));
    return parseFloat(v.toPrecision(8)).toString();
}

// ── UI 状态 ─────────────────────────────────────────

let currentOp = 'transpose';
let grids = [];   // [{ label, rows, cols, inputs: [[<input>]] }]

// ── DOM 工具 ────────────────────────────────────────

const $ = id => document.getElementById(id);

function el(tag, attrs, ...children) {
    const e = document.createElement(tag);
    if (attrs) Object.entries(attrs).forEach(([k, v]) => {
        if (k === 'className') e.className = v;
        else if (k === 'textContent') e.textContent = v;
        else if (k === 'innerHTML') e.innerHTML = v;
        else e.setAttribute(k, v);
    });
    children.flat().forEach(c => { if (c != null) e.appendChild(c); });
    return e;
}

let toastTimer = null;
function showToast(msg, isError) {
    const t = $('toast');
    t.textContent = msg;
    t.className = 'toast show' + (isError ? ' error' : '');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.className = 'toast', 2500);
}

// ── 渲染矩阵 HTML ───────────────────────────────────

function matrixHTML(matrix) {
    let tbl = '<table class="matrix-tbl">';
    for (const row of matrix) {
        tbl += '<tr>';
        for (const v of row) tbl += '<td>' + fmtVal(v) + '</td>';
        tbl += '</tr>';
    }
    tbl += '</table>';
    return '<div class="matrix-wrap">' +
           '<div class="bracket-l"></div>' + tbl + '<div class="bracket-r"></div></div>';
}

function resultBlock(label, content) {
    return '<div class="result-block">' +
           '<div class="result-label">' + label + '</div>' + content + '</div>';
}

// ── 构建维度输入 ────────────────────────────────────

function buildDimInputs() {
    const wrap = $('dim-inputs');
    wrap.innerHTML = '';
    const op = OPS[currentOp];
    for (const [key, label] of op.dims) {
        const item = el('div', { className: 'dim-item' });
        item.appendChild(el('label', { className: 'dim-label', textContent: label }));
        const inp = el('input', {
            className: 'dim-input', type: 'text', inputmode: 'numeric',
            id: 'dim-' + key, value: '3',
        });
        item.appendChild(inp);
        wrap.appendChild(item);
    }
}

// ── 读取维度 ────────────────────────────────────────

function readDims() {
    const op = OPS[currentOp];
    const dims = {};
    for (const [key] of op.dims) {
        const v = parseInt($('dim-' + key).value, 10);
        if (!Number.isInteger(v) || v < 1 || v > 20) {
            showToast('维度须为 1 ~ 20 的正整数', true);
            return null;
        }
        dims[key] = v;
    }
    return dims;
}

// ── 构建矩阵输入格 ──────────────────────────────────

function buildGrids() {
    const dims = readDims();
    if (!dims) return;

    const op = OPS[currentOp];
    const specs = op.matrices(dims);
    const area = $('matrix-area');
    area.innerHTML = '';
    grids = [];

    for (const spec of specs) {
        const block = el('div', { className: 'matrix-block' });
        block.appendChild(el('div', {
            className: 'matrix-label',
            textContent: spec.label + '  (' + spec.rows + ' × ' + spec.cols + ')',
        }));
        const scroll = el('div', { className: 'matrix-scroll' });
        const grid = el('div', { className: 'matrix-grid' });
        grid.style.gridTemplateColumns = 'repeat(' + spec.cols + ', auto)';

        const inputs = [];
        for (let i = 0; i < spec.rows; i++) {
            inputs[i] = [];
            for (let j = 0; j < spec.cols; j++) {
                const inp = el('input', {
                    className: 'cell-input', type: 'text', inputmode: 'decimal',
                    placeholder: '0',
                });
                inp.dataset.r = i;
                inp.dataset.c = j;
                inp.addEventListener('keydown', e => onCellKey(e, inputs, spec.rows, spec.cols));
                grid.appendChild(inp);
                inputs[i][j] = inp;
            }
        }
        scroll.appendChild(grid);
        block.appendChild(scroll);
        area.appendChild(block);
        grids.push({ label: spec.label, rows: spec.rows, cols: spec.cols, inputs });
    }

    $('matrix-card').hidden = false;
    $('calc-area').hidden = false;
    $('result-card').hidden = true;

    grids[0].inputs[0][0].focus();
}

function onCellKey(e, inputs, rows, cols) {
    const r = +e.target.dataset.r, c = +e.target.dataset.c;
    let nr = r, nc = c;
    if (e.key === 'Enter' || (e.key === 'Tab' && !e.shiftKey)) {
        e.preventDefault();
        nc++;
        if (nc >= cols) { nc = 0; nr++; }
        if (nr >= rows) nr = rows - 1, nc = cols - 1;
    } else if (e.key === 'Tab' && e.shiftKey) {
        e.preventDefault();
        nc--;
        if (nc < 0) { nc = cols - 1; nr--; }
        if (nr < 0) nr = 0, nc = 0;
    } else if (e.key === 'ArrowUp' && r > 0) { e.preventDefault(); nr = r - 1; nc = c; }
    else if (e.key === 'ArrowDown' && r < rows - 1) { e.preventDefault(); nr = r + 1; nc = c; }
    else return;
    inputs[nr][nc].focus();
}

// ── 读取矩阵 ────────────────────────────────────────

function readGrid(grid) {
    const matrix = [];
    for (let i = 0; i < grid.rows; i++) {
        matrix[i] = [];
        for (let j = 0; j < grid.cols; j++) {
            const raw = grid.inputs[i][j].value.trim();
            if (raw === '') { matrix[i][j] = 0; continue; }
            const v = Number(raw);
            if (!Number.isFinite(v)) {
                showToast(grid.label + ' 第 ' + (i + 1) + ' 行第 ' + (j + 1) + ' 列不是有效数字', true);
                return null;
            }
            matrix[i][j] = v;
        }
    }
    return matrix;
}

// ── 计算 ────────────────────────────────────────────

function calculate() {
    if (!grids.length) { showToast('请先生成输入格', true); return; }

    const mats = grids.map(g => readGrid(g));
    if (mats.some(m => m === null)) return;

    let html = '';

    switch (currentOp) {
    case 'transpose': {
        const a = mats[0];
        html += resultBlock('原矩阵', matrixHTML(a));
        html += resultBlock('转置矩阵', matrixHTML(transpose(a)));
        break;
    }
    case 'inverse': {
        const a = mats[0];
        html += resultBlock('原矩阵', matrixHTML(a));
        const inv = inverse(a);
        if (inv === null) {
            html += resultBlock('逆矩阵', '<div class="result-note">该矩阵不可逆（行列式为 0）</div>');
        } else {
            html += resultBlock('逆矩阵', matrixHTML(inv));
        }
        break;
    }
    case 'determinant': {
        const a = mats[0];
        html += resultBlock('原矩阵', matrixHTML(a));
        html += resultBlock('行列式', '<div class="result-scalar">det = ' + fmtDet(determinant(a)) + '</div>');
        break;
    }
    case 'multiply': {
        const a = mats[0], b = mats[1];
        html += resultBlock('矩阵 A', matrixHTML(a));
        html += resultBlock('矩阵 B', matrixHTML(b));
        html += resultBlock('乘积 A × B', matrixHTML(multiply(a, b)));
        break;
    }
    case 'standard': {
        const a = mats[0];
        const { std, rank } = equivalentStandardForm(a);
        html += resultBlock('原矩阵', matrixHTML(a));
        html += resultBlock('秩', '<div class="result-scalar">r = ' + rank + '</div>');
        html += resultBlock('等价标准形', matrixHTML(std));
        break;
    }
    }

    const rc = $('result-content');
    rc.innerHTML = html;
    $('result-card').hidden = false;
    $('result-card').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ── 清空 ────────────────────────────────────────────

function clearAll() {
    for (const g of grids)
        for (const row of g.inputs)
            for (const inp of row) inp.value = '';
    $('result-card').hidden = true;
    if (grids.length) grids[0].inputs[0][0].focus();
}

// ── 切换运算 ────────────────────────────────────────

function selectOp(op) {
    currentOp = op;
    document.querySelectorAll('.op-pill').forEach(p =>
        p.classList.toggle('active', p.dataset.op === op));
    buildDimInputs();
    grids = [];
    $('matrix-card').hidden = true;
    $('calc-area').hidden = true;
    $('result-card').hidden = true;
}

// ── 建议反馈 ────────────────────────────────────────

function openFeedback() {
    $('feedback-mask').hidden = false;
    $('feedback-sheet').hidden = false;
    setTimeout(() => $('fb-msg').focus(), 60);
}

function closeFeedback() {
    $('feedback-mask').hidden = true;
    $('feedback-sheet').hidden = true;
}

async function submitFeedback(e) {
    e.preventDefault();
    const form = $('feedback-form');
    const message = $('fb-msg').value.trim();
    if (!message) { showToast('请先填写建议内容', true); return; }
    const contact = $('fb-contact').value.trim();
    const btn = $('feedback-submit');
    btn.disabled = true; btn.textContent = '提交中…';
    try {
        let ok;
        if (window.pywebview && window.pywebview.api) {
            const res = await window.pywebview.api.submit_feedback(message, contact);
            ok = !!(res && res.ok);
        } else {
            const res = await fetch('/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: new URLSearchParams(new FormData(form)).toString(),
            });
            ok = res.ok;
        }
        if (ok) { form.reset(); closeFeedback(); showToast('已收到你的建议，谢谢！'); }
        else showToast('提交失败，请稍后再试', true);
    } catch (err) {
        showToast('网络错误，提交失败', true);
    } finally {
        btn.disabled = false; btn.textContent = '提交';
    }
}

// ── 初始化 ──────────────────────────────────────────

function init() {
    document.querySelectorAll('.op-pill').forEach(p =>
        p.addEventListener('click', () => selectOp(p.dataset.op)));

    $('gen-btn').addEventListener('click', buildGrids);
    $('calc-btn').addEventListener('click', calculate);
    $('clear-btn').addEventListener('click', clearAll);

    $('feedback-open').addEventListener('click', openFeedback);
    $('feedback-cancel').addEventListener('click', closeFeedback);
    $('feedback-mask').addEventListener('click', closeFeedback);
    $('feedback-form').addEventListener('submit', submitFeedback);

    buildDimInputs();
}

document.addEventListener('DOMContentLoaded', init);
