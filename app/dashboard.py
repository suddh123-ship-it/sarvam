"""Self-contained HTML dashboard for the auto dealership voice bot.

Served at GET /dashboard. It polls GET /api/dashboard for live data.
"""

DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>AutoCare Motors — Voice Bot Dashboard</title>
<style>
  :root {
    --bg: #0f1420;
    --panel: #171e2e;
    --panel-2: #1e2739;
    --border: #2a3550;
    --text: #e7ecf5;
    --muted: #8a97b1;
    --accent: #4f8cff;
    --green: #35c98a;
    --amber: #f0b23a;
    --red: #ff6b6b;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--bg); color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }
  header {
    padding: 20px 28px; border-bottom: 1px solid var(--border);
    display: flex; align-items: center; justify-content: space-between;
    background: linear-gradient(180deg, #141b2b, #0f1420);
  }
  header h1 { margin: 0; font-size: 20px; letter-spacing: .3px; }
  header .sub { color: var(--muted); font-size: 13px; margin-top: 3px; }
  .wrap { padding: 24px 28px; max-width: 1200px; margin: 0 auto; }
  .btn {
    background: var(--accent); color: white; border: none; padding: 10px 16px;
    border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer;
    transition: opacity .15s;
  }
  .btn:hover { opacity: .88; }
  .btn:disabled { opacity: .5; cursor: default; }
  .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 26px; }
  .card {
    background: var(--panel); border: 1px solid var(--border);
    border-radius: 12px; padding: 18px 20px;
  }
  .card .label { color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .5px; }
  .card .value { font-size: 30px; font-weight: 700; margin-top: 6px; }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
  @media (max-width: 900px) { .grid { grid-template-columns: 1fr; } .stats { grid-template-columns: repeat(2, 1fr); } }
  .panel {
    background: var(--panel); border: 1px solid var(--border);
    border-radius: 12px; overflow: hidden;
  }
  .panel h2 {
    margin: 0; padding: 16px 20px; font-size: 15px; border-bottom: 1px solid var(--border);
    background: var(--panel-2);
  }
  table { width: 100%; border-collapse: collapse; }
  th, td { text-align: left; padding: 12px 20px; font-size: 13px; border-bottom: 1px solid var(--border); }
  th { color: var(--muted); font-weight: 600; text-transform: uppercase; font-size: 11px; letter-spacing: .5px; }
  tr:last-child td { border-bottom: none; }
  .badge {
    display: inline-block; padding: 3px 10px; border-radius: 999px;
    font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .3px;
  }
  .badge.active { background: rgba(138,151,177,.16); color: var(--muted); }
  .badge.call_completed { background: rgba(53,201,138,.16); color: var(--green); }
  .badge.escalated { background: rgba(255,107,107,.16); color: var(--red); }
  .calls { padding: 6px 0; max-height: 520px; overflow-y: auto; }
  .call {
    padding: 14px 20px; border-bottom: 1px solid var(--border);
  }
  .call:last-child { border-bottom: none; }
  .call .top { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
  .call .who { font-weight: 600; font-size: 14px; }
  .call .meta { color: var(--muted); font-size: 12px; margin-top: 3px; }
  .call .summary { margin-top: 8px; font-size: 13px; line-height: 1.5; color: #cdd6e8; }
  .chips { margin-top: 8px; display: flex; flex-wrap: wrap; gap: 6px; }
  .chip { background: var(--panel-2); border: 1px solid var(--border); color: var(--muted);
          font-size: 11px; padding: 2px 9px; border-radius: 6px; }
  .empty { padding: 30px 20px; color: var(--muted); font-size: 13px; text-align: center; }
  .dot { display:inline-block; width:8px; height:8px; border-radius:50%; background:var(--green); margin-right:6px; }
</style>
</head>
<body>
  <header>
    <div>
      <h1>🚗 AutoCare Motors — Voice Bot Dashboard</h1>
      <div class="sub"><span class="dot"></span>Live • telephonic call summaries &amp; customer status</div>
    </div>
  </header>

  <div class="wrap">
    <div class="stats" id="stats"></div>

    <div class="grid">
      <div class="panel">
        <h2>Customers</h2>
        <table>
          <thead>
            <tr><th>Customer</th><th>Vehicle</th><th>Last Call</th><th>Status</th></tr>
          </thead>
          <tbody id="customers"></tbody>
        </table>
      </div>

      <div class="panel">
        <h2>Recent Calls</h2>
        <div class="calls" id="calls"></div>
      </div>
    </div>
  </div>

<script>
  function badge(status) {
    const label = status.replace('_', ' ');
    return `<span class="badge ${status}">${label}</span>`;
  }

  function renderStats(s) {
    document.getElementById('stats').innerHTML = `
      <div class="card"><div class="label">Customers</div><div class="value">${s.total_customers}</div></div>
      <div class="card"><div class="label">Total Calls</div><div class="value">${s.total_calls}</div></div>
      <div class="card"><div class="label">Completed</div><div class="value" style="color:var(--green)">${s.completed}</div></div>
      <div class="card"><div class="label">Escalated</div><div class="value" style="color:var(--red)">${s.escalated}</div></div>`;
  }

  function renderCustomers(list) {
    const el = document.getElementById('customers');
    if (!list.length) { el.innerHTML = '<tr><td colspan="4" class="empty">No customers.</td></tr>'; return; }
    el.innerHTML = list.map(c => `
      <tr>
        <td><div>${c.name}</div><div class="meta" style="color:var(--muted);font-size:12px">${c.phone}</div></td>
        <td>${c.vehicle_model || '—'} <span style="color:var(--muted)">${c.vehicle_year || ''}</span></td>
        <td>${c.last_call_at || '—'}</td>
        <td>${badge(c.status)}</td>
      </tr>`).join('');
  }

  function renderCalls(list) {
    const el = document.getElementById('calls');
    if (!list.length) { el.innerHTML = '<div class="empty">No calls yet. Incoming calls will appear here.</div>'; return; }
    el.innerHTML = list.map(c => {
      const chips = [];
      if (c.vehicle_model) chips.push(`Vehicle: ${c.vehicle_model}`);
      if (c.service_type) chips.push(`Service: ${c.service_type}`);
      if (c.preferred_date) chips.push(`Date: ${c.preferred_date}`);
      if (c.intent) chips.push(`Intent: ${c.intent}`);
      return `
        <div class="call">
          <div class="top">
            <div>
              <div class="who">${c.customer_name}</div>
              <div class="meta">${c.phone} • ${c.time_label} • ${c.turn_count} turns</div>
            </div>
            ${badge(c.status)}
          </div>
          <div class="summary">${c.summary}</div>
          <div class="chips">${chips.map(x => `<span class="chip">${x}</span>`).join('')}</div>
        </div>`;
    }).join('');
  }

  async function refresh() {
    try {
      const r = await fetch('/api/dashboard');
      const d = await r.json();
      renderStats(d.stats);
      renderCustomers(d.customers);
      renderCalls(d.calls);
    } catch (e) { console.error(e); }
  }

  refresh();
  setInterval(refresh, 4000);
</script>
</body>
</html>
"""
