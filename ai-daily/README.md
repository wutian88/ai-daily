# AI daily cloud updates

UTC 01:00 daily (Beijing 09:00 target), plus manual dispatch. GitHub schedule may be delayed. No desktop process, external model key, or paid API is required. Sources: GitHub API, Hugging Face official blog RSS, arXiv RSS. The generated digest is explicitly a rule-based source digest, not daily Claude authorship or a model experiment. Existing deep topics remain unchanged.

Source failures are recorded in the digest; fewer than two unseen items from at least two source kinds fails before replacing content. Same-day repeats do not duplicate the digest. Tests and the English application build must pass before committing content. Bot commits use GITHUB_TOKEN and the same run deploys the built Pages artifact; no recursive push trigger is required. No external text enters shell commands. Only public source titles, metadata and short extracts are published.

Source of truth: repository public/ai-daily/content.json and ai-daily/archive, not the previous desktop copy. Do not run the old desktop generator against this content: it would overwrite cloud history. Local notes remain a historical copy. Update the dated articles and this workflow through normal repository commits.

Failure recovery: Actions failure leaves the previously deployed site available. If content commit succeeds but Pages deployment fails, manually rerun the workflow; the same-day guard preserves the committed digest and allows redeployment. Missing feeds do not mean no new research exists. No-entry days may fail quality gate rather than fabricate material. Scheduled workflows on inactive public repositories may be disabled by GitHub; keep manual dispatch available and check Actions if updates stop.
