// Invented fixture: the accessible version of ../bad/garden.js.
document.querySelectorAll('.plot').forEach(function (plot) {
  plot.addEventListener('click', function () { plot.classList.toggle('selected'); });
  plot.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' || e.key === ' ') { plot.classList.toggle('selected'); }
  });
});

var closeX = document.querySelector('.dialog .dialog-close');
closeX.addEventListener('click', function () {
  document.getElementById('rules-dialog').hidden = true;
});

var frost = document.getElementById('frost-alerts');
function flipFrost() {
  var on = frost.classList.toggle('is-on');
  frost.setAttribute('aria-checked', on ? 'true' : 'false');
}
frost.addEventListener('click', flipFrost);
frost.addEventListener('keydown', function (e) { if (e.key === ' ') { flipFrost(); } });

var menuButton = document.getElementById('menu-button');
menuButton.addEventListener('click', function () {
  var menu = document.getElementById('plot-menu');
  menu.hidden = !menu.hidden;
  menuButton.setAttribute('aria-expanded', String(!menu.hidden));
});

var help = document.getElementById('rota-help');
var tip = document.getElementById('rota-tip');
help.addEventListener('mouseenter', function () { tip.hidden = false; });
help.addEventListener('focus', function () { tip.hidden = false; });
help.addEventListener('blur', function () { tip.hidden = true; });
document.addEventListener('keydown', function (e) { if (e.key === 'Escape') { tip.hidden = true; } });

var form = document.getElementById('apply-form');
form.addEventListener('submit', function (e) {
  var email = document.getElementById('holder-email');
  var err = document.getElementById('holder-email-error');
  if (!email.value) {
    e.preventDefault();
    email.setAttribute('aria-invalid', 'true');
    email.classList.add('input-error');
    err.textContent = 'Enter your email address, for example name@example.org';
    err.hidden = false;
  }
});
