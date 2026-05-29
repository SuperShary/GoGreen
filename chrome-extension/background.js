/**
 * GoGreen — Background Service Worker
 * Manages badge state and auto-activation on Teams tabs.
 * Per MV3 rules: NO state in global variables — uses chrome.storage.
 */

// ── Badge Updates ───────────────────────────────────────────────
chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg.type === "statusUpdate") {
    (async () => {
      try {
        if (msg.active) {
          await chrome.action.setBadgeBackgroundColor({ color: "#00ff88" });
          await chrome.action.setBadgeText({ text: "ON" });
        } else {
          await chrome.action.setBadgeText({ text: "" });
        }
        await chrome.storage.local.set({ isActive: msg.active });
      } catch (e) {
        // ignore — tab may have closed
      }
      sendResponse({ ok: true });
    })();
    return true;
  }
});

// ── Auto-activate on Teams tabs ─────────────────────────────────
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  if (changeInfo.status !== "complete") return;
  if (!tab.url) return;

  const isTeams =
    tab.url.includes("teams.microsoft.com") ||
    tab.url.includes("teams.live.com");

  if (!isTeams) return;

  try {
    const data = await chrome.storage.local.get(["enabled", "interval"]);
    if (data.enabled) {
      await chrome.tabs.sendMessage(tabId, {
        action: "start",
        interval: (data.interval || 60) * 1000,
      });
    }
  } catch (e) {
    // Content script not ready yet — ignore
  }
});

// ── Install / Startup ───────────────────────────────────────────
chrome.runtime.onInstalled.addListener(async () => {
  // Set defaults on first install
  const existing = await chrome.storage.local.get("enabled");
  if (existing.enabled === undefined) {
    await chrome.storage.local.set({
      enabled: true,
      interval: 60,
      isActive: false,
    });
  }
});
