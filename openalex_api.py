"""
openalex_api.py
----------------
Thin client around the OpenAlex REST API (https://api.openalex.org).

All network calls used by the Streamlit dashboard live here so that
app.py only has to deal with presentation logic.

IMPORTANT: Since February 13, 2026, OpenAlex requires an API key on every
request. Keys are free: create an
account at https://openalex.org and copy your key from
https://openalex.org/settings/api. Every function below takes api_key
as an explicit argument (rather than reading it from global state)
so that Streamlit's cache correctly treats "no key" and "valid key"
as different, separately-cached calls.
"""

import time

import requests
import streamlit as st

BASE_URL = "https://api.openalex.org"
REQUEST_TIMEOUT = 15  # seconds
PAGINATED_REQUEST_TIMEOUT = 30  # seconds - group_by cursor pages can be slower to compute
TRANSIENT_STATUS_CODES = (502, 503, 504)


def _get_with_retry(url, params, timeout=REQUEST_TIMEOUT, retries=3, backoff=1.5):
    """
    GET with retries for transient server-side errors (502/503/504 - the
    request was fine, OpenAlex's server just choked or was overloaded).
    Does NOT retry 4xx errors (bad key, bad filter, etc.) since those
    won't succeed on a second try. Raises the last exception if every
    attempt fails, so callers keep their existing error handling.
    """
    last_exc = None
    for attempt in range(retries):
        try:
            response = requests.get(url, params=params, timeout=timeout)
            status = response.status_code
            if status in TRANSIENT_STATUS_CODES and attempt < retries - 1:
                time.sleep(backoff * (attempt + 1))
                continue
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            last_exc = e
            status = getattr(getattr(e, "response", None), "status_code", None)
            if status in TRANSIENT_STATUS_CODES and attempt < retries - 1:
                time.sleep(backoff * (attempt + 1))
                continue
            raise
    raise last_exc


def _build_params(extra_params, api_key):
    params = dict(extra_params)
    if api_key:
        params["api_key"] = api_key
    return params


def _friendly_error(e, api_key):
    """Turn a requests exception into a message that points at the real fix."""
    status = getattr(getattr(e, "response", None), "status_code", None)
    if status in (401, 403, 409):
        if not api_key:
            return (
                "OpenAlex now requires a free API key for every request. "
                "Get one at https://openalex.org/settings/api."
            )
        return (
            f"OpenAlex rejected the request (HTTP {status}). Your API key may be invalid "
            "or you may have hit your daily usage limit - check https://openalex.org/settings/usage."
        )
    return str(e)


@st.cache_data(ttl=3600)
def fetch_all_countries(api_key=""):
    """
    Return a sorted list of every country_code that has at least one institution.

    Uses group_by=country_code so OpenAlex does the counting itself and
    returns every country in one or two requests, instead of paging through
    all 100,000+ institutions.
    """
    all_countries = set()
    page = 1
    per_page = 100  # OpenAlex's current max page/group size

    while True:
        params = _build_params({"group_by": "country_code", "per_page": per_page, "page": page}, api_key)
        try:
            response = requests.get(f"{BASE_URL}/institutions", params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            st.warning(f"Error fetching institution countries: {_friendly_error(e, api_key)}")
            break

        groups = data.get("group_by", [])
        for group in groups:
            key = group.get("key")
            if not key or key == "unknown":
                continue
            # OpenAlex sometimes returns the group key as a bare code ("AE")
            # and sometimes as a full entity URL
            # (https://openalex.org/countries/AE) - normalize to the bare
            # code so the dropdown never offers a URL as a "country" and
            # fetch_institutions never builds a filter like
            # "country_code:https://openalex.org/countries/AE" (which
            # OpenAlex doesn't resolve cleanly and can hang/504 on).
            code = key.rstrip("/").split("/")[-1].upper()
            all_countries.add(code)

        groups_count = data.get("meta", {}).get("groups_count", len(groups))
        if not groups or page * per_page >= groups_count:
            break
        page += 1

    return sorted(all_countries)


def _normalize_country_code(country_code):
    """Guard against a stray full entity URL sneaking into a country_code
    filter (e.g. from an un-normalized OpenAlex group_by response) - see
    fetch_all_countries."""
    country_code = (country_code or "").strip()
    if country_code.startswith("http"):
        country_code = country_code.rstrip("/").split("/")[-1]
    return country_code.upper()


@st.cache_data(ttl=3600)
def fetch_institutions(country_code, sort_by="works_count:desc", per_page=100, api_key="", max_results=500):
    country_code = _normalize_country_code(country_code)
    all_results = []
    page = 1
    while True:
        params = _build_params(
            {"filter": f"country_code:{country_code}", "per_page": per_page, "sort": sort_by, "page": page},
            api_key,
        )
        try:
            response = requests.get(f"{BASE_URL}/institutions", params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            st.error(f"Error fetching institutions for '{country_code}': {_friendly_error(e, api_key)}")
            break

        results = data.get("results", [])
        all_results.extend(results)

        total = data.get("meta", {}).get("count", len(all_results))
        if not results or len(all_results) >= min(total, max_results):
            break
        page += 1

    return all_results[:max_results]


def _normalize_institution_id(institution_id):
    """
    Make institution-ID lookup forgiving of common copy/paste variations:
    stray whitespace, a full https://openalex.org/I12345 URL, or lowercase input.
    """
    institution_id = institution_id.strip()
    if institution_id.startswith("http"):
        institution_id = institution_id.rstrip("/").split("/")[-1]
    return institution_id.upper()


@st.cache_data(ttl=3600)
def fetch_institution_by_id(institution_id, api_key=""):
    """Fetch a single institution by its OpenAlex ID"""
    clean_id = _normalize_institution_id(institution_id)
    params = _build_params({}, api_key)
    try:
        response = requests.get(f"{BASE_URL}/institutions/{clean_id}", params=params, timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            return response.json()
        if response.status_code == 404:
            return None  # a genuinely unknown ID - handled by the caller as "not found"
        st.error(_friendly_error(requests.exceptions.HTTPError(response=response), api_key))
        return None
    except requests.RequestException as e:
        st.error(f"Error fetching institution '{institution_id}': {_friendly_error(e, api_key)}")
        return None


@st.cache_data(ttl=3600)
def fetch_domain_breakdown(institution_id, api_key=""):
    """
    Full domain breakdown for an institution, computed by grouping ALL of its
    works by primary_topic.domain.
    """
    clean_id = institution_id.rstrip("/").split("/")[-1]
    params = _build_params(
        {
            "filter": f"institutions.id:{clean_id}",
            "group_by": "primary_topic.domain.id",
        },
        api_key,
    )
    try:
        response = requests.get(f"{BASE_URL}/works", params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        groups = response.json().get("group_by", [])
    except requests.RequestException as e:
        st.warning(f"Error fetching domain breakdown: {_friendly_error(e, api_key)}")
        return []

    return [
        {"domain": g.get("key_display_name") or "Other", "count": g["count"]}
        for g in groups
    ]


@st.cache_data(ttl=3600)
def fetch_topic_breakdown(institution_id, api_key=""):
    """
    Full per-topic work counts for an institution - every topic OpenAlex has
    assigned to one of the institution's works, not just the top-25 list
    embedded in the institution object (see build_topics_dataframe). Used
    for the full scatter plot, where we want every point, not a capped view.
    """
    clean_id = institution_id.rstrip("/").split("/")[-1]
    params = _build_params(
        {
            "filter": f"institutions.id:{clean_id}",
            "group_by": "primary_topic.id",
            "per_page": 200,
        },
        api_key,
    )
    try:
        response = requests.get(f"{BASE_URL}/works", params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        groups = response.json().get("group_by", [])
    except requests.RequestException as e:
        st.warning(f"Error fetching topic breakdown: {_friendly_error(e, api_key)}")
        return []

    return [
        {"display_name": g["key_display_name"], "count": g["count"]}
        for g in groups if g.get("key_display_name")
    ]


@st.cache_data(ttl=3600)
def fetch_institution_works_topics(institution_id, api_key="", per_page=200):
    """
    Fetch this institution's most-cited works with just their topic lists
    (not full work objects - only 'topics' is selected, to keep payload
    small). Used to build a topic co-occurrence network.
    """
    clean_id = institution_id.rstrip("/").split("/")[-1]
    params = _build_params(
        {
            "filter": f"institutions.id:{clean_id}",
            "sort": "cited_by_count:desc",
            "per_page": per_page,
            "select": "id,topics",
        },
        api_key,
    )
    try:
        response = requests.get(f"{BASE_URL}/works", params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json().get("results", [])
    except requests.RequestException as e:
        st.warning(f"Error fetching works for topic network: {_friendly_error(e, api_key)}")
        return []


@st.cache_data(ttl=3600)
def fetch_topic_counts_by_domain(institution_id, api_key=""):
    """
    Return {domain_display_name: distinct_topic_count} for ALL of an
    institution's works - not just its top-25 embedded 'topics' list
    (see build_topics_dataframe, which is capped).
    """
    clean_id = institution_id.rstrip("/").split("/")[-1]
    domain_params = _build_params(
        {"filter": f"institutions.id:{clean_id}", "group_by": "primary_topic.domain.id"}, api_key
    )
    try:
        response = _get_with_retry(f"{BASE_URL}/works", domain_params)
        domain_groups = response.json().get("group_by", [])
    except requests.RequestException as e:
        st.warning(f"Error fetching domains for topic counts: {_friendly_error(e, api_key)}")
        return {}

    topic_counts = {}
    incomplete_domains = []
    for g in domain_groups:
        domain_key = g.get("key")
        domain_name = g.get("key_display_name") or "Other"
        if not domain_key:
            continue

        total_topics = 0
        cursor = "*"
        while cursor:
            topic_params = _build_params(
                {
                    "filter": f"institutions.id:{clean_id},primary_topic.domain.id:{domain_key}",
                    "group_by": "primary_topic.id",
                    "per_page": 200,
                    "cursor": cursor,
                },
                api_key,
            )
            try:
                resp = _get_with_retry(f"{BASE_URL}/works", topic_params, timeout=PAGINATED_REQUEST_TIMEOUT)
                data = resp.json()
            except requests.RequestException as e:
                st.warning(
                    f"Error fetching topic count for domain '{domain_name}' "
                    f"(after retries): {_friendly_error(e, api_key)}"
                )
                incomplete_domains.append(domain_name)
                break

            groups = data.get("group_by", [])
            total_topics += len(groups)
            cursor = data.get("meta", {}).get("next_cursor")
            if not groups or not cursor:
                break

        topic_counts[domain_name] = total_topics

    if incomplete_domains:
        st.caption(
            f"⚠️ Topic count may be an undercount for: {', '.join(incomplete_domains)} "
            "(OpenAlex timed out partway through paging - try refreshing)."
        )

    return topic_counts


@st.cache_data(ttl=3600)
def search_institutions(country_code, query, per_page=25, api_key=""):
    """
    Search institutions by name (also matches acronyms and alternative
    names) within a country, instead of relying on a pre-sorted, capped
    list. This finds institutions regardless of how low their works_count
    ranks them - the gap fetch_institutions can't cover.
    """
    if not query or not query.strip():
        return []

    params = _build_params({"search": query.strip(), "per_page": per_page}, api_key)
    try:
        response = requests.get(f"{BASE_URL}/institutions", params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json().get("results", [])
    except requests.RequestException as e:
        st.warning(f"Error searching institutions: {_friendly_error(e, api_key)}")
        return []