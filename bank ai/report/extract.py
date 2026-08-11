import re

with open('bank ai/report/money_magnet_dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

scripts = re.findall(r'<script>.*?</script>', content, re.DOTALL)
with open('bank ai/report/script_dump.js', 'w', encoding='utf-8') as f:
    for script in scripts:
        f.write(script + '\n\n')
