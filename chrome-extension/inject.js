/**
 * GoGreen — MAIN World Content Script
 * Runs in the page's JavaScript context to override APIs that Teams uses
 * to detect user idle/tab visibility. This is the CORE of the extension.
 *
 * THREE LAYERS:
 *   1. Override Page Visibility API (document.hidden, visibilityState)
 *   2. Override Focus Detection (document.hasFocus, focus/blur events)
 *   3. Periodic DOM event simulation (mouse, keyboard, pointer)
 */

(function () {
  "use strict";

  let _active = false;
  let _intervalId = null;
  let _intervalMs = 60000;

  // ═══════════════════════════════════════════════════════════════
  //  LAYER 1 — PAGE VISIBILITY API OVERRIDE
  //  Teams web checks document.hidden & visibilityState to detect
  //  when the user switches tabs. We override these getters.
  // ═══════════════════════════════════════════════════════════════

  const _origHiddenDesc = Object.getOwnPropertyDescriptor(
    Document.prototype,
    "hidden"
  );
  const _origVisDesc = Object.getOwnPropertyDescriptor(
    Document.prototype,
    "visibilityState"
  );

  function applyVisibilityOverride() {
    Object.defineProperty(document, "hidden", {
      get() {
        return _active ? false : _origHiddenDesc.get.call(this);
      },
      configurable: true,
    });
    Object.defineProperty(document, "visibilityState", {
      get() {
        return _active ? "visible" : _origVisDesc.get.call(this);
      },
      configurable: true,
    });
  }

  // Block visibilitychange events at capture phase (runs FIRST)
  document.addEventListener(
    "visibilitychange",
    function (e) {
      if (_active) {
        e.stopImmediatePropagation();
      }
    },
    true
  );

  // ═══════════════════════════════════════════════════════════════
  //  LAYER 2 — FOCUS DETECTION OVERRIDE
  //  Teams may also check document.hasFocus() and listen for
  //  focus/blur events on the window.
  // ═══════════════════════════════════════════════════════════════

  const _origHasFocus = Document.prototype.hasFocus;
  Document.prototype.hasFocus = function () {
    return _active ? true : _origHasFocus.call(this);
  };

  // Block blur events on window when active
  window.addEventListener(
    "blur",
    function (e) {
      if (_active) {
        e.stopImmediatePropagation();
      }
    },
    true
  );

  // Override IdleDetector API if it exists
  if (typeof IdleDetector !== "undefined") {
    const _OrigIdle = IdleDetector;
    window.IdleDetector = class extends _OrigIdle {
      start(opts) {
        if (_active) return new Promise(() => {}); // never resolves
        return super.start(opts);
      }
    };
  }

  // ═══════════════════════════════════════════════════════════════
  //  LAYER 3 — PERIODIC DOM EVENT SIMULATION
  //  Dispatches synthetic mouse/keyboard/pointer events.
  //  Note: Event.isTrusted will be false, but combined with the
  //  visibility override above, this provides defense in depth.
  // ═══════════════════════════════════════════════════════════════

  function simulateActivity() {
    if (!_active) return;

    try {
      // Mouse move at random position
      document.dispatchEvent(
        new MouseEvent("mousemove", {
          bubbles: true,
          cancelable: true,
          clientX: 100 + Math.random() * 300,
          clientY: 100 + Math.random() * 300,
        })
      );
    } catch (e) {
      /* ignore */
    }

    try {
      // Shift key press (harmless)
      document.dispatchEvent(
        new KeyboardEvent("keydown", {
          bubbles: true,
          key: "Shift",
          keyCode: 16,
          which: 16,
        })
      );
      document.dispatchEvent(
        new KeyboardEvent("keyup", {
          bubbles: true,
          key: "Shift",
          keyCode: 16,
          which: 16,
        })
      );
    } catch (e) {
      /* ignore */
    }

    try {
      // Pointer event (touch/pen detection)
      document.dispatchEvent(
        new PointerEvent("pointermove", {
          bubbles: true,
          clientX: 150 + Math.random() * 100,
          clientY: 150 + Math.random() * 100,
        })
      );
    } catch (e) {
      /* ignore */
    }
  }

  // ═══════════════════════════════════════════════════════════════
  //  CONTROL
  // ═══════════════════════════════════════════════════════════════

  function start(interval) {
    _active = true;
    _intervalMs = interval || _intervalMs;
    applyVisibilityOverride();
    if (_intervalId) clearInterval(_intervalId);
    _intervalId = setInterval(simulateActivity, _intervalMs);
    simulateActivity();
    console.log(
      `🟢 GoGreen ACTIVE — interval: ${_intervalMs / 1000}s, ` +
        `visibility override: ON, focus override: ON`
    );
  }

  function stop() {
    _active = false;
    if (_intervalId) clearInterval(_intervalId);
    _intervalId = null;
    console.log("⏹ GoGreen STOPPED");
  }

  // ═══════════════════════════════════════════════════════════════
  //  MESSAGE BRIDGE — communicates with content.js (isolated world)
  //  via window.postMessage
  // ═══════════════════════════════════════════════════════════════

  window.addEventListener("message", function (event) {
    if (event.source !== window) return;
    if (!event.data || event.data.source !== "gogreen-extension") return;

    const msg = event.data;

    if (msg.action === "start") {
      start(msg.interval || 60000);
      window.postMessage(
        { source: "gogreen-page", status: "active" },
        "*"
      );
    } else if (msg.action === "stop") {
      stop();
      window.postMessage(
        { source: "gogreen-page", status: "inactive" },
        "*"
      );
    } else if (msg.action === "getStatus") {
      window.postMessage(
        { source: "gogreen-page", status: _active ? "active" : "inactive" },
        "*"
      );
    }
  });

  console.log("🟢 GoGreen inject.js loaded on", window.location.hostname);
})();
