## 1. Alert module

- [x] 1.1 Create `src/tayyib/alerts.py`
- [x] 1.2 Add `send_telegram_message(text) -> bool` using httpx with a 10 second timeout, skipping when token or chat id is empty
- [x] 1.3 Add `format_failure_alert(run) -> str` containing run id, step name, and failure reason

## 2. Pipeline wiring

- [x] 2.1 In the pipeline failure branch, send the failure alert after `fail_pipeline_run`, and return the incomplete run

## 3. Tests

- [x] 3.1 Message is posted to the Telegram sendMessage URL with chat id and text, and returns True
- [x] 3.2 HTTP error and network error both return False without raising
- [x] 3.3 Empty token makes no request and returns False
- [x] 3.4 Failure alert text contains run id, step name, and reason
- [x] 3.5 A pipeline-wide failure sends one alert
- [x] 3.6 A failing alert send still leaves the run incomplete with its reason
- [x] 3.7 A successful run sends no alert
