import re

# Fix CSP in electoral-list.html
with open('electoral-list.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Remove CSP meta tag (handle both quoted and unquoted attribute names)
csp_pattern = r'<meta http-equiv=(["\']?)content-security-policy\1[^>]*>'
html = re.sub(csp_pattern, '', html, flags=re.IGNORECASE)

with open('electoral-list.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('Removed CSP meta tag from electoral-list.html')

# Fix CSP in dashboard.html
with open('dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

html = re.sub(csp_pattern, '', html, flags=re.IGNORECASE)

with open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('Removed CSP meta tag from dashboard.html')

# Fix CSP in structure.html
with open('structure.html', 'r', encoding='utf-8') as f:
    html = f.read()

html = re.sub(csp_pattern, '', html, flags=re.IGNORECASE)

with open('structure.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('Removed CSP meta tag from structure.html')
