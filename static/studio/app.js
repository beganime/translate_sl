document.querySelectorAll('input[type="file"]').forEach((input) => {
  input.addEventListener('change', () => {
    const label = input.closest('.dropzone')?.querySelector('[data-file-name]');
    if (label && input.files.length) label.textContent = input.files[0].name;
  });
});

document.querySelectorAll('[data-processing-form]').forEach((form) => {
  form.addEventListener('submit', (event) => {
    const button = event.submitter;
    if (!button || !button.matches('[data-submit-button]')) return;
    button.classList.add('is-loading');
    // Do not disable the submitter: disabled controls are omitted from the
    // submitted form and Django would lose action=regenerate.
    button.setAttribute('aria-disabled', 'true');
    const label = button.querySelector('span');
    if (label) label.textContent = 'Агент обрабатывает…';
  });
});

setTimeout(() => {
  document.querySelectorAll('.toast').forEach((toast) => toast.classList.add('is-hidden'));
}, 6000);
