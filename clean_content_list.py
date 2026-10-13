import re

with open('templates/admin/content_list.html', 'r') as f:
    content = f.read()

# remove everything between /* Global table styles ... */ if we didn't add it there, but wait, in content_list.html we just have table.model-list.
# I'll just use a regex to strip out `table.model-list` lines in content_list.html.
new_lines = []
skip = False
for line in content.split('\n'):
    if line.strip().startswith('table.model-list'):
        continue
    if '@media' in line:
        new_lines.append(line)
        continue
    if '.admin-body table.model-list' in line or '.admin-body .table-responsive' in line:
        continue
    new_lines.append(line)

# Also fix the media queries
content = '\n'.join(new_lines)
with open('templates/admin/content_list.html', 'w') as f:
    f.write(content)
