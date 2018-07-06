# How to git with Jupyter Notebooks

This setup
- prints human-readable diffs on notebooks
- removes outputs from notebooks before adding them to git so as to reduce the size of the repository
- saves notebook checkpoints (with outputs) to git-lfs so that results can be viewed in the GitHub/GitLab's web interfaces or "checked out" using the "Revert to Checkpoint" feature in Jupyter Notebook.

## Global setup

1. Install git lfs for your system. e.g. `brew install git-lfs` on MacOS with Homebrew.
2. Run: `git config --global diff.ipynb.textconv jupyter nbconvert --to markdown --stdout --log-level=0 --no-prompt --TemplateExporter.exclude_output=True`
3. Run: `git config --global filter.ipynb.clean jupyter nbconvert --to notebook --stdin --stdout --log-level=0 --ClearOutputPreprocessor.enabled=True`

## Per-repo setup

1. Enable git-lfs for the repo with `git lfs install --local`
2. Create a file named `.gitattributes` at the top of your repo's working tree. Add this line to it: `*.ipynb diff=ipynb filter=ipynb`.
3. Run: `git lfs track '.ipynb_checkpoints/*'`
4. `git add .gitattributes`

## Normal workflow

In Jupyter Notebook, click "File > Save and Checkpoint" and check-in both the notebook and its checkpoint into git. Git commands such as `git status` should work as usual. Behind the scenes, the notebook will be stripped of outputs and stored in git, and the checkpoint will be stored with outputs in git-lfs.

When you pull/clone a repo with this setup, the notebook will not have any outputs. You can do "File > Revert to Checkpoint" to restore the outputs.

## Troubleshooting

- `git check-attr -a <notebook> <checkpoint>` should print:

```
<notebook>: diff: ipynb
<notebook>: filter: ipynb
<checkpoint>: diff: lfs
<checkpoint>: merge: lfs
<checkpoint>: text: unset
<checkpoint>: filter: lfs
```

If it returns something different (e.g. `filter: ipynb` for the checkpoint), swap the order of the corresponding lines in `.gitattributes`.

- `git lfs ls-files` should list all the checkpoint files that you previously added to git.
