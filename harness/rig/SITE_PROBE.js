// Observation only. The existing READY.js decides success, unchanged in R6.
function rigSiteProbe(pageCondition, legacyClauses = []) {
  let pageReady = false, pageError = null;
  try { pageReady = !!pageCondition(); } catch (e) { pageError = String(e); }
  const visible = Array.from(document.images || []).filter(i => {
    const r = i.getBoundingClientRect();
    return r.bottom > 0 && r.right > 0 && r.top < innerHeight && r.left < innerWidth;
  });
  return {
    pageReady, pageError,
    legacyClauses: legacyClauses.map(c => {
      try { return {label: c.label, value: !!c.check()}; }
      catch (e) { return {label: c.label, error: String(e)}; }
    }),
    paint: {documentComplete: document.readyState === 'complete',
      readyState: document.readyState, fontsStatus: document.fonts ? document.fonts.status : 'unavailable',
      visibleImages: visible.length, pendingVisibleImages: visible.filter(i => !i.complete).length,
      pendingResources: visible.filter(i => !i.complete).map(i => ({src: i.currentSrc || i.src || '', complete: i.complete}))},
    url: location.href, title: document.title
  };
}
