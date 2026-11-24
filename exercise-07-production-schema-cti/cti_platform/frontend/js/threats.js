/**
 * Threats Module: Search, Filtering, Inspection & Threat Classification
 */

let allThreats = [];
let selectedThreat = null;

async function loadOverviewStats() {
  try {
    const res = await fetch('/api/overview-stats');
    const data = await res.json();
    document.getElementById('stat-total-threats').textContent = data.total_threats?.toLocaleString() || '0';
    document.getElementById('stat-critical-threats').textContent = data.critical_threats?.toLocaleString() || '0';
    document.getElementById('stat-actual-threats').textContent = data.actual_threats?.toLocaleString() || '0';
    document.getElementById('stat-sources-count').textContent = data.total_sources?.toLocaleString() || '0';
  } catch (err) {
    console.error('Failed to load stats:', err);
  }
}

async function fetchThreats() {
  const container = document.getElementById('threat-cards-container');
  const searchInput = document.getElementById('threat-search-input').value.trim();
  const filterType = document.getElementById('filter-type').value;
  const filterSeverity = document.getElementById('filter-severity').value;
  const filterVerdict = document.getElementById('filter-verdict').value;

  const params = new URLSearchParams();
  if (searchInput) params.append('q', searchInput);
  if (filterType) params.append('threat_type', filterType);
  if (filterSeverity) params.append('severity', filterSeverity);
  if (filterVerdict) params.append('verdict', filterVerdict);

  try {
    const res = await fetch(`/api/threats?${params.toString()}`);
    const data = await res.json();
    allThreats = data.threats || [];

    document.getElementById('stream-count-label').textContent = `Showing ${allThreats.length} of ${data.total_in_db} threats`;

    if (allThreats.length === 0) {
      container.innerHTML = `<div class="empty-state"><span class="empty-icon">🔎</span><p>No matching threat intelligence records found.</p></div>`;
      return;
    }

    container.innerHTML = allThreats.map(t => {
      const isActual = t.classification?.verdict === 'Actual Threat';
      const sevClass = (t.severity || 'medium').toLowerCase();
      const isActive = selectedThreat && selectedThreat.threat_id === t.threat_id ? 'active' : '';

      return `
        <div class="threat-card ${isActive}" onclick="inspectThreat('${t.threat_id}')">
          <div class="card-top-row">
            <span class="badge-tag ${sevClass}">${t.severity}</span>
            <span class="card-threat-id">${t.threat_id}</span>
          </div>
          <div class="card-threat-title">${t.title}</div>
          <div class="card-bottom-row">
            <span class="card-verdict-chip ${isActual ? 'actual' : 'fp'}">
              ${isActual ? '⚡ Actual Threat' : '🛡️ Benign / False Positive'}
            </span>
            <span>${t.threat_type} • BSON: ${t.bson_size_bytes || '~1.5'} B</span>
          </div>
        </div>
      `;
    }).join('');

    // If first load or selected disappeared, select first
    if (!selectedThreat && allThreats.length > 0) {
      inspectThreat(allThreats[0].threat_id);
    }
  } catch (err) {
    container.innerHTML = `<div class="empty-state"><p style="color:var(--accent-red)">Error loading threats: ${err.message}</p></div>`;
  }
}

function inspectThreat(threatId) {
  const threat = allThreats.find(t => t.threat_id === threatId);
  if (!threat) return;

  selectedThreat = threat;

  // Highlight active card
  document.querySelectorAll('.threat-card').forEach(el => el.classList.remove('active'));
  // Re-highlight if needed

  document.getElementById('inspector-placeholder').style.display = 'none';
  document.getElementById('inspector-content').style.display = 'block';

  document.getElementById('inspect-threat-id').textContent = threat.threat_id;
  document.getElementById('inspect-title').textContent = threat.title;
  document.getElementById('inspect-desc').textContent = threat.description || 'No detailed description provided.';
  document.getElementById('active-doc-size-badge').textContent = `BSON: ${threat.bson_size_bytes || 1500} Bytes`;
  document.getElementById('inspect-exact-bytes').textContent = `${threat.bson_size_bytes || 1500} bytes ($$ROOT)`;

  // Form values
  document.getElementById('form-verdict').value = threat.classification?.verdict || 'Actual Threat';
  document.getElementById('form-severity').value = threat.severity || 'High';

  // Referenced entities
  document.getElementById('inspect-source-ref').textContent = threat.source_id || 'SRC-001';
  document.getElementById('inspect-actor-ref').textContent = threat.actor_id || 'ACT-001';
  document.getElementById('inspect-cve-ref').textContent = (threat.cve_ids && threat.cve_ids.join(', ')) || 'None';

  // IOCs list (Embedded)
  const iocsList = document.getElementById('inspect-iocs-list');
  if (threat.indicators && threat.indicators.length > 0) {
    iocsList.innerHTML = threat.indicators.map(ioc => `
      <div class="ioc-item">
        <span class="ioc-type">[${ioc.type.toUpperCase()}]</span>
        <span class="ioc-val">${ioc.value}</span>
      </div>
    `).join('');
  } else {
    iocsList.innerHTML = `<span class="text-dim">No indicators embedded in this report.</span>`;
  }

  // Raw JSON
  document.getElementById('inspect-raw-json').textContent = JSON.stringify(threat, null, 2);
}

async function saveThreatClassification() {
  if (!selectedThreat) return;

  const btn = document.getElementById('btn-save-classification');
  btn.disabled = true;
  btn.innerHTML = `<span>⏳</span> Saving...`;

  const newVerdict = document.getElementById('form-verdict').value;
  const newSeverity = document.getElementById('form-severity').value;

  try {
    const res = await fetch(`/api/threats/${selectedThreat.threat_id}/classify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        verdict: newVerdict,
        severity: newSeverity
      })
    });
    const result = await res.json();

    btn.innerHTML = `<span>✓</span> Saved!`;
    setTimeout(() => {
      btn.disabled = false;
      btn.innerHTML = `<span>✓</span> Save Classification`;
    }, 1500);

    // Refresh threats list and stats
    await fetchThreats();
    await loadOverviewStats();
  } catch (err) {
    alert(`Error updating classification: ${err.message}`);
    btn.disabled = false;
    btn.innerHTML = `<span>✓</span> Save Classification`;
  }
}

// Event Listeners
document.getElementById('threat-search-input').addEventListener('input', () => {
  clearTimeout(window.searchTimeout);
  window.searchTimeout = setTimeout(fetchThreats, 300);
});

document.getElementById('btn-clear-search').addEventListener('click', () => {
  document.getElementById('threat-search-input').value = '';
  fetchThreats();
});

document.getElementById('filter-type').addEventListener('change', fetchThreats);
document.getElementById('filter-severity').addEventListener('change', fetchThreats);
document.getElementById('filter-verdict').addEventListener('change', fetchThreats);
document.getElementById('btn-refresh-threats').addEventListener('click', () => {
  fetchThreats();
  loadOverviewStats();
});
document.getElementById('btn-save-classification').addEventListener('click', saveThreatClassification);
