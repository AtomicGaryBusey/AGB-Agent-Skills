// Feedback form validation.
(function () {
  var form = document.getElementById('feedback-form');
  var email = document.getElementById('fb-email');
  var message = document.getElementById('fb-message');
  var thanks = document.getElementById('fb-thanks');

  function check(field, ok) {
    field.classList.toggle('is-invalid', !ok);
    field.setAttribute('aria-invalid', ok ? 'false' : 'true');
    return ok;
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var okEmail = check(email, /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email.value));
    var okMessage = check(message, message.value.trim().length > 0);
    if (okEmail && okMessage) {
      form.reset();
      thanks.textContent = 'Thank you. Your feedback has been sent.';
    }
  });
})();
