/*
 * Sandbox Pilot · embed.js
 *
 * Drop-in widget. Reads window.SANDBOX_CONTEXT to know where it lives,
 * then renders a floating chat bubble that streams from the configured
 * pilot endpoint.
 *
 *   <script src="https://your-pilot/widget/embed.js" defer></script>
 *
 * Optional:
 *   window.SANDBOXPILOT_ENDPOINT = "https://your-pilot";
 *   window.SANDBOXPILOT_BRAND    = { accent: "#D4AF37", name: "Acme" };
 */
(function () {
  if (window.__sandboxPilotLoaded) return;
  window.__sandboxPilotLoaded = true;

  const ENDPOINT = window.SANDBOXPILOT_ENDPOINT || "http://localhost:8094";
  const BRAND = window.SANDBOXPILOT_BRAND || {};
  const ACCENT = BRAND.accent || "#D4AF37";
  // Back-compat: accept legacy AXE_CONTEXT if set
  const CONTEXT = window.SANDBOX_CONTEXT || window.AXE_CONTEXT || {
    surface: location.host,
    surface_purpose: BRAND.name || "Sandbox Pilot",
    audience: "general",
    page: { url: location.pathname, title: document.title },
    related: [],
  };

  const css = `
    .sandboxpilot-bubble {
      position: fixed; bottom: 20px; right: 20px;
      width: 56px; height: 56px;
      background: ${ACCENT}; border: none; cursor: pointer;
      display: flex; align-items: center; justify-content: center;
      color: #000; font-family: 'IBM Plex Mono', monospace;
      font-size: 22px; font-weight: 600;
      z-index: 9998;
      transition: transform 180ms cubic-bezier(0.22,1,0.36,1);
      box-shadow: 0 4px 24px ${ACCENT}59;
    }
    .sandboxpilot-bubble:hover { transform: scale(1.06); }
    .sandboxpilot-bubble .sp-cube { width: 18px; height: 18px; background: #000; transform: rotate(45deg); }
    .sandboxpilot-panel {
      position: fixed; bottom: 88px; right: 20px;
      width: min(420px, calc(100vw - 40px));
      height: min(560px, calc(100vh - 140px));
      background: #0a0a0a; color: #f5f5f5;
      border: 1px solid rgba(255,255,255,0.08);
      border-top: 2px solid ${ACCENT};
      font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif;
      display: none; flex-direction: column;
      z-index: 9999;
      box-shadow: 0 12px 48px rgba(0,0,0,0.6);
    }
    .sandboxpilot-panel.open { display: flex; }
    .sandboxpilot-header { background: #171717; border-bottom: 1px solid rgba(255,255,255,0.08); padding: 14px 18px; display: flex; align-items: center; justify-content: space-between; }
    .sandboxpilot-header .sp-label { font-family: 'IBM Plex Mono', monospace; font-size: 10px; letter-spacing: 0.28em; text-transform: uppercase; color: ${ACCENT}; }
    .sandboxpilot-header .sp-title { font-size: 14px; font-weight: 500; margin-top: 4px; }
    .sandboxpilot-header .sp-close { background: transparent; color: #a3a3a3; border: none; font-size: 20px; cursor: pointer; line-height: 1; }
    .sandboxpilot-header .sp-close:hover { color: #fff; }
    .sandboxpilot-body { flex: 1; overflow-y: auto; padding: 18px; }
    .sandboxpilot-msg { margin-bottom: 14px; max-width: 90%; font-size: 14px; line-height: 1.5; }
    .sandboxpilot-msg.user { margin-left: auto; background: #171717; border: 1px solid rgba(255,255,255,0.08); padding: 10px 14px; color: #f5f5f5; }
    .sandboxpilot-msg.assistant { background: transparent; color: #e5e5e5; padding: 6px 0; border-left: 2px solid ${ACCENT}; padding-left: 12px; }
    .sandboxpilot-msg.system { color: #737373; font-family: 'IBM Plex Mono', monospace; font-size: 11px; padding: 6px 0; }
    .sandboxpilot-input { border-top: 1px solid rgba(255,255,255,0.08); padding: 12px; display: flex; gap: 8px; background: #171717; }
    .sandboxpilot-input input { flex: 1; background: #0a0a0a; border: 1px solid rgba(255,255,255,0.18); color: #f5f5f5; padding: 10px 14px; font-family: inherit; font-size: 14px; outline: none; }
    .sandboxpilot-input input:focus { border-color: ${ACCENT}; }
    .sandboxpilot-input button { background: ${ACCENT}; color: #000; border: none; padding: 10px 16px; font-family: 'IBM Plex Mono', monospace; font-size: 12px; font-weight: 600; cursor: pointer; letter-spacing: 0.04em; text-transform: uppercase; }
    .sandboxpilot-input button:disabled { background: #525252; color: #171717; cursor: not-allowed; }
    .sandboxpilot-foot { padding: 8px 14px; font-family: 'IBM Plex Mono', monospace; font-size: 10px; color: #525252; border-top: 1px solid rgba(255,255,255,0.04); letter-spacing: 0.04em; text-transform: uppercase; }
    .sp-cursor { display: inline-block; width: 8px; height: 14px; background: ${ACCENT}; vertical-align: text-bottom; animation: sp-blink 0.9s steps(2) infinite; }
    @keyframes sp-blink { 0%,100%{opacity:1} 50%{opacity:0} }
  `;
  const styleEl = document.createElement("style");
  styleEl.id = "sandboxpilot-css";
  styleEl.textContent = css;
  document.head.appendChild(styleEl);
  if (!document.querySelector('link[href*="Space+Grotesk"]')) {
    const f = document.createElement("link");
    f.rel = "stylesheet";
    f.href = "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500&family=IBM+Plex+Mono:wght@500;600&display=swap";
    document.head.appendChild(f);
  }

  const bubble = document.createElement("button");
  bubble.className = "sandboxpilot-bubble";
  bubble.setAttribute("aria-label", "Open Sandbox Pilot");
  bubble.innerHTML = '<div class="sp-cube"></div>';

  const panel = document.createElement("div");
  panel.className = "sandboxpilot-panel";
  panel.innerHTML = `
    <div class="sandboxpilot-header">
      <div>
        <div class="sp-label">Pilot · ${CONTEXT.surface || "sandbox"}</div>
        <div class="sp-title">${CONTEXT.surface_purpose || 'Ask the resident'}</div>
      </div>
      <button class="sp-close" aria-label="Close">×</button>
    </div>
    <div class="sandboxpilot-body" id="sp-body">
      <div class="sandboxpilot-msg system">Resident AI · context: ${CONTEXT.page?.title || location.pathname}</div>
      <div class="sandboxpilot-msg assistant">Ask me about this page, this surface, or what I can see. I'm grounded in the context you can see.</div>
    </div>
    <form class="sandboxpilot-input" id="sp-form">
      <input type="text" placeholder="Where am I?" autocomplete="off" id="sp-q">
      <button type="submit" id="sp-send">Send</button>
    </form>
    <div class="sandboxpilot-foot">sandboxpilot v0.1 · sandboxed · captured</div>
  `;
  document.body.appendChild(bubble);
  document.body.appendChild(panel);

  const body = panel.querySelector("#sp-body");
  const input = panel.querySelector("#sp-q");
  const send = panel.querySelector("#sp-send");
  const form = panel.querySelector("#sp-form");
  const closeBtn = panel.querySelector(".sp-close");

  bubble.addEventListener("click", () => {
    panel.classList.toggle("open");
    if (panel.classList.contains("open")) input.focus();
  });
  closeBtn.addEventListener("click", () => panel.classList.remove("open"));

  const messages = [];
  function appendMsg(role, text) {
    const div = document.createElement("div");
    div.className = "sandboxpilot-msg " + role;
    div.textContent = text;
    body.appendChild(div);
    body.scrollTop = body.scrollHeight;
    return div;
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const q = input.value.trim();
    if (!q) return;
    input.value = "";
    send.disabled = true;
    appendMsg("user", q);
    messages.push({ role: "user", content: q });
    const replyEl = appendMsg("assistant", "");
    const cursor = document.createElement("span");
    cursor.className = "sp-cursor";
    replyEl.appendChild(cursor);
    try {
      const resp = await fetch(`${ENDPOINT}/v1/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages, context: CONTEXT, stream: true }),
      });
      if (!resp.ok) {
        replyEl.textContent = "(blocked) " + (await resp.json()).message;
        send.disabled = false; return;
      }
      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "", answer = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";
        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const data = line.slice(6).trim();
          if (data === "[DONE]") continue;
          try {
            const obj = JSON.parse(data);
            const delta = obj.choices?.[0]?.delta?.content || "";
            if (delta) {
              answer += delta;
              replyEl.textContent = answer;
              replyEl.appendChild(cursor);
              body.scrollTop = body.scrollHeight;
            }
          } catch {}
        }
      }
      cursor.remove();
      messages.push({ role: "assistant", content: answer });
    } catch (err) {
      replyEl.textContent = "(error) " + err.message;
    } finally {
      send.disabled = false;
      input.focus();
    }
  });

  console.log("[sandboxpilot] loaded · context:", CONTEXT, "endpoint:", ENDPOINT);
})();
