// Fares: jump straight to the chosen zone's fare sheet.
(function () {
  var select = document.getElementById('zone-select');
  var params = new URLSearchParams(window.location.search);
  if (params.get('zone')) select.value = params.get('zone');

  select.addEventListener('change', function () {
    window.location.href = 'fares.html?zone=' + encodeURIComponent(select.value);
  });
})();
