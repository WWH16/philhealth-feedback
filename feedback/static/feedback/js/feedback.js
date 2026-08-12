function getCookie(name) {
  var value = '; ' + document.cookie;
  var parts = value.split('; ' + name + '=');
  if (parts.length === 2) return parts.pop().split(';').shift();
  return '';
}

function updateDateTime() {
  var dtInput = document.getElementById('dateTime');
  if (dtInput && !dtInput.value) {
    var now = new Date();
    var year = now.getFullYear();
    var month = String(now.getMonth() + 1).padStart(2, '0');
    var day = String(now.getDate()).padStart(2, '0');
    var hours = String(now.getHours()).padStart(2, '0');
    var mins = String(now.getMinutes()).padStart(2, '0');
    dtInput.value = year + '-' + month + '-' + day + 'T' + hours + ':' + mins;
  }
}

function handleCC1Change(optionValue) {
  if (optionValue === 4) {
    // If option 4 (do not know CC), specification mandates answering "N/A" on CC2 (value 5) and CC3 (value 4)
    var cc2NA = document.querySelector('input[name="cc2"][value="5"]');
    if (cc2NA) cc2NA.checked = true;

    var cc3NA = document.querySelector('input[name="cc3"][value="4"]');
    if (cc3NA) cc3NA.checked = true;
  }
}

function handleSubmitCSM(event) {
  if (event) event.preventDefault();

  var privacyConsent = document.getElementById('privacyConsent');
  if (privacyConsent && !privacyConsent.checked) {
    alert('Please confirm your privacy consent before submitting.');
    return;
  }

  var btnSubmit = document.getElementById('btnSubmitCSM');
  if (btnSubmit && btnSubmit.disabled) {
    return; // Hardened against double-click double submission
  }

  var submitIcon = document.getElementById('submitIcon');
  var submitText = document.getElementById('submitText');

  if (btnSubmit) {
    btnSubmit.disabled = true;
    btnSubmit.style.opacity = '0.75';
    btnSubmit.style.cursor = 'not-allowed';
  }
  if (submitIcon) {
    submitIcon.textContent = 'sync';
    submitIcon.classList.add('animate-spin');
  }
  if (submitText) {
    submitText.textContent = 'Submitting CSM...';
  }

  // Submission handling with safety delay
  setTimeout(function () {
    var today = new Date().toISOString().slice(0, 10).replace(/-/g, '');
    var randomHex = Math.floor(Math.random() * 16777215).toString(16).toUpperCase().padStart(6, '0');
    var trackingCode = 'CSM-' + today + '-' + randomHex;

    var detailEl = document.getElementById('successDetailText');
    if (detailEl) detailEl.textContent = 'PhilHealth LHIO Cauayan City';

    var metaEl = document.getElementById('successMetaText');
    if (metaEl) metaEl.textContent = 'Tracking ID: ' + trackingCode + ' · Recorded: Just now';

    var sw = document.getElementById('successWrap');
    if (sw) {
      sw.classList.add('is-open');
    }
    document.body.style.overflow = 'hidden';

    if (btnSubmit) {
      btnSubmit.disabled = false;
      btnSubmit.style.opacity = '';
      btnSubmit.style.cursor = '';
    }
    if (submitIcon) {
      submitIcon.textContent = 'send';
      submitIcon.classList.remove('animate-spin');
    }
    if (submitText) {
      submitText.textContent = 'Submit CSM Form';
    }
  }, 500);
}

function resetCSMForm() {
  var form = document.getElementById('csmForm');
  if (form) form.reset();

  updateDateTime();

  var sw = document.getElementById('successWrap');
  if (sw) sw.classList.remove('is-open');

  document.body.style.overflow = '';
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function handleBackdropClick(event) {
  resetCSMForm();
}

document.addEventListener('DOMContentLoaded', function () {
  updateDateTime();
});

document.addEventListener('keydown', function (event) {
  if (event.key === 'Escape') {
    var sw = document.getElementById('successWrap');
    if (sw && sw.classList.contains('is-open')) {
      resetCSMForm();
    }
  }
});
