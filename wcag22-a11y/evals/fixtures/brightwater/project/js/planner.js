// Trip planner: swap, locate, saved-trip reordering.
(function () {
  var from = document.getElementById('from');
  var to = document.getElementById('to');

  document.getElementById('swap').addEventListener('click', function () {
    var tmp = from.value;
    from.value = to.value;
    to.value = tmp;
  });

  document.getElementById('locate-me').addEventListener('click', function () {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(function () {
      from.value = 'Current location';
    });
  });

  // Saved trips: drag and drop, plus Move up / Move down buttons.
  var list = document.getElementById('saved-list');
  var status = document.getElementById('saved-status');
  var dragged = null;

  function announce(item) {
    var pos = Array.prototype.indexOf.call(list.children, item) + 1;
    status.textContent = item.dataset.name + ' moved to position ' + pos + ' of ' + list.children.length + '.';
  }

  list.addEventListener('dragstart', function (e) {
    dragged = e.target.closest('.saved');
    if (dragged) dragged.classList.add('is-dragging');
  });
  list.addEventListener('dragend', function () {
    if (dragged) dragged.classList.remove('is-dragging');
    dragged = null;
  });
  list.addEventListener('dragover', function (e) {
    e.preventDefault();
  });
  list.addEventListener('drop', function (e) {
    e.preventDefault();
    var target = e.target.closest('.saved');
    if (!dragged || !target || target === dragged) return;
    list.insertBefore(dragged, target);
    announce(dragged);
  });

  list.addEventListener('click', function (e) {
    var btn = e.target.closest('button[data-move]');
    if (!btn) return;
    var item = btn.closest('.saved');
    if (btn.dataset.move === 'up' && item.previousElementSibling) {
      list.insertBefore(item, item.previousElementSibling);
    } else if (btn.dataset.move === 'down' && item.nextElementSibling) {
      list.insertBefore(item.nextElementSibling, item);
    }
    btn.focus();
    announce(item);
  });
})();
