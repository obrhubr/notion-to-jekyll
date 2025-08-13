from setuptools import setup

VERSION = "0.1.0"

setup(
    name="notion-to-jekyll",
    description=(
        "A CLI utility and Python library to "
        "export your blogposts from Notion to Jekyll."
    ),
    author="obrhubr",
    url="https://github.com/obrhubr/notion-to-jekyll",
    license="MIT",
    version=VERSION,
    entry_points="""
        [console_scripts]
        notion-to-jekyll=notion_to_jekyll.cli:cli
    """,
    install_requires=[
		"click",
		"python-dotenv",
		"requests",
        "setuptools",
        "pip",
		"pillow",
		"enlighten",
		"notion-client",
		"notion2md",
		"urllib3",
		"markdown"
    ],
	packages=['notion_to_jekyll']
)