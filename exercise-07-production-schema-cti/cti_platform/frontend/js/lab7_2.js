/**
 * Lab 7.2 Module: Working Set Analysis, WiredTiger Cache Metrics,
 * Random Reads Simulation with Chart.js, and Activity 7.2 Real-time 10s Monitoring
 */

let randomReadsChart = null;

async function loadWorkingSetData() {
  try {
    const res = await fetch('/api/lab72/working-set');
    const data = await res.json();

    document.getElementById('wt-total-docs').textContent = data.total_documents?.toLocaleString() || '100,000';
    document.getElementById('wt-avg-size').textContent = `${(data.sample_doc_size_bytes / 1024).toFixed(2)} KB`;
    document.getElementById('wt-working-set-mb').textContent = `${data.total_working_set_mb} MB`;
    document.getElementById('wt-cache-size-mb').textContent = `${data.wiredtiger_cache_mb} MB`;
    document.getElementById('wt-cache-fit-pct').textContent = `${data.cache_fit_percentage}%`;
    document.getElementById('wt-cache-fit-status').textContent = data.cache_status;
  } catch (err) {
    console.error('Error loading working set data:', err);
  }
}

async function loadServerStatusMetrics() {
  try {
    const res = await fetch('/api/lab72/server-status');
    const status = await res.json();
    const wtCache = status.wiredTiger?.cache || {};

    const inCacheMb = (wtCache['bytes currently in the cache'] || 0) / (1024 * 1024);
    const dirtyMb = (wtCache['tracked dirty bytes in the cache'] || 0) / (1024 * 1024);
    const hitRatio = wtCache['calculated cache hit ratio'] ?? 98.4;
    const pctInCache = wtCache['percentage of data in cache'] ?? 100.0;

    document.getElementById('wt-bytes-in-cache').textContent = `${inCacheMb.toFixed(2)} MB`;
    document.getElementById('wt-pct-in-cache').textContent = `${pctInCache.toFixed(1)}% resident in cache`;
    document.getElementById('wt-dirty-bytes').textContent = `${dirtyMb.toFixed(2)} MB`;
    document.getElementById('wt-live-hit-ratio').textContent = `${hitRatio.toFixed(2)}%`;
    document.getElementById('top-cache-hit-ratio').textContent = `${hitRatio.toFixed(1)}%`;
  } catch (err) {
    console.error('Error loading serverStatus:', err);
  }
}

async function triggerInsert100k() {
  const btn = document.getElementById('btn-insert-100k');
  btn.disabled = true;
  btn.innerHTML = `<span>⏳</span> Inserting 100,000 Documents...`;

  try {
    const res = await fetch('/api/lab72/insert-100k', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ count: 100000 })
    });
    const result = await res.json();

    btn.disabled = false;
    btn.innerHTML = `<span>✓</span> 100,000 Documents Inserted!`;
    setTimeout(() => {
      btn.innerHTML = `<span>📥</span> Re-run 100,000 Document Ingestion`;
    }, 2500);

    await loadWorkingSetData();
    await loadServerStatusMetrics();
  } catch (err) {
    alert(`Insertion error: ${err.message}`);
    btn.disabled = false;
    btn.innerHTML = `<span>📥</span> Insert 100,000 Security Documents`;
  }
}

function initRandomReadsChart(labels = [], hitRatios = []) {
  const ctx = document.getElementById('random-reads-chart');
  if (!ctx) return;

  if (randomReadsChart) {
    randomReadsChart.destroy();
  }

  randomReadsChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels.length ? labels : ['0 Ops', '500 Ops', '1,000 Ops', '2,000 Ops', '3,500 Ops', '5,000 Ops'],
      datasets: [{
        label: 'WiredTiger Cache Hit Ratio (%)',
        data: hitRatios.length ? hitRatios : [72.4, 88.6, 94.2, 97.8, 98.6, 99.2],
        borderColor: '#00f0ff',
        backgroundColor: 'rgba(0, 240, 255, 0.12)',
        borderWidth: 2,
        fill: true,
        tension: 0.35,
        pointBackgroundColor: '#00f0ff',
        pointBorderColor: '#fff',
        pointRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { labels: { color: '#94a3b8', font: { family: 'Plus Jakarta Sans' } } },
        tooltip: {
          backgroundColor: '#111827',
          titleColor: '#00f0ff',
          bodyColor: '#f8fafc',
          borderColor: '#27354f',
          borderWidth: 1
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#64748b', font: { family: 'JetBrains Mono' } }
        },
        y: {
          min: 60,
          max: 100,
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: {
            color: '#64748b',
            font: { family: 'JetBrains Mono' },
            callback: v => `${v}%`
          }
        }
      }
    }
  });
}

async function runRandomReadsWorkload() {
  const btn = document.getElementById('btn-run-random-reads');
  btn.disabled = true;
  btn.innerHTML = `<span>⏳</span> Simulating Random Reads...`;

  try {
    const res = await fetch('/api/lab72/random-reads', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ cycles: 2500 })
    });
    const data = await res.json();
    const timeline = data.timeline || [];

    const labels = timeline.map(t => `${t.reads_completed} Reads`);
    const ratios = timeline.map(t => t.hit_ratio);

    initRandomReadsChart(labels, ratios);
    await loadServerStatusMetrics();

    btn.disabled = false;
    btn.innerHTML = `<span>⚡</span> Execute 2,500 Random Reads`;
  } catch (err) {
    alert(`Workload error: ${err.message}`);
    btn.disabled = false;
    btn.innerHTML = `<span>⚡</span> Execute 2,500 Random Reads`;
  }
}

async function pollMonitoringStream() {
  try {
    const res = await fetch('/api/lab72/monitoring-stream');
    const data = await res.json();

    // 1. Update Telemetry Table
    const history = data.history || [];
    const tbody = document.getElementById('telemetry-log-tbody');
    if (history.length > 0) {
      tbody.innerHTML = history.slice().reverse().map(h => `
        <tr>
          <td>${h.timestamp}</td>
          <td style="color:var(--primary-cyan); font-weight:700;">${h.hit_ratio.toFixed(2)}%</td>
          <td>${h.bytes_in_cache_mb} MB</td>
          <td style="color:var(--accent-yellow);">${h.dirty_bytes_mb} MB</td>
          <td>${h.pages_requested.toLocaleString()}</td>
          <td style="color:var(--accent-crimson);">${h.pages_read.toLocaleString()}</td>
        </tr>
      `).join('');
    }

    // 2. Update Discovery Crawler Stream
    const discoveries = data.recent_discoveries || [];
    const crawlerList = document.getElementById('crawler-discoveries-list');
    if (discoveries.length > 0) {
      crawlerList.innerHTML = discoveries.map(d => {
        const sevClass = (d.severity || 'high').toLowerCase();
        return `
          <div class="crawler-threat-card">
            <div class="crawler-card-top">
              <span class="badge-tag ${sevClass}">${d.severity}</span>
              <span class="crawler-time">${d.discovered_at}</span>
            </div>
            <div style="font-weight:600; color:var(--text-main); margin-bottom:0.2rem;">${d.title}</div>
            <div style="color:var(--text-dim); font-size:0.72rem;">Classification: Actual Threat • ${d.threat_type}</div>
          </div>
        `;
      }).join('');
    }

    if (data.last_check) {
      document.getElementById('top-cache-hit-ratio').textContent = `${data.last_check.hit_ratio.toFixed(1)}%`;
      document.getElementById('wt-live-hit-ratio').textContent = `${data.last_check.hit_ratio.toFixed(2)}%`;
    }
  } catch (err) {
    console.error('Error polling monitoring stream:', err);
  }
}

// Event Listeners
document.getElementById('btn-insert-100k').addEventListener('click', triggerInsert100k);
document.getElementById('btn-run-random-reads').addEventListener('click', runRandomReadsWorkload);

// Polling intervals for Activity 7.2 real-time monitoring
setInterval(pollMonitoringStream, 5000);
