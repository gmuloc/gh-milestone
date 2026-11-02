# gh-milestone

A small, read-only GitHub CLI extension for browsing milestones and their issues and pull requests. Requires [GitHub CLI](https://cli.github.com/) and Python 3.9 or newer; no Python packages are needed.

## Install

Authenticate with `gh auth login`, then install the local repository:

```sh
cd ~/Github/gh-milestone
gh extension install .
gh milestone --help
```

GitHub CLI links the local executable, so edits take effect immediately. To remove the extension, run `gh extension remove milestone`.

## Usage

```sh
# List open milestones in the current repository (also the default command).
gh milestone list

# List every milestone, including closed ones.
gh milestone list -R aristanetworks/avd --state all --limit 100

# Show a milestone by number or exact title.
gh milestone view 111 -R aristanetworks/avd
gh milestone view 'v6.5.0' -R aristanetworks/avd

# Show the milestone and every assigned issue and PR, including closed/merged items.
gh milestone view 'v6.5.0' -R aristanetworks/avd --items

# Optionally filter or limit the combined list.
gh milestone view 111 -R aristanetworks/avd --items --state open --limit 50

# List open issues or PRs assigned to a milestone.
gh milestone issues 'v6.5.0' -R aristanetworks/avd
gh milestone prs 111 -R aristanetworks/avd

# Include closed items, and emit JSON for scripts.
gh milestone prs 111 -R aristanetworks/avd --state all --limit 100 --json

# Repository options also work before the command.
gh milestone -R aristanetworks/avd list
```

`-R` accepts `OWNER/REPO` or `HOST/OWNER/REPO`; without it, `gh` resolves the current repository (including `GH_REPO`). GitHub Enterprise uses the hostname returned by `gh repo view` and your existing `gh` authentication.

Milestone titles must match exactly. An all-digit argument is treated as a milestone number. Closed milestones can be viewed and queried without adding a state option: `--state` on `issues` and `prs` filters the assigned items, not the milestone. Closed PRs include merged PRs; merged items are labeled `merged` in the table when GitHub provides the merge timestamp.

Lists default to 30 matching results and open items. Increase `--limit` to retrieve more; the extension follows REST API pages until it reaches the limit or exhausts the results. Milestones are ordered by due date, ascending; issues and PRs by creation time, newest first. Filtering out PRs from issues (and issues from PRs) happens before applying the limit.

`view --items` displays a combined table with each item's type, number, title, state, and URL. Unlike the standalone lists, it defaults to **all states and no result limit**, following every page so the full milestone is available locally. Use `--state` or `--limit` with `--items` to narrow the result. Items are ordered newest first; `closed` includes merged PRs, labeled `merged` when GitHub provides the merge timestamp.

`--json` returns the complete REST API objects: an array for lists or the milestone object for plain `view`. With `view --items --json`, it returns `{"milestone": {...}, "items": [...]}`. GitHub's milestone `open_issues` and `closed_issues` counts include pull requests, which `view` explicitly labels. The extension does not modify milestones or repository content.

## How it works

The executable invokes `gh repo view --json nameWithOwner,url` to resolve the repository and host. It then calls the GitHub REST API using `gh api`, reusing GitHub CLI's credentials and error handling. A numeric milestone is fetched directly; a title is resolved by scanning all milestones, including closed ones. GitHub's milestone-filtered issues endpoint returns both issues and PRs, so the extension splits them using the API's `pull_request` field. No search-query interpolation or separate credentials are needed.

## Development

```sh
python3 -m unittest discover -s tests -v
```

Tests mock GitHub CLI responses and do not use network access or credentials.
