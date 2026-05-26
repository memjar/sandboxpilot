/*
 * keep.js · context capsule for keep.axetechnologies.ca
 *
 * Loaded by every page in The Keep. Builds window.SANDBOX_CONTEXT from the page
 * structure + the global manifest. Tells the pilot exactly where it lives.
 */
(async function () {
  // Auto-detect dev vs prod pilot endpoint
  if (!window.SANDBOXPILOT_ENDPOINT) {
    window.SANDBOXPILOT_ENDPOINT =
      location.hostname === "localhost" || location.hostname === "127.0.0.1"
        ? "http://localhost:8094"
        : "https://pilot.axe.onl";
  }

  const baseURL = location.origin;
  let manifest = null;
  try {
    const r = await fetch("/manifest.json");
    if (r.ok) manifest = await r.json();
  } catch (e) {}

  // Detect current artifact (if any) from path /r/<slug>/...
  const m = location.pathname.match(/^\/r\/([^/]+)/);
  const slug = m ? m[1] : null;
  const artifact = slug && manifest
    ? manifest.artifacts.find((a) => a.slug === slug) || null
    : null;

  // Compose page summary + related items
  let page_title = document.title;
  let page_summary, related = [];

  if (artifact) {
    page_summary = `${artifact.title} (${artifact.type}). ${artifact.summary} Knox sig ${artifact.knox.ed25519_sig.slice(0,16)}…, signed ${artifact.knox.signed_at}.`;
    related = (manifest.artifacts || [])
      .filter((a) => a.slug !== slug)
      .slice(0, 5)
      .map((a) => ({ title: a.title, url: `/r/${a.slug}/` }));
  } else if (location.pathname === "/" || location.pathname === "/index.html") {
    page_summary = `The Keep is AXE's design archive. ${manifest?.artifacts?.length || 0} artifact(s) currently indexed. Every entry is Ed25519-signed at archive time using key fingerprint ${manifest?.signing_key_fingerprint || '?'}.`;
    related = (manifest?.artifacts || []).slice(0, 5).map((a) => ({ title: a.title, url: `/r/${a.slug}/` }));
  } else if (location.pathname.endsWith("lineage.html") || location.pathname.endsWith("/lineage")) {
    page_summary = `This is the provenance page for ${artifact?.title || 'an artifact'}. It shows the cryptographic chain: sha256, Ed25519 signature, signing key fingerprint, signed timestamp, append-only version chain, and the source materials referenced when the design was produced.`;
  } else {
    page_summary = "A page on The Keep, AXE's Knox-attested design archive.";
  }

  window.SANDBOX_CONTEXT = {
    surface: "keep.axetechnologies.ca",
    surface_purpose: "AXE Design Archive · The Keep",
    audience: "internal · investor · auditor",
    page: {
      url: location.pathname,
      title: page_title,
      summary: page_summary,
      artifact_slug: slug,
      artifact_type: artifact?.type || null,
    },
    related,
    fleet_knowledge: {
      sibling_surfaces: [
        { name: "intel", url: "https://intel.axetechnologies.ca", purpose: "OSINT synthesis · Hercules-72B" },
        { name: "observer", url: "https://axe.observer", purpose: "Knox control plane" },
        { name: "arena", url: "https://arena.axe.onl", purpose: "model arena · LoRA-as-evolution" },
        { name: "marketing", url: "https://axetechnologies.ca", purpose: "AXE public site" },
      ],
      castle_pillars: ["echo", "crown", "atlas", "shield", "tower", "lens"],
    },
  };

  console.log("[sandboxpilot/keep] loaded:", window.SANDBOX_CONTEXT);
})();
