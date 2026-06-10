var selectedReaction = null;

function selectReaction(val) {
  selectedReaction = val;
  ['pos', 'neu', 'neg'].forEach(function (e) {
    var b = document.getElementById('btn-' + e);
    b.classList.remove('sel-pos', 'sel-neu', 'sel-neg');
    b.setAttribute('aria-pressed', 'false');
  });
  var btn = document.getElementById('btn-' + val);
  btn.classList.add('sel-' + val);
  btn.setAttribute('aria-pressed', 'true');
  document.getElementById('reactionErr').classList.add('hidden');
  document.getElementById('reactionErr').classList.remove('flex');
}

function updateCount() {
  var ta = document.getElementById('concern');
  document.getElementById('charCount').textContent = ta.value.length + ' / 500';
}

function handleSubmit() {
  if (!selectedReaction) {
    document.getElementById('reactionErr').classList.remove('hidden');
    document.getElementById('reactionErr').classList.add('flex');
    return;
  }
  var labels = { pos: 'Very satisfactory', neu: 'Satisfactory', neg: 'Unsatisfactory' };
  document.getElementById('successDetailText').textContent = labels[selectedReaction];
  document.getElementById('headerArea').style.display = 'none';
  document.getElementById('formArea').style.display = 'none';
  var sw = document.getElementById('successWrap');
  sw.classList.add('is-open');
  document.body.style.overflow = 'hidden';
}

function resetForm() {
  selectedReaction = null;
  document.getElementById('concern').value = '';
  document.getElementById('charCount').textContent = '0 / 500';
  ['pos', 'neu', 'neg'].forEach(function (e) {
    var b = document.getElementById('btn-' + e);
    b.classList.remove('sel-pos', 'sel-neu', 'sel-neg');
    b.setAttribute('aria-pressed', 'false');
  });
  document.getElementById('reactionErr').classList.add('hidden');
  document.getElementById('reactionErr').classList.remove('flex');
  document.getElementById('headerArea').style.display = 'block';
  document.getElementById('formArea').style.display = 'block';
  document.getElementById('successWrap').classList.remove('is-open');
  document.body.style.overflow = '';
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function handleBackdropClick(event) {
  resetForm();
}