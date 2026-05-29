/**
 * GoGreen — Popup Script
 * Controls the extension popup UI.
 * Per MV3 rules: async/await everywhere, no .then() chains.
 */

const $ = (sel) => document.querySelector(sel);

const statusCard = $("#statusCard");
const statusDot = $("#statusDot");
const statusText = $("#statusText");
const statusDetail = $("#statusDetail");
const toggleBtn = $("#toggleBtn");
const intervalSlider = $("#intervalSlider");
const intervalValue = $("#intervalValue");
const autoStartCb = $("#autoStart");

let isActive = false;

// ── Initialize ──────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", async () => {
  // Load saved settings
  const data = await chrome.storage.local.get(["enabled", "interval", "isActive"]);
  const interval = data.interval || 60;

  intervalSlider.value = interval;
  updateIntervalLabel(interval);
  autoStartCb.checked = data.enabled !== false; // default true

  // Check if currently active on any Teams tab
  isActive = data.isActive || false;
  updateUI(isActive);

  // Also query the active Teams tab for real status
  try {
    const tabs = await chrome.tabs.query({
      url: ["*://teams.microsoft.com/*", "*://teams.live.com/*"],
    });
    if (tabs.length > 0) {
      const response = await chrome.tabs.sendMessage(tabs[0].id, {
        action: "getStatus",
      });
      if (response && response.ok) {
        isActive = response.active;
        updateUI(isActive);
      }
    }
  } catch (e) {
    // Teams tab not open or content script not loaded
  }
});

// ── Toggle Button ───────────────────────────────────────────────
toggleBtn.addEventListener("click", async () => {
  const newState = !isActive;
  const interval = parseInt(intervalSlider.value, 10);

  // Send to all Teams tabs
  try {
    const tabs = await chrome.tabs.query({
      url: ["*://teams.microsoft.com/*", "*://teams.live.com/*"],
    });

    if (tabs.length === 0) {
      statusDetail.textContent = "⚠ Open teams.microsoft.com first!";
      statusDetail.style.color = "#ffab00";
      setTimeout(() => {
        statusDetail.style.color = "";
        updateUI(isActive);
      }, 3000);
      return;
    }

    for (const tab of tabs) {
      await chrome.tabs.sendMessage(tab.id, {
        action: newState ? "start" : "stop",
        interval: interval * 1000,
      });
    }

    isActive = newState;
    await chrome.storage.local.set({
      enabled: autoStartCb.checked,
      interval: interval,
      isActive: isActive,
    });
    updateUI(isActive);
  } catch (e) {
    statusDetail.textContent = "⚠ Could not reach Teams tab. Reload it.";
    statusDetail.style.color = "#ff4757";
  }
});

// ── Interval Slider ─────────────────────────────────────────────
intervalSlider.addEventListener("input", () => {
  const val = parseInt(intervalSlider.value, 10);
  updateIntervalLabel(val);
});

intervalSlider.addEventListener("change", async () => {
  const val = parseInt(intervalSlider.value, 10);
  await chrome.storage.local.set({ interval: val });

  // If active, update the running interval
  if (isActive) {
    try {
      const tabs = await chrome.tabs.query({
        url: ["*://teams.microsoft.com/*", "*://teams.live.com/*"],
      });
      for (const tab of tabs) {
        await chrome.tabs.sendMessage(tab.id, {
          action: "start",
          interval: val * 1000,
        });
      }
    } catch (e) {
      /* ignore */
    }
  }
});

// ── Auto-start Checkbox ─────────────────────────────────────────
autoStartCb.addEventListener("change", async () => {
  await chrome.storage.local.set({ enabled: autoStartCb.checked });
});

// ── UI Helpers ──────────────────────────────────────────────────
function updateUI(active) {
  if (active) {
    statusCard.classList.add("active");
    statusDot.classList.add("active");
    statusText.classList.add("active");
    statusText.textContent = "Active";
    statusDetail.textContent = "Teams status is being kept green 🟢";
    statusDetail.style.color = "";
    toggleBtn.textContent = "⏹  STOP";
    toggleBtn.classList.add("stop");
  } else {
    statusCard.classList.remove("active");
    statusDot.classList.remove("active");
    statusText.classList.remove("active");
    statusText.textContent = "Inactive";
    statusDetail.textContent = "Click START to keep Teams green";
    statusDetail.style.color = "";
    toggleBtn.textContent = "▶  START";
    toggleBtn.classList.remove("stop");
  }
}

function updateIntervalLabel(seconds) {
  if (seconds < 60) {
    intervalValue.textContent = `Every ${seconds} seconds`;
  } else {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    intervalValue.textContent = s
      ? `Every ${m}m ${s}s`
      : `Every ${m} minute${m > 1 ? "s" : ""}`;
  }
}
