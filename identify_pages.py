import re

files = ['page1.html', 'page2.html', 'page3.html', 'page4.html', 'page5.html', 'page6.html', 'page7.html']

for file in files:
    try:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
            # Check for the specific search input
            search_input = re.search(r'placeholder=["\'].*votues', content, re.IGNORECASE)
            if search_input:
                print(f'{file}: HAS SEARCH INPUT - Electoral List')
            else:
                # Check for other indicators
                has_stats = 'statistik' in content.lower() or 'chart' in content.lower()
                has_structure = 'struktur' in content.lower() or 'member' in content.lower()
                
                if has_stats and not has_structure:
                    print(f'{file}: Likely Dashboard')
                elif has_structure:
                    print(f'{file}: Likely Structure')
                else:
                    print(f'{file}: Unknown')
    except Exception as e:
        print(f'{file}: Error - {e}')
