/* site.js · context capsule for axetechnologies.ca (production marketing) */
(function () {
  window.SANDBOX_CONTEXT = {
    surface: "axetechnologies.ca",
    surface_purpose: "AXE Technologies · public site",
    audience: "public · prospect · regulator",
    page: {
      url: location.pathname,
      title: document.title,
      summary: "A page on the AXE Technologies public website. AXE is a Canadian AI company that builds auditable, on-prem AI fleets. The CASTLE platform is the productized stack.",
    },
    related: [
      { title: "The Keep · Design Archive", url: "https://keep.axetechnologies.ca/" },
      { title: "Intel · OSINT synthesis",   url: "https://intel.axetechnologies.ca/" },
    ],
    fleet_knowledge: {
      castle_pillars: ["echo", "crown", "atlas", "shield", "tower", "lens"],
    },
  };
})();
