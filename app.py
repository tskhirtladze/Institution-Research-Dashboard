import os

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

import networkx as nx

from openalex_api import fetch_all_countries, fetch_institutions, fetch_institution_by_id, fetch_domain_breakdown, fetch_topic_counts_by_domain, fetch_institution_works_topics, search_institutions
from data_processing import (
    build_years_dataframe,
    build_topics_dataframe,
    build_topic_share_dataframe,
    build_domain_breakdown_dataframe,
    build_topic_network,
)
os.environ.get("OPENALEX_API_KEY", "")



# Page config
st.set_page_config(
    page_title="Institution Research Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

from theme import INK, INK_SOFT, NAVY, GOLD, RULE, PAPER, PAPER_SUBTLE, CHART_PALETTE, inject_css, styled_chart, eyebrow

inject_css()

def get_api_key():
    """
    OpenAlex has required a key on every request since Feb 13, 2026
    (free - sign up at https://openalex.org/settings/api). Without one,
    requests fail once a tiny trial allowance is used up, which is what
    causes the dashboard to show no data at all.
    """
    if st.session_state.get("openalex_api_key"):
        return st.session_state["openalex_api_key"]
    try:
        if "OPENALEX_API_KEY" in st.secrets:
            return st.secrets["OPENALEX_API_KEY"]
    except Exception:
        pass
    return os.environ.get("OPENALEX_API_KEY", "")


# ========== SELECTION INTERFACE ==========
st.markdown('<div class="masthead-title">Institution Research Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="masthead-rule"></div>', unsafe_allow_html=True)
st.markdown('<div class="masthead-sub">Select a country and institution to open its research profile</div>', unsafe_allow_html=True)

api_key = get_api_key()


SORT_OPTIONS = {
    "Most Works": "works_count:desc",
    "Most Citations": "cited_by_count:desc",
    "Name (A-Z)": "display_name",
}

# Create selection columns
col1, col2, col3, col4 = st.columns([2.5, 2, 1.5, 1])

with col1:
    countries = fetch_all_countries(api_key=api_key)
    selected_country = st.selectbox(
        "Country",
        options=countries,
        index=countries.index('GE') if 'GE' in countries else 0,
        help="Choose a country to see its institutions"
    )

with col2:
    name_query = st.text_input(
        "Search by name",
        placeholder="e.g., Georgian National University",
        help="Can't find it in the dropdown? Search by name instead."
    )

with col3:
    sort_label = st.selectbox(
        "Sort by",
        options=list(SORT_OPTIONS.keys()),
        index=0,
        help="Institutions are sorted so the ones with real data show up first"
    )

with col4:
    direct_id = st.text_input(
        "Or enter an ID",
        placeholder="e.g., I102808428",
        help="Enter OpenAlex institution ID directly"
    )

# ========== DETERMINE SELECTED INSTITUTION ==========
organization = None

if direct_id:
    organization = fetch_institution_by_id(direct_id, api_key=api_key)
    if organization is None:
        st.error(f"❌ Institution ID '{direct_id}' not found. Please try another ID.")
        st.stop()
elif name_query:
    institutions = search_institutions(selected_country, name_query, api_key=api_key)
    if not institutions:
        st.warning(f"No institutions matching '{name_query}' found in {selected_country}.")
        st.stop()

    institution_options = [
        f"{inst['display_name']} | {inst['id'].split('/')[-1]} | {inst.get('country_code', 'N/A')}"
        for inst in institutions
    ]
    selected_option = st.selectbox("Matching institutions", options=institution_options, index=0)
    selected_index = institution_options.index(selected_option)
    organization = institutions[selected_index]
else:
    institutions = fetch_institutions(selected_country, sort_by=SORT_OPTIONS[sort_label], api_key=api_key)
    if not institutions:
        st.error(f"No institutions found for country: {selected_country}")
        st.stop()

    institution_options = [
        f"{inst['display_name']} | {inst['id'].split('/')[-1]} | {inst.get('country_code', 'N/A')}"
        for inst in institutions
    ]
    selected_option = st.selectbox("Institution", options=institution_options, index=0)
    selected_index = institution_options.index(selected_option)
    organization = institutions[selected_index]

if organization is None:
    st.error("No institution selected")
    st.stop()

# ========== EXTRACT VARIABLES ==========
org_id = organization['id']
org_ror = organization['ror']
org_name = organization['display_name']
org_country_code = organization['country_code']
org_type = organization['type']
org_url = organization['homepage_url']
org_image_thumbnail_url = organization.get('image_thumbnail_url', '')
org_display_name_acronyms = organization.get('display_name_acronyms', [])
org_display_name_alternatives = organization.get('display_name_alternatives', [])
org_works_count = organization['works_count']
org_cited_by_count = organization['cited_by_count']
org_summary_stats = organization['summary_stats']
org_ids = organization.get('ids', {})
org_geo = organization.get('geo', {})
org_associated_institutions = organization.get('associated_institutions', [])
org_counts_by_year = organization.get('counts_by_year', [])
org_topics = organization.get('topics', [])
org_topic_share = organization.get('topic_share', [])
org_status = organization.get('status', 'unknown')
org_updated_date = organization.get('updated_date', '')
org_created_date = organization.get('created_date', '')
org_lineage = organization.get('lineage', [])
org_is_super_system = organization.get('is_super_system', False)

# ========== DATA PREPARATION ==========
df_years = build_years_dataframe(org_counts_by_year)
df_topics = build_topics_dataframe(org_topics)
df_topic_share = build_topic_share_dataframe(org_topic_share)

# ========== DEBUG: RAW API RESPONSE ==========
# Shows exactly what OpenAlex returned for the selected institution, so a
# "0 works" or "no data" result can be checked against the real API response
# instead of guessed at. I’ll delete this block later, once the users have tested it and I’m sure there are no bugs.
with st.expander("Debug: raw API response for this institution"):
    st.write(f"**works_count:** {org_works_count}  |  **cited_by_count:** {org_cited_by_count}  "
             f"|  **counts_by_year entries:** {len(org_counts_by_year)}  |  **topics entries:** {len(org_topics)}")
    st.json(organization, expanded=False)

# ========== SIDEBAR ==========
with st.sidebar:
    st.caption("Built by [Tornike Skhirtladze](https://www.linkedin.com/in/tornike-skhirtladze-463120b6/)")
    st.markdown("---")
    if org_image_thumbnail_url:
        try:
            st.image(org_image_thumbnail_url, width=200)
        except Exception:
            pass
    st.markdown(f"### {org_display_name_acronyms[0] if org_display_name_acronyms else 'Institution'}")
    eyebrow("Key metrics")
    st.metric(
        "Total Works",
        f"{org_works_count:,}",
        help="Total number of research outputs (articles, books, datasets, etc.) attributed to this institution in OpenAlex."
    )
    st.metric(
        "Total Citations",
        f"{org_cited_by_count:,}",
        help="Total number of times this institution's works have been cited by other works."
    )
    st.metric(
        "h-index",
        org_summary_stats.get('h_index', 'N/A'),
        help="The institution has at least h works that have each been cited at least h times."
    )
    st.metric(
        "i10-index",
        f"{org_summary_stats.get('i10_index', 0):,}",
        help="The number of works by this institution that have been cited at least 10 times."
    )
    st.metric(
        "2yr Mean Citedness",
        f"{org_summary_stats.get('2yr_mean_citedness', 0):.2f}",
        help="Average number of citations received in a given year by works published in the two preceding years - similar to a journal impact factor, but for an institution."
    )
    if not df_years.empty:
        st.metric(
            "OA Rate",
            f"{df_years['oa_percentage'].mean():.1f}%",
            help="Average share of this institution's works that are freely available (open access) rather than paywalled."
        )
    st.markdown("---")
    eyebrow("Links")
    st.markdown(f"[Website]({org_url})")
    st.markdown(f"[OpenAlex]({org_id})")
    st.markdown(f"[ROR]({org_ror})")
    if org_ids and 'wikipedia' in org_ids:
        st.markdown(f"[Wikipedia]({org_ids['wikipedia']})")

# ========== MAIN CONTENT ==========
st.markdown(f'<div class="masthead-title" style="font-size:2.2rem;">{org_name}</div>', unsafe_allow_html=True)
st.markdown('<div class="masthead-rule"></div>', unsafe_allow_html=True)
st.markdown('<div class="masthead-sub">Research output, impact, and topics</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Research Output", "Research Topics", "Geographic & Network", "Advanced Analytics", "About"])

# TAB 1: Research Output
with tab1:
    st.header("Publication and Citation Trends")

    if not df_years.empty:
        st.markdown('''
        The following line chart shows how many papers this institution published each year, how many were free to read, and how many citations they got. Helps you see if research output is growing or shrinking over time.
        ''')
        st.caption("OpenAlex only reports yearly counts for the last 10 years, so totals here will fall short of the institution's all-time paper count.")
        # Chart 1: Publications & Citations Timeline
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=df_years['year'], y=df_years['works_count'],
            name='Total Works', line=dict(color=CHART_PALETTE[0], width=3)
        ))
        fig1.add_trace(go.Scatter(
            x=df_years['year'], y=df_years['oa_works_count'],
            name='Open Access Works', line=dict(color=CHART_PALETTE[2], width=3)
        ))
        fig1.add_trace(go.Scatter(
            x=df_years['year'], y=df_years['cited_by_count'],
            name='Citations', line=dict(color=CHART_PALETTE[1], width=3), yaxis='y2'
        ))
        fig1.update_layout(
            title='Publications & Citations Over Time',

            xaxis=dict(
                title='Year',
                title_font=dict(color=INK),
                tickfont=dict(color=INK_SOFT),
            ),

            yaxis=dict(
                title='Number of Works',
                title_font=dict(color=INK),
                tickfont=dict(color=INK_SOFT),
            ),

            yaxis2=dict(
                title='Citations',
                title_font=dict(color=INK),
                tickfont=dict(color=INK_SOFT),
                overlaying='y',
                side='right',
            ),

            hovermode='x unified',

            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(
                    color=INK,
                    family="'IBM Plex Mono', monospace",
                    size=12
                )
            )
        )
        st.plotly_chart(styled_chart(fig1, height=400), width='stretch')

        # Chart 2: Open vs Closed Access
        eyebrow("Access")
        st.markdown('''
        The following stacked bar chart shows how many papers were free to read (open access) versus paywalled (closed access) each year. The taller the green part, the more open the institution's research is.
        ''')

        fig2 = go.Figure()

        fig2.add_trace(go.Bar(
            x=df_years['year'],
            y=df_years['oa_works_count'],
            name='Open Access',
            marker_color=CHART_PALETTE[2]
        ))

        fig2.add_trace(go.Bar(
            x=df_years['year'],
            y=df_years['non_oa_works'],
            name='Closed Access',
            marker_color=CHART_PALETTE[3]
        ))

        fig2.update_layout(
            title='Open vs. closed access, by year',
            xaxis=dict(
                title='Year',
                title_font=dict(color=INK),
                tickfont=dict(color=INK_SOFT),
            ),
            yaxis=dict(
                title='Number of Works',
                title_font=dict(color=INK),
                tickfont=dict(color=INK_SOFT),
            ),
            barmode='stack',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(
                    color=INK,
                    family="'IBM Plex Mono', monospace",
                    size=12
                )
            )
        )

        st.plotly_chart(styled_chart(fig2, height=340), width='stretch')

        # Chart 3: Citation Velocity
        eyebrow("Impact")
        st.markdown('''
        The following line chart shows the average number of citations each paper got, by publication year. A rising line means newer papers are getting noticed faster.
        ''')
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=df_years['year'], y=df_years['citation_velocity'],
            name='Citation Velocity', line=dict(color=CHART_PALETTE[4], width=3),
            marker=dict(size=8)
        ))
        fig3.update_layout(xaxis_title='Year', yaxis_title='Citations/Work', hovermode='x unified', title='Citations per Work by Year',
                           xaxis=dict(
                               title_font=dict(color=INK),
                               tickfont=dict(color=INK_SOFT),
                           ),
                           yaxis=dict(
                               title_font=dict(color=INK),
                               tickfont=dict(color=INK_SOFT),
                           )
                           )
        st.plotly_chart(styled_chart(fig3, height=340), width='stretch')

        st.markdown('''
        The following area chart shows what percentage of papers were open access each year. Useful for seeing if the institution is becoming more or less open over time.
        ''')
        col1, col2 = st.columns(2)
        with col1:
            eyebrow("Open access share")
            fig_oa = px.area(df_years, x='year', y='oa_percentage', title='Open Access % Over Time',
                             color_discrete_sequence=[CHART_PALETTE[2]])
            fig_oa.update_layout(
                xaxis=dict(
                    title_font=dict(color=INK),
                    tickfont=dict(color=INK_SOFT),
                ),
                yaxis=dict(
                    title_font=dict(color=INK),
                    tickfont=dict(color=INK_SOFT),
                )
            )
            st.plotly_chart(styled_chart(fig_oa, height=380), width='stretch')
        with col2:
            eyebrow("Yearly summary")
            summary = df_years[['year', 'works_count', 'cited_by_count', 'oa_percentage']].copy()
            summary.columns = ['Year', 'Works', 'Citations', 'OA %']
            summary['Works'] = summary['Works'].apply(lambda x: f"{x:,}")
            summary['Citations'] = summary['Citations'].apply(lambda x: f"{x:,}")
            summary['OA %'] = summary['OA %'].apply(lambda x: f"{x:.1f}%")
            st.dataframe(summary, width='stretch', height=380)

        with st.expander("Complete yearly data"):
            st.markdown('''
            Complete Yearly Data (table): The full, unformatted data behind all the charts on this page. Use this if you want every number OpenAlex provided, not just the summary.
            ''')
            st.dataframe(df_years, width='stretch')
    else:
        st.info("No yearly data available for this institution.")

# TAB 2: Research Topics
with tab2:
    st.header("Research Topics & Domain Analysis")

    if not df_topics.empty:
        eyebrow("By domain")
        st.markdown('''
        The following donut chart shows how the institution's papers are split across broad research areas, like Life Sciences or Physical Sciences.
        ''')
        col1, col2 = st.columns([2, 1])

        domain_data = fetch_domain_breakdown(org_id, api_key=api_key)
        domain_works = build_domain_breakdown_dataframe(domain_data, total_works_count=org_works_count)
        if not domain_works.empty:
            domain_works = domain_works.groupby('Domain', as_index=False)['Total Works'].sum()

        with col1:
            if not domain_works.empty:
                fig_domains = px.pie(
                    domain_works, values='Total Works', names='Domain',
                    title='Research Output by Domain', hole=0.5,
                    color_discrete_sequence=CHART_PALETTE
                )
                st.plotly_chart(styled_chart(fig_domains, height=460), width='stretch')
                if 'Other' in domain_works['Domain'].values:
                    st.caption(
                        "'Other' represents works with no primary topic domain assigned in OpenAlex, "
                        "so every one of the institution's works is accounted for."
                    )
            else:
                st.info("No domain breakdown available for this institution.")

        with col2:
            st.subheader("Domain Breakdown")
            if not domain_works.empty:
                for _, row in domain_works.iterrows():
                    pct = (row['Total Works'] / domain_works['Total Works'].sum() * 100)
                    st.metric(str(row['Domain']), f"{row['Total Works']:,} ({pct:.1f}%)")

        st.markdown("---")

        st.subheader("Top Topics")
        st.markdown('''
        The following bar chart shows the specific research topics this institution publishes the most about.
        ''')
        st.caption("Shows only the institution's top 25 listed topics from OpenAlex, narrowed further by the slider above - not a full breakdown of every topic.")
        top_n = st.slider("Number of topics", 5, 25, 15)
        df_top = df_topics.sort_values('count', ascending=False).head(top_n)
        fig_topics = px.bar(df_top, x='count', y='display_name', orientation='h',
                            title=f'Top {top_n} Topics', color='count',
                            color_continuous_scale=['#C9D6E3', NAVY])
        fig_topics.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False)
        st.plotly_chart(styled_chart(fig_topics, height=700), width='stretch')

        st.subheader("Fields")
        st.markdown('''
        The bar chart groups topics into broader fields, like Medicine or Computer Science. Shows which fields the institution focuses on most.
        ''')
        st.caption("Grouped from the institution's top 25 listed topics only - a curated subset, not every topic OpenAlex has for this institution.")
        len_unique_fields = len(df_topics['field'].unique())
        field_n = st.slider("Number of fields", min_value=1, max_value=len_unique_fields, value=5, key='field')
        field_works = df_topics.groupby('field')['count'].sum().reset_index()
        field_works.columns = ['Field', 'Total Works']
        field_works = field_works.sort_values('Total Works', ascending=False).head(field_n)
        fig_fields = px.bar(field_works, x='Total Works', y='Field', orientation='h', title=f'Top {field_n} Fields',
                            color='Total Works', color_continuous_scale=['#C9D6E3', NAVY])
        fig_fields.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False)
        st.plotly_chart(styled_chart(fig_fields, height=380), width='stretch')

        st.subheader("Subfields")
        st.markdown('''
        A middle level between topics and fields, showing more specific research areas than fields but broader than individual topics.
        ''')
        st.caption("Grouped from the institution's top 25 listed topics only - a curated subset, not every topic OpenAlex has for this institution.")
        len_unique_subfields = len(df_topics['subfield'].unique())
        subfield_n = st.slider("Number of subfields", min_value=1, max_value=len_unique_subfields, value=5,
                               key='subfield')
        subfield_works = df_topics.groupby('subfield')['count'].sum().reset_index()
        subfield_works.columns = ['Subfield', 'Total Works']
        subfield_works = subfield_works.sort_values('Total Works', ascending=False).head(subfield_n)
        fig_sub = px.bar(subfield_works, x='Total Works', y='Subfield', orientation='h',
                         title=f'Top {subfield_n} Subfields',
                         color='Total Works', color_continuous_scale=['#C9D6E3', NAVY])
        fig_sub.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False)
        st.plotly_chart(styled_chart(fig_sub, height=460), width='stretch')

        st.markdown("---")
        st.subheader("Topic Share & Score Analysis")
        st.markdown('''
        Ranks topics by how distinctive they are to this institution, not by paper count. A topic can rank high with few papers if this institution accounts for an unusually large slice of the world's research on it.
        ''')
        st.caption("Based on the institution's top 25 listed topics only, not every topic OpenAlex has for this institution.")

        share_n = st.slider("Share topics", 5, 25, 15, key='share')
        df_share = df_topic_share.sort_values('value', ascending=False).head(share_n)
        fig_share = px.bar(df_share, x='value', y='display_name', orientation='h',
                           title=f'Top {share_n} by Share', color='value',
                           color_continuous_scale=['#C9D6E3', NAVY])
        fig_share.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False)
        st.plotly_chart(styled_chart(fig_share, height=560), width='stretch')

        st.subheader("Topic Co-occurrence Network")
        st.markdown('''
        The network diagram shows which research topics often appear together in the same paper. Lines connect topics that overlap, and thicker lines mean they overlap more often.
        ''')
        st.caption("Built from the institution's 200 most-cited papers and capped to the top 30 topics, for readability - not all of the institution's papers.")

        works = fetch_institution_works_topics(org_id, api_key=api_key)
        nodes_df, edges_df = build_topic_network(works, top_n=30)

        if not nodes_df.empty:
            G = nx.Graph()
            for _, row in nodes_df.iterrows():
                G.add_node(row['display_name'], count=row['count'], domain=row['domain'])
            for _, row in edges_df.iterrows():
                G.add_edge(row['source'], row['target'], weight=row['weight'])

            pos = nx.spring_layout(G, k=0.6, iterations=50, seed=42)

            # Edge traces - one line per edge, thickness scaled by co-occurrence weight
            edge_traces = []
            max_weight = edges_df['weight'].max() if not edges_df.empty else 1
            for _, row in edges_df.iterrows():
                x0, y0 = pos[row['source']]
                x1, y1 = pos[row['target']]
                edge_traces.append(go.Scatter(
                    x=[x0, x1, None], y=[y0, y1, None],
                    mode='lines',
                    line=dict(width=0.5 + 3 * (row['weight'] / max_weight), color=RULE),
                    hoverinfo='none',
                    showlegend=False
                ))

            # Node trace - colored by domain, sized by frequency
            domains = nodes_df['domain'].unique()
            domain_color = {d: CHART_PALETTE[i % len(CHART_PALETTE)] for i, d in enumerate(domains)}

            node_traces = []
            for domain in domains:
                sub = nodes_df[nodes_df['domain'] == domain]
                xs = [pos[n][0] for n in sub['display_name']]
                ys = [pos[n][1] for n in sub['display_name']]
                node_traces.append(go.Scatter(
                    x=xs, y=ys, mode='markers',
                    marker=dict(
                        size=[8 + c * 3 for c in sub['count']],
                        color=domain_color[domain],
                        line=dict(width=1, color=PAPER)
                    ),
                    text=sub['display_name'],
                    hovertemplate='<b>%{text}</b><br>Appears in %{marker.size} works<extra></extra>',
                    name=domain
                ))

            fig_network = go.Figure(data=edge_traces + node_traces)
            fig_network.update_layout(
                title='Topic Co-occurrence Network',
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                legend_title='Domain',
                height=650
            )
            st.plotly_chart(styled_chart(fig_network), width='stretch')
        else:
            st.info("Not enough topic co-occurrence data to build a network for this institution.")

# TAB 3: Geographic & Network
with tab3:
    st.header("Geographic & Institutional Network")

    if org_geo:
        col1, col2 = st.columns([3, 1])
        with col1:
            map_data = pd.DataFrame({
                'lat': [org_geo.get('latitude')],
                'lon': [org_geo.get('longitude')],
                'name': [org_name]
            })
            if not map_data['lat'].isna().any():
                st.map(map_data, zoom=8, width='stretch')
                st.caption(
                    f"{org_geo.get('city', 'N/A')}, {org_geo.get('country', 'N/A')} · ({org_geo.get('latitude', 0):.4f}, {org_geo.get('longitude', 0):.4f})")
            else:
                st.info("Location data not available")
        with col2:
            st.subheader("Location")
            st.write(f"**City:** {org_geo.get('city', 'N/A')}")
            st.write(f"**Country:** {org_geo.get('country', 'N/A')} ({org_country_code})")
            st.write(f"**Region:** {org_geo.get('region', 'N/A')}")
            if org_geo.get('latitude') and org_geo.get('longitude'):
                st.code(f"Lat: {org_geo['latitude']}\nLon: {org_geo['longitude']}")

        st.markdown("---")
        if org_associated_institutions:
            st.subheader("Associated Institutions")
            st.markdown('''
            The network diagram shows how this institution connects to others, like parent universities, child campuses, or related organizations. The institution itself sits in the center, with connected institutions branching out.
            ''')

            assoc_df = pd.DataFrame(org_associated_institutions)

            REL_COLOR = {'parent': NAVY, 'child': CHART_PALETTE[2], 'related': GOLD}
            ROW_SPACING = 0.75
            COL_SPACING = 1.0
            MAX_PER_ROW = 8
            MAX_PER_COL = 6  # for related institutions' side grid
            MAX_NODES_PER_GROUP = 25  # diagram cap per relationship type; full list always in the table


            def short_label(name, max_len=18):
                return name if len(name) <= max_len else name[:max_len - 1] + "…"


            def acronym_or_name(record_or_name, acronyms=None, max_len=18):
                """
                Prefer an institution's acronym for chart labels; fall back to its
                display name (truncated) when no acronym is available.
                Accepts either:
                  - acronym_or_name(org_name, org_display_name_acronyms)
                  - acronym_or_name(row)  where row is a dict/Series with
                    'display_name' and optionally 'display_name_acronyms'
                """
                if acronyms is None:
                    # record_or_name is a dict-like row (e.g. from assoc_df)
                    name = record_or_name.get('display_name', '')
                    acronyms = record_or_name.get('display_name_acronyms') or []
                else:
                    name = record_or_name

                if acronyms:
                    return acronyms[0]
                return name if len(name) <= max_len else name[:max_len - 1] + "…"


            def grid_positions(n, base_y, direction):
                positions = []
                for i in range(n):
                    row = i // MAX_PER_ROW
                    col = i % MAX_PER_ROW
                    row_count = min(MAX_PER_ROW, n - row * MAX_PER_ROW)
                    x = (col - (row_count - 1) / 2) * COL_SPACING
                    y = base_y + direction * row * ROW_SPACING
                    positions.append((x, y))
                return positions


            def side_grid_positions(n, max_per_col=MAX_PER_COL):
                """
                Lay out n nodes split alternately left/right of center, each side
                stacked as a vertical grid (columns growing outward in x, rows
                centered around y=0). Avoids the label overlap that a flat
                single-row fan-out gets once there are more than a handful of
                related institutions.
                """
                positions = [None] * n
                side_counters = {1: 0, -1: 0}
                for i in range(n):
                    side = 1 if i % 2 == 0 else -1
                    idx = side_counters[side]
                    side_counters[side] += 1
                    col = idx // max_per_col
                    row = idx % max_per_col
                    x = side * (1.4 + col * COL_SPACING)
                    y = (row - (max_per_col - 1) / 2) * (ROW_SPACING * 0.8)
                    positions[i] = (x, y)
                return positions


            fig_assoc = go.Figure()
            max_extent_x, max_extent_y = 2.5, 2.0

            for rel_type, group in assoc_df.groupby('relationship'):
                group = group.sort_values('display_name').reset_index(drop=True)
                total_n = len(group)
                truncated = total_n > MAX_NODES_PER_GROUP
                shown = group.head(MAX_NODES_PER_GROUP) if truncated else group
                n = len(shown)
                color = REL_COLOR.get(rel_type, INK_SOFT)

                if rel_type == 'parent':
                    positions = grid_positions(n, base_y=1.2, direction=1)
                elif rel_type == 'child':
                    positions = grid_positions(n, base_y=-1.2, direction=-1)
                elif rel_type == 'related':
                    positions = side_grid_positions(n)
                else:
                    positions = grid_positions(n, base_y=0, direction=1)

                for (x, y) in positions:
                    fig_assoc.add_trace(go.Scatter(
                        x=[0, x], y=[0, y], mode='lines',
                        line=dict(width=1, color=RULE), hoverinfo='none', showlegend=False
                    ))
                    max_extent_x = max(max_extent_x, abs(x) + 1.5)
                    max_extent_y = max(max_extent_y, abs(y) + 0.6)

                xs = [p[0] for p in positions]
                ys = [p[1] for p in positions]
                text_positions = ['top center' if y >= 0 else 'bottom center' for y in ys]

                fig_assoc.add_trace(go.Scatter(
                    x=xs, y=ys, mode='markers+text',
                    marker=dict(size=16, color=color, line=dict(width=1, color=PAPER)),
                    text=[
                        acronym_or_name(r) if isinstance(r, dict) else short_label(r)
                        for r in shown.to_dict('records')
                    ],
                    textposition=text_positions,
                    textfont=dict(size=9, color=INK),
                    customdata=shown['display_name'],
                    name=str(rel_type).capitalize(),
                    hovertemplate='<b>%{customdata}</b><br>' + str(rel_type).capitalize() + '<extra></extra>'
                ))

                # "+N more" summary node if this group was truncated
                if truncated:
                    remaining = total_n - n
                    if rel_type == 'parent':
                        more_pos = grid_positions(n + 1, base_y=1.2, direction=1)[-1]
                    elif rel_type == 'child':
                        more_pos = grid_positions(n + 1, base_y=-1.2, direction=-1)[-1]
                    elif rel_type == 'related':
                        more_pos = side_grid_positions(n + 1)[-1]
                    else:
                        more_pos = grid_positions(n + 1, base_y=0, direction=1)[-1]

                    mx, my = more_pos
                    fig_assoc.add_trace(go.Scatter(
                        x=[0, mx], y=[0, my], mode='lines',
                        line=dict(width=1, color=RULE, dash='dot'), hoverinfo='none', showlegend=False
                    ))
                    fig_assoc.add_trace(go.Scatter(
                        x=[mx], y=[my], mode='markers+text',
                        marker=dict(size=16, color=PAPER, line=dict(width=1.5, color=color)),
                        text=[f"+{remaining} more"], textposition='top center' if my >= 0 else 'bottom center',
                        textfont=dict(size=9, color=INK_SOFT),
                        showlegend=False,
                        hovertemplate=f'{remaining} more {str(rel_type)} institution(s) — see table below<extra></extra>'
                    ))
                    max_extent_x = max(max_extent_x, abs(mx) + 1.5)
                    max_extent_y = max(max_extent_y, abs(my) + 0.6)

            fig_assoc.add_trace(go.Scatter(
                x=[0], y=[0], mode='markers+text',
                marker=dict(size=50, color=GOLD, line=dict(width=2, color=NAVY)),
                text=[acronym_or_name(org_name, org_display_name_acronyms, max_len=24)], textposition='middle center',
                textfont=dict(size=10, color=PAPER),
                showlegend=False,
                hovertemplate=f'<b>{org_name}</b><extra></extra>'
            ))

            fig_assoc.update_layout(
                title='Associated Institutions',
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-max_extent_x, max_extent_x]),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-max_extent_y, max_extent_y]),
                height=min(1000, max(460, 90 * (max_extent_y * 2))),
                margin=dict(t=60, l=20, r=20, b=20),
                legend_title='Relationship'
            )
            st.plotly_chart(styled_chart(fig_assoc), width='stretch')

            total_count = len(assoc_df)
            shown_count = min(total_count,
                              sum(min(len(g), MAX_NODES_PER_GROUP) for _, g in assoc_df.groupby('relationship')))
            if total_count > shown_count:
                st.caption(
                    f"Showing {shown_count} of {total_count} associated institutions on the diagram. Full list below.")

            with st.expander(f"View all {total_count} as a table"):
                st.markdown('''
                A full list of every institution connected to this one, with its type and relationship (parent, child, or related). Use this if the diagram is too crowded to read everything.
                ''')
                st.dataframe(assoc_df[['display_name', 'type', 'relationship']], width='stretch')
        else:
            st.info("No associated institutions found.")

        st.markdown("---")
        st.subheader("Institution Details")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Type",
                org_type.capitalize() if org_type else "N/A",
                help="The institution category as classified by OpenAlex, e.g. education, healthcare, government, company, or nonprofit."
            )
            st.metric(
                "Super System",
                "No" if not org_is_super_system else "Yes",
                help="Whether this institution is a large umbrella system encompassing multiple sub-institutions (e.g. a university system or hospital network)."
            )
        with col2:
            st.metric(
                "Lineage",
                len(org_lineage),
                help="Number of institutions in this institution's organizational hierarchy, including itself and any parent organizations."
            )
            st.metric(
                "Status",
                org_status.capitalize() if org_status else "N/A",
                help="Whether this institution record is active or has been marked as merged/deprecated in OpenAlex."
            )
        with col3:
            st.metric(
                "Created",
                org_created_date[:10] if org_created_date else "N/A",
                help="The date this institution's record was first added to OpenAlex."
            )
            st.metric(
                "Updated",
                org_updated_date[:10] if org_updated_date else "N/A",
                help="The date this institution's record was last refreshed with new data."
            )

        st.markdown("---")
        st.subheader("Alternative Names")
        if org_display_name_alternatives:
            for name in org_display_name_alternatives:
                st.write(f"- {name}")
        else:
            st.info("No alternative names available.")
    else:
        st.info("Geographic data not available for this institution.")

# TAB 4: Advanced Analytics
with tab4:
    st.header("Advanced Research Analytics")

    if not df_years.empty:
        st.subheader("Cumulative Growth")
        st.markdown('''
        Shows the running total of works and citations added up over time, instead of yearly amounts. Shows how fast the institution has grown overall.
        ''')
        st.caption("OpenAlex only reports yearly counts for the last 10 years, so totals here will fall short of the institution's all-time paper count.")
        df_years_sorted = df_years.sort_values('year')
        df_years_sorted['cum_works'] = df_years_sorted['works_count'].cumsum()
        df_years_sorted['cum_citations'] = df_years_sorted['cited_by_count'].cumsum()
        df_years_sorted['cum_oa'] = df_years_sorted['oa_works_count'].cumsum()

        fig_cum = make_subplots(rows=1, cols=2, subplot_titles=("Works & Citations", "OA Works"),
                                specs=[[{"secondary_y": True}, {"type": "scatter"}]])
        fig_cum.add_trace(go.Scatter(x=df_years_sorted['year'], y=df_years_sorted['cum_works'], name='Works',
                                     line=dict(color=CHART_PALETTE[0], width=3)), row=1, col=1)
        fig_cum.add_trace(go.Scatter(x=df_years_sorted['year'], y=df_years_sorted['cum_citations'], name='Citations',
                                     line=dict(color=CHART_PALETTE[1], width=3)), row=1, col=1, secondary_y=True)
        fig_cum.add_trace(go.Scatter(x=df_years_sorted['year'], y=df_years_sorted['cum_oa'], name='OA Works',
                                     line=dict(color=CHART_PALETTE[2], width=3)), row=1, col=2)
        fig_cum.update_layout(showlegend=True, hovermode='x unified')
        st.plotly_chart(styled_chart(fig_cum, height=460), width='stretch')

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Domain Intensity")
            st.markdown('''
            Shows how research output is spread across broad domains, and how many distinct topics make up each one. Avg/Topic is Total Works ÷ Topics — a higher number means the domain's output is concentrated in fewer topics; a lower number means it's spread thin across many.
            ''')
            domain_data_adv = fetch_domain_breakdown(org_id, api_key=api_key)
            domain_works_adv = build_domain_breakdown_dataframe(domain_data_adv, total_works_count=org_works_count)

            topic_counts_full = fetch_topic_counts_by_domain(org_id, api_key=api_key)
            topic_counts_by_domain = pd.Series(topic_counts_full, name='Topics')
            domain_stats = domain_works_adv.set_index('Domain').join(topic_counts_by_domain, how='left')
            domain_stats['Topics'] = domain_stats['Topics'].fillna(0).astype(int)
            domain_stats['Avg/Topic'] = (
                    domain_stats['Total Works'] / domain_stats['Topics'].replace(0, np.nan)
            ).round(2)

            st.caption(
                "Total Works and Topics both cover every one of the institution's works, not just its "
                "top 25 listed topics - 'Other' represents works with no primary topic domain assigned, "
                "so it has no topics of its own and Avg/Topic is blank there."
            )
            st.dataframe(domain_stats.sort_values('Total Works', ascending=False), width='stretch')
        with col2:
            st.subheader("Top Topics")
            st.markdown('''
            Lists the institution's 10 most-published topics, with their paper count and research domain.
            ''')
            top_10 = df_topics.nlargest(10, 'count')[['display_name', 'count', 'domain']]
            st.dataframe(top_10, width='stretch')

        st.markdown("---")
        st.subheader("Year-over-Year Growth")
        st.markdown('''
        Shows how much faster or slower the institution's works, citations, and open-access output grew each year compared to the year before, as a percentage. Bars above zero mean growth; below zero means a decline from the prior year.
        ''')
        st.caption("Based on OpenAlex's last 10 years of yearly counts, so growth can't be calculated for the earliest year shown (no prior year to compare against) or for any year before this window.")
        df_growth = df_years_sorted.copy()
        df_growth['works_gr'] = df_growth['works_count'].pct_change() * 100
        df_growth['cit_gr'] = df_growth['cited_by_count'].pct_change() * 100
        df_growth['oa_gr'] = df_growth['oa_works_count'].pct_change() * 100
        df_growth = df_growth.replace([np.inf, -np.inf], np.nan)

        fig_gr = go.Figure()
        fig_gr.add_trace(go.Bar(x=df_growth['year'], y=df_growth['works_gr'], name='Works', marker_color=CHART_PALETTE[0]))
        fig_gr.add_trace(go.Bar(x=df_growth['year'], y=df_growth['cit_gr'], name='Citations', marker_color=CHART_PALETTE[1]))
        fig_gr.add_trace(go.Bar(x=df_growth['year'], y=df_growth['oa_gr'], name='OA', marker_color=CHART_PALETTE[2]))
        fig_gr.update_layout(title='YoY Growth Rates', xaxis_title='Year', yaxis_title='Growth %',
                             barmode='group', hovermode='x unified')
        st.plotly_chart(styled_chart(fig_gr, height=460), width='stretch')

        with st.expander("Growth data"):
            st.dataframe(df_growth[['year', 'works_count', 'works_gr', 'cited_by_count', 'cit_gr']], width='stretch')
    else:
        st.info("No data available for advanced analytics.")

# TAB 5: About
with tab5:
    st.header(f"About {org_name}")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Profile")
        acronyms = ', '.join(org_display_name_acronyms) if org_display_name_acronyms else ''
        primary_name = org_display_name_acronyms[0] if org_display_name_acronyms else org_name
        st.markdown(f"""**{org_name}** ({acronyms}) is a {org_type} institution in
        **{org_geo.get('city', 'N/A')}, {org_geo.get('country', 'N/A')}**, with
        **{org_works_count:,}** works and **{org_cited_by_count:,}** citations recorded in OpenAlex.""")

        st.markdown("---")
        eyebrow("Impact")
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Works", f"{org_works_count:,}",
                      help="Total number of research outputs attributed to this institution in OpenAlex.")
            st.metric("h-index", org_summary_stats.get('h_index', 'N/A'),
                      help="The institution has at least h works each cited at least h times.")
        with m2:
            st.metric("Citations", f"{org_cited_by_count:,}",
                      help="Total number of times this institution's works have been cited.")
            st.metric("i10-index", f"{org_summary_stats.get('i10_index', 0):,}",
                      help="Number of works cited at least 10 times.")
        with m3:
            st.metric("2yr Citedness", f"{org_summary_stats.get('2yr_mean_citedness', 0):.2f}",
                      help="Average citations per work published in the two preceding years, similar to a journal impact factor.")
            st.metric(
                "OA Rate",
                f"{df_years['oa_percentage'].mean():.1f}%" if not df_years.empty else "N/A",
                help="Average share of this institution's works that are freely available (open access)."
            )

        st.markdown("---\n### Alternative Names")
        if org_display_name_alternatives:
            for name in org_display_name_alternatives:
                st.write(f"- {name}")
        else:
            st.info("No alternative names available.")
    with col2:
        if org_image_thumbnail_url:
            try:
                st.image(org_image_thumbnail_url, width=200)
            except Exception:
                pass
        st.caption(f"Coat of Arms of {org_name}")
        st.markdown("---\n### Identifiers")
        if org_ids:
            for name, url in org_ids.items():
                if name and url is not None:
                    st.markdown(f"**{name.upper()}:**")
                    st.markdown(
                        f'<a href="{url}" target="_blank" rel="noopener noreferrer">{url.split("/")[-1]}</a>',
                        unsafe_allow_html=True
                    )
        else:
            st.info("No identifiers available.")

    st.markdown("---")
    st.subheader("External Resources")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"[🌐 Website]({org_url})")
        if org_ids and 'wikipedia' in org_ids:
            st.markdown(f"[📖 Wikipedia]({org_ids['wikipedia']})")
    with col2:
        st.markdown(f"[🔍 OpenAlex]({org_id})")
        st.markdown(f"[🏛️ ROR]({org_ror})")
    with col3:
        if org_ids and 'grid' in org_ids:
            try:
                st.markdown(f"[🔗 GRID](https://www.grid.ac/institutes/{org_ids['grid'].split('/')[-1]})")
            except Exception:
                pass
        if org_ids and 'wikidata' in org_ids:
            st.markdown(f"[📊 Wikidata]({org_ids['wikidata']})")

    st.markdown("---")
    st.subheader("Data Info")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Status", org_status.capitalize() if org_status else "N/A",
                  help="Whether this institution record is active or merged/deprecated in OpenAlex.")
    with col2:
        st.metric("Updated", org_updated_date[:10] if org_updated_date else "N/A",
                  help="The date this institution's record was last refreshed with new data.")
    with col3:
        st.metric("Created", org_created_date[:10] if org_created_date else "N/A",
                  help="The date this institution's record was first added to OpenAlex.")

    st.markdown("---")
    st.caption("Dashboard created using Streamlit | Data: OpenAlex")

# Footer
st.markdown("---")
st.markdown(f"<div style='text-align: center; color: #666; padding: 1rem;'>"
            f"<strong>{org_name} Research Dashboard</strong><br>"
            "Comprehensive analysis of research output, impact, and topics</div>",
            unsafe_allow_html=True)