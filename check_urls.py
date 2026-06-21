from django.urls import reverse, NoReverseMatch

names = [
    'admin_panel:transcript_pdf',
    'reports:transcript_pdf',
    'student_portal:transcript_pdf',
    'transcript_pdf',
]

for name in names:
    try:
        url = reverse(name, args=[1])
        print(f"FOUND: {name} -> {url}")
    except NoReverseMatch:
        try:
            url = reverse(name)
            print(f"FOUND (no args): {name} -> {url}")
        except NoReverseMatch:
            print(f"MISSING: {name}")
