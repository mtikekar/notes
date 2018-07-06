# How to git-diff Jupyter Notebooks

This setup prints human-readable diffs on Notebook files:

1. Add the following line to your gitattributes file: `*.ipynb diff=ipynb`. The gitattributes file is at `~/.config/git/attributes` if the folder `~/.config/git` exists, else it is at `~/.gitattributes`.

2. Run: `git config --global diff.ipynb.textconv jupyter nbconvert --to markdown --stdout --log-level=0 --no-prompt --TemplateExporter.exclude_output=True`
