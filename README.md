# Institution Research Dashboard

A Streamlit dashboard for exploring the research output, impact, and topic
profile of academic and research institutions worldwide, powered by the
[OpenAlex](https://openalex.org) API.

Pick a country, find an institution (by name, by browsing a sorted list, or
by its OpenAlex ID), and get a research profile: publication and
citation trends over time, topic and domain breakdowns, a topic
co-occurrence network, geographic and institutional relationships, and
growth analytics.

## Features

- **Flexible institution selection** - browse by country, search by name,
  or jump straight to an institution via its OpenAlex ID (e.g.
  `I4387153981`).
- **Research Output** - yearly works, citations, and open-access trends,
  plus citation velocity.
- **Research Topics** - domain and field/subfield breakdowns, top topics,
  topic share/score analysis, and an interactive topic co-occurrence
  network built from the institution's most-cited works.
- **Geographic & Network** - institution location and associated
  institutions (parents, children, related orgs) laid out visually.
- **Advanced Analytics** - cumulative growth, domain intensity, and
  year-over-year growth.
- **About** - profile summary, alternative names, identifiers, and links
  to the institution's website, OpenAlex record, ROR record, and Wikipedia
  page.
- **Key metrics sidebar** - total works, total citations, h-index,
  i10-index, 2-year mean citedness, and average open-access rate.

## Requirements

- Python 3.10+
- A free [OpenAlex API key](https://openalex.org/settings/api). Since
  February 13, 2026, OpenAlex requires an API key on every request.

## Setup

1. **Clone the project and install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Provide your OpenAlex API key.** The app looks for it in this order:

   1. A key typed into the sidebar during the session.
   2. Streamlit secrets - add to `.streamlit/secrets.toml`:

      ```toml
      OPENALEX_API_KEY = "your-key-here"
      ```

   3. The `OPENALEX_API_KEY` environment variable:

      ```bash
      export OPENALEX_API_KEY="your-key-here"
      ```

3. **Run the app:**

   ```bash
   streamlit run app.py
   ```

   The dashboard will open in your browser at `http://localhost:8501`.

## Project Structure

```
.
├── app.py               # Streamlit UI, layout, and tabs (presentation logic)
├── openalex_api.py       # OpenAlex REST API client (all network calls, caching, retries)
├── data_processing.py    # Pure functions: raw OpenAlex JSON -> pandas DataFrames
├── theme.py               # "Scholarly ledger" CSS theme and chart styling
├── requirements.txt      # Python dependencies
└── .streamlit/
    ├── config.toml        # Native Streamlit widget theme (not included here)
    └── secrets.toml       # Optional: OPENALEX_API_KEY (not committed)
```

- **`openalex_api.py`** - thin client around `https://api.openalex.org`.
  Every function accepts `api_key` explicitly (rather than reading it from
  global state) so Streamlit's caching correctly distinguishes "no key"
  from "valid key" calls. Includes retry logic for transient `502/503/504`
  errors and cursor-pagination helpers for endpoints where OpenAlex's
  `group_by` responses are capped per page.
- **`data_processing.py`** - has no dependency on Streamlit or the
  network, so it can be unit tested independently. Turns raw institution,
  topic, and works JSON into the DataFrames the charts consume, including
  derived metrics like open-access percentage and citation velocity.
- **`theme.py`** - injects the dashboard's custom CSS and provides
  `styled_chart()` to apply consistent Plotly styling across all charts.

## Notes

- Some very small institutions genuinely have no yearly publication data -
  this is expected, not a bug.
- OpenAlex's `group_by` domain breakdown only counts works that have a
  `primary_topic` assigned; the dashboard adds back any shortfall as an
  explicit "Other" category so totals always reconcile with the
  institution's real works count.
- If you hit your OpenAlex daily usage limit or see authentication errors,
  check your key and usage at
  [openalex.org/settings/usage](https://openalex.org/settings/usage).

## Credits

Built by [Tornike Skhirtladze](https://www.linkedin.com/in/tornike-skhirtladze-463120b6/).
Data provided by [OpenAlex](https://openalex.org).