(async function () {
  const api = CyberShield.browserAPI;
  const { RISK_LEVELS } = CyberShield;

  const els = {
    connStatus: document.getElementById("connStatus"),
    stateLoading: document.getElementById("stateLoading"),
    stateSignedOut: document.getElementById("stateSignedOut"),
    stateUnscannable: document.getElementById("stateUnscannable"),
    stateError: document.getElementById("stateError"),
    stateResult: document.getElementById("stateResult"),
    stateBlocked: document.getElementById("stateBlocked"),
    errorMessage: document.getElementById("errorMessage"),
    blockedHost: document.getElementById("blockedHost"),
    blockedScore: document.getElementById("blockedScore"),
    blockedReason: document.getElementById("blockedReason"),
    blockedReasonWrap: document.getElementById("blockedReasonWrap"),
    btnUnblock: document.getElementById("btnUnblock"),
    unblockError: document.getElementById("unblockError"),
    siteHost: document.getElementById("siteHost"),
    gaugeCircle: document.getElementById("gaugeCircle"),
    scoreValue: document.getElementById("scoreValue"),
    riskBadge: document.getElementById("riskBadge"),
    scanTime: document.getElementById("scanTime"),
    reasonsSection: document.getElementById("reasonsSection"),
    reasonsList: document.getElementById("reasonsList"),
    recommendationsSection: document.getElementById("recommendationsSection"),
    recommendationsList: document.getElementById("recommendationsList"),
    btnSignIn: document.getElementById("btnSignIn"),
    btnRetryError: document.getElementById("btnRetryError"),
    btnDashboard: document.getElementById("btnDashboard"),
    btnReport: document.getElementById("btnReport"),
    btnRescan: document.getElementById("btnRescan"),
    btnSettings: document.getElementById("btnSettings"),
  };

  const ALL_STATES = [
    els.stateLoading,
    els.stateSignedOut,
    els.stateUnscannable,
    els.stateError,
    els.stateResult,
    els.stateBlocked,
  ];

  let currentBlockedEntry = null;

  function renderBlocked(blockedEntry) {
    currentBlockedEntry = blockedEntry;
    els.blockedHost.textContent = blockedEntry.domain;
    els.blockedScore.textContent = String(blockedEntry.trust_score);
    els.blockedReasonWrap.style.display = blockedEntry.reason ? "" : "none";
    els.blockedReason.textContent = blockedEntry.reason || "";
    els.unblockError.style.display = "none";
    els.unblockError.textContent = "";
  }

  function showState(el) {
    for (const s of ALL_STATES) s.classList.toggle("state-hidden", s !== el);
  }

  function applyTheme(theme) {
    const resolved = theme === "system" ? (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light") : theme;
    document.documentElement.dataset.theme = resolved;
  }

  function riskBadgeClass(risk) {
    return `badge risk-${risk.toLowerCase().replace(/\s+/g, "-")}`;
  }

  function updateConnectionStatus() {
    const online = navigator.onLine;
    els.connStatus.classList.toggle("offline", !online);
    els.connStatus.querySelector(".conn-label").textContent = online ? "Online" : "Offline";
  }

  function formatScanTime(isoString) {
    if (!isoString) return "";
    const date = new Date(isoString);
    return `Scanned ${date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
  }

  function renderResult(result) {
    const circumference = 326.7;
    const score = Math.max(0, Math.min(100, result.trust_score));
    els.gaugeCircle.style.strokeDashoffset = String(circumference * (1 - score / 100));
    els.gaugeCircle.style.stroke = CyberShield.RISK_COLORS[result.risk] || "#64748b";
    els.scoreValue.textContent = String(score);
    els.riskBadge.textContent = result.risk;
    els.riskBadge.className = riskBadgeClass(result.risk);
    els.scanTime.textContent = formatScanTime(result.scan_date);

    els.reasonsList.innerHTML = "";
    for (const reason of (result.reasons || []).slice(0, 8)) {
      const li = document.createElement("li");
      li.textContent = reason;
      els.reasonsList.appendChild(li);
    }
    els.reasonsSection.style.display = (result.reasons || []).length ? "" : "none";

    els.recommendationsList.innerHTML = "";
    for (const rec of (result.recommendations || []).slice(0, 8)) {
      const li = document.createElement("li");
      li.textContent = rec;
      els.recommendationsList.appendChild(li);
    }
    els.recommendationsSection.style.display = (result.recommendations || []).length ? "" : "none";
  }

  let currentTab = null;
  let currentResult = null;
  let currentSettings = null;

  async function getActiveTab() {
    const [tab] = await api.tabs.query({ active: true, currentWindow: true });
    return tab || null;
  }

  async function loadAndRender() {
    showState(els.stateLoading);

    currentSettings = await CyberShield.storage.getSettings();
    applyTheme(currentSettings.theme);

    currentTab = await getActiveTab();
    if (!currentTab || !currentTab.url || CyberShield.SKIPPED_URL_PATTERN.test(currentTab.url)) {
      showState(els.stateUnscannable);
      return;
    }

    els.siteHost.textContent = new URL(currentTab.url).host;
    els.siteHost.title = currentTab.url;

    const isAuthed = await CyberShield.api.checkAuth(currentSettings);
    if (!isAuthed) {
      showState(els.stateSignedOut);
      return;
    }

    try {
      const cached = await api.runtime.sendMessage({ type: "GET_TAB_STATE", tabId: currentTab.id });
      if (cached?.state?.url === currentTab.url && cached.state.hardBlocked && cached.state.blockedEntry) {
        renderBlocked(cached.state.blockedEntry);
        showState(els.stateBlocked);
        return;
      }
      if (cached?.state?.result && cached.state.url === currentTab.url) {
        currentResult = cached.state.result;
        renderResult(currentResult);
        showState(els.stateResult);
        return;
      }

      const response = await api.runtime.sendMessage({
        type: "GET_OR_SCAN_VERDICT",
        tabId: currentTab.id,
        url: currentTab.url,
      });
      if (response?.hardBlocked && response.blockedEntry) {
        renderBlocked(response.blockedEntry);
        showState(els.stateBlocked);
      } else if (response?.result) {
        currentResult = response.result;
        renderResult(currentResult);
        showState(els.stateResult);
      } else {
        els.errorMessage.textContent = response?.error || "This page could not be checked.";
        showState(els.stateError);
      }
    } catch (err) {
      els.errorMessage.textContent = err?.message || "Something went wrong.";
      showState(els.stateError);
    }
  }

  els.btnSignIn.addEventListener("click", async () => {
    const settings = currentSettings || (await CyberShield.storage.getSettings());
    api.tabs.create({ url: `${settings.dashboardBaseUrl.replace(/\/$/, "")}/login` });
  });

  els.btnRetryError.addEventListener("click", loadAndRender);

  els.btnUnblock.addEventListener("click", async () => {
    if (!currentBlockedEntry || !currentTab) return;
    els.btnUnblock.disabled = true;
    els.unblockError.style.display = "none";
    const response = await api.runtime.sendMessage({
      type: "UNBLOCK_FROM_WARNING",
      tabId: currentTab.id,
      entryId: currentBlockedEntry.id,
    });
    els.btnUnblock.disabled = false;
    if (response?.ok) {
      api.tabs.reload(currentTab.id);
      loadAndRender();
    } else {
      els.unblockError.textContent = response?.error || "Could not remove this site from your block list. Please try again.";
      els.unblockError.style.display = "";
    }
  });

  els.btnDashboard.addEventListener("click", async () => {
    const settings = currentSettings || (await CyberShield.storage.getSettings());
    api.tabs.create({ url: settings.dashboardBaseUrl.replace(/\/$/, "") });
  });

  els.btnReport.addEventListener("click", async () => {
    const settings = currentSettings || (await CyberShield.storage.getSettings());
    const base = settings.dashboardBaseUrl.replace(/\/$/, "");
    const path = currentResult?.id ? `/dashboard/reports/url/${currentResult.id}` : "/dashboard/url-scanner";
    api.tabs.create({ url: `${base}${path}` });
  });

  els.btnRescan.addEventListener("click", async () => {
    if (!currentTab) return;
    showState(els.stateLoading);
    try {
      const response = await api.runtime.sendMessage({ type: "RESCAN", tabId: currentTab.id, url: currentTab.url });
      if (response?.result) {
        currentResult = response.result;
        renderResult(currentResult);
        showState(els.stateResult);
      } else {
        els.errorMessage.textContent = response?.error || "This page could not be checked.";
        showState(els.stateError);
      }
    } catch (err) {
      els.errorMessage.textContent = err?.message || "Something went wrong.";
      showState(els.stateError);
    }
  });

  els.btnSettings.addEventListener("click", () => {
    api.runtime.openOptionsPage();
  });

  window.addEventListener("online", updateConnectionStatus);
  window.addEventListener("offline", updateConnectionStatus);
  updateConnectionStatus();

  loadAndRender();
})();
