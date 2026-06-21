document.addEventListener('DOMContentLoaded', function() {
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const mobileToggle = document.getElementById('mobile-toggle');
    const body = document.body;

    // Load saved preference
    const isCollapsed = localStorage.getItem('sidebar-collapsed') === 'true';
    if (isCollapsed && window.innerWidth >= 992) {
        body.classList.add('sidebar-collapsed');
    }

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            body.classList.toggle('sidebar-collapsed');
            localStorage.setItem('sidebar-collapsed', body.classList.contains('sidebar-collapsed'));
        });
    }

    if (mobileToggle) {
        mobileToggle.addEventListener('click', function(e) {
            e.stopPropagation();
            body.classList.toggle('sidebar-open');
        });
    }

    // Close mobile sidebar when clicking outside
    document.addEventListener('click', function(e) {
        if (body.classList.contains('sidebar-open')) {
            const sidebar = document.querySelector('.app-sidebar');
            if (sidebar && !sidebar.contains(e.target) && e.target !== mobileToggle) {
                body.classList.remove('sidebar-open');
            }
        }
    });
});
