# gh-milestone

A small, read-only GitHub CLI extension for browsing milestones and their issues and pull requests from your terminal.

All code and documentation in this repository were written by Codex, an AI agent using the GPT 6.1 model.

## Requirements

- [GitHub CLI](https://cli.github.com/) (`gh`), authenticated for the repositories you want to browse.
- A currently supported Python release (3.11 or newer), available as `python3` on your `PATH`.

No additional Python packages are needed.

## Install

Install with GitHub CLI:

```sh
gh auth login
gh extension install gmuloc/gh-milestone
gh milestone --help
```

To install from a local clone instead, run this from the clone's root directory:

```sh
gh extension install .
gh milestone --help
```

For a local installation, GitHub CLI links the executable, so edits take effect immediately. To remove the extension, run `gh extension remove milestone`.

## Quick start

From any GitHub repository checkout:

```sh
gh milestone
gh milestone view 7
gh milestone view 7 --items
```

The first command lists open milestones. The second shows milestone 7's details. The third also lists every assigned issue and pull request, including closed and merged items.

Outside a checkout, select a repository explicitly with `-R OWNER/REPO`. Replace `OWNER/REPO`, milestone numbers, and milestone titles in the examples with values from your repository.

## Commands

| Command | Result | Default state | Default limit |
| --- | --- | --- | --- |
| `gh milestone` or `gh milestone list` | Milestones | Open | 30 |
| `gh milestone view MILESTONE` | One milestone's details | Any milestone state | One milestone |
| `gh milestone view MILESTONE --items` | Details and assigned issues and PRs | All item states | Unlimited |
| `gh milestone issues MILESTONE` | Assigned issues, excluding PRs | Open | 30 |
| `gh milestone prs MILESTONE` | Assigned PRs | Open | 30 |

Use `--help` after any command for its options.

## Examples

```sh
# List open milestones in the current repository (also the default command).
gh milestone list

# List every milestone, including closed ones.
gh milestone list -R OWNER/REPO --state all --limit 100

# Show a milestone by number or exact title.
gh milestone view 7 -R OWNER/REPO
gh milestone view 'v1.0.0' -R OWNER/REPO

# Show the milestone and every assigned issue and PR, including closed/merged items.
gh milestone view 'v1.0.0' -R OWNER/REPO --items

# Optionally filter or limit the combined list.
gh milestone view 7 -R OWNER/REPO --items --state open --limit 50

# List open issues or PRs assigned to a milestone.
gh milestone issues 'v1.0.0' -R OWNER/REPO
gh milestone prs 7 -R OWNER/REPO

# Include closed items, and emit JSON for scripts.
gh milestone prs 7 -R OWNER/REPO --state all --limit 100 --json

# Repository options also work before the command.
gh milestone -R OWNER/REPO list
```

`-R` accepts `OWNER/REPO` or `HOST/OWNER/REPO`; without it, `gh` resolves the current repository (including `GH_REPO`). For GitHub Enterprise, authenticate to your host first, then include it in the repository argument:

```sh
gh auth login --hostname github.example.com
gh milestone list -R github.example.com/OWNER/REPO
```

Milestone titles must match exactly. An all-digit argument is treated as a milestone number. Closed milestones can be viewed and queried without adding a state option: `--state` on `issues` and `prs` filters the assigned items, not the milestone. Closed PRs include merged PRs; merged items are labeled `merged` in the table when GitHub provides the merge timestamp.

Lists default to 30 matching results and open items. Increase `--limit` to retrieve more; the extension follows REST API pages until it reaches the limit or exhausts the results. Milestones are ordered by due date, ascending; issues and PRs by creation time, newest first. Filtering out PRs from issues (and issues from PRs) happens before applying the limit.

`view --items` displays a combined table with each item's type, number, title, state, and URL. Unlike the standalone lists, it defaults to **all states and no result limit**, following every page. Use `--state` or `--limit` with `--items` to narrow the result; these options require `--items` on `view`. Items are ordered newest first; `closed` includes merged PRs, labeled `merged` when GitHub provides the merge timestamp. Large milestones can require many API requests.

## JSON output

`--json` returns the complete REST API objects: an array for lists or the milestone object for plain `view`. With `view --items --json`, it returns `{"milestone": {...}, "items": [...]}`. GitHub's milestone `open_issues` and `closed_issues` counts include pull requests, which `view` explicitly labels. The extension does not modify milestones or repository content.

```sh
gh milestone view 7 -R OWNER/REPO --items --json > milestone.json
```

Output may contain private repository content when you have access to it. Review exported files before sharing or committing them.

Human-readable output displays terminal control characters and bidirectional formatting controls as visible escapes. JSON output escapes non-ASCII characters; parsing the JSON restores the original values.

## How it works

The executable invokes `gh repo view --json nameWithOwner,url` to resolve the repository and host. It then calls the GitHub REST API using `gh api`, reusing GitHub CLI's credentials and error handling. A numeric milestone is fetched directly; a title is resolved by scanning all milestones, including closed ones. GitHub's milestone-filtered issues endpoint returns both issues and PRs, so the extension splits them using the API's `pull_request` field. No search-query interpolation or separate credentials are needed.

## Troubleshooting

- **Missing `gh` or `python3`:** install the requirements and ensure both commands are on your `PATH`.
- **Authentication or repository access errors:** run `gh auth status`, confirm your account has access, and check `-R`. For Enterprise, use `gh auth status --hostname YOUR_HOST`.
- **Milestone not found:** use its number or exact title, quoting titles that contain spaces. Run `gh milestone list --state all` to include closed milestones.
- **Missing issues or PRs:** standalone lists default to open items and 30 results. Set `--state all` and increase `--limit`, or use `view MILESTONE --items` for the combined list.

## Development

```sh
python3 -m unittest discover -s tests -v
```

Tests mock GitHub CLI responses and do not use network access or credentials.

## License

[MIT](LICENSE). Provided "as is", without warranty. Use at your own risk; see the license for the full warranty and liability disclaimer.
