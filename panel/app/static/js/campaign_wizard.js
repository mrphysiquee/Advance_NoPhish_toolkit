// Campaign creation wizard - step navigation and validation
let currentStep = 1;
const totalSteps = 4;

function wizardNext() {
    if (!validateStep(currentStep)) return;
    if (currentStep < totalSteps) {
        setStep(currentStep + 1);
    }
}

function wizardPrev() {
    if (currentStep > 1) {
        setStep(currentStep - 1);
    }
}

function setStep(step) {
    // Hide current panel
    document.querySelector('.wizard-panel[data-step="' + currentStep + '"]').classList.remove('active');
    document.querySelector('.wizard-step[data-step="' + currentStep + '"]').classList.remove('active');
    document.querySelector('.wizard-step[data-step="' + currentStep + '"]').classList.add('completed');

    currentStep = step;

    // Show new panel
    document.querySelector('.wizard-panel[data-step="' + currentStep + '"]').classList.add('active');
    document.querySelector('.wizard-step[data-step="' + currentStep + '"]').classList.add('active');
    document.querySelector('.wizard-step[data-step="' + currentStep + '"]').classList.remove('completed');

    // Update review if on step 4
    if (currentStep === 4) {
        updateReview();
    }
}

function validateStep(step) {
    if (step === 1) {
        const name = document.getElementById('name').value.trim();
        const domain = document.getElementById('domain').value.trim();
        const target = document.getElementById('target').value.trim();
        if (!name || !domain || !target) {
            alert('Please fill in all required fields.');
            return false;
        }
    }
    if (step === 2) {
        const ssl = document.getElementById('ssl').checked;
        if (ssl) {
            const cert = document.getElementById('cert_path').value.trim();
            const key = document.getElementById('key_path').value.trim();
            if (!cert || !key) {
                alert('SSL is enabled. Please provide certificate and key paths.');
                return false;
            }
        }
    }
    return true;
}

function updateReview() {
    const fields = [
        { label: 'Name', value: document.getElementById('name').value },
        { label: 'Domain', value: document.getElementById('domain').value },
        { label: 'Target', value: document.getElementById('target').value },
        { label: 'Users', value: document.getElementById('num_users').value },
        { label: 'Browser', value: document.getElementById('browser').options[document.getElementById('browser').selectedIndex].text },
        { label: 'SSL', value: document.getElementById('ssl').checked ? 'Yes' : 'No' },
        { label: 'Redirect', value: document.getElementById('redirect').checked ? 'Yes' : 'No' },
        { label: 'Export', value: document.getElementById('export_format').value },
    ];

    if (document.getElementById('ssl').checked) {
        fields.push({ label: 'Cert Path', value: document.getElementById('cert_path').value });
        fields.push({ label: 'Key Path', value: document.getElementById('key_path').value });
    }

    const ua = document.getElementById('useragent').value;
    if (ua) fields.push({ label: 'User Agent', value: ua });

    const param = document.getElementById('custom_param').value;
    if (param) fields.push({ label: 'URL Params', value: param });

    let html = '';
    fields.forEach(f => {
        html += '<div><strong>' + f.label + ':</strong> ' + f.value + '</div>';
    });
    document.getElementById('review-summary').innerHTML = html;
}

// Toggle SSL fields visibility
document.getElementById('ssl').addEventListener('change', function() {
    document.getElementById('ssl-fields').style.display = this.checked ? 'block' : 'none';
});
