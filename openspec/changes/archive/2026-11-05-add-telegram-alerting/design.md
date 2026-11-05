## Context

See proposal.md. `Settings` already has `telegram_bot_token` and `telegram_chat_id`. `pipeline.py` has one outer `except Exception` that calls `fail_pipeline_run`. `httpx` is already a dependency.

## Goals / Non-Goals

**Goals**
- One small module, `alerts.py`, with `send_telegram_message(text)` and `format_failure_alert(run)`.
- Delivery problems never change a run's outcome.

**Non-Goals**
- Retries, rich formatting, inbound commands, weekly summaries.

## Decisions

**Decision: call the Telegram HTTP API directly with httpx.** One POST to `sendMessage` does the whole job, so a bot library would add a dependency for nothing.

**Decision: `send_telegram_message` returns a bool and swallows httpx errors.** The caller is the failure branch of the pipeline, and an alert problem must not hide the original failure.

**Decision: skip silently when token or chat id is empty.** Local runs and tests have no Telegram, so an empty setting means alerting is off, not broken.

**Decision: the pipeline calls the alert after `fail_pipeline_run`.** The database record is the source of truth and gets written first.

**Decision: plain text, no Markdown parse mode.** Failure reasons can contain characters that break Markdown and cause Telegram to reject the message.

## Risks / Trade-offs

- [Silent skip hides a typo in the token] -> The function returns False, and a later change can log it once logging exists.
- [A slow Telegram call delays the failure return] -> A short request timeout of 10 seconds bounds it.
