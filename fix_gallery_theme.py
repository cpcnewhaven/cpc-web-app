import re

with open('templates/admin/model/gallery_form.html', 'r') as f:
    content = f.read()

# Change the CSS variables to light theme
content = content.replace(
    "--ge-bg:#111b28; --ge-panel:#172535; --ge-border:rgba(180,205,230,.14); --ge-muted:#aab8c8; max-width:1120px; margin:0 auto; padding:12px 0 36px; color:#f5f8fc;",
    "--ge-bg:#f6f8fa; --ge-panel:#ffffff; --ge-border:#d9e5ee; --ge-muted:#6e7d8b; max-width:1120px; margin:0 auto; padding:12px 0 36px; color:#1d2a36;"
)
content = content.replace("color:#fff;", "color:#1d2a36;")
content = content.replace("background:#0c1520;", "background:#e3ebf2;")
content = content.replace("color:#eaf2fa;", "color:#1d2a36;")
content = content.replace("color:#a9c9e8;", "color:#3f8ed0;")
content = content.replace("border-color:rgba(180,205,230,.32)", "border-color:#3f8ed0")

with open('templates/admin/model/gallery_form.html', 'w') as f:
    f.write(content)
