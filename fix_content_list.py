import re

with open('templates/admin/content_list.html', 'r') as f:
    content = f.read()

# Replace document.addEventListener('DOMContentLoaded', function () {
# with adding the admin-list class to the table

script_addition = """
document.addEventListener('DOMContentLoaded', function () {
  const modelTable = document.querySelector('table.model-list');
  if (modelTable) modelTable.classList.add('admin-list');
  const button = document.getElementById('futureToggle');
  const table = document.querySelector('.admin-list');
"""

content = content.replace("document.addEventListener('DOMContentLoaded', function () {\n  const button = document.getElementById('futureToggle');\n  const table = document.querySelector('.admin-list');", script_addition)

with open('templates/admin/content_list.html', 'w') as f:
    f.write(content)
print("Added JS to content_list.html to ensure .admin-list class is added to table.model-list")
