/* observer.js · context capsule for axe.observer */
(function () {
  window.SANDBOX_CONTEXT = {
    surface: "axe.observer",
    surface_purpose: "AXE Observer · Knox control plane",
    audience: "operator · auditor",
    page: { url: location.pathname, title: document.title,
            summary: "axe.observer is the Knox attestation control plane: where Ed25519 lineage chains are queried, verified, and audited across all AXE artifacts." },
    related: [],
    fleet_knowledge: { castle_pillars: ["shield", "atlas"] },
  };
})();
