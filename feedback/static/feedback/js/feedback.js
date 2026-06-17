var selectedReaction = null;
var selectedCategory = null;
var lastTrackingCode = null;

function getCookie(name) {
  var value = '; ' + document.cookie;
  var parts = value.split('; ' + name + '=');
  if (parts.length === 2) return parts.pop().split(';').shift();
  return '';
}

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

function selectCategory(val) {
  if (selectedCategory === val) {
    selectedCategory = null;
    document.getElementById('cat-' + val).classList.remove('sel-cat');
  } else {
    ['complaint', 'suggestion', 'compliment', 'concern'].forEach(function (e) {
      var b = document.getElementById('cat-' + e);
      if (b) b.classList.remove('sel-cat');
    });
    selectedCategory = val;
    var btn = document.getElementById('cat-' + val);
    if (btn) btn.classList.add('sel-cat');
  }
}

function updateCount() {
  var ta = document.getElementById('concern');
  document.getElementById('charCount').textContent = ta.value.length + ' / 500';
}

function handleSubmit(event) {
  if (!selectedReaction) {
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
      rating: selectedReaction,
      category: selectedCategory,
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
      lastTrackingCode = data.tracking_code;
      document.getElementById('successDetailText').textContent = data.rating;
      document.getElementById('successTrackingCode').textContent = data.tracking_code;
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
  selectedReaction = null;
  selectedCategory = null;
  lastTrackingCode = null;
  document.getElementById('concern').value = '';
  document.getElementById('charCount').textContent = '0 / 500';
  ['pos', 'neu', 'neg'].forEach(function (e) {
    var b = document.getElementById('btn-' + e);
    b.classList.remove('sel-pos', 'sel-neu', 'sel-neg');
    b.setAttribute('aria-pressed', 'false');
  });
  ['complaint', 'suggestion', 'compliment', 'concern'].forEach(function (e) {
    var b = document.getElementById('cat-' + e);
    if (b) b.classList.remove('sel-cat');
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

function copyTrackingCode() {
  if (!lastTrackingCode) return;
  if (navigator.clipboard) {
    navigator.clipboard.writeText(lastTrackingCode);
  }
}

function lookupTrackingCode() {
  var input = document.getElementById('trackingCodeInput');
  var result = document.getElementById('trackResult');
  var code = input.value.trim().toUpperCase();
  result.className = 'track-result is-open';

  if (!code) {
    result.classList.add('is-error');
    result.textContent = 'Enter the tracking code shown after submission.';
    return;
  }

  var url = window.FEEDBACK_TRACK_URL_TEMPLATE.replace('TRACKING_CODE', encodeURIComponent(code));
  fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
    .then(function (response) {
      return response.json().then(function (data) {
        if (!response.ok || !data.ok) throw new Error('Tracking code not found.');
        return data;
      });
    })
    .then(function (data) {
      result.className = 'track-result is-open';
      result.innerHTML =
        '<strong>' + escapeHtml(data.tracking_code) + '</strong><br>' +
        'Status: <strong>' + escapeHtml(data.status) + '</strong><br>' +
        'Submitted: ' + escapeHtml(data.created_at) + '<br>' +
        'Last updated: ' + escapeHtml(data.updated_at);
    })
    .catch(function (err) {
      result.className = 'track-result is-open is-error';
      result.textContent = err.message;
    });
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
