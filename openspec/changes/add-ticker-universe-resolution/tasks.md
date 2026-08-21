## 1. Data sourcing

- [x] 1.1 Fetch the current S&P 500 constituent list from a reliable public reference (e.g. Wikipedia's "List of S&P 500 companies") and extract just the ticker symbols. This requires live web access (WebFetch/WebSearch) to real, current data - it is NOT to be filled in from training-data memory of what the S&P 500 "probably" contains, since constituents change over time and a memorized list could be stale or wrong in ways that are hard to catch after the fact (REQ 1.12's "don't substitute your own judgment silently" principle applies here too). If web access is unavailable when this task is worked, stop and tell the user rather than approximating. (WebFetch's LLM summarization pass proved unreliable for a 500+ row table - truncated and appeared to fabricate entries; resolved via direct `curl` of the raw CSV from `datasets/s-and-p-500-companies` on GitHub, giving byte-accurate data. Two tickers, MRSH and VMRK, could not be corroborated against training data and were independently verified by the user before use.)
- [x] 1.2 Write the tickers to `src/tayyib/data/sp500_constituents.csv`: one uppercase ticker per line, no header row, no duplicates, no blank lines

## 2. Universe module

- [x] 2.1 Create `src/tayyib/universe.py`
- [x] 2.2 Add `UniverseResolutionError(Exception)`
- [x] 2.3 Add `_read_ticker_file(path) -> list[str]`: reads the file, uppercases each entry, raises `UniverseResolutionError` if the file is missing, if it's empty, on the first blank entry, or on the first duplicate (case-insensitive)
- [x] 2.4 Add `resolve_universe(universe_source=None) -> list[str]`, defaulting to `settings.universe_source`: for `"sp500"`, calls `_read_ticker_file` against `src/tayyib/data/sp500_constituents.csv`; for any other value, raises `UniverseResolutionError` naming the unrecognized value

## 3. Tests

- [x] 3.1 Unit test: `resolve_universe("sp500")` returns a non-empty list of uppercase tickers read from the real checked-in file
- [x] 3.2 Unit test: `resolve_universe()` with no argument defaults to `settings.universe_source`
- [x] 3.3 Unit test: an unrecognized universe source raises `UniverseResolutionError` naming the value
- [x] 3.4 Unit test: a missing file (via `_read_ticker_file` against a nonexistent `tmp_path`) raises `UniverseResolutionError`
- [x] 3.5 Unit test: an empty file raises `UniverseResolutionError`
- [x] 3.6 Unit test: a file with a blank entry raises `UniverseResolutionError`
- [x] 3.7 Unit test: a file with a duplicate ticker raises `UniverseResolutionError`
- [x] 3.8 Unit test: a file with a case-only duplicate (e.g. `AAPL` and `aapl`) raises `UniverseResolutionError`
- [x] 3.9 Unit test: a valid file with mixed-case tickers is returned fully uppercased, in the same order, with no entries dropped
