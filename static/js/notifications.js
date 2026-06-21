document.addEventListener('DOMContentLoaded', function() {
    const unreadBadge = document.getElementById('unread-badge');
    const notifDropdownList = document.getElementById('notification-dropdown-list');
    const bellIcon = document.getElementById('notification-bell');

    if (!unreadBadge) return; // Not logged in or view components not loaded

    // ── Determine correct notification base URL from current path ──
    // Each panel has its own notification routes:
    //   /panel/admin/notifications/
    //   /panel/teacher/notifications/
    //   /panel/accounts/notifications/
    //   /panel/registrar/notifications/
    //   /portal/student/notifications/
    //   /portal/guardian/notifications/
    function getNotificationBaseUrl() {
        const path = window.location.pathname;
        if (path.startsWith('/panel/admin/'))      return '/panel/admin/notifications/';
        if (path.startsWith('/panel/teacher/'))     return '/panel/teacher/notifications/';
        if (path.startsWith('/panel/accounts/'))    return '/panel/accounts/notifications/';
        if (path.startsWith('/panel/registrar/'))   return '/panel/registrar/notifications/';
        if (path.startsWith('/portal/student/'))    return '/portal/student/notifications/';
        if (path.startsWith('/portal/guardian/'))   return '/portal/guardian/notifications/';
        // Fallback: admin (superuser/principal also use admin panel)
        return '/panel/admin/notifications/';
    }

    const NOTIF_BASE = getNotificationBaseUrl();

    // Get cookie helper for Django CSRF
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    const csrftoken = getCookie('csrftoken');

    function fetchNotifications() {
        // Fetch unread count from the role-appropriate panel
        fetch(NOTIF_BASE + 'unread-count/', {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) {
                // Not all panels expose unread-count — gracefully degrade
                unreadBadge.style.display = 'none';
                return null;
            }
            return response.json();
        })
        .then(data => {
            if (!data) return;
            const count = data.unread_count || 0;
            if (count > 0) {
                unreadBadge.textContent = count;
                unreadBadge.style.display = 'inline-block';
                unreadBadge.classList.add('pulse-badge');
            } else {
                unreadBadge.style.display = 'none';
            }
        })
        .catch(() => {
            // Silently hide badge on network error
            unreadBadge.style.display = 'none';
        });

        // Fetch notifications list
        fetch(NOTIF_BASE + '?format=json', {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) return null;
            return response.json();
        })
        .then(data => {
            if (!data) {
                notifDropdownList.innerHTML = '<li class="p-3 text-center text-muted">Notifications unavailable</li>';
                return;
            }
            const list = data.notifications || [];
            notifDropdownList.innerHTML = '';
            
            if (list.length === 0) {
                notifDropdownList.innerHTML = '<li class="p-3 text-center text-muted small">No new notifications</li>';
                return;
            }

            // List up to 5 recent notifications
            list.slice(0, 5).forEach(notif => {
                const item = document.createElement('li');
                item.className = `p-3 border-bottom notification-item ${notif.is_read ? 'read' : 'unread'}`;
                item.style.cursor = 'pointer';
                item.dataset.id = notif.id;
                
                const time = new Date(notif.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                
                item.innerHTML = `
                    <div class="d-flex justify-content-between align-items-start">
                        <strong class="text-primary">${notif.title}</strong>
                        <small class="text-muted">${time}</small>
                    </div>
                    <p class="mb-1 text-secondary text-truncate small">${notif.content || ''}</p>
                `;

                item.addEventListener('click', function(e) {
                    e.preventDefault();
                    markAsRead(notif.id, item);
                });
                
                notifDropdownList.appendChild(item);
            });
        })
        .catch(() => {
            notifDropdownList.innerHTML = '<li class="p-3 text-center text-muted">Notifications unavailable</li>';
        });
    }

    function markAsRead(id, itemElement) {
        fetch(NOTIF_BASE + 'mark-read/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: `notification_id=${id}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                itemElement.classList.remove('unread');
                itemElement.classList.add('read');
                // Refresh counts and lists
                fetchNotifications();
            }
        })
        .catch(() => {
            // Silently fail
        });
    }

    // Refresh every 30 seconds
    fetchNotifications();
    setInterval(fetchNotifications, 30000);
});
