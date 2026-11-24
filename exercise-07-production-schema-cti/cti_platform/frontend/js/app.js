/**
 * Main Application Controller: Tab Navigation & Bootloader
 */

document.addEventListener('DOMContentLoaded', async () => {
  setupTabs();

  // Initial Data Loads
  await loadOverviewStats();
  await fetchThreats();
  await loadLab71Schema();
  await loadBsonSizeMetrics();
  await loadWorkingSetData();
  await loadServerStatusMetrics();
  initRandomReadsChart();
  await pollMonitoringStream();

  // Background ticker for header metrics
  setInterval(loadServerStatusMetrics, 10000);
});

function setupTabs() {
  const tabButtons = document.querySelectorAll('.nav-btn');
  const tabPanels = document.querySelectorAll('.tab-content');

  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-tab');

      tabButtons.forEach(b => b.classList.remove('active'));
      tabPanels.forEach(p => p.classList.remove('active'));

      btn.classList.add('active');
      const targetPanel = document.getElementById(targetId);
      if (targetPanel) {
        targetPanel.classList.add('active');
      }

      // If switching to Lab 7.2, redraw chart to match dimensions
      if (targetId === 'tab-lab72') {
        setTimeout(() => {
          if (randomReadsChart) randomReadsChart.resize();
        }, 150);
      }
    });
  });
}
