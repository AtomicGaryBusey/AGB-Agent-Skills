// Home page: rider survey dialog (native <dialog>).
(function () {
  var opener = document.getElementById('open-survey');
  var dialog = document.getElementById('survey-dialog');
  if (!opener || !dialog) return;
  opener.addEventListener('click', function () {
    dialog.showModal();
  });
  dialog.addEventListener('close', function () {
    opener.focus();
  });
})();
