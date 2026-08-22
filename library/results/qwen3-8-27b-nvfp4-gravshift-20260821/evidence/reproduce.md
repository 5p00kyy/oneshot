# Reproduction notes

1. Use OpenCode `1.18.18` with its `build` agent and exact model route `vllm/qwen3.8-27b-nvfp4`.
2. Configure the model context limit as 122,880 tokens and start from an empty writable directory.
3. Submit the exact bytes from `library/challenges/gravshift/prompt.md` as the only human brief. Do not provide follow-up messages or continue the session after it stops.
4. Preserve the OpenCode JSONL event stream, run log, exit code, runtime, and final work-directory inventory.
5. For this recorded attempt, the only model step ended with reason `length` at OpenCode's 32,000-token generation cap. It emitted no tool event, no final handoff, and no challenge artifact.
6. Confirm `index.html` and `README.md` are absent, then attempt to open the expected `index.html` over `file://`; the retained screenshot records Chromium's `ERR_FILE_NOT_FOUND` result.

The stochastic attempt was not rerun or continued. A second independent run would be a separate result, not a repair of this one-shot record.
