
# Institution Research Dashboard

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24177249.svg)](https://doi.org/10.5281/zenodo.24177249)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**[Launch the live dashboard](https://institution-research-dashboard-ts.streamlit.app/)**

A Streamlit dashboard for exploring the research output, impact, and topic profile of academic and research institutions worldwide, powered by the [OpenAlex](https://openalex.org) API.

Pick a country, find an institution (by name, by browsing a sorted list, or by its OpenAlex ID), and get a research profile: publication and citation trends over time, topic and domain breakdowns, a topic co-occurrence network, geographic and institutional relationships, and growth analytics.

## Features

- **Flexible institution selection** - browse by country, search by name, or jump straight to an institution via its OpenAlex ID (e.g. `I4387153981`).
- **Research Output** - yearly works, citations, and open-access trends, plus citation velocity.
- **Research Topics** - domain and field/subfield breakdowns, top topics, topic share/score analysis, and an interactive topic co-occurrence network built from the institution's most-cited works.
- **Geographic & Network** - institution location and associated institutions (parents, children, related orgs) laid out visually.
- **Advanced Analytics** - cumulative growth, domain intensity, and year-over-year growth.
- **About** - profile summary, alternative names, identifiers, and links to the institution's website, OpenAlex record, ROR record, and Wikipedia page.
- **Key metrics sidebar** - total works, total citations, h-index, i10-index, 2-year mean citedness, and average open-access rate.

## Requirements

- Python 3.10+
- A free [OpenAlex API key](https://openalex.org/settings/api). Since February 13, 2026, OpenAlex requires an API key on every request.

## Setup

1. **Clone the project and install dependencies:**

   ```bash
   git clone https://github.com/tskhirtladze/Institution-Research-Dashboard.git
   cd Institution-Research-Dashboard
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

```text
.
├── app.py                # Streamlit UI, layout, and tabs (presentation logic)
├── openalex_api.py       # OpenAlex REST API client (network calls, caching, retries)
├── data_processing.py    # Pure functions: raw OpenAlex JSON -> pandas DataFrames
├── theme.py              # "Scholarly ledger" CSS theme and chart styling
├── requirements.txt      # Python dependencies
├── CITATION.cff          # Software citation metadata
└── .streamlit/
    ├── config.toml       # Native Streamlit widget theme
    └── secrets.toml      # Optional: OPENALEX_API_KEY (not committed)
```

### Main modules

- **`openalex_api.py`** - thin client around `https://api.openalex.org`. Every function accepts `api_key` explicitly (rather than reading it from global state) so Streamlit's caching correctly distinguishes "no key" from "valid key" calls. Includes retry logic for transient `502/503/504` errors and cursor-pagination helpers for endpoints where OpenAlex's `group_by` responses are capped per page.

- **`data_processing.py`** - has no dependency on Streamlit or the network, so it can be unit tested independently. Turns raw institution, topic, and works JSON into the DataFrames the charts consume, including derived metrics like open-access percentage and citation velocity.

- **`theme.py`** - injects the dashboard's custom CSS and provides `styled_chart()` to apply consistent Plotly styling across all charts.

## Notes

- Some very small institutions genuinely have no yearly publication data - this is expected, not a bug.
- OpenAlex's `group_by` domain breakdown only counts works that have a `primary_topic` assigned; the dashboard adds back any shortfall as an explicit "Other" category so totals always reconcile with the institution's real works count.
- If you hit your OpenAlex daily usage limit or see authentication errors, check your key and usage at [OpenAlex API usage](https://openalex.org/settings/usage).
- Research indicators and bibliometric metrics should be interpreted in the context of institutional size, disciplinary composition, publication practices, and citation patterns.

## Credits

Built by [Tornike Skhirtladze](https://www.linkedin.com/in/tornike-skhirtladze-463120b6/).

Research metadata provided by [OpenAlex](https://openalex.org).

## How to Cite

If you use the Institution Research Dashboard in academic research, publications, presentations, or other scholarly work, please cite the software as follows:

**APA:**

Skhirtladze, T. (2026). *Institution Research Dashboard* (Version 1.0.0) [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.24177249

**BibTeX:**

```bibtex
@software{skhirtladze_2026_institution_research_dashboard,
  author    = {Skhirtladze, Tornike},
  title     = {Institution Research Dashboard},
  year      = {2026},
  version   = {1.0.0},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.24177249},
  url       = {https://doi.org/10.5281/zenodo.24177249}
}
```

For reproducibility, please cite the specific software version used in your research.

### Data Source and Acknowledgement

This dashboard uses bibliographic and research metadata provided by [OpenAlex](https://openalex.org).

If you use the dashboard's analytical results in your research, please also acknowledge and cite OpenAlex as the underlying data source. Consult the [OpenAlex documentation](https://docs.openalex.org/) for information about its data and recommended citation practices.

## Contributing

Contributions, suggestions, bug reports, and feature requests are welcome.

If you are interested in improving the dashboard, please feel free to open an issue or submit a pull request through GitHub.

Researchers and developers are particularly welcome to contribute ideas related to research evaluation, bibliometrics, institutional benchmarking, and research analytics.

## License

This project is released under the [MIT License](LICENSE).
