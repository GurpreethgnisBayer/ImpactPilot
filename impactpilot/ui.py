"""UI rendering functions for each step of ImpactPilot."""

import streamlit as st
from impactpilot.query_suggest import suggest_pubmed_query
from impactpilot.services.pubmed_eutils import search_pubmed
from impactpilot.services.llm_provider import get_provider
from impactpilot.evidence_numbers import extract_all_numeric_evidence
from impactpilot.assumptions import derive_assumptions
from impactpilot.calc import compute_tco, compute_productivity
from impactpilot.report import build_brief_markdown


def render_step_0_idea():
    """Render Step 1: Idea input form."""
    st.header("Step 1: Define Your R&D Idea")
    
    # Title input with auto-update callback
    title = st.text_input(
        "Idea Title",
        key="idea_title_input",
        value=st.session_state.idea.get("title", ""),
        help="A concise title for your R&D idea",
        on_change=_auto_update_query_from_idea
    )
    
    # Description input with auto-update callback
    description = st.text_area(
        "Idea Description",
        key="idea_description_input",
        value=st.session_state.idea.get("description", ""),
        help="Describe your R&D idea in plain language",
        height=150,
        on_change=_auto_update_query_from_idea
    )
    
    st.selectbox(
        "Idea Type",
        options=["", "Software/Digital Tool", "Assay/Analytical Method", "Therapeutic/Drug", 
                 "Diagnostic", "Medical Device", "Platform Technology", "Process Optimization", "Other"],
        key="idea_type_input",
        index=0
    )
    
    st.selectbox(
        "R&D Stage",
        options=["", "Discovery/Research", "Proof of Concept", "Preclinical", 
                 "Phase 1 Clinical", "Phase 2 Clinical", "Phase 3 Clinical", "Regulatory/Commercialization"],
        key="rd_stage_input",
        index=0
    )
    
    st.text_input(
        "Tags (comma-separated)",
        key="idea_tags_input",
        help="Optional tags to categorize your idea"
    )


def render_step_1_evidence_shell():
    """Render Step 2: Evidence search with PubMed integration."""
    st.header("Step 2: Find Evidence")
    
    # Initialize query from idea if empty
    if not st.session_state.evidence_query.get("query") and st.session_state.auto_update_query:
        title = st.session_state.idea.get("title", "")
        description = st.session_state.idea.get("description", "")
        if title or description:
            provider = get_provider(st.session_state.llm_settings)
            st.session_state.evidence_query["query"] = suggest_pubmed_query(
                title, description, provider=provider
            )
    
    # Auto-update toggle
    auto_update = st.checkbox(
        "Auto-update query from idea",
        value=st.session_state.auto_update_query,
        key="auto_update_query_checkbox",
        help="Automatically update the search query when you change the idea title or description"
    )
    st.session_state.auto_update_query = auto_update
    
    # Query input
    query = st.text_input(
        "PubMed Search Query",
        value=st.session_state.evidence_query.get("query", ""),
        key="evidence_query_input",
        help="Search keywords (auto-suggested from your idea)"
    )
    st.session_state.evidence_query["query"] = query
    
    # Basic filters in columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        date_preset = st.selectbox(
            "Date Range",
            options=["2years", "5years", "10years", "all"],
            index=1,  # Default to 5years
            key="date_preset_select",
            format_func=lambda x: {
                "2years": "Last 2 years",
                "5years": "Last 5 years",
                "10years": "Last 10 years",
                "all": "All time"
            }[x]
        )
        st.session_state.evidence_query["date_preset"] = date_preset
    
    with col2:
        max_results = st.number_input(
            "Max Results",
            min_value=5,
            max_value=100,
            value=st.session_state.evidence_query.get("max_results", 20),
            step=5,
            key="max_results_input"
        )
        st.session_state.evidence_query["max_results"] = max_results
    
    with col3:
        sort = st.selectbox(
            "Sort By",
            options=["relevance", "pub_date"],
            index=0,
            key="sort_select",
            format_func=lambda x: "Relevance" if x == "relevance" else "Publication Date"
        )
        st.session_state.evidence_query["sort"] = sort
    
    # Advanced filters in expander
    with st.expander("Advanced Filters"):
        publication_types = st.multiselect(
            "Publication Types",
            options=[
                "Clinical Trial",
                "Meta-Analysis",
                "Randomized Controlled Trial",
                "Review",
                "Systematic Review",
                "Case Reports",
                "Comparative Study"
            ],
            default=st.session_state.evidence_query["advanced"].get("publication_types", []),
            key="publication_types_select"
        )
        st.session_state.evidence_query["advanced"]["publication_types"] = publication_types
        
        col1, col2 = st.columns(2)
        
        with col1:
            journal = st.text_input(
                "Journal",
                value=st.session_state.evidence_query["advanced"].get("journal", ""),
                key="journal_input",
                help="Filter by specific journal name"
            )
            st.session_state.evidence_query["advanced"]["journal"] = journal
            
            language = st.text_input(
                "Language",
                value=st.session_state.evidence_query["advanced"].get("language", ""),
                key="language_input",
                help="e.g., 'eng' for English"
            )
            st.session_state.evidence_query["advanced"]["language"] = language
        
        with col2:
            author = st.text_input(
                "Author",
                value=st.session_state.evidence_query["advanced"].get("author", ""),
                key="author_input",
                help="Filter by author name"
            )
            st.session_state.evidence_query["advanced"]["author"] = author
            
            field_restriction = st.selectbox(
                "Search In",
                options=["", "tiab", "title"],
                index=0,
                key="field_restriction_select",
                format_func=lambda x: {
                    "": "All fields",
                    "tiab": "Title/Abstract",
                    "title": "Title only"
                }[x]
            )
            st.session_state.evidence_query["advanced"]["field_restriction"] = field_restriction
        
        has_abstract = st.checkbox(
            "Require abstract",
            value=st.session_state.evidence_query["advanced"].get("has_abstract", True),
            key="has_abstract_checkbox"
        )
        st.session_state.evidence_query["advanced"]["has_abstract"] = has_abstract
    
    # Search button
    if st.button("🔍 Search PubMed", type="primary", use_container_width=True):
        if not query:
            st.error("Please enter a search query.")
        else:
            with st.spinner("Searching PubMed..."):
                results = search_pubmed(
                    query=query,
                    date_preset=date_preset,
                    max_results=int(max_results),
                    sort=sort,
                    journal=st.session_state.evidence_query["advanced"].get("journal", ""),
                    author=st.session_state.evidence_query["advanced"].get("author", ""),
                    language=st.session_state.evidence_query["advanced"].get("language", ""),
                    has_abstract=st.session_state.evidence_query["advanced"].get("has_abstract", True),
                    publication_types=st.session_state.evidence_query["advanced"].get("publication_types", []),
                    field_restriction=st.session_state.evidence_query["advanced"].get("field_restriction", "")
                )
                st.session_state.evidence_results = results
                st.success(f"Found {len(results)} articles")
    
    # Display results
    if st.session_state.evidence_results:
        st.markdown("---")
        st.subheader(f"Results ({len(st.session_state.evidence_results)} articles)")
        
        # Selection basket summary
        selected_count = len(st.session_state.evidence_selected_pmids)
        if selected_count > 0:
            st.info(f"📚 {selected_count} article(s) selected for analysis")
        
        # Display each result with checkbox
        for idx, article in enumerate(st.session_state.evidence_results):
            pmid = article["pmid"]
            
            # Checkbox for selection
            is_selected = pmid in st.session_state.evidence_selected_pmids
            selected = st.checkbox(
                f"Select",
                value=is_selected,
                key=f"select_pmid_{pmid}_{idx}",
                label_visibility="collapsed"
            )
            
            # Update selection set
            if selected and pmid not in st.session_state.evidence_selected_pmids:
                st.session_state.evidence_selected_pmids.add(pmid)
            elif not selected and pmid in st.session_state.evidence_selected_pmids:
                st.session_state.evidence_selected_pmids.remove(pmid)
            
            # Article citation
            st.markdown(
                f"""
                **{article['title']}**  
                {article['authors']} ({article['year']})  
                *{article['journal']}*  
                PMID: [{pmid}]({article['url']})
                """,
                unsafe_allow_html=False
            )
            
            # Show abstract in expander
            with st.expander("View Abstract"):
                st.write(article['abstract'])
            
            st.markdown("---")


def render_step_2_assumptions_shell():
    """Render Step 3: Assumptions with evidence-grounded values."""
    st.header("Step 3: Review Assumptions")
    
    # Get selected articles
    selected_pmids = st.session_state.evidence_selected_pmids
    selected_articles = [
        article for article in st.session_state.evidence_results
        if article["pmid"] in selected_pmids
    ]
    
    if not selected_articles:
        st.warning("⚠️ No articles selected. Please go back to Evidence step and select articles to analyze.")
        return
    
    st.info(f"📚 Analyzing {len(selected_articles)} selected article(s)")
    
    # Extract numeric evidence on first load or when selection changes
    if "last_analyzed_pmids" not in st.session_state or st.session_state.last_analyzed_pmids != selected_pmids:
        with st.spinner("Extracting numeric evidence from selected abstracts..."):
            # Extract numeric evidence
            extracted_evidence = extract_all_numeric_evidence(selected_articles)
            st.session_state.extracted_numeric_evidence = extracted_evidence
            
            # Derive assumptions
            assumptions = derive_assumptions(
                idea=st.session_state.idea,
                selected_articles=selected_articles,
                extracted_numeric_evidence=extracted_evidence
            )
            st.session_state.assumptions = assumptions
            st.session_state.last_analyzed_pmids = selected_pmids
    
    # Show extracted evidence summary
    with st.expander(f"📊 Extracted Numeric Evidence ({len(st.session_state.extracted_numeric_evidence)} items)", expanded=False):
        if st.session_state.extracted_numeric_evidence:
            for i, evidence in enumerate(st.session_state.extracted_numeric_evidence):
                st.markdown(f"""
                **{i+1}.** `{evidence['raw']}` ({evidence['type']})  
                **PMID:** {evidence['pmid']}  
                **Context:** "{evidence['context'][:150]}..."
                """)
                st.markdown("---")
        else:
            st.write("No numeric evidence found in selected abstracts.")
    
    st.markdown("---")
    
    # Display assumptions with teal highlighting for evidence-backed values
    assumptions = st.session_state.assumptions
    
    st.subheader("💼 Productivity Impact")
    
    # Time saved
    time_saved = assumptions["productivity"]["time_saved_hours_per_month"]
    st.markdown("**Time Saved (hours per month)**")
    if time_saved["value"] is not None:
        # Teal-highlighted value
        st.markdown(
            f'<span style="color: #008080; font-size: 24px; font-weight: bold;">{time_saved["value"]}</span> hours/month',
            unsafe_allow_html=True
        )
        # Show evidence source
        for i, pmid in enumerate(time_saved["evidence_pmids"]):
            raw = time_saved["evidence_raw"][i] if i < len(time_saved["evidence_raw"]) else ""
            st.caption(f"Source: PMID [{pmid}](https://pubmed.ncbi.nlm.nih.gov/{pmid}/) — '{raw}'")
        st.info(time_saved["explanation"])
    else:
        st.write("—")
        st.caption(time_saved["explanation"])
    
    st.markdown("---")
    
    # Cost avoided
    cost_avoided = assumptions["productivity"]["cost_avoided_per_year"]
    st.markdown("**Cost Avoided (per year)**")
    if cost_avoided["value"] is not None:
        # Teal-highlighted value
        st.markdown(
            f'<span style="color: #008080; font-size: 24px; font-weight: bold;">${cost_avoided["value"]:,.2f}</span>',
            unsafe_allow_html=True
        )
        # Show evidence source
        for i, pmid in enumerate(cost_avoided["evidence_pmids"]):
            raw = cost_avoided["evidence_raw"][i] if i < len(cost_avoided["evidence_raw"]) else ""
            st.caption(f"Source: PMID [{pmid}](https://pubmed.ncbi.nlm.nih.gov/{pmid}/) — '{raw}'")
        st.info(cost_avoided["explanation"])
    else:
        st.write("—")
        st.caption(cost_avoided["explanation"])
    
    st.markdown("---")
    st.subheader("💰 Total Cost of Ownership (TCO)")
    
    # Implementation cost
    impl_cost = assumptions["tco"]["implementation_cost"]
    st.markdown("**Implementation Cost**")
    if impl_cost["value"] is not None:
        st.markdown(
            f'<span style="color: #008080; font-size: 24px; font-weight: bold;">${impl_cost["value"]:,.2f}</span>',
            unsafe_allow_html=True
        )
        for i, pmid in enumerate(impl_cost["evidence_pmids"]):
            raw = impl_cost["evidence_raw"][i] if i < len(impl_cost["evidence_raw"]) else ""
            st.caption(f"Source: PMID [{pmid}](https://pubmed.ncbi.nlm.nih.gov/{pmid}/) — '{raw}'")
        st.info(impl_cost["explanation"])
    else:
        st.write("—")
        st.caption(impl_cost["explanation"])
    
    st.markdown("---")
    
    # Annual operating cost
    annual_cost = assumptions["tco"]["annual_operating_cost"]
    st.markdown("**Annual Operating Cost**")
    if annual_cost["value"] is not None:
        st.markdown(
            f'<span style="color: #008080; font-size: 24px; font-weight: bold;">${annual_cost["value"]:,.2f}</span>',
            unsafe_allow_html=True
        )
        for i, pmid in enumerate(annual_cost["evidence_pmids"]):
            raw = annual_cost["evidence_raw"][i] if i < len(annual_cost["evidence_raw"]) else ""
            st.caption(f"Source: PMID [{pmid}](https://pubmed.ncbi.nlm.nih.gov/{pmid}/) — '{raw}'")
        st.info(annual_cost["explanation"])
    else:
        st.write("—")
        st.caption(annual_cost["explanation"])
    
    st.markdown("---")
    st.caption("⚠️ **Important:** All numeric values are extracted directly from selected PubMed abstracts. Values shown in teal are evidence-backed with PMID sources. Fields without evidence remain blank.")


def render_step_3_brief_shell():
    """Render Step 4: Generate Impact Brief."""
    st.header("Step 4: Generate Impact Brief")
    
    # Check prerequisites
    if not st.session_state.evidence_selected_pmids:
        st.warning("⚠️ No articles selected. Please go back to Evidence step and select articles.")
        return
    
    if not st.session_state.assumptions:
        st.warning("⚠️ No assumptions generated. Please go back to Assumptions step.")
        return
    
    st.info("📄 Ready to generate your evidence-grounded Impact Brief")
    
    # Configuration inputs
    col1, col2 = st.columns(2)
    
    with col1:
        hourly_rate = st.number_input(
            "Hourly Rate ($)",
            min_value=0.0,
            max_value=1000.0,
            value=100.0,
            step=10.0,
            help="Effective hourly cost/value rate"
        )
    
    with col2:
        horizon_years = st.number_input(
            "Planning Horizon (years)",
            min_value=1,
            max_value=10,
            value=3,
            step=1,
            help="Analysis time horizon"
        )
    
    st.markdown("---")
    
    # TCO inputs (optional - for demonstration)
    with st.expander("⚙️ TCO Inputs (optional - leave blank if not in evidence)", expanded=False):
        st.caption("These are typically NOT found in research abstracts. Leave blank unless you have organizational data.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            build_person_days = st.number_input("Build person-days", min_value=0.0, value=0.0, step=1.0)
            run_person_days_per_year = st.number_input("Run person-days/year", min_value=0.0, value=0.0, step=1.0)
            training_hours = st.number_input("Training hours (one-time)", min_value=0.0, value=0.0, step=1.0)
        
        with col2:
            license_cost_per_year = st.number_input("License cost/year ($)", min_value=0.0, value=0.0, step=1000.0)
            compute_cost_per_year = st.number_input("Compute cost/year ($)", min_value=0.0, value=0.0, step=1000.0)
            downtime_hours_per_year = st.number_input("Downtime hours/year", min_value=0.0, value=0.0, step=1.0)
    
    # Generate brief button
    if st.button("📊 Generate Impact Brief", type="primary", use_container_width=True):
        with st.spinner("Generating Impact Brief..."):
            # Get selected articles
            selected_articles = [
                article for article in st.session_state.evidence_results
                if article["pmid"] in st.session_state.evidence_selected_pmids
            ]
            
            # Prepare TCO inputs
            tco_inputs = {
                "build_person_days": build_person_days if build_person_days > 0 else None,
                "run_person_days_per_year": run_person_days_per_year if run_person_days_per_year > 0 else None,
                "license_cost_per_year": license_cost_per_year if license_cost_per_year > 0 else None,
                "compute_cost_per_year": compute_cost_per_year if compute_cost_per_year > 0 else None,
                "training_hours": training_hours if training_hours > 0 else None,
                "downtime_hours_per_year": downtime_hours_per_year if downtime_hours_per_year > 0 else None
            }
            
            # Prepare productivity inputs from assumptions
            assumptions = st.session_state.assumptions
            prod_inputs = {
                "time_saved_hours_per_month": assumptions["productivity"]["time_saved_hours_per_month"].get("value"),
                "cost_avoided_per_year": assumptions["productivity"]["cost_avoided_per_year"].get("value"),
                "throughput_delta_per_year": None,  # Not extracted by default
                "success_prob_delta": None  # Not extracted by default
            }
            
            # Compute TCO and productivity
            tco_out = compute_tco(tco_inputs, hourly_rate, horizon_years)
            prod_out = compute_productivity(prod_inputs, hourly_rate, horizon_years)
            
            # Build markdown report
            brief_md = build_brief_markdown(
                idea=st.session_state.idea,
                selected_articles=selected_articles,
                extracted_numeric_evidence=st.session_state.extracted_numeric_evidence,
                assumptions=assumptions,
                tco_out=tco_out,
                prod_out=prod_out,
                horizon_years=horizon_years
            )
            
            # Store in session state
            st.session_state.generated_brief = brief_md
            st.success("✓ Impact Brief generated successfully!")
    
    # Display generated brief
    if "generated_brief" in st.session_state and st.session_state.generated_brief:
        st.markdown("---")
        st.subheader("Generated Impact Brief")
        
        # Download button
        st.download_button(
            label="📥 Download as Markdown",
            data=st.session_state.generated_brief,
            file_name=f"impact_brief_{st.session_state.idea['title'].replace(' ', '_')}.md",
            mime="text/markdown",
            use_container_width=True
        )
        
        st.markdown("---")
        
        # Render the markdown
        st.markdown(st.session_state.generated_brief, unsafe_allow_html=False)


def render_navigation():
    """Render Back/Next navigation buttons at the bottom."""
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.session_state.step > 0:
            if st.button("← Back", use_container_width=True):
                st.session_state.step -= 1
                st.rerun()
    
    with col3:
        if st.session_state.step < 3:
            if st.button("Next →", use_container_width=True):
                # Save current step data before moving forward
                _save_current_step_data()
                st.session_state.step += 1
                st.rerun()


def _save_current_step_data():
    """Save data from current step to session state."""
    if st.session_state.step == 0:
        # Save idea data
        st.session_state.idea["title"] = st.session_state.get("idea_title_input", "")
        st.session_state.idea["description"] = st.session_state.get("idea_description_input", "")
        st.session_state.idea["idea_type"] = st.session_state.get("idea_type_input", "")
        st.session_state.idea["rd_stage"] = st.session_state.get("rd_stage_input", "")
        
        # Trigger query auto-update when moving to next step
        _auto_update_query_from_idea()


def _auto_update_query_from_idea():
    """Auto-update the PubMed query from idea title and description."""
    if st.session_state.auto_update_query:
        title = st.session_state.get("idea_title_input", "")
        description = st.session_state.get("idea_description_input", "")

        # Generate suggested query – use LLM if available, fallback to keywords
        provider = get_provider(st.session_state.get("llm_settings", {}))
        suggested_query = suggest_pubmed_query(title, description, provider=provider)

        # Update the evidence query
        st.session_state.evidence_query["query"] = suggested_query
