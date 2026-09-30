/* Larkspur Library - page behaviour (no build step, no dependencies) */
(function () {
  'use strict';

  var page = document.body.getAttribute('data-page');

  /* ---------- home: "What's new" carousel ---------- */
  function initCarousel() {
    var root = document.getElementById('whats-new');
    if (!root) return;
    var track = root.querySelector('.carousel-track');
    var count = track.children.length;
    var index = 0;
    setInterval(function () {
      index = (index + 1) % count;
      track.style.transform = 'translateX(' + (-100 * index) + '%)';
    }, 4000);
  }

  /* ---------- catalog: sort toggle ---------- */
  function initSort() {
    var toggle = document.getElementById('sort-toggle');
    if (!toggle) return;
    function flip() {
      toggle.textContent = toggle.textContent.indexOf('A') === 6 ? 'Title Z–A' : 'Title A–Z';
      var list = document.querySelector('.results');
      var items = Array.prototype.slice.call(list.children).reverse();
      items.forEach(function (li) { list.appendChild(li); });
    }
    toggle.addEventListener('click', flip);
    toggle.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); flip(); }
    });
  }

  /* ---------- catalog: add to reading list ---------- */
  window.addToList = function (el) {
    var title = el.getAttribute('data-title');
    var li = document.createElement('li');
    li.setAttribute('draggable', 'true');
    li.textContent = title;
    document.getElementById('reading-list').appendChild(li);
    bindDrag(li);
    document.getElementById('list-status').textContent = 'Added “' + title + '” to your reading list.';
  };

  /* ---------- catalog: reading list reordering ---------- */
  var dragged = null;
  function bindDrag(li) {
    li.addEventListener('dragstart', function () { dragged = li; });
    li.addEventListener('dragover', function (e) { e.preventDefault(); });
    li.addEventListener('drop', function (e) {
      e.preventDefault();
      if (!dragged || dragged === li) return;
      var list = li.parentNode;
      var rect = li.getBoundingClientRect();
      var after = e.clientY > rect.top + rect.height / 2;
      list.insertBefore(dragged, after ? li.nextSibling : li);
    });
  }
  function initReadingList() {
    var list = document.getElementById('reading-list');
    if (!list) return;
    Array.prototype.forEach.call(list.children, bindDrag);
  }

  /* ---------- events: reservation modal ---------- */
  var modal = null;
  function openModal(eventName) {
    modal = document.getElementById('register-modal');
    document.getElementById('modal-event').textContent = eventName;
    modal.hidden = false;
    document.getElementById('res-name').focus();
  }
  window.closeModal = function () {
    if (modal) modal.hidden = true;
  };
  function initModal() {
    var buttons = document.querySelectorAll('[data-event]');
    Array.prototype.forEach.call(buttons, function (b) {
      b.addEventListener('click', function () { openModal(b.getAttribute('data-event')); });
    });
    document.addEventListener('keydown', function (e) {
      if (!modal || modal.hidden) return;
      if (e.key === 'Tab') {
        e.preventDefault();
        document.getElementById('res-name').focus();
      }
      if (e.key === 'Escape') {
        e.preventDefault();
      }
    });
  }

  /* ---------- signup: two-step form ---------- */
  function initSignup() {
    var next = document.getElementById('to-step-2');
    if (!next) return;
    next.addEventListener('click', function () {
      var fields = document.querySelectorAll('#step-1 input[required]');
      var ok = true;
      Array.prototype.forEach.call(fields, function (f) {
        if (!f.value.trim()) { f.classList.add('invalid'); ok = false; }
        else { f.classList.remove('invalid'); }
      });
      if (!ok) return;
      document.getElementById('step-1').hidden = true;
      document.getElementById('step-2').hidden = false;
      document.getElementById('card-email').focus();
    });
  }

  /* ---------- login: audio CAPTCHA alternative ---------- */
  function initCaptcha() {
    var audio = document.getElementById('captcha-audio');
    if (!audio) return;
    audio.addEventListener('click', function () {
      document.getElementById('audio-instructions').hidden = false;
    });
  }

  if (page === 'home') initCarousel();
  if (page === 'catalog') { initSort(); initReadingList(); }
  if (page === 'events') initModal();
  if (page === 'signup') initSignup();
  if (page === 'login') initCaptcha();
})();
