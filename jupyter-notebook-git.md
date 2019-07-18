# How to git with Jupyter Notebooks

This setup
- prints human-readable diffs on notebooks
- removes outputs from notebooks before adding them to git so as to reduce the
  size of the repository
- saves notebook checkpoints (with outputs) to git-lfs so that results can be
  viewed in the GitHub/GitLab's web interfaces or "checked out" using the
  "Revert to Checkpoint" feature in Jupyter Notebook.

## Global setup

1. Install git lfs for your system. e.g. `brew install git-lfs` on MacOS with Homebrew.
2. Run:

```bash
git config --global diff.ipynb.textconv jupyter nbconvert --to markdown --stdout --log-level=0 --ClearOutputPreprocessor.enabled=True
git config --global filter.ipynb.clean jupyter nbconvert --to notebook --stdin --stdout --log-level=0 --ClearOutputPreprocessor.enabled=True
```

## Per-repo setup

1. Enable git-lfs for the repo with `git lfs install --local`
2. At the top of your repo's working tree, run:

```bash
echo '*.ipynb diff=ipynb filter=ipynb' >> .gitattributes
git lfs track '.ipynb_checkpoints/*'
git add .gitattributes
```

## Normal workflow

When you're ready to commit your work:

1. In Jupyter Notebook, click "File > Save and Checkpoint".
2. `git add <notebook> <checkpoint>`

That's it! All git commands such as `git status`, `git commit`, etc. should
work as usual. Behind the scenes, the notebook will be stripped of outputs and
stored in git, and the checkpoint will be stored with outputs in git-lfs.

When you pull/clone a repo with this setup, the notebook will not have any
outputs. You can do "File > Revert to Checkpoint" to restore the outputs.

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

If it returns something different (e.g. `filter: ipynb` for the checkpoint),
swap the order of the corresponding lines in `.gitattributes`.

- `git lfs ls-files` should list all the checkpoint files that you previously
  added to git.

## Known Issues

- jupyter nbconvert is slow (see faster scripts below)
- Due to mismatch between the clean and diff filters, git status may signal a
  difference that git diff does not show. It seems that the only way to avoid
  this problem for sure is to use the same filter for clean and diff.


## Faster textconv and clean (potentially unsafe)

We can emulate nbconvert with custom json processing scripts. The [textconv
script](nb2txt) is safe to use as it only produces text for us to read.
However, the [clean script](nbclean) changes what gets saved in the repo. I ran
a single test to check that the clean script produces the same output as
nbconvert, but use it at your own risk!

I also intended for the two scripts to match with each other so that git status
and git diff do not contradict each other.
