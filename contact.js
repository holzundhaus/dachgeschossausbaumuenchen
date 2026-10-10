const origins = new Set(["https://holzundhaus.github.io"]);
const originConfirmed = false;
document.querySelectorAll('form[data-contact]').forEach(form => {
  const button = form.querySelector('button[type="submit"]');
  const status = form.querySelector('[role="status"]');
  let pending = false;
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (!originConfirmed) { status.textContent = "Der Versand ist noch nicht freigeschaltet."; return; }
    if (pending || !form.reportValidity()) return;
    if (form.elements.url.value) { status.textContent = 'Die Anfrage konnte nicht übermittelt werden.'; return; }
    if (!origins.has(window.location.origin)) { status.textContent = 'Dies ist eine Vorschau. Ihre Anfrage wird hier nicht versendet; Ihre Eingaben bleiben erhalten.'; return; }
    pending = true; button.disabled = true; form.setAttribute('aria-busy', 'true');
    status.textContent = 'Ihre Anfrage wird übermittelt …';
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 15000);
    try {
      const response = await fetch('https://odoo.saatpilot.de/contact', {
        method: 'POST', headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: new URLSearchParams(new FormData(form)), signal: controller.signal
      });
      const result = await response.json();
      if (!response.ok || result?.ok !== true) throw new Error('unconfirmed');
      form.reset(); status.textContent = 'Ihre Anfrage wurde übermittelt.';
    } catch { status.textContent = 'Die Übermittlung wurde nicht bestätigt. Ihre Eingaben bleiben erhalten. Bitte versuchen Sie es später erneut.'; }
    finally { clearTimeout(timer); pending = false; button.disabled = !originConfirmed; form.removeAttribute('aria-busy'); }
  });
  button.disabled = !originConfirmed;
});
