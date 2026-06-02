import re

def fix_html_table(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Find all tables
    table_pattern = r'<table[^>]*>(.*?)</table>'
    tables = re.findall(table_pattern, html, re.DOTALL)
    
    if not tables:
        print(f'No tables found in {file_path}')
        return
    
    modified = False
    for i, table_content in enumerate(tables):
        # Check if table has tbody
        tbody_match = re.search(r'<tbody[^>]*>(.*?)</tbody>', table_content, re.DOTALL)
        
        if tbody_match:
            # Table has tbody, remove data rows but keep structure
            tbody_content = tbody_match.group(1)
            # Remove all tr elements except the first one (which might be a header or placeholder)
            rows = re.findall(r'<tr[^>]*>.*?</tr>', tbody_content, re.DOTALL)
            if len(rows) > 1:
                # Keep only the first row (placeholder or header)
                new_tbody_content = rows[0]
                # Replace the tbody content
                new_table_content = table_content.replace(tbody_content, new_tbody_content)
                html = html.replace(table_content, new_table_content)
                modified = True
        else:
            # Table has no tbody, we need to add one
            # Extract thead if it exists
            thead_match = re.search(r'<thead[^>]*>(.*?)</thead>', table_content, re.DOTALL)
            if thead_match:
                thead = thead_match.group(0)
                # Remove all tr elements from the table content except thead
                table_without_thead = table_content.replace(thead, '')
                rows = re.findall(r'<tr[^>]*>.*?</tr>', table_without_thead, re.DOTALL)
                if len(rows) > 0:
                    # Keep the table opening tag and thead, add empty tbody
                    table_open_match = re.match(r'(<table[^>]*>)', table_content)
                    table_open = table_open_match.group(1) if table_open_match else '<table>'
                    
                    # Create new table structure
                    new_table = table_open + '\n    ' + thead + '\n    <tbody>\n        <tr class="border-b">\n            <td class="p-6 text-center text-muted-foreground" colspan="11">Shkruani te pakten 2 karaktere per kerkim</td>\n        </tr>\n    </tbody>\n</table>'
                    
                    html = html.replace(table_content, new_table)
                    modified = True
    
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f'Fixed {file_path}')
    else:
        print(f'No changes needed for {file_path}')

# Fix all three HTML files
fix_html_table('dashboard.html')
fix_html_table('structure.html')
fix_html_table('electoral-list.html')
