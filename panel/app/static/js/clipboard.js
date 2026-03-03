// Copy link text to clipboard
function copyLink(elementId) {
    var el = document.getElementById(elementId);
    if (!el) return;
    var text = el.textContent || el.innerText;
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function() {
            showCopyFeedback(el);
        });
    } else {
        // Fallback
        var ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.left = '-9999px';
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        showCopyFeedback(el);
    }
}

function showCopyFeedback(el) {
    var orig = el.style.background;
    el.style.background = 'rgba(46,204,113,0.3)';
    setTimeout(function() { el.style.background = orig; }, 600);
}
