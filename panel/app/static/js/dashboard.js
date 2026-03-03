// Auto-refresh dashboard stats every 10 seconds
(function() {
    function refreshDashboard() {
        // Find all running campaign IDs by checking badge-running elements
        const rows = document.querySelectorAll('tbody tr');
        let totalCookies = 0;
        let totalSessions = 0;
        let pending = 0;

        rows.forEach(row => {
            const link = row.querySelector('td a');
            if (!link) return;
            const href = link.getAttribute('href');
            if (!href) return;
            const match = href.match(/\/campaigns\/(\d+)/);
            if (!match) return;
            const cid = match[1];
            const badge = row.querySelector('.badge-running');
            if (!badge) return;

            pending++;
            fetch('/api/campaigns/' + cid + '/status')
                .then(r => r.json())
                .then(data => {
                    totalCookies += data.cookie_count || 0;
                    totalSessions += data.session_count || 0;
                    pending--;
                    if (pending <= 0) {
                        const ce = document.getElementById('stat-cookies');
                        const se = document.getElementById('stat-sessions');
                        if (ce) ce.textContent = totalCookies;
                        if (se) se.textContent = totalSessions;
                    }
                })
                .catch(() => { pending--; });
        });

        if (pending === 0) {
            const ce = document.getElementById('stat-cookies');
            const se = document.getElementById('stat-sessions');
            if (ce) ce.textContent = '0';
            if (se) se.textContent = '0';
        }
    }

    refreshDashboard();
    setInterval(refreshDashboard, 10000);
})();
