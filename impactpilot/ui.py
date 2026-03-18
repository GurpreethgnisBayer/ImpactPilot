"""UI rendering functions for each step."""

import streamlit as st
from impactpilot.constants import IDEA_TYPE_OPTIONS, RD_STAGE_OPTIONS
from impactpilot.query_suggest import suggest_pubmed_query, suggest_pubmed_query_with_llm
from impactpilot.services.pubmed_eutils import search_pubmed
from impactpilot.services.llm_provider import build_provider
from impactpilot.services.llm_health import validate_llm_settings
from impactpilot.infer_engine import run_inference_pipeline
from impactpilot.assumptions import normalize_and_validate
from impactpilot.calc import compute_tco_from_ranges, compute_productivity_from_ranges
from impactpilot.report import build_brief_markdown


def _generate_query_with_llm_or_fallback(title: str, description: str) -> str:
    """Try to generate query with LLM, fall back to deterministic if fails."""
    # Check if LLM is configured
    validation_errors = validate_llm_settings(st.session_state.llm_settings)
    
    if not validation_errors:
        try:
            # Build provider and generate MeSH query
            provider = build_provider(st.session_state.llm_settings)
            return suggest_pubmed_query_with_llm(title, description, provider)
        except Exception as e:
            # Fall back to deterministic
            print(f"LLM query generation failed: {e}")
            return suggest_pubmed_query(title, description)
    else:
        # LLM not configured, use fallback
        return suggest_pubmed_query(title, description)


def render_step_0_idea():
    """Render Step 0: Idea input form."""
    st.header("Step 1: Idea")
    st.write("Describe your R&D idea and provide context.")
    
    # Store previous values to detect changes
    prev_title = st.session_state.idea.get("title", "")
    prev_description = st.session_state.idea.get("description", "")
    
    # Title
    title = st.text_input(
        "Idea Title",
        value=prev_title,
        placeholder="e.g., AI-powered drug screening platform",
        help="A concise title for your R&D idea"
    )
    st.session_state.idea["title"] = title
    
    # Description
    description = st.text_area(
        "Idea Description",
        value=prev_description,
        placeholder="Describe the problem, solution, and potential impact...",
        height=150,
        help="Detailed description of your R&D idea"
    )
    st.session_state.idea["description"] = description
    
    # Auto-update query if enabled and title/description changed
    if st.session_state.evidence_query.get("auto_update", True):
        if title != prev_title or description != prev_description:
            # Use LLM if available, otherwise fallback
            new_query = _generate_query_with_llm_or_fallback(title, description)
            st.session_state.evidence_query["query"] = new_query
    
    # Idea Type
    idea_type = st.selectbox(
        "Idea Type",
        options=IDEA_TYPE_OPTIONS,
        index=IDEA_TYPE_OPTIONS.index(st.session_state.idea["idea_type"]) 
              if st.session_state.idea.get("idea_type") in IDEA_TYPE_OPTIONS 
              else 0,
        help="Select the category that best describes your idea"
    )
    st.session_state.idea["idea_type"] = idea_type
    
    # R&D Stage
    rd_stage = st.selectbox(
        "R&D Stage",
        options=RD_STAGE_OPTIONS,
        index=RD_STAGE_OPTIONS.index(st.session_state.idea["rd_stage"]) 
              if st.session_state.idea.get("rd_stage") in RD_STAGE_OPTIONS 
              else 0,
        help="Select the current development stage"
    )
    st.session_state.idea["rd_stage"] = rd_stage
    
    # Navigation buttons
    st.write("")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col3:
        if st.button("Next →", type="primary", use_container_width=True):
            st.session_state.step = 1
            st.rerun()


def render_step_1_evidence_shell():
    """Render Step 1: Evidence search with PubMed integration."""
    st.header("Step 2: Evidence")
    st.write("Search PubMed for relevant scientific evidence.")
    
    # Query input
    query = st.text_input(
        "PubMed Search Query",
        value=st.session_state.evidence_query.get("query", ""),
        placeholder="Enter keywords to search PubMed...",
        help="Search terms for PubMed. Auto-generated from your idea by default."
    )
    st.session_state.evidence_query["query"] = query
    
    # Auto-update checkbox
    col1, col2 = st.columns([3, 1])
    with col1:
        auto_update = st.checkbox(
            "Auto-update query from idea",
            value=st.session_state.evidence_query.get("auto_update", True),
            help="Automatically regenerate query when you edit the idea title/description"
        )
        st.session_state.evidence_query["auto_update"] = auto_update
    
    with col2:
        if st.button("🔄 Regenerate query", use_container_width=True):
            # Use LLM if available, otherwise fallback
            new_query = _generate_query_with_llm_or_fallback(
                st.session_state.idea.get("title", ""),
                st.session_state.idea.get("description", "")
            )
            st.session_state.evidence_query["query"] = new_query
            st.rerun()
    
    # Filters
    st.subheader("Filters")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        date_preset = st.selectbox(
            "Date Range",
            options=["2years", "5years", "10years", "custom", "all"],
            index=["2years", "5years", "10years", "custom", "all"].index(
                st.session_state.evidence_query.get("date_preset", "5years")
            ),
            help="Filter by publication date"
        )
        st.session_state.evidence_query["date_preset"] = date_preset
    
    with col2:
        max_results = st.number_input(
            "Max Results",
            min_value=5,
            max_value=100,
            value=st.session_state.evidence_query.get("max_results", 20),
            step=5,
            help="Maximum number of results to retrieve"
        )
        st.session_state.evidence_query["max_results"] = max_results
    
    with col3:
        sort = st.selectbox(
            "Sort By",
            options=["relevance", "pub_date"],
            index=["relevance", "pub_date"].index(
                st.session_state.evidence_query.get("sort", "relevance")
            ),
            help="Sort order for results"
        )
        st.session_state.evidence_query["sort"] = sort
    
    # Custom date range (if custom selected)
    if date_preset == "custom":
        col1, col2 = st.columns(2)
        with col1:
            custom_mindate = st.text_input(
                "Min Date (YYYY/MM/DD)",
                value=st.session_state.evidence_query.get("custom_mindate", ""),
                placeholder="2020/01/01"
            )
            st.session_state.evidence_query["custom_mindate"] = custom_mindate
        with col2:
            custom_maxdate = st.text_input(
                "Max Date (YYYY/MM/DD)",
                value=st.session_state.evidence_query.get("custom_maxdate", ""),
                placeholder="2024/12/31"
            )
            st.session_state.evidence_query["custom_maxdate"] = custom_maxdate
    
    # Advanced filters
    with st.expander("Advanced Filters"):
        col1, col2 = st.columns(2)
        
        with col1:
            journal = st.text_input(
                "Journal",
                value=st.session_state.evidence_query.get("journal", ""),
                placeholder="e.g., Nature, Science",
                help="Filter by journal name"
            )
            st.session_state.evidence_query["journal"] = journal
            
            author = st.text_input(
                "Author",
                value=st.session_state.evidence_query.get("author", ""),
                placeholder="e.g., Smith J",
                help="Filter by author name"
            )
            st.session_state.evidence_query["author"] = author
            
            language = st.text_input(
                "Language",
                value=st.session_state.evidence_query.get("language", ""),
                placeholder="e.g., eng",
                help="Filter by language (3-letter code)"
            )
            st.session_state.evidence_query["language"] = language
        
        with col2:
            has_abstract = st.checkbox(
                "Has Abstract",
                value=st.session_state.evidence_query.get("has_abstract", False),
                help="Only include articles with abstracts"
            )
            st.session_state.evidence_query["has_abstract"] = has_abstract
            
            field_restriction = st.selectbox(
                "Search In",
                options=["all", "title", "title_abstract"],
                index=["all", "title", "title_abstract"].index(
                    st.session_state.evidence_query.get("field_restriction", "all")
                ),
                help="Restrict search to specific fields"
            )
            st.session_state.evidence_query["field_restriction"] = field_restriction
            
            publication_types = st.multiselect(
                "Publication Types",
                options=[
                    "Clinical Trial",
                    "Meta-Analysis",
                    "Randomized Controlled Trial",
                    "Review",
                    "Systematic Review",
                ],
                default=st.session_state.evidence_query.get("publication_types", []),
                help="Filter by publication type"
            )
            st.session_state.evidence_query["publication_types"] = publication_types
    
    # Search button
    st.write("")
    if st.button("🔍 Search PubMed", type="primary", use_container_width=True):
        if not query.strip():
            st.error("Please enter a search query.")
        else:
            with st.spinner("Searching PubMed..."):
                try:
                    results = search_pubmed(
                        query=query,
                        date_preset=date_preset,
                        max_results=int(max_results),
                        sort=sort,
                        journal=journal,
                        author=author,
                        language=language,
                        has_abstract=has_abstract,
                        publication_types=publication_types,
                        field_restriction=field_restriction,
                        custom_mindate=st.session_state.evidence_query.get("custom_mindate", ""),
                        custom_maxdate=st.session_state.evidence_query.get("custom_maxdate", ""),
                    )
                    st.session_state.evidence_results = results
                    st.success(f"Found {len(results)} results!")
                except Exception as e:
                    st.error(f"Search failed: {str(e)}")
    
    # Display results
    if st.session_state.evidence_results:
        st.write("---")
        st.subheader(f"Results ({len(st.session_state.evidence_results)})")
        
        # Select all / deselect all
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("Select All"):
                st.session_state.evidence_selected_pmids = {
                    article["pmid"] for article in st.session_state.evidence_results
                }
                st.rerun()
        with col2:
            if st.button("Deselect All"):
                st.session_state.evidence_selected_pmids = set()
                st.rerun()
        
        # Render each article
        for article in st.session_state.evidence_results:
            pmid = article["pmid"]
            
            col1, col2 = st.columns([0.5, 9.5])
            with col1:
                is_selected = pmid in st.session_state.evidence_selected_pmids
                if st.checkbox("", value=is_selected, key=f"select_{pmid}"):
                    st.session_state.evidence_selected_pmids.add(pmid)
                else:
                    st.session_state.evidence_selected_pmids.discard(pmid)
            
            with col2:
                st.markdown(f"**[{pmid}] {article['title']}**")
                
                # Authors
                if article.get("authors"):
                    authors_str = ", ".join(article["authors"][:3])
                    if len(article["authors"]) > 3:
                        authors_str += " et al."
                    st.caption(authors_str)
                
                # Journal and year
                st.caption(f"{article['journal']} ({article['year']})")
                
                # Abstract preview (first 300 chars)
                if article.get("abstract"):
                    abstract_preview = article["abstract"][:300]
                    if len(article["abstract"]) > 300:
                        abstract_preview += "..."
                    st.write(abstract_preview)
                
                # Link
                st.markdown(f"[View on PubMed]({article['url']})")
                
                st.write("")
        
        # Show selected count
        st.info(f"✓ Selected {len(st.session_state.evidence_selected_pmids)} articles")
    
    # Navigation buttons
    st.write("")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = 0
            st.rerun()
    with col3:
        if st.button("Next →", type="primary", use_container_width=True):
            st.session_state.step = 2
            st.rerun()


def render_step_2_assumptions_shell():
    """Render Step 2: Assumptions with LLM inference."""
    st.header("Step 3: Assumptions")
    st.write("Infer key assumptions using LLM analysis of selected evidence.")
    
    # Check if we have selected articles
    selected_count = len(st.session_state.evidence_selected_pmids)
    
    if selected_count == 0:
        st.warning("⚠️ No evidence articles selected. Please go back to Step 2 and select at least one article.")
    else:
        st.info(f"📊 {selected_count} articles selected for analysis")
    
    # Infer button
    st.write("")
    if st.button("🤖 Infer Assumptions from Evidence", 
                 type="primary", 
                 use_container_width=True,
                 disabled=selected_count == 0):
        
        with st.spinner("Running LLM inference... This may take 30-60 seconds."):
            try:
                # Build selected articles list
                selected_articles = [
                    article for article in st.session_state.evidence_results
                    if article["pmid"] in st.session_state.evidence_selected_pmids
                ]
                
                # Run inference
                result = run_inference_pipeline(
                    idea=st.session_state.idea,
                    selected_articles=selected_articles,
                    llm_settings=st.session_state.llm_settings
                )
                
                # Validate
                validated = normalize_and_validate(
                    result["inference"],
                    st.session_state.evidence_selected_pmids
                )
                
                # Store in session state
                st.session_state.assumptions = validated
                st.session_state.extracted_numeric_evidence = result["numeric_evidence"]
                
                st.success("✓ Inference complete!")
                st.rerun()
                
            except ValueError as e:
                st.error(f"❌ Validation error: {str(e)}")
            except Exception as e:
                st.error(f"❌ Inference failed: {str(e)}")
    
    # Display results if available
    if st.session_state.assumptions:
        st.write("---")
        st.subheader("📊 Estimated Impact")
        
        inference = st.session_state.assumptions
        
        # Productivity section
        st.write("### 💰 Productivity Gains")
        
        if "productivity" in inference:
            prod = inference["productivity"]
            
            # Time saved
            if "time_saved_hours_per_month" in prod:
                _render_numeric_field(
                    "Time Saved",
                    prod["time_saved_hours_per_month"],
                    "hours/month"
                )
            
            # Cost avoided
            if "cost_avoided_per_year" in prod:
                _render_numeric_field(
                    "Cost Avoided",
                    prod["cost_avoided_per_year"],
                    "$/year"
                )
        
        # TCO section
        st.write("### 🏗️ Total Cost of Ownership (TCO)")
        
        if "tco" in inference:
            tco = inference["tco"]
            
            # Build time
            if "build_person_days" in tco:
                _render_numeric_field(
                    "Build Time",
                    tco["build_person_days"],
                    "person-days"
                )
            
            # Run time
            if "run_person_days_per_year" in tco:
                _render_numeric_field(
                    "Annual Operational Cost",
                    tco["run_person_days_per_year"],
                    "person-days/year"
                )
        
        # Overall confidence
        if "overall_confidence" in inference:
            st.write("### 📈 Overall Confidence")
            confidence = inference["overall_confidence"]
            if confidence == "high":
                st.success(f"**{confidence.upper()}** - Strong evidence base")
            elif confidence == "medium":
                st.warning(f"**{confidence.upper()}** - Moderate evidence base")
            else:
                st.info(f"**{confidence.upper()}** - Limited evidence base")
        
        # Assumptions
        if "assumptions" in inference and inference["assumptions"]:
            st.write("### 📝 Key Assumptions")
            for assumption in inference["assumptions"]:
                st.write(f"- {assumption}")
        
        # Open questions
        if "open_questions" in inference and inference["open_questions"]:
            st.write("### ❓ Open Questions")
            for question in inference["open_questions"]:
                st.write(f"- {question}")
    
    # Navigation buttons
    st.write("")
    st.write("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = 1
            st.rerun()
    with col3:
        if st.button("Next →", type="primary", use_container_width=True):
            st.session_state.step = 3
            st.rerun()


def _render_numeric_field(label: str, field_data: dict, unit: str):
    """Helper to render a numeric estimate field with support badges."""
    
    range_min = field_data.get("range_min", 0)
    range_max = field_data.get("range_max", 0)
    support_level = field_data.get("support_level", "unknown")
    evidence_pmids = field_data.get("evidence_pmids", [])
    evidence_quotes = field_data.get("evidence_quotes", [])
    explanation = field_data.get("explanation", "")
    
    # Display label and range in teal
    st.markdown(f"**{label}:** <span style='color: teal; font-size: 1.2em;'>{range_min}–{range_max}</span> {unit}", unsafe_allow_html=True)
    
    # Support badge
    if support_level == "evidence_supported":
        st.success("✓ Evidence-supported")
        
        # Show PMIDs and quotes
        if evidence_pmids:
            st.caption(f"📄 Based on: {', '.join(evidence_pmids)}")
        
        if evidence_quotes:
            with st.expander("View supporting evidence"):
                for i, quote in enumerate(evidence_quotes, 1):
                    st.write(f"{i}. \"{quote}\"")
    
    elif support_level == "heuristic_ballpark":
        st.warning("⚠️ Heuristic/Ballpark")
        
        # Show the required explanation
        if explanation:
            st.caption(f"ℹ️ {explanation}")
    
    # Show additional explanation if not shown above
    if support_level == "evidence_supported" and explanation:
        st.caption(f"ℹ️ {explanation}")
    
    st.write("")


def render_step_3_brief_shell():
    """Render Step 3: Impact Brief generation and display."""
    st.header("Step 4: Impact Brief")
    st.write("Generate a comprehensive markdown impact estimate brief.")
    
    # Check if assumptions are available
    if not st.session_state.assumptions:
        st.warning("⚠️ No assumptions available. Please go back to Step 3 and run inference first.")
        
        # Navigation buttons
        st.write("")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("← Back", use_container_width=True):
                st.session_state.step = 2
                st.rerun()
        return
    
    # Configuration for calculations
    st.subheader("⚙️ Calculation Parameters")
    
    col1, col2 = st.columns(2)
    with col1:
        hourly_rate = st.number_input(
            "Hourly Rate ($)",
            min_value=50,
            max_value=500,
            value=100,
            step=10,
            help="Hourly rate for cost calculations"
        )
    
    with col2:
        horizon_years = st.number_input(
            "Time Horizon (Years)",
            min_value=1,
            max_value=10,
            value=3,
            step=1,
            help="Time horizon for TCO and productivity calculations"
        )
    
    # Generate Brief button
    st.write("")
    if st.button("📄 Generate Impact Brief", type="primary", use_container_width=True):
        with st.spinner("Generating brief..."):
            try:
                # Get selected articles
                selected_articles = [
                    article for article in st.session_state.evidence_results
                    if article["pmid"] in st.session_state.evidence_selected_pmids
                ]
                
                # Compute TCO
                tco_out = compute_tco_from_ranges(
                    st.session_state.assumptions.get("tco", {}),
                    hourly_rate=hourly_rate,
                    horizon_years=horizon_years
                )
                
                # Compute Productivity
                prod_out = compute_productivity_from_ranges(
                    st.session_state.assumptions.get("productivity", {}),
                    hourly_rate=hourly_rate,
                    horizon_years=horizon_years
                )
                
                # Build markdown
                brief_markdown = build_brief_markdown(
                    idea=st.session_state.idea,
                    selected_articles=selected_articles,
                    assumptions=st.session_state.assumptions,
                    tco_out=tco_out,
                    prod_out=prod_out,
                    horizon_years=horizon_years
                )
                
                # Store in session state
                st.session_state.brief_markdown = brief_markdown
                
                st.success("✓ Brief generated successfully!")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Brief generation failed: {str(e)}")
    
    # Display brief if available
    if st.session_state.brief_markdown:
        st.write("---")
        st.subheader("📋 Generated Brief")
        
        # Display the markdown
        st.markdown(st.session_state.brief_markdown)
        
        # Download button
        st.write("")
        st.download_button(
            label="⬇️ Download Brief as Markdown",
            data=st.session_state.brief_markdown,
            file_name=f"impact_estimate_{st.session_state.idea.get('title', 'untitled').replace(' ', '_')}.md",
            mime="text/markdown",
            use_container_width=True
        )
    
    # Navigation buttons
    st.write("")
    st.write("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = 2
            st.rerun()
