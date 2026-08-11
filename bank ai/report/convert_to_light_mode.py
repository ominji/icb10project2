import re

file_path = "bank ai/report/money_magnet_dashboard.html"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. :root variables
root_old = """        :root {
            --primary: #00bda7;
            --primary-light: #e2f1f0;
            --primary-dark: #008f7e;
            --bg-dark: #080f19;
            --sidebar-bg: #0c1625;
            --card-bg: rgba(15, 27, 46, 0.7);
            --card-border: rgba(0, 189, 167, 0.12);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent-yellow: #fbbf24;
            --accent-red: #f87171;
            --accent-green: #34d399;
            --input-bg: #111e30;
            --input-border: #1e2e45;
        }"""
root_new = """        :root {
            --primary: #00998f;
            --primary-light: #e2f1f0;
            --primary-dark: #007a72;
            --bg-dark: #f4f7f6;
            --sidebar-bg: #ffffff;
            --card-bg: #ffffff;
            --card-border: #e2e8f0;
            --text-main: #1e293b;
            --text-muted: #64748b;
            --accent-yellow: #f59e0b;
            --accent-red: #ef4444;
            --accent-green: #10b981;
            --input-bg: #f8fafc;
            --input-border: #cbd5e1;
        }"""
content = content.replace(root_old, root_new)

# 2. Body gradient
body_grad_old = """            background-image: radial-gradient(circle at 10% 20%, rgba(0, 189, 167, 0.04) 0%, transparent 40%),
                              radial-gradient(circle at 90% 80%, rgba(0, 143, 126, 0.03) 0%, transparent 40%);"""
body_grad_new = """            background-image: radial-gradient(circle at 10% 20%, rgba(0, 153, 143, 0.02) 0%, transparent 40%),
                              radial-gradient(circle at 90% 80%, rgba(0, 122, 114, 0.015) 0%, transparent 40%);"""
content = content.replace(body_grad_old, body_grad_new)

# 3. Replace white semi-transparent borders with black semi-transparent
content = content.replace("rgba(255, 255, 255, 0.08)", "rgba(0, 0, 0, 0.08)")
content = content.replace("rgba(255, 255, 255, 0.05)", "rgba(0, 0, 0, 0.05)")
content = content.replace("rgba(255, 255, 255, 0.04)", "rgba(0, 0, 0, 0.05)")
content = content.replace("rgba(255, 255, 255, 0.1)", "rgba(0, 0, 0, 0.1)")

# 4. Text colors hardcoded to #ffffff -> #1e293b (except buttons if any, but let's check class)
# Dandi report card background (dark gradient -> white)
dandi_bg_old = "background: linear-gradient(135deg, rgba(15, 27, 46, 0.95), rgba(8, 15, 25, 0.98));"
dandi_bg_new = "background: #ffffff;"
content = content.replace(dandi_bg_old, dandi_bg_new)

dandi_body_bg_old = "background: rgba(0, 0, 0, 0.25);"
dandi_body_bg_new = "background: rgba(0, 153, 143, 0.05);"
content = content.replace(dandi_body_bg_old, dandi_body_bg_new)

# 5. Box shadows on cards
card_shadow_old = "box-shadow: 0 4px 20px rgba(0, 189, 167, 0.05);"
card_shadow_new = "box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);"
content = content.replace(card_shadow_old, card_shadow_new)

# 6. .header-title background
header_title_old = "background: linear-gradient(45deg, #ffffff, var(--primary));"
header_title_new = "background: linear-gradient(45deg, #1e293b, var(--primary));"
content = content.replace(header_title_old, header_title_new)

# 7. JS Chart options
# ticks color
content = content.replace("color: '#94a3b8'", "color: '#64748b'")
content = content.replace("color: '#ffffff'", "color: '#1e293b'")
# Doughnut/Pie border color '#0b131f'
content = content.replace("borderColor: '#0b131f'", "borderColor: '#ffffff'")

# 8. specific color fixes
content = content.replace("color: #ffffff;", "color: var(--text-main);")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Conversion to light mode completed.")
