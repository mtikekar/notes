# All about completions in Vim

A summary of `:h ins-completion`

## Sources

There are several completion sources such as current files, dictionary,
thesaurus, tags, file names, user-completion, omni-completion, spelling, etc.
You can get suggestions from these sources individually using their own
insert-mode mappings that come baked into vim, e.g. <C-x><C-n> for current file,
<C-x><C-f> for file names, etc.

Some of these single sources can be aggregated and activated by C-N/C-P. The
list of sources to be aggregated is in the 'complete' option. However, this
only aggregates keyword sources (files, buffers, dictionary, thesaurus, spell).
It does not include user-completion, omni-completion and file names.

You can also complete entire lines (as opposed to single keywords) with <C-x><C-l>.
The sources for these are shared with keywords in 'complete'.

## Completion menu

Activating any completion will open a popup menu (unless disabled in
'completeopt') listing the possible completions, and optionally a preview
window with more info about each completion.

You can navigate through the menu with arrow keys or C-N/C-P and select a
completion with Enter. More settings on completion menu are in 'completeopt'.
You can add settings to it with `set completeopt+=setting1,setting2,...` and
remove a setting with `set completeopt-=setting1`.

## User-completion and omni-completion

These require setting 'completefunc' and 'omnifunc' to functions that return a
list of completions. They can then be used with <C-x><C-u> and <C-x><C-o>. Both
forms use functions with the same signature (`:h complete-func`).

The difference is that omnifunc is meant to be filetype specific and
completefunc is meant to be activated on demand (e.g. when a connection to an
external program such as a REPL or a language server is established).

Vim comes with omnifuncs for many languages and loads them by default. You can
define your own and load it as: `autocmd FileType <ft> set
omnifunc=<func-name>`.

## Aggregating all sources

[mucomplete](https://github.com/lifepillar/vim-mucomplete) is a plugin that can
aggregate all sources: everything in 'complete', file names, omnifunc,
completefunc, and more. It can also automatically show the completion menu
without having to press any key.

## Asynchronous completion

All of the above completions are synchronous and will be slow on large projects.
Neovim and Vim 8+ allow for asynchronous functions. There are several plugins
that connect this functionality with completions:

- [asynccomplete.vim](https://github.com/prabirshrestha/asycomplete.vim)
- [deoplete.vim](https://github.com/Shougo/deoplete.vim)
- [nvim-completion-manager](https://github.com/roxma/nvim-completion-manager)
