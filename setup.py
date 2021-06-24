import re
from setuptools import setup


with open('obsidian/__init__.py') as f:
    try:
        version = re.search(
            r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.M
        ).group(1)
    except AttributeError:
        raise RuntimeError('Could not identify version') from None

    # look at this boilerplate code
    try:
        author = re.search(
            r'^__author__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.M
        ).group(1)
    except AttributeError:
        author = 'jay3332'


with open('README.md', encoding='utf-8') as f:
    readme = f.read()


setup(
    name='obsidian.py',
    author=author,
    url='https://github.com/jay3332/obsidian.py',
    project_urls={
        "Issue tracker": "https://github.com/jay3332/obsidian.py/issues",
    },
    version=version,
    packages=[
        'obsidian'
    ],
    license='MIT',
    description='A wrapper around Obsidian\'s REST and Websocket API.',
    long_description=readme,
    long_description_content_type="text/markdown",
    include_package_data=True,
    install_requires=[
        'discord.py>=1.6.0',
        'aiohttp<3.8.0,>=3.6.0'
    ],
    python_requires='>=3.7.0',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Internet',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
    ]
)
