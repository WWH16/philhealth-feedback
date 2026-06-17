var selectedExperience = null;

var EXPERIENCE_BUTTONS = ['vsat', 'sat', 'unsat'];
var EXPERIENCE_SELECTED_CLASS = {
  vsat: 'sel-pos',
  sat: 'sel-neu',
  unsat: 'sel-neg'
};

function getCookie(name) {
  var value = '; ' + document.cookie;
  var parts = value.split('; ' + name + '=');
  if (parts.length === 2) return parts.pop().split(';').shift();
  return '';
}

function selectExperience(value) {
  selectedExperience = value;
  EXPERIENCE_BUTTONS.forEach(function (experience) {
    var b = document.getElementById('btn-' + experience);
    b.classList.remove('sel-pos', 'sel-neu', 'sel-neg');
    b.setAttribute('aria-pressed', 'false');
  });
  var btn = document.getElementById('btn-' + value);
  btn.classList.add(EXPERIENCE_SELECTED_CLASS[value]);
  btn.setAttribute('aria-pressed', 'true');
  document.getElementById('reactionErr').classList.add('hidden');
  document.getElementById('reactionErr').classList.remove('flex');
}

function updateCount() {
  var ta = document.getElementById('concern');
  document.getElementById('charCount').textContent = ta.value.length + ' / 500';
}

function handleSubmit(event) {
  if (!selectedExperience) {
    document.getElementById('reactionErr').classList.remove('hidden');
    document.getElementById('reactionErr').classList.add('flex');
    return;
  }
  var submitButton = event && event.currentTarget ? event.currentTarget : null;
  if (submitButton) {
    submitButton.disabled = true;
    submitButton.style.opacity = '0.7';
  }

  fetch(window.FEEDBACK_SUBMIT_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken'),
      'X-Requested-With': 'XMLHttpRequest'
    },
    body: JSON.stringify({
      experience: selectedExperience,
      comment: document.getElementById('concern').value
    })
  })
    .then(function (response) {
      return response.json().then(function (data) {
        if (!response.ok || !data.ok) throw new Error(data.error || 'Unable to submit feedback.');
        return data;
      });
    })
    .then(function (data) {
      document.getElementById('successDetailText').textContent = data.experience;
      document.getElementById('successMetaText').textContent =
        'Tracking code: ' + data.tracking_code + ' · Status: ' + data.status;
      document.getElementById('headerArea').style.display = 'none';
      document.getElementById('formArea').style.display = 'none';
      var sw = document.getElementById('successWrap');
      sw.classList.add('is-open');
      document.body.style.overflow = 'hidden';
    })
    .catch(function (err) {
      alert(err.message);
    })
    .finally(function () {
      if (submitButton) {
        submitButton.disabled = false;
        submitButton.style.opacity = '';
      }
    });
}

function resetForm() {
  selectedExperience = null;
  document.getElementById('concern').value = '';
  document.getElementById('charCount').textContent = '0 / 500';
  EXPERIENCE_BUTTONS.forEach(function (experience) {
    var b = document.getElementById('btn-' + experience);
    b.classList.remove('sel-pos', 'sel-neu', 'sel-neg');
    b.setAttribute('aria-pressed', 'false');
  });
  document.getElementById('reactionErr').classList.add('hidden');
  document.getElementById('reactionErr').classList.remove('flex');
  document.getElementById('headerArea').style.display = 'block';
  document.getElementById('formArea').style.display = 'block';
  document.getElementById('successWrap').classList.remove('is-open');
  document.getElementById('successMetaText').textContent = '—';
  document.body.style.overflow = '';
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function handleBackdropClick(event) {
  resetForm();
}
