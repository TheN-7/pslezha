import re

with open('electoral-list.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Find and replace the tbody section
tbody_pattern = r'<tbody[^>]*>.*?</tbody>'
placeholder_tbody = '<tbody class="[&_tr:last-child]:border-0">\n        <tr class="border-b">\n            <td class="p-6 text-center text-muted-foreground" colspan="11">Shkruani te pakten 2 karaktere per kerkim</td>\n        </tr>\n    </tbody>'

new_html = re.sub(tbody_pattern, placeholder_tbody, html, flags=re.DOTALL)

with open('electoral-list.html', 'w', encoding='utf-8') as f:
    f.write(new_html)

print('Modified electoral-list.html')
