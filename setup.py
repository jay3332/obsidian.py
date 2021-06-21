import re
from setuptools import setup


with open('obsidian/__init__.py') as f:
    try:
        print(f.read())
        version = re.match(
            r'''^__version__\s*=\s*['"]([^'"]*)['"]\s*''',
            f.read(),
            re.MULTILINE
        ).group(1)
    except AttributeError:
        raise RuntimeError('Could not identify version') from None

print(version)
