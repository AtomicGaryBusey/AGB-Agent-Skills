// Invented fixture: listeners attached in an external file.
var season = document.getElementById('season');
season.addEventListener('change', function () {
  window.location.href = '/plots?season=' + season.value;
});

document.querySelectorAll('.plot').forEach(function (plot) {
  plot.addEventListener('click', function () { plot.classList.toggle('selected'); });
});
document.getElementById('water-point').onclick = function () { showWater(); };
function showWater() { document.getElementById('rules-dialog').hidden = false; }

var closeX = document.querySelector('.dialog .dialog-close');
closeX.addEventListener('click', function () {
  document.getElementById('rules-dialog').hidden = true;
});

var frost = document.getElementById('frost-alerts');
frost.addEventListener('click', function () { frost.classList.toggle('is-on'); });
frost.addEventListener('keydown', function (e) {
  if (e.key === ' ') { frost.classList.toggle('is-on'); }
});

var menuButton = document.getElementById('menu-button');
menuButton.addEventListener('click', function () {
  var menu = document.getElementById('plot-menu');
  menu.hidden = !menu.hidden;
});

var help = document.getElementById('rota-help');
help.addEventListener('mouseenter', showTip);
help.addEventListener('focus', showTip);
help.addEventListener('mouseleave', hideTip);
help.addEventListener('blur', hideTip);
function showTip() { document.getElementById('rota-tip').hidden = false; }
function hideTip() { document.getElementById('rota-tip').hidden = true; }

var form = document.getElementById('apply-form');
form.addEventListener('submit', function (e) {
  var email = document.getElementById('holder-email');
  if (!email.value) {
    e.preventDefault();
    email.setAttribute('aria-invalid', 'true');
    email.classList.add('input-error');
  }
});
