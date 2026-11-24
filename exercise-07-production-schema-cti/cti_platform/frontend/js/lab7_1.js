/**
 * Lab 7.1 Module: Schema Analysis, $bsonSize Evaluation, and Activity 7.1 Embedded Redesign
 */

async function loadLab71Schema() {
  try {
    const res = await fetch('/api/lab71/schema-analysis');
    const data = await res.json();
    const container = document.getElementById('relationships-container');

    container.innerHTML = data.relationships.map(r => {
      const isEmb = r.is_embedded;
      const tagClass = isEmb ? 'embedded' : 'referenced';
      const label = isEmb ? 'EMBEDDING' : 'REFERENCING';

      return `
        <div class="rel-card">
          <div class="rel-header">
            <span class="pattern-tag ${tagClass}">${label}</span>
            <span class="badge-pill">${r.pattern}</span>
          </div>
          <h4>${r.relationship}</h4>
          <span class="rel-field">Mapping: ${r.fields}</span>
          <p class="rel-text">${isEmb ? r.why_used : r.why_referencing}</p>
          ${!isEmb && r.embedded_alternative ? `
            <details style="margin-top:0.6rem; font-size:0.75rem;">
              <summary style="cursor:pointer; color:var(--primary-cyan)">View Embedded Alternative</summary>
              <pre class="code-preview" style="margin-top:0.4rem;">${JSON.stringify(r.embedded_alternative, null, 2)}</pre>
            </details>
          ` : ''}
        </div>
      `;
    }).join('');
  } catch (err) {
    console.error('Error loading schema analysis:', err);
  }
}

async function loadBsonSizeMetrics() {
  try {
    const res = await fetch('/api/lab71/bson-size');
    const data = await res.json();

    document.getElementById('bson-avg-size').textContent = `${data.avg_document_size_kb} KB`;
    document.getElementById('bson-avg-bytes').textContent = `${data.avg_document_size_bytes?.toLocaleString()} bytes ($$ROOT)`;
    document.getElementById('bson-max-size').textContent = `${data.max_document_size_kb} KB`;
    document.getElementById('bson-max-bytes').textContent = `${data.max_document_size_bytes?.toLocaleString()} bytes`;
    document.getElementById('bson-headroom').textContent = `${data.headroom_mb_remaining} MB`;

    // Progress bar
    const pct = Math.max(0.05, data.max_pct_of_limit);
    document.getElementById('headroom-progress-bar').style.width = `${pct}%`;
    document.getElementById('headroom-pct-label').textContent = `${data.max_pct_of_limit}% of 16 MB limit`;
  } catch (err) {
    console.error('Error loading BSON metrics:', err);
  }
}

async function runActivity71Benchmark() {
  const btn = document.getElementById('btn-run-activity71');
  btn.disabled = true;
  btn.innerHTML = `<span>⏳</span> Benchmarking...`;

  try {
    const res = await fetch('/api/lab71/redesign-benchmark');
    const data = await res.json();

    document.getElementById('bench-ref-time').textContent = `${data.referenced_design_time_ms} ms`;
    document.getElementById('bench-emb-time').textContent = `${data.embedded_design_time_ms} ms`;
    document.getElementById('bench-speedup-label').textContent = `🚀 ${data.speedup_factor}x Faster Reads`;

    btn.disabled = false;
    btn.innerHTML = `<span>⚡</span> Run Comparative Latency Benchmark`;
  } catch (err) {
    alert(`Benchmark error: ${err.message}`);
    btn.disabled = false;
    btn.innerHTML = `<span>⚡</span> Run Comparative Latency Benchmark`;
  }
}

// Event Listeners
document.getElementById('btn-run-activity71').addEventListener('click', runActivity71Benchmark);
