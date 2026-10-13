import re

with open('templates/admin/content_list.html', 'r') as f:
    content = f.read()

new_style = """<style>
  .content-list-header, .advanced-toggle-section { display:flex; align-items:center; gap:1rem; flex-wrap:wrap; }
  .new-entry-widget { width:100%; display:flex; align-items:center; justify-content:space-between; gap:1rem; padding:1.35rem 1.5rem; margin-bottom:1rem; border:1px solid #d9e5ee; border-radius:18px; background:linear-gradient(135deg,#ffffff 0%,#f3f8fc 100%); box-shadow:0 12px 28px rgba(54,88,116,.08); }
  .new-entry-widget strong { display:block; color:#1d2a36; font-size:1.08rem; }
  .new-entry-widget-actions { display:flex; align-items:center; gap:.7rem; flex-wrap:wrap; }
  .future-toggle { min-height:50px; padding:.8rem 1.15rem; border:1px solid #9bc9e3; border-radius:.8rem; background:#eaf5fb; color:#1f6c97; font-weight:800; font-size:.72rem; letter-spacing:.08em; text-transform:uppercase; cursor:pointer; transition:all .15s ease; }
  .future-toggle.active { background:#3f97d8; color:#fff; border-color:#3f97d8; box-shadow:0 6px 14px rgba(63,151,216,.22); }
  .new-entry-eyebrow { display:block; margin-bottom:.3rem; color:#3f8ed0; font-size:.68rem; font-weight:800; letter-spacing:.16em; text-transform:uppercase; }
  .content-new-entry { display:inline-flex; align-items:center; justify-content:center; min-height:50px; padding:.8rem 1.5rem; border-radius:.8rem; background:#3f97d8; color:#fff !important; font-weight:800; font-size:.78rem; letter-spacing:.1em; text-transform:uppercase; text-decoration:none !important; box-shadow:0 8px 18px rgba(63,151,216,.2); transition:all .15s ease; }
  .content-new-entry:hover { background:#2f82bf; box-shadow:0 10px 22px rgba(63,151,216,.28); transform:translateY(-1px); }

  @media (max-width: 760px) {
    .new-entry-widget { align-items:stretch; flex-direction:column; }
    .new-entry-widget-actions { width:100%; }
    .new-entry-widget-actions .content-new-entry, .new-entry-widget-actions .future-toggle { flex:1; text-align:center; }
    .content-list-header { gap:.5rem; }
  }
</style>"""

content = re.sub(r'<style>.*?</style>', new_style, content, flags=re.DOTALL)

with open('templates/admin/content_list.html', 'w') as f:
    f.write(content)
