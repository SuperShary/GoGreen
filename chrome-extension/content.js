/**
 * GoGreen — Isolated World Content Script
 * Bridges between the extension APIs (popup, background, storage)
 * and the MAIN world inject.js via window.postMessage.
 */

// ── Listen for messages from popup / background ─────────────────
chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg.action === "start") {
    window.postMessage(
      { source: "gogreen-extension", action: "start", interval: msg.interval },
      "*"
    );
    sendResponse({ ok: true });
  } else if (msg.action === "stop") {
    window.postMessage(
      { source: "gogreen-extension", action: "stop" },
      "*"
    );
    sendResponse({ ok: true });
  } else if (msg.action === "getStatus") {
    // Request status from inject.js
    window.postMessage(
      { source: "gogreen-extension", action: "getStatus" },
      "*"
    );
    // Listen for the response (one-time)
    const handler = function (event) {
      if (
        event.source === window &&
        event.data &&
        event.data.source === "gogreen-page"
      ) {
        window.removeEventListener("message", handler);
        sendResponse({ ok: true, active: event.data.status === "active" });
      }
    };
    window.addEventListener("message", handler);
    return true; // keep sendResponse channel open for async
  }
  return true;
});

// ── Listen for status updates from inject.js ────────────────────
window.addEventListener("message", function (event) {
  if (event.source !== window) return;
  if (!event.data || event.data.source !== "gogreen-page") return;

  // Forward status to background service worker
  chrome.runtime.sendMessage({
    type: "statusUpdate",
    active: event.data.status === "active",
  }).catch(() => {});
});

// ── Auto-start if enabled ───────────────────────────────────────
(async () => {
  try {
    const data = await chrome.storage.local.get(["enabled", "interval"]);
    if (data.enabled) {
      // Small delay to ensure inject.js is loaded
      setTimeout(() => {
        window.postMessage(
          {
            source: "gogreen-extension",
            action: "start",
            interval: (data.interval || 60) * 1000,
          },
          "*"
        );
      }, 1000);
    }
  } catch (e) {
    // ignore
  }
})();

console.log("🟢 GoGreen content.js (isolated world) loaded");
