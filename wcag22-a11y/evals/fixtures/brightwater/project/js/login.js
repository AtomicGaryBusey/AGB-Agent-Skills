// Sign in, then one-time code.
(function () {
  var form = document.getElementById('login-form');
  var twofa = document.getElementById('twofa');
  var pw = document.getElementById('pw');
  var digits = Array.prototype.slice.call(document.querySelectorAll('.otp-digit'));

  function blockPaste(e) {
    // Security team request: credentials and codes must be typed.
    e.preventDefault();
  }
  pw.addEventListener('paste', blockPaste);

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    form.hidden = true;
    twofa.hidden = false;
    digits[0].focus();
  });

  digits.forEach(function (input, i) {
    input.addEventListener('paste', blockPaste);
    input.addEventListener('input', function () {
      input.value = input.value.replace(/\D/g, '').slice(0, 1);
      if (input.value && digits[i + 1]) digits[i + 1].focus();
    });
    input.addEventListener('keydown', function (e) {
      if (e.key === 'Backspace' && !input.value && digits[i - 1]) digits[i - 1].focus();
    });
  });

  document.getElementById('verify').addEventListener('click', function () {
    window.location.href = 'index.html';
  });
})();
