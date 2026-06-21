# Final Deployment Checklist

Use this checklist to deploy the Iqra Academy CRM to production environments safely.

## 1. Environment and Secret Keys
- [ ] **Secret Key:** Generate a unique, cryptographically secure string and configure `SECRET_KEY` in the environment variables. Do not reuse the development key.
- [ ] **Debug Mode:** Set `DEBUG=False` in environment settings to hide traceback logs.
- [ ] **Allowed Hosts:** List only your explicit production domain names in `ALLOWED_HOSTS`.

## 2. Database Configuration
- [ ] **Production Database:** Setup a stable database engine (such as PostgreSQL or MySQL) and specify the access path in `DATABASE_URL`.
- [ ] **Migrations:** Run `python manage.py migrate` to create all required database tables.
- [ ] **Superuser:** Initialize the primary administrator account using `python manage.py createsuperuser`.

## 3. Static and Media Assets
- [ ] **Collect Static:** Compile frontend assets using `python manage.py collectstatic`.
- [ ] **Web Server Mapping:** Map the web server (Nginx or Apache) to serve files from the static files root directory.
- [ ] **Uploads Directory:** Define the media uploads root path. Ensure the system user has write permission, but restrict script execution within this folder.

## 4. HTTPS and Web Security
- [ ] **SSL/TLS Certificates:** Obtain and install SSL certificates (such as Let's Encrypt certificates).
- [ ] **Secure Session Cookies:** Enable secure flags in Django:
  - Set `SESSION_COOKIE_SECURE = True`
  - Set `CSRF_COOKIE_SECURE = True`
  - Set `SECURE_SSL_REDIRECT = True`
- [ ] **HSTS Headers:** Configure HTTP Strict Transport Security.
- [ ] **Security Headers:** Review the SecurityHardeningMiddleware configuration. Ensure the CSP settings match your hostnames.

## 5. Integrations Configuration
- [ ] **SMTP Server:** Configure `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, and `EMAIL_HOST_PASSWORD` settings for automated client notifications.
- [ ] **Payment Providers:** Map any merchant keys for fee handling.

## 6. Backups and Monitoring
- [ ] **Automated Backups:** Set up hourly database backup scripts and daily media folder sync actions.
- [ ] **Logging:** Map stdout logs to rolling files on disk. Monitor log output for security alert warnings.
