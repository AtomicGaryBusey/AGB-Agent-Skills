// Claim step 3: enable submit once the confirmation box is ticked.
(function () {
  var confirmBox = document.getElementById('c3-confirm');
  var submit = document.getElementById('c3-submit');
  confirmBox.addEventListener('change', function () {
    submit.disabled = !confirmBox.checked;
  });
})();
