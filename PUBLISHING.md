# Publishing OneShot

This repository has one release authority: the tag-triggered GitHub Actions workflow in `.github/workflows/release.yml`.

`gh skill publish . --dry-run` is a compatibility check. Do not run it without `--dry-run`; live publisher mode also creates a tag and release, which would race the repository workflow.

## Release Contract

- `metadata.version` in `skills/oneshot/SKILL.md`, `CHANGELOG.md`, the Git tag, and the GitHub release must match.
- Release tags use `vMAJOR.MINOR.PATCH` and point to a reviewed commit on `main`.
- Published tags and release assets are immutable. Never move a release tag or overwrite an asset.
- Repository settings must keep immutable releases and the protected `v*` tag ruleset enabled.
- Generated `dist/` files are release artifacts and are never committed.
- A failed or defective release is superseded by a new semantic version.

## 1. Prepare the Version

Choose the semantic version according to the public change:

- Patch for fixes, evaluator corrections, wording improvements, and compatible script changes.
- Minor for new templates, playbooks, evaluation classes, or substantial compatible behavior.
- Major for incompatible activation semantics, layout, naming, or output-contract changes.

Update both:

- `metadata.version` in `skills/oneshot/SKILL.md`.
- `CHANGELOG.md` with the release date and user-visible changes.

## 2. Validate Locally

From the repository root, run:

```bash
python3 scripts/validate_repo.py
python3 -m unittest discover -s tests -p "test_*.py"
python3 scripts/package_release.py --clean
gh skill publish . --dry-run
```

Use `python` instead of `python3` where required.

Inspect the generated archive and verify its checksum:

```bash
unzip -Z1 dist/oneshot-skill-vX.Y.Z.zip
(cd dist && sha256sum -c oneshot-skill-vX.Y.Z.zip.sha256)
```

The archive must contain one top-level `oneshot/` directory and no repository-only files, caches, links, or credentials.

## 3. Merge and Verify Main

Commit the reviewed changes and push them to `main`. Wait for the `Validate` workflow to pass before tagging.

Confirm the worktree is clean and record the release commit:

```bash
git status --short --branch
git rev-parse HEAD
gh run list --workflow Validate --limit 5
```

## 4. Publish Through the Tag Workflow

Create one annotated tag at the validated `main` commit and push only that tag:

```bash
git tag -a vX.Y.Z -m "OneShot vX.Y.Z"
git push origin vX.Y.Z
```

The `Release` workflow then:

1. Checks out the tagged commit without persisted credentials.
2. validates the repository and version/tag match.
3. Runs the tests and builds the deterministic package.
4. Transfers the package to a separate publication job.
5. Fails if the tag already has a GitHub release.
6. Creates one release with the ZIP and checksum assets.

GitHub's immutable-release setting and the `v*` tag ruleset provide the remote enforcement behind this workflow contract.

Do not create the release manually while the workflow is running.

## 5. Verify the Release

Wait for the workflow and inspect the result:

```bash
gh run list --workflow Release --limit 5
gh release view vX.Y.Z
gh skill preview 5p00kyy/oneshot oneshot@vX.Y.Z
```

Download the public assets to a temporary directory and verify the published checksum before announcing the release. Verify the pinned skill in an isolated, host-neutral directory:

```bash
verification_dir=$(mktemp -d)
trap 'rm -rf "$verification_dir"' EXIT
gh skill install 5p00kyy/oneshot oneshot@vX.Y.Z --dir "$verification_dir"
python3 "$verification_dir/oneshot/scripts/validate_skill.py"
```

The pinned user installation command is:

```bash
AGENT_ID=universal  # Replace with the ID for the target host when needed.
gh skill install 5p00kyy/oneshot oneshot@vX.Y.Z --agent "$AGENT_ID" --scope user
```

## Failure Recovery

- If validation fails before a release exists, fix the cause on `main`, create a new version, and tag the corrected commit.
- If the publication job is interrupted before creating a release, inspect the workflow and remote state before rerunning it.
- If any release or asset already exists for the tag, stop. Do not use `--clobber` or move the tag.
- If published content is defective, document it and release the smallest appropriate successor version.

## Official References

- Agent Skills specification: https://agentskills.io/specification
- GitHub CLI `gh skill install`: https://cli.github.com/manual/gh_skill_install
- GitHub CLI `gh skill publish`: https://cli.github.com/manual/gh_skill_publish
- GitHub Actions security hardening: https://docs.github.com/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions
