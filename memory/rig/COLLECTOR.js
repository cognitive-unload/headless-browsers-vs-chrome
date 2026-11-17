// Appended to the pinned testharness.js in the disposable test tree.
// Registers before test scripts execute. Original assertions are unmodified.
add_completion_callback((tests, status) => {
  window.__rigWpt = {
    complete: true,
    harness: {status: status.status, message: status.message || null},
    tests: tests.map(t => ({name: t.name, status: t.status,
      message: t.message || null, stack: t.stack || null}))
  };
});
