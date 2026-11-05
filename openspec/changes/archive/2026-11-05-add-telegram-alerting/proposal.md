## Why

The pipeline records failures in the database, but nobody reads a database row at 3am. Tayyib is an alert-only system, so the user needs a message on their phone when a run fails. This change adds the Telegram delivery layer and wires failure alerts into the pipeline.

## What Changes

- Add a function that sends a plain text message to the configured Telegram chat through the Telegram Bot API.
- Add a failure alert formatter that states which run failed, the step name, and the stored failure reason.
- When `run_screening_pipeline` hits a pipeline-wide failure, it sends a failure alert after marking the run incomplete.
- Alert delivery never changes the outcome of a run. If Telegram is unreachable or not configured, the run result stays the same and the delivery problem does not raise.

**Out of scope**
- Weekly summary alerts with entries and exits. They need the ranking capability first and get their own change.
- Retry and backoff on delivery.
- Any inbound bot commands.

## Capabilities

### New Capabilities
- `telegram-alerting`: Delivers messages to a configured Telegram chat and sends a failure alert when a pipeline run ends incomplete.

### Modified Capabilities
- `pipeline-orchestration`: A pipeline-wide failure also triggers a failure alert, in addition to marking the run incomplete.

## Impact

- New module `src/tayyib/alerts.py`.
- `src/tayyib/pipeline.py` calls the alert function in its failure branch.
- Uses the existing `httpx` dependency and the existing `telegram_bot_token` and `telegram_chat_id` settings.
