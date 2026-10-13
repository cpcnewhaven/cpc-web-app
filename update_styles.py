import re

with open('templates/admin/content_list.html', 'r') as f:
    content = f.read()

new_css = """
  .content-list-header, .advanced-toggle-section { display:flex; align-items:center; gap:1rem; flex-wrap:wrap; }
  .new-entry-widget { width:100%; display:flex; align-items:center; justify-content:space-between; gap:1rem; padding:1.35rem 1.5rem; margin-bottom:1rem; border:1px solid #d9e5ee; border-radius:18px; background:linear-gradient(135deg,#ffffff 0%,#f3f8fc 100%); box-shadow:0 12px 28px rgba(54,88,116,.08); }
  .new-entry-widget strong { display:block; color:#1d2a36; font-size:1.08rem; }
  .new-entry-widget-actions { display:flex; align-items:center; gap:.7rem; flex-wrap:wrap; }
  .future-toggle { min-height:50px; padding:.8rem 1.15rem; border:1px solid #9bc9e3; border-radius:.8rem; background:#eaf5fb; color:#1f6c97; font-weight:800; font-size:.72rem; letter-spacing:.08em; text-transform:uppercase; cursor:pointer; transition:all .15s ease; }
  .future-toggle.active { background:#3f97d8; color:#fff; border-color:#3f97d8; box-shadow:0 6px 14px rgba(63,151,216,.22); }
  .new-entry-eyebrow { display:block; margin-bottom:.3rem; color:#3f8ed0; font-size:.68rem; font-weight:800; letter-spacing:.16em; text-transform:uppercase; }
  .content-new-entry { display:inline-flex; align-items:center; justify-content:center; min-height:50px; padding:.8rem 1.5rem; border-radius:.8rem; background:#3f97d8; color:#fff !important; font-weight:800; font-size:.78rem; letter-spacing:.1em; text-transform:uppercase; text-decoration:none !important; box-shadow:0 8px 18px rgba(63,151,216,.2); transition:all .15s ease; }
  .content-new-entry:hover { background:#2f82bf; box-shadow:0 10px 22px rgba(63,151,216,.28); transform:translateY(-1px); }

  .admin-list { width:100%; table-layout:fixed; border-collapse:separate; border-spacing:0; border:1px solid #d9e5ee; border-radius:18px; overflow:hidden; background:#fff !important; box-shadow:0 16px 34px rgba(54,88,116,.08); }
  .admin-list thead th { padding:1rem 1.1rem !important; background:#eef5fa !important; color:#5f7486 !important; border-bottom:1px solid #d9e5ee !important; font-size:.7rem; letter-spacing:.12em; text-transform:uppercase; }
  .admin-list tbody tr td { padding:1.2rem 1.1rem !important; min-height:84px; background:#fff !important; color:#304254 !important; border-bottom:1px solid #e7eef3 !important; vertical-align:middle; border-top:none !important; }
  .admin-list tbody tr:hover td { background:#f7fbfe !important; }
  .admin-list th, .admin-list td { overflow:hidden; text-overflow:ellipsis; }

  .admin-body .admin-list tbody tr td { background:#fff !important; }
  .admin-body .admin-list tbody tr:hover td { background:#f7fbfe !important; }
  .admin-body .table-responsive { background:transparent !important; backdrop-filter:none !important; -webkit-backdrop-filter:none !important; }

  /* Flask-Admin supplied icon-only edit and delete controls */
  .admin-list .list-buttons-column { white-space:nowrap; width:100px; }
  .admin-list .list-buttons-column > a.icon,
  .admin-list .list-buttons-column > form.icon { display:inline-flex; vertical-align:middle; margin:0 .35rem 0 0; }
  .admin-list .list-buttons-column > a.icon,
  .admin-list .list-buttons-column > form.icon button { width:34px !important; min-width:34px !important; height:34px !important; box-sizing:border-box; align-items:center; justify-content:center; border:1px solid #9bc9e3 !important; border-radius:9px !important; background:#eaf5fb !important; color:#1f6c97 !important; font-size:.9rem !important; line-height:1 !important; text-decoration:none; cursor:pointer; transition:all .16s ease; }
  .admin-list .list-buttons-column > a.icon .fa,
  .admin-list .list-buttons-column > form.icon button .fa { color:inherit !important; }
  .admin-list .list-buttons-column > form.icon button { border-color:#e6b2b2 !important; background:#fff1f1 !important; color:#a72d2d !important; }
  .admin-list .list-buttons-column > a.icon:hover { border-color:#237fab !important; background:#237fab !important; color:#fff !important; box-shadow:0 4px 10px rgba(35,127,171,.22); transform:translateY(-1px); }
  .admin-list .list-buttons-column > form.icon button:hover { border-color:#a72d2d !important; background:#a72d2d !important; color:#fff !important; box-shadow:0 4px 10px rgba(167,45,45,.18); transform:translateY(-1px); }

  @media (max-width: 1200px) {
    .admin-list th:nth-child(n+6), .admin-list td:nth-child(n+6) { display:none; }
    .admin-list { font-size:.82rem; }
  }
  @media (max-width: 760px) {
    .new-entry-widget { align-items:stretch; flex-direction:column; }
    .new-entry-widget-actions { width:100%; }
    .new-entry-widget-actions .content-new-entry, .new-entry-widget-actions .future-toggle { flex:1; text-align:center; }

    .admin-list { display:block; border:0; border-radius:0; box-shadow:none; background:transparent !important; overflow:visible; }
    .admin-list thead { display:none; }
    .admin-list tbody { display:block; background:#edf4f8; border-radius:18px; padding:.25rem; }
    .admin-list tbody tr {
        display:grid;
        grid-template-columns:2.75rem minmax(0,1fr) minmax(7.5rem, 9rem);
        grid-template-areas:
          "select title status"
          ". title status"
          ". actions status";
        align-items:center;
        margin:0 0 1rem;
        border:1px solid #d9e5ee;
        border-radius:18px;
        overflow:hidden;
        background:#fff;
        box-shadow:0 12px 26px rgba(54,88,116,.08);
        width:100%;
    }
    .admin-list td {
        display:block !important;
        min-height:0;
        padding:.8rem 1rem !important;
        border:0 !important;
        background:#fff !important;
        white-space:normal;
        overflow:visible;
        text-overflow:clip;
    }
    .admin-list td:nth-child(1) { grid-area:select; padding-right:0 !important; }
    .admin-list td.list-buttons-column, .admin-list td:nth-child(2) { grid-area:actions; align-self:end; display:flex !important; flex-direction:row; gap:.45rem; padding:.15rem 1rem 1rem !important; }
    .admin-list td:nth-child(3) { grid-area:title; align-self:stretch; display:flex !important; align-items:center; padding:1.15rem 1rem .7rem !important; color:#1d2a36 !important; font-size:1rem; font-weight:750; line-height:1.4; }
    .admin-list td:nth-child(4), .admin-list td:nth-child(5) { display:none !important; }
    .admin-list td:nth-child(n+6) { display:none !important; }
    .content-list-header { gap:.5rem; }
  }
"""

start_str = "<style>"
end_str = "</style>"
start_idx = content.find(start_str)
end_idx = content.find(end_str)

if start_idx != -1 and end_idx != -1:
    new_content = content[:start_idx + len(start_str)] + "\n" + new_css + content[end_idx:]
    with open('templates/admin/content_list.html', 'w') as f:
        f.write(new_content)
    print("Updated content_list.html successfully.")
else:
    print("Could not find style tags in content_list.html")
