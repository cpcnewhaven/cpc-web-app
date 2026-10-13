import re

with open('templates/admin/content_list.html', 'r') as f:
    content = f.read()

# Replace the media query block
new_media = """
  @media (max-width: 760px) {
    .new-entry-widget { align-items:stretch; flex-direction:column; }
    .new-entry-widget-actions { width:100%; }
    .new-entry-widget-actions .content-new-entry, .new-entry-widget-actions .future-toggle { flex:1; text-align:center; }

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

    /* We assume Status is the last column, or active is column 7 */
    /* Let's just use the `.col-active` class which Flask-admin uses for active/status */
    table.model-list td.col-active, table.model-list td.col-status { grid-area:status; align-self:stretch; padding:1.15rem .75rem !important; border-left:1px solid #edf2f5 !important; }

    table.model-list td:nth-child(4), table.model-list td:nth-child(5), table.model-list td:nth-child(6) { display:none !important; }
    table.model-list td:not(:nth-child(1)):not(.list-buttons-column):not(:nth-child(3)):not(.col-active):not(.col-status) { display:none !important; }
    .content-list-header { gap:.5rem; }
  }
"""

content = re.sub(r'@media \(max-width: 760px\) \{.*?\n  \}', new_media.strip(), content, flags=re.DOTALL)

with open('templates/admin/content_list.html', 'w') as f:
    f.write(content)
print("Fixed grid layout in content_list.html")
