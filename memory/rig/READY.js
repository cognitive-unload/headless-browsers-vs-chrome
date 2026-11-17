// Read-only readiness probe. Does not fix page layout or replace page content.
async function rigPaintReady() {
  if (document.readyState !== 'complete') return false;
  if (document.fonts) await document.fonts.ready;
  const visible = Array.from(document.images || []).filter(i => {
    const r = i.getBoundingClientRect();
    return r.bottom > 0 && r.right > 0 && r.top < innerHeight && r.left < innerWidth;
  });
  if (visible.some(i => !i.complete)) return false;
  await Promise.all(visible.filter(i => i.naturalWidth && i.decode).map(i => i.decode().catch(() => {})));
  await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
  return true;
}
