import re

with open('templates/admin/master.html', 'r') as f:
    master = f.read()

badge_css = """
  /* Light-theme status badges for white tables */
  .admin-body .admin-status-tag {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0.35rem 0.75rem !important;
    font-size: 0.65rem !important;
    font-weight: 800 !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    border-radius: 999px !important;
    border: 1px solid transparent !important;
    margin: 0;
    white-space: nowrap;
    box-shadow: 0 2px 6px rgba(0,0,0,0.04);
  }

  .admin-body table.model-list .admin-status-tag {
      margin: 0;
  }

  .admin-body .admin-status-published,
  table.model-list .col-active .admin-status-published {
    background: #edfcf1 !important;
    color: #1a7f37 !important;
    border-color: #a3e6b5 !important;
  }

  .admin-body .admin-status-draft,
  table.model-list .col-active .admin-status-draft {
    background: #f6f8fa !important;
    color: #57606a !important;
    border-color: #d0d7de !important;
  }

  .admin-body .admin-status-archived,
  table.model-list .col-active .admin-status-archived {
    background: #24292f !important;
    color: #ffffff !important;
    border-color: #24292f !important;
  }

  .admin-body .admin-status-scheduled,
  table.model-list .col-active .admin-status-scheduled {
    background: #fff8c5 !important;
    color: #9a6700 !important;
    border-color: #e5c05c !important;
  }

  .admin-body .admin-status-featured,
  .admin-body .admin-status-banner,
  table.model-list .col-active .admin-status-featured,
  table.model-list .col-active .admin-status-banner {
    background: #f3f0ff !important;
    color: #6e40c9 !important;
    border-color: #dcb8ff !important;
  }
"""

if "/* Light-theme status badges for white tables */" not in master:
    master = master.replace('</style>', badge_css + '\n</style>')
    with open('templates/admin/master.html', 'w') as f:
        f.write(master)
    print("Added light-theme badges to master.html")
else:
    print("Light-theme badges already present in master.html")
