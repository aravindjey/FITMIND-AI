import re, html

with open('docs/FITMIND_AI_SRS_DOCUMENT.md', 'r') as f:
    text = f.read()

# Replace LaTeX expressions with clean, human-readable Unicode equivalents
text = text.replace(r'$$\text{\bf Invariant: The Relational Database is the Single Authoritative Source of Truth.}$$',
                    '**Invariant: The Relational Database is the Single Authoritative Source of Truth.**')
text = text.replace(r'\text{\bf Invariant: The Relational Database is the Single Authoritative Source of Truth.}',
                    '**Invariant: The Relational Database is the Single Authoritative Source of Truth.**')

# Specific strings
text = text.replace(r'($4\text{ kcal/g protein} + 4\text{ kcal/g carb} + 9\text{ kcal/g fat} \neq \text{total calories}$)',
                    '(4 kcal/g protein + 4 kcal/g carb + 9 kcal/g fat ≠ total calories)')
text = text.replace(r'($\text{INR } ₹$)', '(INR ₹)')
text = text.replace(r'(\text{INR } ₹)', '(INR ₹)')
text = text.replace(r'($1\text{--}100$)', '(1–100)')
text = text.replace(r'($1\text{--}100$)', '(1–100)')
text = text.replace(r'($\alpha = 0.25$)', '(α = 0.25)')
text = text.replace(r'$\alpha = 0.25$', 'α = 0.25')
text = text.replace(r'$\alpha$', 'α')
text = text.replace(r'($\mathbf{\Delta = 0.0\text{ kcal}}$)', '(Δ = 0.0 kcal)')
text = text.replace(r'($\Delta = 0.0\text{ kcal}$)', '(Δ = 0.0 kcal)')
text = text.replace(r'$\text{1RM} = w \cdot (1 + r/30)$', '1RM = w · (1 + r/30)')
text = text.replace(r'$\text{1RM} = 80.0 \times (1 + 8/30) = 80.0 \times 1.2667 = \mathbf{101.33\text{ kg}}$',
                    '1RM = 80.0 × (1 + 8/30) = 80.0 × 1.2667 = 101.33 kg')

# Regex cleanups
text = re.sub(r'\\text\{INR\s*\}\s*₹', 'INR ₹', text)
text = re.sub(r'\\text\{([^}]+)\}', r'\1', text)
text = re.sub(r'\\mathbf\{([^}]+)\}', r'**\1**', text)
text = text.replace(r'\le', '≤')
text = text.replace(r'\ge', '≥')
text = text.replace(r'\neq', '≠')
text = text.replace(r'\times', '×')
text = text.replace(r'\cdot', '·')
text = text.replace(r'\rightarrow', '→')
text = text.replace(r'\pm', '±')
text = text.replace(r'\text{--}', '–')
text = text.replace(r'--', '–')

# Remove leftover $ enclosing simple text
text = re.sub(r'\$([0-9a-zA-Z.,_+\-*/= ()%≤≥≠×·→±–]+)\$', r'\1', text)
# Clean double spaces
text = re.sub(r'\$([0-9.,]+)\s*kg\$', r'\1 kg', text)
text = re.sub(r'\$([0-9.,]+)\s*kcal\$', r'\1 kcal', text)

with open('docs/FITMIND_AI_SRS_DOCUMENT.md', 'w') as f:
    f.write(text)

# Also generate clean HTML
lines = text.split('\n')
html_out = ['<!DOCTYPE html><html><head><meta charset="utf-8"><title>FITMIND AI PRS Report</title><style>body{font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; font-size: 11pt; line-height: 1.6; color: #111827; margin: 40px auto; max-width: 900px;} h1{color: #0f172a; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px; margin-top: 32px;} h2{color: #1e293b; border-bottom: 1px solid #e2e8f0; padding-bottom: 6px; margin-top: 28px;} h3{color: #334155; margin-top: 22px;} h4{color: #475569;} table{border-collapse: collapse; width: 100%; margin: 20px 0; font-size: 10pt;} th, td{border: 1px solid #cbd5e1; padding: 10px 14px; text-align: left; vertical-align: top;} th{background-color: #f1f5f9; font-weight: 600; color: #0f172a;} tr:nth-child(even){background-color: #f8fafc;} pre{background: #f8fafc; border: 1px solid #e2e8f0; padding: 14px; border-radius: 6px; overflow-x: auto; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 9.5pt; line-height: 1.45;} code{font-family: ui-monospace, Menlo, monospace; font-size: 9.5pt; background: #f1f5f9; padding: 2px 4px; border-radius: 4px;} hr{border: 0; border-top: 1px solid #e2e8f0; margin: 32px 0;} ul, ol{padding-left: 24px; margin: 12px 0;} li{margin-bottom: 6px;}</style></head><body>']

in_table = False
in_code = False
table_header = True

for line in lines:
    if line.startswith('```'):
        if in_code:
            html_out.append('</pre>')
            in_code = False
        else:
            html_out.append('<pre>')
            in_code = True
        continue
    
    if in_code:
        html_out.append(html.escape(line))
        continue
        
    stripped = line.strip()
    
    if stripped.startswith('|') and stripped.endswith('|'):
        cells = [c.strip() for c in stripped[1:-1].split('|')]
        if all(re.match(r'^:?-+:?$', c) for c in cells):
            table_header = False
            continue
        if not in_table:
            html_out.append('<table>')
            in_table = True
            table_header = True
            
        tag = 'th' if table_header else 'td'
        row_str = '<tr>' + ''.join(f'<{tag}>{re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", html.escape(c))}</{tag}>' for c in cells) + '</tr>'
        html_out.append(row_str)
        table_header = False
        continue
    else:
        if in_table:
            html_out.append('</table>')
            in_table = False
            
    if not stripped:
        html_out.append('<p></p>')
        continue
        
    if stripped == '---':
        html_out.append('<hr/>')
        continue
        
    if line.startswith('# '):
        html_out.append(f'<h1>{html.escape(line[2:])}</h1>')
        continue
    if line.startswith('## '):
        html_out.append(f'<h2>{html.escape(line[3:])}</h2>')
        continue
    if line.startswith('### '):
        html_out.append(f'<h3>{html.escape(line[4:])}</h3>')
        continue
    if line.startswith('#### '):
        html_out.append(f'<h4>{html.escape(line[5:])}</h4>')
        continue
        
    p_line = html.escape(line)
    p_line = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', p_line)
    p_line = re.sub(r'\*(.*?)\*', r'<em>\1</em>', p_line)
    
    if stripped.startswith('- '):
        html_out.append(f'<li>{p_line[2:]}</li>')
    else:
        html_out.append(f'<p>{p_line}</p>')

if in_table:
    html_out.append('</table>')
if in_code:
    html_out.append('</pre>')
    
html_out.append('</body></html>')

with open('docs/FITMIND_AI_SRS_DOCUMENT.html', 'w') as f:
    f.write('\n'.join(html_out))

with open('FITMIND_AI_SRS_DOCUMENT.html', 'w') as f:
    f.write('\n'.join(html_out))

print('Cleaned files generated.')
