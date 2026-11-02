// Keep the bundled host alive while either learning mode is open.
export function keepWindowsRuntimeAlive() {
  if (window.QihangNative?.oralCall || location.hostname !== '127.0.0.1' || !['5188','5194'].includes(location.port)) return () => {};
  let stopped = false, pending = false, controller;
  async function ping() {
    if (stopped || pending) return;
    pending = true;
    controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 8000);
    try {
      await fetch('/oral-api', {
        method: 'POST', credentials: 'same-origin', signal: controller.signal,
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({method: 'heartbeat', args: {}}),
      });
    } catch {} finally { clearTimeout(timeout); pending = false; }
  }
  ping();
  const timer = setInterval(ping, 20000);
  document.addEventListener('visibilitychange', ping);
  return () => { stopped = true; clearInterval(timer); controller?.abort(); document.removeEventListener('visibilitychange', ping); };
}
