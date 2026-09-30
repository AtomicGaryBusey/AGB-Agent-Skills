// Route map widget.
(function () {
  var svg = document.getElementById('route-map');
  var body = document.getElementById('stop-panel-body');
  var stops = {
    market: { name: 'Market Square', lines: 'Harbour Line, Route 14', stepFree: 'Platform 1 only' },
    keel: { name: 'Keel Street', lines: 'Harbour Line', stepFree: 'Yes' },
    saltmarsh: { name: 'Saltmarsh', lines: 'Harbour Line', stepFree: 'Yes' },
    ferry: { name: 'Ferry Terminal', lines: 'Harbour Line, ferries', stepFree: 'Platform B elevator closed weekday mornings' },
    pier3: { name: 'Pier 3', lines: 'Harbour Line', stepFree: 'Yes' },
    anchor: { name: 'Anchor Lane', lines: 'Route 14 (temporary stop)', stepFree: 'Yes' },
    dock: { name: 'Dock Road', lines: 'Route 14 (closed until 12 October)', stepFree: 'Yes' }
  };

  svg.querySelectorAll('.stop').forEach(function (g) {
    g.addEventListener('click', function () {
      var s = stops[g.dataset.stop];
      body.innerHTML = '<h3>' + s.name + '</h3><p>Lines: ' + s.lines + '</p><p>Step-free access: ' + s.stepFree + '</p>';
    });
  });

  // Zoom by adjusting the viewBox (1x to 2x).
  var scale = 1;
  function apply() {
    var w = 600 / scale, h = 360 / scale;
    svg.setAttribute('viewBox', ((600 - w) / 2) + ' ' + ((360 - h) / 2) + ' ' + w + ' ' + h);
  }
  document.getElementById('zoom-in').addEventListener('click', function () { scale = Math.min(2, scale + 0.25); apply(); });
  document.getElementById('zoom-out').addEventListener('click', function () { scale = Math.max(1, scale - 0.25); apply(); });
})();
