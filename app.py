<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>NHS Vision – Planejamento</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.19.0/dist/tabler-icons.min.css">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --bg: #ffffff; --bg-2: #f6f6f4; --bg-3: #efefec;
      --text: #1a1a18; --text-2: #6b6b67; --text-3: #a0a09c;
      --border: rgba(0,0,0,0.12); --border-2: rgba(0,0,0,0.24);
      --info-bg: #e6f1fb; --info-text: #185fa5;
      --success-bg: #eaf3de; --success-text: #3b6d11;
      --warn-bg: #faeeda; --warn-text: #854f0b;
      --danger-bg: #fcebeb; --danger-text: #a32d2d;
    }
    @media (prefers-color-scheme: dark) {
      :root {
        --bg: #1e1e1c; --bg-2: #2a2a28; --bg-3: #333331;
        --text: #f0f0ec; --text-2: #a0a09c; --text-3: #6b6b67;
        --border: rgba(255,255,255,0.10); --border-2: rgba(255,255,255,0.20);
        --info-bg: #042c53; --info-text: #85b7eb;
        --success-bg: #173404; --success-text: #97c459;
        --warn-bg: #412402; --warn-text: #fac775;
        --danger-bg: #501313; --danger-text: #f09595;
      }
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, sans-serif;
      background: var(--bg-3); color: var(--text);
      min-height: 100vh; padding: 1.5rem 1rem 4rem;
    }
    .container { max-width: 920px; margin: 0 auto; }
    .header {
      display: flex; align-items: center; gap: 12px;
      margin-bottom: 1.5rem; padding-bottom: 1.25rem;
      border-bottom: 0.5px solid var(--border);
    }
    .header i { font-size: 28px; color: var(--text-2); }
    .header h1 { font-size: 20px; font-weight: 600; }
    .header span { font-size: 13px; color: var(--text-2); }
    .api-banner {
      display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
      padding: .75rem 1rem; margin-bottom: 1.25rem;
      background: var(--warn-bg); border-radius: 10px;
      font-size: 13px; color: var(--warn-text);
      border: 0.5px solid rgba(133,79,11,0.3);
    }
    .api-banner i { font-size: 16px; flex-shrink: 0; }
    .api-banner input {
      flex: 1; min-width: 220px; padding: 5px 10px;
      font-size: 13px; font-family: monospace;
      border: 0.5px solid var(--border-2); border-radius: 8px;
      background: var(--bg); color: var(--text);
    }
    .api-banner small { font-size: 11px; opacity: .75; width: 100%; }
    .layout { display: grid; grid-template-columns: 240px 1fr; gap: 1rem; align-items: start; }
    @media (max-width: 660px) { .layout { grid-template-columns: 1fr; } }
    .card {
      background: var(--bg); border: 0.5px solid var(--border);
      border-radius: 12px; padding: 1rem 1.25rem; margin-bottom: .875rem;
    }
    .section-label {
      font-size: 11px; font-weight: 600; text-transform: uppercase;
      letter-spacing: .05em; color: var(--text-3); margin-bottom: .75rem;
    }
    .field { margin-bottom: .75rem; }
    .field label { display: block; font-size: 13px; color: var(--text-2); margin-bottom: 4px; }
    .field select, .field input[type=text], .field input[type=number] {
      width: 100%; padding: 7px 10px; font-size: 13px; font-family: inherit;
      border: 0.5px solid var(--border-2); border-radius: 8px;
      background: var(--bg-2); color: var(--text); transition: border-color .15s;
    }
    .field select:focus, .field input:focus { outline: none; border-color: var(--text-2); }
    textarea {
      width: 100%; padding: 7px 10px; font-size: 12px;
      font-family: 'Courier New', monospace; resize: vertical;
      border: 0.5px solid var(--border-2); border-radius: 8px;
      background: var(--bg-2); color: var(--text); line-height: 1.5;
    }
    textarea:focus { outline: none; border-color: var(--text-2); }
    .check-row { display: flex; align-items: center; gap: 8px; font-size: 13px; color: var(--text-2); margin-top: .25rem; }
    .check-row input[type=checkbox] { width: 15px; height: 15px; cursor: pointer; accent-color: var(--text); }
    .upload-zone {
      border: 1.5px dashed var(--border-2); border-radius: 10px;
      padding: 1.5rem 1rem; text-align: center; cursor: pointer;
      background: var(--bg-2); transition: background .15s;
    }
    .upload-zone:hover, .upload-zone.drag { background: var(--bg-3); }
    .upload-zone i { font-size: 34px; color: var(--text-3); display: block; margin-bottom: .5rem; }
    .upload-zone p { font-size: 13px; color: var(--text-2); }
    .upload-zone small { font-size: 11px; color: var(--text-3); margin-top: 3px; display: block; }
    #preview-img {
      width: 100%; max-height: 230px; object-fit: contain; display: none;
      border-radius: 8px; border: 0.5px solid var(--border); margin-top: .75rem;
    }
    .btn {
      display: inline-flex; align-items: center; gap: 6px;
      padding: 7px 14px; font-size: 13px; font-weight: 500; font-family: inherit;
      border: 0.5px solid var(--border-2); border-radius: 8px; cursor: pointer;
      background: var(--bg); color: var(--text); transition: background .12s, transform .1s;
    }
    .btn:hover { background: var(--bg-2); }
    .btn:active { transform: scale(.97); }
    .btn-primary { background: var(--text); color: var(--bg); border-color: transparent; }
    .btn-primary:hover { opacity: .82; background: var(--text); }
    .btn-primary:disabled { opacity: .38; cursor: not-allowed; transform: none; }
    .btn-danger { background: var(--danger-bg); color: var(--danger-text); border-color: transparent; }
    .row-btns { display: flex; gap: 8px; margin-top: .75rem; flex-wrap: wrap; align-items: center; }
    .table-wrap { overflow-x: auto; margin-top: .5rem; }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th {
      font-size: 11px; font-weight: 600; text-transform: uppercase;
      letter-spacing: .04em; color: var(--text-3);
      text-align: left; padding: 6px 10px; border-bottom: 0.5px solid var(--border);
    }
    td { padding: 8px 10px; border-bottom: 0.5px solid var(--border); }
    tr:last-child td { border-bottom: none; }
    tr.lunch td { background: var(--info-bg); color: var(--info-text); font-style: italic; }
    input.qty-inp {
      width: 68px; text-align: center; padding: 5px 6px; font-size: 13px;
      border: 0.5px solid var(--border-2); border-radius: 8px;
      background: var(--bg-2); color: var(--text);
    }
    .add-row-area { display: flex; gap: 8px; margin-top: .75rem; align-items: center; flex-wrap: wrap; }
    .add-row-area input {
      padding: 7px 10px; font-size: 13px; font-family: inherit;
      border: 0.5px solid var(--border-2); border-radius: 8px;
      background: var(--bg-2); color: var(--text);
    }
    .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; margin-bottom: 1rem; }
    .metric-card { background: var(--bg-2); border-radius: 8px; padding: .875rem 1rem; }
    .metric-card .mlabel { font-size: 12px; color: var(--text-2); margin-bottom: 4px; }
    .metric-card .mval { font-size: 24px; font-weight: 600; }
    .tag {
      display: inline-block; font-size: 11px; padding: 2px 8px;
      border-radius: 999px; background: var(--bg-2); color: var(--text-2);
      border: 0.5px solid var(--border); margin: 1px;
    }
    .status {
      display: inline-flex; align-items: center; gap: 5px;
      font-size: 12px; padding: 3px 10px; border-radius: 999px;
    }
    .status.ok { background: var(--success-bg); color: var(--success-text); }
    .status.warn { background: var(--warn-bg); color: var(--warn-text); }
    .status.err { background: var(--danger-bg); color: var(--danger-text); }
    .spinner {
      display: inline-block; width: 14px; height: 14px;
      border: 2px solid var(--border-2); border-top-color: var(--text);
      border-radius: 50%; animation: spin .7s linear infinite; vertical-align: middle;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    #resultado { margin-top: 1rem; display: none; }
    code {
      font-family: 'Courier New', monospace; font-size: 11px;
      background: var(--bg-2); padding: 1px 5px; border-radius: 4px;
    }
  </style>
</head>
<body>
<div class="container">

  <div class="header">
    <i class="ti ti-building-factory-2"></i>
    <div>
      <h1>NHS Vision – Planejamento de Produção</h1>
      <span>Leitura de imagem por IA + cronograma automático de célula</span>
    </div>
  </div>

  <div class="api-banner">
    <i class="ti ti-key"></i>
    <span>Chave da API Anthropic (necessária para leitura de imagem):</span>
    <input type="password" id="api-key" placeholder="sk-ant-api03-..." oninput="salvarChave(this.value)">
    <small>A chave fica salva apenas no seu navegador (sessionStorage) e é enviada somente para api.anthropic.com.</small>
  </div>

  <div class="layout">

    <!-- COLUNA ESQUERDA -->
    <div>
      <div class="card">
        <div class="section-label">Configuração da célula</div>
        <div class="field">
          <label>Célula / UPS</label>
          <select id="sel-ups" onchange="onUpsChange()">
            <option>UPS - 1</option>
            <option>UPS - 2</option>
            <option>UPS - 3</option>
            <option>UPS - 4</option>
            <option>UPS - 6</option>
            <option>UPS - 7</option>
            <option>UPS - 8</option>
            <option>ACS - 01</option>
          </select>
        </div>
        <div class="field">
          <label>Horário de início</label>
          <input type="text" id="h-ini" value="07:45" placeholder="HH:MM">
        </div>
        <div class="field">
          <label>Pessoas na célula</label>
          <input type="number" id="n-dia" value="5" min="1" max="25">
        </div>
        <div class="check-row">
          <input type="checkbox" id="gin" checked>
          <label for="gin">Ginástica laboral (09:30–09:40)</label>
        </div>
      </div>

      <div class="card">
        <div class="section-label">Base de cadência</div>
        <p style="font-size:12px;color:var(--text-2);margin-bottom:.6rem;line-height:1.6">
          Cole os dados da planilha BASE.<br>
          Formato: <code>MODELO,unid/hora</code> por linha.<br>
          Exemplo: <code>85.ABC.001,150</code>
        </p>
        <textarea id="base-raw" rows="5" placeholder="85.ABC.001,150&#10;85.XYZ.002,200&#10;190.DEF.003,120"></textarea>
        <div class="row-btns">
          <button class="btn" onclick="parsarBase()">
            <i class="ti ti-table-import"></i> Importar base
          </button>
          <span id="base-status" style="font-size:12px"></span>
        </div>
        <div id="base-tags" style="margin-top:.5rem;line-height:2"></div>
      </div>
    </div>

    <!-- COLUNA DIREITA -->
    <div>
      <div class="card">
        <div class="section-label">Imagem da programação</div>
        <div class="upload-zone" id="drop-zone" onclick="document.getElementById('file-in').click()">
          <i class="ti ti-photo-up"></i>
          <p>Clique ou arraste o print aqui</p>
          <small>PNG · JPG · JPEG</small>
        </div>
        <input type="file" id="file-in" accept="image/*" style="display:none" onchange="onFile(this)">
        <img id="preview-img">
        <div class="row-btns">
          <button class="btn btn-primary" id="btn-ler" onclick="lerImagem()" disabled>
            <i class="ti ti-brain"></i> Ler com IA
          </button>
          <span id="ler-status"></span>
        </div>
      </div>

      <div class="card">
        <div class="section-label">Ordens de produção</div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Modelo / Equipamento</th>
                <th>Qtd (un)</th>
                <th>Cadência</th>
                <th></th>
              </tr>
            </thead>
            <tbody id="ordens-body"></tbody>
          </table>
        </div>
        <div class="add-row-area">
          <input type="text" id="new-eq" placeholder="Código do modelo" style="flex:1;min-width:120px">
          <input type="number" id="new-qty" placeholder="Qtd" style="width:80px" min="1">
          <button class="btn" onclick="addRow()">
            <i class="ti ti-plus"></i> Adicionar
          </button>
        </div>
        <div class="row-btns">
          <button class="btn btn-primary" onclick="calcular()">
            <i class="ti ti-calendar-clock"></i> Gerar cronograma
          </button>
          <button class="btn btn-danger" onclick="limparOrdens()">
            <i class="ti ti-trash"></i> Limpar
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- RESULTADO -->
  <div id="resultado">
    <div class="card">
      <div class="section-label">Cronograma gerado</div>
      <div class="metrics" id="metrics-area"></div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Horário</th>
              <th>Modelos produzidos</th>
              <th style="text-align:center">Peças no período</th>
              <th style="text-align:center">Acumulado</th>
            </tr>
          </thead>
          <tbody id="cron-body"></tbody>
        </table>
      </div>
      <p style="margin-top:.75rem;font-size:12px;color:var(--text-3)">
        * Pausas descontadas: café manhã (09:20–09:30), café tarde (15:20–15:30), almoço (11:30–12:30) e ginástica laboral quando ativada.
      </p>
    </div>
  </div>

</div>
<script>
// ==============================================
//  CONSTANTES
// ==============================================
const MAPA_N = {
  "UPS - 1": 5, "UPS - 2": 3, "UPS - 3": 3, "UPS - 4": 3,
  "UPS - 6": 4, "UPS - 7": 4, "UPS - 8": 4, "ACS - 01": 3
};

// ==============================================
//  ESTADO
// ==============================================
let baseMap = {};
let ordens  = [];
let imgB64  = null;

// ==============================================
//  API KEY
// ==============================================
function salvarChave(v) { if (v) sessionStorage.setItem('nhsApiKey', v); }
function getChave() {
  const s = sessionStorage.getItem('nhsApiKey');
  if (s) { document.getElementById('api-key').value = s; return s; }
  return document.getElementById('api-key').value.trim();
}
window.addEventListener('DOMContentLoaded', () => {
  const k = sessionStorage.getItem('nhsApiKey');
  if (k) document.getElementById('api-key').value = k;
  onUpsChange();
});

// ==============================================
//  UPS
// ==============================================
function onUpsChange() {
  const ups = document.getElementById('sel-ups').value;
  document.getElementById('n-dia').value = MAPA_N[ups] || 5;
  renderOrdens();
}

// ==============================================
//  BASE DE CADÊNCIA
// ==============================================
function parsarBase() {
  const raw = document.getElementById('base-raw').value.trim();
  if (!raw) { document.getElementById('base-status').textContent = 'Nenhum dado colado.'; return; }
  baseMap = {};
  raw.split('\n').forEach(linha => {
    const p = linha.trim().split(/[,;\t]+/);
    if (p.length >= 2) {
      const id = p[0].trim().toUpperCase();
      const uh = parseFloat(p[1].replace(',', '.'));
      if (id && !isNaN(uh)) baseMap[id] = uh;
    }
  });
  const n = Object.keys(baseMap).length;
  const el = document.getElementById('base-status');
  if (n > 0) {
    el.innerHTML = `<span class="status ok"><i class="ti ti-check"></i> ${n} modelos importados</span>`;
    document.getElementById('base-tags').innerHTML =
      Object.keys(baseMap).slice(0, 40).map(k => `<span class="tag">${k}</span>`).join(' ')
      + (n > 40 ? ` <span class="tag">+${n - 40} mais</span>` : '');
  } else {
    el.innerHTML = `<span class="status warn"><i class="ti ti-alert-triangle"></i> Nenhum modelo reconhecido</span>`;
  }
  renderOrdens();
}

// ==============================================
//  UPLOAD
// ==============================================
function onFile(inp) {
  const f = inp.files[0]; if (!f) return;
  const reader = new FileReader();
  reader.onload = e => {
    imgB64 = e.target.result.split(',')[1];
    const prev = document.getElementById('preview-img');
    prev.src = e.target.result;
    prev.style.display = 'block';
    document.getElementById('btn-ler').disabled = false;
  };
  reader.readAsDataURL(f);
}

const dz = document.getElementById('drop-zone');
dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('drag'); });
dz.addEventListener('dragleave', () => dz.classList.remove('drag'));
dz.addEventListener('drop', e => {
  e.preventDefault(); dz.classList.remove('drag');
  const f = e.dataTransfer.files[0]; if (!f) return;
  const dt = new DataTransfer(); dt.items.add(f);
  const fi = document.getElementById('file-in');
  fi.files = dt.files;
  onFile(fi);
});

// ==============================================
//  CLAUDE VISION
// ==============================================
async function lerImagem() {
  if (!imgB64) { alert('Nenhuma imagem carregada.'); return; }
  const chave = getChave();
  if (!chave) { alert('Informe a chave da API Anthropic no campo acima.'); return; }

  const statusEl = document.getElementById('ler-status');
  statusEl.innerHTML = '<span class="spinner"></span> Lendo com IA...';
  document.getElementById('btn-ler').disabled = true;

  const prompt = `Você é um assistente industrial especializado em leitura de programações de produção.

Analise esta imagem e extraia TODOS os itens de produção visíveis.

Retorne EXCLUSIVAMENTE um JSON puro no formato abaixo, sem explicação, sem markdown, sem backticks:
[{"modelo":"CODIGO_DO_MODELO","qtd":QUANTIDADE_INTEIRA}]

Instruções:
- "modelo": código alfanumérico do produto/equipamento (normalmente começa com 85. ou 190. mas aceite qualquer código)
- "qtd": quantidade de peças como número inteiro positivo
- Se uma linha tiver "(un)" após o número, esse número é a quantidade
- Ignore cabeçalhos, datas, nomes de célula e informações que não sejam modelos + quantidades
- Se não encontrar nada, retorne exatamente: []`;

  try {
    const resp = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': chave,
        'anthropic-version': '2023-06-01',
        'anthropic-dangerous-direct-browser-access': 'true'
      },
      body: JSON.stringify({
        model: 'claude-sonnet-4-20250514',
        max_tokens: 1024,
        messages: [{
          role: 'user',
          content: [
            { type: 'image', source: { type: 'base64', media_type: 'image/jpeg', data: imgB64 } },
            { type: 'text', text: prompt }
          ]
        }]
      })
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err?.error?.message || `HTTP ${resp.status}`);
    }

    const data = await resp.json();
    const texto = (data.content || []).map(b => b.text || '').join('').trim();

    let parsed;
    try {
      parsed = JSON.parse(texto.replace(/```json|```/g, '').trim());
    } catch (e) {
      statusEl.innerHTML = `<span class="status err"><i class="ti ti-alert-circle"></i> Não foi possível interpretar a resposta</span>`;
      document.getElementById('btn-ler').disabled = false;
      return;
    }

    if (!Array.isArray(parsed) || parsed.length === 0) {
      statusEl.innerHTML = `<span class="status warn"><i class="ti ti-alert-triangle"></i> Nenhum item encontrado na imagem</span>`;
      document.getElementById('btn-ler').disabled = false;
      return;
    }

    ordens = parsed
      .map(p => ({ eq: String(p.modelo || '').toUpperCase().trim(), qty: Math.max(0, parseInt(p.qtd) || 0) }))
      .filter(o => o.eq && o.qty > 0);

    renderOrdens();
    statusEl.innerHTML = `<span class="status ok"><i class="ti ti-check"></i> ${ordens.length} item(ns) extraído(s)</span>`;

  } catch (e) {
    statusEl.innerHTML = `<span class="status err"><i class="ti ti-alert-circle"></i> Erro: ${e.message}</span>`;
  }
  document.getElementById('btn-ler').disabled = false;
}

// ==============================================
//  RENDER ORDENS
// ==============================================
function renderOrdens() {
  const ups  = document.getElementById('sel-ups').value;
  const nN   = MAPA_N[ups] || 5;
  const nDia = parseInt(document.getElementById('n-dia').value) || nN;
  const body = document.getElementById('ordens-body');
  body.innerHTML = '';

  ordens.forEach((o, i) => {
    const uh  = baseMap[o.eq] || null;
    const cad = uh ? Math.round((uh / nN) * nDia * 10) / 10 : null;
    const tr  = document.createElement('tr');
    tr.innerHTML = `
      <td style="color:var(--text-3)">${i + 1}</td>
      <td>
        <strong style="font-weight:500">${o.eq}</strong>
        ${!uh ? ' <span class="tag" style="color:var(--warn-text);background:var(--warn-bg);border-color:transparent">sem base</span>' : ''}
      </td>
      <td><input class="qty-inp" type="number" value="${o.qty}" min="0" onchange="ordens[${i}].qty = Math.max(0, +this.value)"></td>
      <td>${cad ? `<span class="tag">${cad} pc/h</span>` : '<span style="color:var(--text-3);font-size:12px">—</span>'}</td>
      <td>
        <button class="btn" style="padding:3px 8px;font-size:12px" onclick="ordens.splice(${i},1);renderOrdens()">
          <i class="ti ti-x"></i>
        </button>
      </td>`;
    body.appendChild(tr);
  });
}

function addRow() {
  const eq  = document.getElementById('new-eq').value.trim().toUpperCase();
  const qty = parseInt(document.getElementById('new-qty').value) || 0;
  if (!eq || !qty) { alert('Preencha o modelo e a quantidade.'); return; }
  ordens.push({ eq, qty });
  document.getElementById('new-eq').value  = '';
  document.getElementById('new-qty').value = '';
  renderOrdens();
}

function limparOrdens() {
  ordens = [];
  renderOrdens();
  document.getElementById('resultado').style.display = 'none';
}

// ==============================================
//  HELPERS DE TEMPO
// ==============================================
function toMin(s) { const [h, m] = s.split(':').map(Number); return h * 60 + m; }
function toHM(mins) {
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}

// ==============================================
//  CÁLCULO DO CRONOGRAMA
// ==============================================
function calcular() {
  if (ordens.length === 0) { alert('Adicione ao menos uma ordem de produção.'); return; }

  const ups    = document.getElementById('sel-ups').value;
  const nN     = MAPA_N[ups] || 5;
  const nDia   = parseInt(document.getElementById('n-dia').value) || nN;
  const hIni   = document.getElementById('h-ini').value.trim() || '07:45';
  const temGin = document.getElementById('gin').checked;

  const mAlmI  = toMin('11:30'), mAlmF  = toMin('12:30');
  const mCafeM = toMin('09:20'), mCafeT = toMin('15:20');
  const mGinI  = toMin('09:30'), mGinF  = toMin('09:40');

  const MARCOS = ['08:30','09:30','10:30','11:30','12:30','13:30','14:30','15:30','16:30','17:30'];
  const mIni   = toMin(hIni);
  const pontos = [hIni, ...MARCOS.filter(m => toMin(m) > mIni)];

  const proc = ordens.map(o => {
    const uh  = baseMap[o.eq] || 30;
    const cad = (uh / nN) * nDia;
    return { id: o.eq, tPc: 60 / cad, falta: o.qty, orig: o.qty };
  });

  const totalPedir = proc.reduce((s, p) => s + p.orig, 0);
  let idx = 0, acum = 0.0, tot = 0, hFim = 'Não finalizado';
  const rows = [];

  for (let p = 0; p < pontos.length - 1; p++) {
    const p1 = toMin(pontos[p]);
    const p2 = toMin(pontos[p + 1]);
    const isAlm = (p1 === mAlmI && p2 === mAlmF);

    let minU = 0;
    if (!isAlm) {
      for (let m = p1; m < p2; m++) {
        const inCafe = (m >= mCafeM && m < mCafeM + 10) || (m >= mCafeT && m < mCafeT + 10);
        const inAlm  = (m >= mAlmI && m < mAlmF);
        const inGin  = temGin && (m >= mGinI && m < mGinF);
        if (!inCafe && !inAlm && !inGin) minU++;
      }
    }
    acum += minU;

    if (isAlm) {
      rows.push({ h: `${pontos[p]} – ${pontos[p+1]}`, mod: '🍱 Almoço', pc: 0, acum: tot, lunch: true });
      continue;
    }

    let pH = 0, mN = [], guard = 0;
    while (idx < proc.length && guard++ < 999999) {
      const tPc = proc[idx].tPc;
      if (acum >= tPc - 0.00001) {
        const q = Math.min(Math.floor(acum / tPc + 0.00001), proc[idx].falta);
        if (q > 0) {
          acum -= q * tPc;
          proc[idx].falta -= q;
          tot += q; pH += q;
          mN.push(`${proc[idx].id} (${q})`);
        }
        if (proc[idx].falta <= 0) idx++;
        else break;
      } else break;
    }

    rows.push({ h: `${pontos[p]} – ${pontos[p+1]}`, mod: mN.join(' + ') || '—', pc: pH, acum: tot, lunch: false });

    if (tot >= totalPedir && hFim === 'Não finalizado' && totalPedir > 0) {
      const sobrouMin = minU - Math.max(0, Math.ceil(acum));
      hFim = toHM(p1 + sobrouMin);
    }
  }

  // Métricas
  document.getElementById('metrics-area').innerHTML = `
    <div class="metric-card">
      <div class="mlabel">Total de peças</div>
      <div class="mval">${tot} <span style="font-size:14px;font-weight:400;color:var(--text-2)">un</span></div>
    </div>
    <div class="metric-card">
      <div class="mlabel">Término estimado</div>
      <div class="mval">${hFim}</div>
    </div>
    <div class="metric-card">
      <div class="mlabel">Modelos</div>
      <div class="mval">${ordens.length}</div>
    </div>
    <div class="metric-card">
      <div class="mlabel">Célula</div>
      <div class="mval" style="font-size:16px;padding-top:6px">${ups}</div>
    </div>`;

  // Cronograma
  const body = document.getElementById('cron-body');
  body.innerHTML = '';
  rows.forEach(r => {
    const tr = document.createElement('tr');
    if (r.lunch) tr.className = 'lunch';
    tr.innerHTML = `
      <td style="font-weight:500;white-space:nowrap">${r.h}</td>
      <td style="line-height:1.7">${r.mod}</td>
      <td style="text-align:center">${r.pc > 0 ? r.pc : '—'}</td>
      <td style="text-align:center;font-weight:600">${r.acum}</td>`;
    body.appendChild(tr);
  });

  document.getElementById('resultado').style.display = 'block';
  document.getElementById('resultado').scrollIntoView({ behavior: 'smooth', block: 'start' });
}
</script>
</body>
</html>
