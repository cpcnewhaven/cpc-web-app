import re

with open('templates/admin/master.html', 'r') as f:
    master = f.read()

global_table_css = """
  /* Global table styles for all list views to match Announcement/Content lists */
  table.model-list { width:100%; table-layout:auto; border-collapse:separate; border-spacing:0; border:1px solid #d9e5ee; border-radius:18px; overflow:hidden; background:#fff !important; box-shadow:0 16px 34px rgba(54,88,116,.08); }
  table.model-list thead th { padding:1rem 1.1rem !important; background:#eef5fa !important; color:#5f7486 !important; border-bottom:1px solid #d9e5ee !important; font-size:.7rem; letter-spacing:.12em; text-transform:uppercase; font-weight:800; border-top:none !important; }
  table.model-list tbody tr td { padding:1.2rem 1.1rem !important; min-height:84px; background:#fff !important; color:#304254 !important; border-bottom:1px solid #e7eef3 !important; vertical-align:middle; border-top:none !important; }
  table.model-list tbody tr:hover td { background:#f7fbfe !important; }
  table.model-list th, table.model-list td { overflow:hidden; text-overflow:ellipsis; }

  .admin-body table.model-list tbody tr td { background:#fff !important; }
  .admin-body table.model-list tbody tr:hover td { background:#f7fbfe !important; }
  .admin-body .table-responsive { background:transparent !important; backdrop-filter:none !important; -webkit-backdrop-filter:none !important; border:none !important; }

  /* Flask-Admin supplied icon-only edit and delete controls */
  table.model-list .list-buttons-column { white-space:nowrap; width:100px; }
  table.model-list .list-buttons-column > a.icon,
  table.model-list .list-buttons-column > form.icon { display:inline-flex; vertical-align:middle; margin:0 .35rem 0 0; }
  table.model-list .list-buttons-column > a.icon,
  table.model-list .list-buttons-column > form.icon button { width:34px !important; min-width:34px !important; height:34px !important; box-sizing:border-box; align-items:center; justify-content:center; border:1px solid #9bc9e3 !important; border-radius:9px !important; background:#eaf5fb !important; color:#1f6c97 !important; font-size:.9rem !important; line-height:1 !important; text-decoration:none; cursor:pointer; transition:all .16s ease; }
  table.model-list .list-buttons-column > a.icon .fa,
  table.model-list .list-buttons-column > form.icon button .fa { color:inherit !important; }
  table.model-list .list-buttons-column > form.icon button { border-color:#e6b2b2 !important; background:#fff1f1 !important; color:#a72d2d !important; }
  table.model-list .list-buttons-column > a.icon:hover { border-color:#237fab !important; background:#237fab !important; color:#fff !important; box-shadow:0 4px 10px rgba(35,127,171,.22); transform:translateY(-1px); }
  table.model-list .list-buttons-column > form.icon button:hover { border-color:#a72d2d !important; background:#a72d2d !important; color:#fff !important; box-shadow:0 4px 10px rgba(167,45,45,.18); transform:translateY(-1px); }

  @media (max-width: 1200px) {
    table.model-list th:nth-child(n+6), table.model-list td:nth-child(n+6) { display:none; }
    table.model-list { font-size:.82rem; }
  }
  @media (max-width: 760px) {
    table.model-list { display:block; border:0; border-radius:0; box-shadow:none; background:transparent !important; overflow:visible; }
    table.model-list thead { display:none; }
    table.model-list tbody { display:block; background:#edf4f8; border-radius:18px; padding:.25rem; }
    table.model-list tbody tr {
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
    table.model-list td {
        display:block !important;
        min-height:0;
        padding:.8rem 1rem !important;
        border:0 !important;
        background:#fff !important;
        white-space:normal;
        overflow:visible;
        text-overflow:clip;
    }
    table.model-list td:nth-child(1) { grid-area:select; padding-right:0 !important; }
    table.model-list td.list-buttons-column { grid-area:actions; align-self:end; display:flex !important; flex-direction:row; gap:.45rem; padding:.15rem 1rem 1rem !important; }
    table.model-list td:nth-child(3) { grid-area:title; align-self:stretch; display:flex !important; align-items:center; padding:1.15rem 1rem .7rem !important; color:#1d2a36 !important; font-size:1rem; font-weight:750; line-height:1.4; }
    table.model-list td.col-active, table.model-list td.col-status { grid-area:status; align-self:stretch; padding:1.15rem .75rem !important; border-left:1px solid #edf2f5 !important; }
    table.model-list td:not(:nth-child(1)):not(.list-buttons-column):not(:nth-child(3)):not(.col-active):not(.col-status) { display:none !important; }
  }
"""

if "/* Global table styles for all list views" not in master:
    master = master.replace('</style>', global_table_css + '\n</style>')
    with open('templates/admin/master.html', 'w') as f:
        f.write(master)
    print("Added global table styles to master.html")
else:
    print("Global styles already present in master.html")
