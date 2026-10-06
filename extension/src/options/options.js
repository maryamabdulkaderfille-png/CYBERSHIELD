(async function () {
  const els = {
    protectionEnabled: document.getElementById("protectionEnabled"),
    autoScan: document.getElementById("autoScan"),
    dangerThreshold: document.getElementById("dangerThreshold"),
    dangerThresholdValue: document.getElementById("dangerThresholdValue"),
    notifications: document.getElementById("notifications"),
    soundAlerts: document.getElementById("soundAlerts"),
    privacyMode: document.getElementById("privacyMode"),
    statisticsCollection: document.getElementById("statisticsCollection"),
    theme: document.getElementById("theme"),
    apiBaseUrl: document.getElementById("apiBaseUrl"),
    dashboardBaseUrl: document.getElementById("dashboardBaseUrl"),
    btnSave: document.getElementById("btnSave"),
    saveStatus: document.getElementById("saveStatus"),
    statTotal: document.getElementById("statTotal"),
    statDangerous: document.getElementById("statDangerous"),
    statSuspicious: document.getElementById("statSuspicious"),
    statFailed: document.getElementById("statFailed"),
  };

  function fillForm(settings) {
    els.protectionEnabled.checked = settings.protectionEnabled;
    els.autoScan.checked = settings.autoScan;
    els.dangerThreshold.value = settings.dangerThreshold;
    els.dangerThresholdValue.textContent = settings.dangerThreshold;
    els.notifications.checked = settings.notifications;
    els.soundAlerts.checked = settings.soundAlerts;
    els.privacyMode.checked = settings.privacyMode;
    els.statisticsCollection.checked = settings.statisticsCollection;
    els.theme.value = settings.theme;
    els.apiBaseUrl.value = settings.apiBaseUrl;
    els.dashboardBaseUrl.value = settings.dashboardBaseUrl;
  }

  function readForm() {
    return {
      protectionEnabled: els.protectionEnabled.checked,
      autoScan: els.autoScan.checked,
      dangerThreshold: Number(els.dangerThreshold.value),
      notifications: els.notifications.checked,
      soundAlerts: els.soundAlerts.checked,
      privacyMode: els.privacyMode.checked,
      statisticsCollection: els.statisticsCollection.checked,
      theme: els.theme.value,
      apiBaseUrl: els.apiBaseUrl.value.trim().replace(/\/$/, ""),
      dashboardBaseUrl: els.dashboardBaseUrl.value.trim().replace(/\/$/, ""),
    };
  }

  async function renderStats() {
    const stats = await CyberShield.storage.getStats();
    els.statTotal.textContent = stats.totalScans;
    els.statDangerous.textContent = stats.dangerousBlocked;
    els.statSuspicious.textContent = stats.suspiciousWarned;
    els.statFailed.textContent = stats.failedScans;
  }

  els.dangerThreshold.addEventListener("input", () => {
    els.dangerThresholdValue.textContent = els.dangerThreshold.value;
  });

  // Empty is allowed (api-client.js treats a blank apiBaseUrl as "signed
  // out"/unconfigured rather than an error) — only a non-empty, malformed
  // value is rejected.
  function isValidHttpUrlOrEmpty(value) {
    if (!value) return true;
    try {
      const parsed = new URL(value);
      return parsed.protocol === "http:" || parsed.protocol === "https:";
    } catch {
      return false;
    }
  }

  els.btnSave.addEventListener("click", async () => {
    const values = readForm();
    if (!isValidHttpUrlOrEmpty(values.apiBaseUrl)) {
      els.saveStatus.textContent = "API URL must be a valid http:// or https:// address.";
      els.saveStatus.classList.add("visible");
      return;
    }
    if (!isValidHttpUrlOrEmpty(values.dashboardBaseUrl)) {
      els.saveStatus.textContent = "Dashboard URL must be a valid http:// or https:// address.";
      els.saveStatus.classList.add("visible");
      return;
    }
    await CyberShield.storage.setSettings(values);
    els.saveStatus.textContent = "Saved.";
    els.saveStatus.classList.add("visible");
    setTimeout(() => els.saveStatus.classList.remove("visible"), 2000);
  });

  const settings = await CyberShield.storage.getSettings();
  fillForm(settings);
  renderStats();
})();
