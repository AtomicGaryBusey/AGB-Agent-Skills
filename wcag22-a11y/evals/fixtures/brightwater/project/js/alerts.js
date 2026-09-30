// Service alerts: rotating banner, notification switch, refresh, email modal.
(function () {
  // ---- Rotating banner ----
  var messages = [
    'Harbour Line: trains running normally.',
    'Route 14: detour on Keel Street until 12 October.',
    'Ferry Terminal: platform B elevator closed weekday mornings.'
  ];
  var index = 0;
  var banner = document.getElementById('live-banner');
  var bannerText = document.getElementById('live-banner-text');
  function show(i) {
    index = (i + messages.length) % messages.length;
    bannerText.textContent = messages[index];
  }
  var timer = setInterval(function () { show(index + 1); }, 20000);
  document.getElementById('banner-prev').addEventListener('click', function () { show(index - 1); });
  document.getElementById('banner-next').addEventListener('click', function () { show(index + 1); });
  document.getElementById('banner-dismiss').addEventListener('click', function () {
    clearInterval(timer);
    banner.hidden = true;
  });

  // ---- Notification switch ----
  var sw = document.getElementById('notify-switch');
  function toggle() {
    sw.classList.toggle('is-on');
  }
  sw.addEventListener('click', toggle);
  sw.addEventListener('keydown', function (e) {
    if (e.key === ' ' || e.key === 'Enter') {
      e.preventDefault();
      toggle();
    }
  });

  // ---- Refresh ----
  var refreshResult = document.getElementById('refresh-result');
  document.getElementById('refresh-alerts').addEventListener('click', function () {
    refreshResult.textContent = 'Checking...';
    setTimeout(function () {
      var now = new Date();
      var hh = String(now.getHours()).padStart(2, '0');
      var mm = String(now.getMinutes()).padStart(2, '0');
      refreshResult.textContent = 'Updated at ' + hh + ':' + mm + '. No new alerts.';
    }, 800);
  });

  // ---- Email alerts modal (custom) ----
  var modal = document.getElementById('email-modal');
  var emailInput = document.getElementById('alert-email');
  var subscribe = document.getElementById('alert-subscribe');
  var msg = document.getElementById('alert-subscribe-msg');

  document.getElementById('open-email-modal').addEventListener('click', function () {
    modal.hidden = false;
    emailInput.focus();
  });

  function closeModal() {
    modal.hidden = true;
    document.getElementById('open-email-modal').focus();
  }
  document.getElementById('email-modal-close').addEventListener('click', closeModal);
  modal.addEventListener('click', function (e) {
    if (e.target === modal) closeModal();
  });

  subscribe.addEventListener('click', function () {
    msg.textContent = emailInput.value ? 'Thanks. Check your inbox to confirm.' : 'Enter an email address.';
  });

  // Keep keyboard focus inside the modal.
  modal.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      e.preventDefault(); // avoid losing a half-typed address
      return;
    }
    if (e.key !== 'Tab') return;
    e.preventDefault();
    if (document.activeElement === emailInput) {
      subscribe.focus();
    } else {
      emailInput.focus();
    }
  });
})();
