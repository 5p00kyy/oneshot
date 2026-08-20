## Problem

Describe the behavior or reliability issue this change addresses.

## Changes

-

## Evaluation impact

- [ ] Trigger evaluations updated when activation behavior changed.
- [ ] Output evaluations updated when workflow or quality expectations changed.
- [ ] Changelog updated for public behavior changes.

## Verification

- [ ] `python3 scripts/validate_repo.py`
- [ ] `python3 -m unittest discover -s tests -p "test_*.py"`
- [ ] `python3 scripts/package_release.py`
- [ ] `gh skill publish . --dry-run` when available

List actual command results and any host-specific checks below.
