# How to git-diff Jupyter Notebooks

This setup prints human-readable diffs on Notebook files:

1. Create an executable script called `nb2md` somewhere in your path:

```bash
#!/bin/bash
exec jupyter nbconvert --to markdown "$1" --stdout --log-level=0 --no-prompt --TemplateExporter.exclude_output=True
```

2. Add the following line to your gitattributes file: `*.ipynb diff=nb2md`. The gitattributes file is at `~/.config/git/attributes` if the folder `~/.config/git` exists, else it is at `~/.gitattributes`.

3. Run: `git config --global diff.nb2md.textconv nb2md`
