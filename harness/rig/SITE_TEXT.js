// No layout reads: identical title/body text policy for every engine.
function rigTextReady(rule) {
  const norm = value => String(value || '').normalize('NFKC').replace(/\s+/g, ' ').trim().toLowerCase();
  return document.readyState !== 'loading' &&
    norm(document.title).includes(norm(rule.title)) &&
    norm(document.body?.textContent).includes(norm(rule.phrase));
}
