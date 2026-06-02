import re

with open('electoral-list.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Search for input elements with placeholder
input_pattern = r'<input[^>]*placeholder=["\']([^"\']*votues[^"\']*)["\']'
matches = re.findall(input_pattern, html, re.IGNORECASE)

if matches:
    print('Found input with votues in placeholder:')
    for match in matches:
        print(f'  {match}')
else:
    print('No input with votues in placeholder found')
    # Search for any input elements
    all_inputs = re.findall(r'<input[^>]*>', html)
    print(f'Found {len(all_inputs)} input elements total')
    for i, inp in enumerate(all_inputs[:5]):
        print(f'  Input {i+1}: {inp[:100]}')
