import re

with open('.github/workflows/github-actions.yml', 'r') as f:
    content = f.read()

# Pattern to find job blocks
# - name: 'py38-nocov (ubuntu)'
#   python: '3.8'
#   toxpython: 'python3.8'
#   python_arch: 'x64'
#   tox_env: 'py38-nocov'
#   os: 'ubuntu-20.04'

# List of versions that NEED 20.04
legacy_prefixes = ['py27', 'py36', 'py37', 'pypy27']

def replacer(match):
    name_line = match.group(1)
    # Extract prefix from name, e.g. 'py38' from 'py38-nocov (ubuntu)'
    prefix = name_line.split('-')[0]

    body = match.group(2)
    os_line = match.group(3)

    if any(prefix == lp for lp in legacy_prefixes):
        new_os = 'ubuntu-20.04'
    else:
        new_os = 'ubuntu-latest'

    return f"          - name: '{name_line}'{body}os: '{new_os}'"

# Match ubuntu jobs
pattern = r"          - name: '([^']+ \(ubuntu\))'((?:\n[ ]+[^:\n]+: '[^'\n]+')+)\n[ ]+os: 'ubuntu-20.04'"
new_content = re.sub(pattern, replacer, content)

# Also update check and docs back to latest
new_content = new_content.replace("- name: 'check'\n            python: '3.9'\n            toxpython: 'python3.9'\n            tox_env: 'check'\n            os: 'ubuntu-20.04'",
                                  "- name: 'check'\n            python: '3.9'\n            toxpython: 'python3.9'\n            tox_env: 'check'\n            os: 'ubuntu-latest'")
new_content = new_content.replace("- name: 'docs'\n            python: '3.9'\n            toxpython: 'python3.9'\n            tox_env: 'docs'\n            os: 'ubuntu-20.04'",
                                  "- name: 'docs'\n            python: '3.9'\n            toxpython: 'python3.9'\n            tox_env: 'docs'\n            os: 'ubuntu-latest'")

with open('.github/workflows/github-actions.yml', 'w') as f:
    f.write(new_content)
