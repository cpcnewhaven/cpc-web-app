import re

with open('templates/admin/content_list.html', 'r') as f:
    content = f.read()

# Update the button rendering logic
content = content.replace(
    "{% if admin_view.endpoint == 'sermon' %}<button type=\"button\" class=\"future-toggle\" id=\"futureToggle\">Show future sermons</button>{% endif %}",
    "{% if admin_view.endpoint in ['sermon', 'podcastepisode'] %}<button type=\"button\" class=\"future-toggle\" id=\"futureToggle\">Show future {{ 'sermons' if admin_view.endpoint == 'sermon' else 'episodes' }}</button>{% endif %}"
)

# Update the javascript rendering condition and text
old_js_start = "{% if admin_view.endpoint == 'sermon' %}\n<script>"
new_js_start = "{% if admin_view.endpoint in ['sermon', 'podcastepisode'] %}\n<script>"

content = content.replace(old_js_start, new_js_start)

# Update button text inside JS
old_btn_text = "button.textContent = showing ? 'Hide future sermons' : 'Show future sermons';"
new_btn_text = "button.textContent = showing ? 'Hide future {{ \"sermons\" if admin_view.endpoint == \"sermon\" else \"episodes\" }}' : 'Show future {{ \"sermons\" if admin_view.endpoint == \"sermon\" else \"episodes\" }}';"

content = content.replace(old_btn_text, new_btn_text)

with open('templates/admin/content_list.html', 'w') as f:
    f.write(content)
print("Updated content_list.html to support podcast episodes")
