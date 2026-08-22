# Reproduce the Loopback finding

1. From this result directory, open `index.html` directly from disk in a fresh Chromium profile with local storage cleared.
2. Confirm the start screen appears with no network dependency, then select **Play Level 1**.
3. Confirm pointer rotation, arrow-key focus movement, Enter rotation, undo, reset, and locked-level feedback.
4. Test Level 1 from the initial state. Independent validation enumerated all 81 ordered two-click sequences implied by par 2 and observed no win screen or unlock. It also ran 500 random 20-click walks without finding a win.
5. Reload the page. Completion/unlock persistence cannot be meaningfully validated because no completion state was reachable through the tested UI.

The exact model prompt is `prompt/prompt.md`. The direct OpenCode records are `evidence/events.jsonl` and `evidence/run.log`; public copies replace machine-specific absolute paths with explicit placeholders. The model-authored `evidence/model-verification.log` is preserved but contradicted by `evidence/independent-validation.txt`. From this directory, verify the listed preserved bytes with `sha256sum -c evidence/SHA256SUMS.txt`.
