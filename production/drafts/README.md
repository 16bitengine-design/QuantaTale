Drop assistant-written topic drafts (JSON) here. On push to main the topic-authoring workflow fetches the cited pages and runs the evidence gates plus an independent model check; accepted drafts become specs, rejected ones move to rejected/ with reasons.


To rewrite a topic that is not scheduled yet, add `"replaces": "<spec file name without .json>"` to the draft. It passes every gate again and then overwrites that spec in place; topics already in the publishing ledger are never replaced.
