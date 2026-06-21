# Final Known Limitations

This document lists the operational boundaries of the Iqra Academy CRM.

## 1. AI Engine Limits
* **No Inline Mock Generation:** AI views display real historical database entries only. They do not simulate fake forecasts.
* **External Calculations:** New dropout predictions require an external machine learning worker pipeline to write results into the `PredictionLog` database tables.

## 2. PDF Parsing constraints
* **OCR Dependencies:** Comparing scanned documents requires text extraction. Scanned PDFs without embedded text layer require an OCR processor.
* **Format Structure:** The document parser supports pre-configured layouts. Drastic structure changes in the uploaded files require parser updates.

## 3. PDF Comparison Limitations
* **Preview-Only Operations:** The comparison tool runs as a preview panel. It does not update student names, roll numbers, or academic credentials in the database automatically. All discrepancies must be fixed manually.

## 4. Local Verification Tunnels
* **Security Validation:** Using local tunnels (such as Ngrok or LocalTunnel) is strictly for remote reviews. Do not run public tunnels in production.
* **Hosts Header Configuration:** Running with tunnels requires adding the tunnel domain name to the `ALLOWED_HOSTS` list in your settings configuration.
