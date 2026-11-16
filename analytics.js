/* Visitor analytics (Umami Cloud: cookie-free, no consent banner needed).
   To turn it on: paste the website ID from cloud.umami.is below. Until then nothing is loaded or sent.
   Tracking only runs on the public domain, so local previews never count.

   What is recorded (anonymous; no names, no cookies):
   - page views, referrer, country, device (Umami's defaults)
   - cv-download, contact-email, project-open (+ which project), outbound links
   - every button / toggle press and slider change on the interactive pages (page + label)
   - theme switch, scroll depth (50% / 90%), and ?ref=<tag> campaign tags from application links */
(function () {
  var WEBSITE_ID = 'bc6a171b-b82e-48d0-89bc-6b86477f5efc';   // Umami Cloud (EU), site "Daniele Re portfolio"
  var DOMAIN = 'danielere.github.io';
  var page = (location.pathname.split('/').pop() || 'index.html').replace('.html', '') || 'index';
  var queue = [];
  function track(name, data) {
    if (window.umami && typeof umami.track === 'function') umami.track(name, data);
    else queue.push([name, data]);
  }
  window.drTrack = track;
  if (WEBSITE_ID && location.hostname === DOMAIN) {
    var s = document.createElement('script');
    s.defer = true; s.src = 'https://cloud.umami.is/script.js';
    s.setAttribute('data-website-id', WEBSITE_ID);
    s.setAttribute('data-domains', DOMAIN);
    s.onload = function () { queue.splice(0).forEach(function (e) { umami.track(e[0], e[1]); }); };
    document.head.appendChild(s);
  }
  // campaign tag: danielere.github.io/?ref=dsgai -> event "ref" {tag: "dsgai"}; remembered for the visit
  try {
    var ref = new URLSearchParams(location.search).get('ref');
    if (ref) { sessionStorage.setItem('dr-ref', ref); track('ref', { tag: ref, page: page }); }
  } catch (e) {}
  function label(el) { return (el.getAttribute('aria-label') || el.textContent || el.value || '').trim().replace(/\s+/g, ' ').slice(0, 60); }
  document.addEventListener('click', function (ev) {
    var el = ev.target.closest('a, button, [role="link"], .proj.linked');
    if (!el) return;
    var ref = null; try { ref = sessionStorage.getItem('dr-ref'); } catch (e) {}
    var extra = ref ? { ref: ref } : {};
    var href = el.getAttribute('href') || el.dataset.href || '';
    if (/\.pdf($|\?)/i.test(href)) return track('cv-download', Object.assign({ page: page }, extra));
    if (/^mailto:/i.test(href)) return track('contact-email', Object.assign({ page: page }, extra));
    if (el.classList.contains('proj')) return track('project-open', Object.assign({ project: label(el.querySelector('h3') || el) }, extra));
    if (/^https?:/i.test(href) && href.indexOf(location.host) < 0) return track('outbound', { url: href.slice(0, 120), page: page });
    if (el.tagName === 'BUTTON') return track('ui', { page: page, control: label(el) });
  }, true);
  document.addEventListener('change', function (ev) {
    var el = ev.target;
    if (el.matches && el.matches('input[type=range], select')) track('ui', { page: page, control: (el.id || el.name || 'slider') + '=' + el.value });
  }, true);
  // scroll depth, once per page view
  var marks = { 50: false, 90: false };
  addEventListener('scroll', function () {
    var h = document.documentElement, p = (h.scrollTop + innerHeight) / h.scrollHeight * 100;
    [50, 90].forEach(function (m) { if (!marks[m] && p >= m) { marks[m] = true; track('scroll', { page: page, depth: m }); } });
  }, { passive: true });
})();
