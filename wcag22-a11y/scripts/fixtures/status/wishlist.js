// Invented fixture: writes status text after form submissions.
const feedback = document.getElementById('wish-feedback');
const items = document.querySelector('#wish-items');
document.getElementById('wish-form').addEventListener('submit', function (e) {
  e.preventDefault();
  const li = document.createElement('li');
  li.textContent = document.getElementById('seed').value;
  items.appendChild(li);
  feedback.textContent = 'Added ' + li.textContent + ' to your wishlist.';
});
document.getElementById('news-form').addEventListener('submit', function (e) {
  e.preventDefault();
  document.getElementById('news-result').textContent = 'Thanks, you are subscribed.';
});
