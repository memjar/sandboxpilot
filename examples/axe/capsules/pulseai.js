/*
 * pulseai.js · context capsule for live.pulseai.my (Mike's IMI Live surface)
 *
 * Mike-audience: plain language, ≤120 word answers, no fleet jargon, no code
 * unless he asks. Captures route to bunker/external_interactions.jsonl (not
 * the AXE-internal training corpus).
 */
(function () {
  if (!window.SANDBOXPILOT_ENDPOINT) {
    window.SANDBOXPILOT_ENDPOINT =
      location.hostname === "localhost" || location.hostname === "127.0.0.1"
        ? "http://localhost:8094"
        : "https://pilot.axe.onl";
  }

  window.SANDBOXPILOT_BRAND = { accent: "#D4AF37", name: "AXE × IMI" };

  window.SANDBOX_CONTEXT = {
    surface: "live.pulseai.my",
    surface_purpose: "IMI Live · AXE's auditable AI for partners",
    audience: "mike",
    page: {
      url: location.pathname,
      title: document.title,
      summary: "Mike's IMI Live workspace. AXE's pilot is embedded here to answer questions about whatever Mike is reading. Mike values brevity and decision-relevance.",
    },
    related: [
      { title: "The Keep · AXE Design Archive", url: "https://keep.axetechnologies.ca/" },
      { title: "AXE Captain Roadmap (18mo)",     url: "https://keep.axetechnologies.ca/r/captain-roadmap-18mo/" },
    ],
  };
  console.log("[sandboxpilot/pulseai] mike-audience capsule loaded");
})();
