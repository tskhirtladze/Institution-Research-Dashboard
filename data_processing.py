"""
Pure functions that turn raw OpenAlex institution JSON into the pandas
DataFrames and derived metrics the dashboard charts need.
"""

import numpy as np
import pandas as pd
import itertools
from collections import Counter
from datetime import datetime

EARLIEST_PLAUSIBLE_YEAR = 1900


def extract_display_name(obj):
    """Return a readable name from an OpenAlex sub-object, or str(obj) as a fallback."""
    if isinstance(obj, dict):
        return obj.get("display_name", str(obj))
    return str(obj)


def build_years_dataframe(counts_by_year):
    """
    Build the yearly works / citations / open-access dataframe plus the
    derived oa_percentage and citation_velocity columns.
    """
    if not counts_by_year:
        return pd.DataFrame()

    df = pd.DataFrame(counts_by_year)
    if df.empty or "works_count" not in df.columns:
        return pd.DataFrame()
    current_year = datetime.now().year
    df = df[(df["year"] >= EARLIEST_PLAUSIBLE_YEAR) & (df["year"] <= current_year + 1)]
    if df.empty:
        return pd.DataFrame()

    if "oa_works_count" not in df.columns:
        df["oa_works_count"] = 0

    works = df["works_count"].replace(0, np.nan)  # avoid divide-by-zero -> inf
    df["non_oa_works"] = df["works_count"] - df["oa_works_count"]
    df["oa_percentage"] = ((df["oa_works_count"] / works) * 100).round(2)
    df["citation_velocity"] = (
        (df["cited_by_count"] / works).replace([np.inf, -np.inf], np.nan).round(2)
    )

    return df.sort_values("year").reset_index(drop=True)


def build_topics_dataframe(topics):
    """Flatten the nested topic objects (with domain/field/subfield) into a flat dataframe."""
    if not topics:
        return pd.DataFrame()

    rows = [
        {
            "display_name": t["display_name"],
            "count": t["count"],
            "score": t["score"],
            "domain": extract_display_name(t.get("domain", {})),
            "field": extract_display_name(t.get("field", {})),
            "subfield": extract_display_name(t.get("subfield", {})),
        }
        for t in topics
    ]
    return pd.DataFrame(rows)


def build_topic_share_dataframe(topic_share):
    """Flatten topic_share entries into a flat dataframe."""
    if not topic_share:
        return pd.DataFrame()

    rows = [
        {
            "display_name": ts["display_name"],
            "value": ts["value"],
            "domain": extract_display_name(ts.get("domain", {})),
        }
        for ts in topic_share
    ]
    return pd.DataFrame(rows)


def build_domain_breakdown_dataframe(domain_breakdown, total_works_count=None):
    """
    Flatten fetch_domain_breakdown results into a flat dataframe.

    OpenAlex's group_by=primary_topic.domain.id only returns a group for
    works that actually have a primary_topic assigned - works with none
    (no primary topic at all) are simply missing from the response, not
    grouped under 'unknown' or 'Other'. Left alone, that makes the domain
    totals undercount the institution's real works_count with no visible
    trace of the gap.

    If total_works_count is provided (e.g. the institution's works_count),
    any shortfall between that and the sum of the grouped domains is added
    back as an explicit 'Other' row, so the chart/table always accounts for
    100% of the institution's works.
    """
    if not domain_breakdown and not total_works_count:
        return pd.DataFrame()

    if domain_breakdown:
        df = pd.DataFrame(domain_breakdown)
        df.columns = ["Domain", "Total Works"]
    else:
        df = pd.DataFrame(columns=["Domain", "Total Works"])

    if total_works_count:
        assigned = df["Total Works"].sum() if not df.empty else 0
        missing = total_works_count - assigned
        if missing > 0:
            df = pd.concat(
                [df, pd.DataFrame([{"Domain": "Other", "Total Works": missing}])],
                ignore_index=True,
            )

    return df


def build_topic_breakdown_dataframe(topic_breakdown, domain_lookup=None):
    """
    Flatten fetch_topic_breakdown results into a flat dataframe, with an
    optional domain_lookup (display_name -> domain) to color topics that
    also appear in the institution's top-25 list. Topics outside that
    top-25 are labeled 'Other' since OpenAlex's
    group_by response doesn't include domain/field/subfield directly.
    """
    if not topic_breakdown:
        return pd.DataFrame()

    domain_lookup = domain_lookup or {}
    rows = [
        {
            "display_name": t["display_name"],
            "count": t["count"],
            "domain": domain_lookup.get(t["display_name"], "Other"),
        }
        for t in topic_breakdown
    ]
    return pd.DataFrame(rows)


def build_topic_network(works, top_n=30):
    """
    Build a topic co-occurrence graph from a list of work objects (each
    with a 'topics' list). Nodes are topics; an edge between two topics
    means at least one work was tagged with both. Returns (nodes_df, edges_df).
    """
    if not works:
        return pd.DataFrame(), pd.DataFrame()

    topic_freq = Counter()
    domain_lookup = {}
    edge_weights = Counter()

    for w in works:
        topics = w.get("topics") or []
        names = []
        for t in topics:
            name = t.get("display_name")
            if not name:
                continue
            names.append(name)
            topic_freq[name] += 1
            domain_lookup[name] = extract_display_name(t.get("domain", {}))

        for a, b in itertools.combinations(sorted(set(names)), 2):
            edge_weights[(a, b)] += 1

    if not topic_freq:
        return pd.DataFrame(), pd.DataFrame()

    top_topics = {name for name, _ in topic_freq.most_common(top_n)}

    nodes_df = pd.DataFrame([
        {"display_name": name, "count": freq, "domain": domain_lookup.get(name, "Unknown")}
        for name, freq in topic_freq.items() if name in top_topics
    ])

    edges_df = pd.DataFrame([
        {"source": a, "target": b, "weight": weight}
        for (a, b), weight in edge_weights.items()
        if a in top_topics and b in top_topics and weight > 0
    ])

    return nodes_df, edges_df