# Iqra Academy CRM

A Django-based school and academy management CRM for student records, admissions, academics, attendance, exams, finance workflows, reports, document handling, PDF comparison, audit logs, and role-based portals.

## Release Status
**Release Ready Confirmed**

---

## Key Modules

* **Role-Based Dashboards:** Isolated work areas tailored for administrators, academic coordinators, staff members, students, and guardians.
* **Student Management:** Central directory for student enrollment profiles, demographic tracking, and session mappings.
* **Admissions Management:** Pipeline for application review, decision flows, automated email notifications, and conversion into active student profiles.
* **Session and Academics Management:** Scheduling tool for academic sessions, classroom assignations, subjects, and instructor allocations.
* **Attendance Management:** Digital marking sheets, low attendance reporting, and record locking systems.
* **Exams and Grade Configuration:** Customizable grade boundaries, score entries, and transcript generation.
* **Finance Navigation and Payment Records:** Tracking system for tuition fees, installments, payment entries, and financial ledgers.
* **Reports and PDF Exports:** Performance reports, attendance analytics, and dynamic PDF student transcript downloads.
* **Student Document and CNIC Upload:** Secure file storage for student identification card photos and admissions documents.
* **PDF Result Comparison:** Preview and comparison utility for parsed exam sheets with candidates database, running as a safe preview-only tool.
* **Audit Logs:** System-wide activity logs monitoring staff actions for full operations traceability.
* **AI Engine Pages:** Analytical views showing dropout risk logs and model versions utilizing real database-backed records only.

---

## Role Access Summary

* **Admin:** Complete access to all configurations, audit logs, AI model versions, user permissions, finance ledgers, and academic settings.
* **Principal:** Access to academic tracking, exams configuration, attendance logs, reports dashboard, and AI dropout risk indicators.
* **Registrar:** Enrolls students, handles admissions applications, views reports, generates transcripts, and manages documents.
* **Teacher:** Marks attendance for assigned classes, enters grades, and views schedules.
* **Accountant:** Manages payment lists, reviews receipts, and updates ledger entries.
* **Student:** Logged into their portal dashboard to review their schedules, view attendance percentages, and download published grades.
* **Guardian:** Monitors academic scores and attendance trends for all linked children.

---

## Final QA Status

* **14 Original Issues Closed:** All core release bugs and stubs have been closed and verified.
* **290 Tests Passing:** Complete test suite execution is fully green.
* **Migration Dry-Run Clean:** No database model mutations or pending migration conflicts.
* **No Open Blockers:** System validated as fully release-ready.
* **Finance Integrity:** Verified that reading reports and opening session metrics does not mutate payment or fee records.
* **PDF Comparison:** Confirmed as a preview-only utility that does not edit student or achievement records.
* **AI Predictions:** Functions without generating fake predictions or dummy entries.

---

## Local Setup Instructions

### Prerequisites
* Python 3.10+
* Pip (Python package manager)
* Virtualenv (recommended)

### Installation
1. **Clone the repository:**
   ```bash
   git clone https://github.com/awanafnan17/Iqra-Academy-CRM.git
   cd Iqra-Academy-CRM
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup environment variables:**
   Create a `.env` file in the project root directory based on the `.env.example` file:
   ```bash
   cp .env.example .env
   ```

5. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser:**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start the development server:**
   ```bash
   python manage.py runserver
   ```

---

## Demo Setup Instructions

To run the local system with specific demo and testing configurations:
1. Ensure your `.env` is configured for local SQLite test environments.
2. Run the application utilizing the test settings explicitly:
   ```bash
   python manage.py runserver --settings=config.settings.test
   ```
3. If exposing the local environment for stakeholders validation using tools such as LocalTunnel or Ngrok, configure the allowed hosts header accordingly. Note that external tunnels are strictly for validation and are not suitable for production deployment.

---

## Test Commands

Run the test suite using the Django test settings configuration:
```bash
python manage.py test --settings=config.settings.test --verbosity=2
```

To test code checking and styling:
```bash
python manage.py check --settings=config.settings.test
```

---

## Deployment Checklist Summary

* **Environment Variables:** Configure database urls, secure email settings, and session parameters.
* **Debug Mode:** Ensure `DEBUG = False` is set in the production settings.
* **Allowed Hosts:** Restrict headers to authorized domains only.
* **Database Migration:** Run migrations against the production database engine.
* **Static Files:** Compile assets using `python manage.py collectstatic`.
* **Media Storage:** Secure uploads directory with correct permissions and restrict executions.
* **Email/SMS/Payment Gateway:** Establish credentials for actual integrations.
* **HTTPS/SSL:** Force secure connections and HTTP Strict Transport Security (HSTS).
* **Backups:** Set up automated databases and media backups.

---

## Known Limitations

* **AI Engine Data:** Dropout risk panels show existing, real database records of predictions and model versions only. Prediction calculations are not faked by the views.
* **AI Prediction Calculations:** Generating new calculations requires a separate running background pipeline.
* **Scanned PDF Support:** Comparison of scanned documents requires an external OCR processing module. Scanned pages without text are reported as such.
* **PDF Heuristics:** The PDF parsing comparison behaves as a preview tool only and does not edit student records or achievement tables.
* **Local Tunnels:** Public tunnel connections are strictly for developer validation.

---

## Security Note

Never commit `.env` configuration files, database files containing private information, credentials, or actual student documentation files to the public repository history.

---

## License

License: Proprietary. All rights reserved unless a license is added by the owner.
