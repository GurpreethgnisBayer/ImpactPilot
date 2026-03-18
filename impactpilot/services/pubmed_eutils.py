"""PubMed E-utilities API wrapper for searching and fetching articles."""

import requests
import xml.etree.ElementTree as ET
from typing import Optional
from datetime import datetime, timedelta


EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
PUBMED_BASE = "https://pubmed.ncbi.nlm.nih.gov"


def build_term(
    base_query: str,
    journal: str = "",
    author: str = "",
    language: str = "",
    has_abstract: bool = False,
    publication_types: Optional[list[str]] = None,
    field_restriction: str = "all",
) -> str:
    """
    Build a PubMed search term with optional filters.
    
    Args:
        base_query: The base search query
        journal: Journal name filter
        author: Author name filter
        language: Language filter (e.g., "eng")
        has_abstract: Whether to require an abstract
        publication_types: List of publication types (e.g., ["Clinical Trial", "Review"])
        field_restriction: Where to search - "all", "title", or "title_abstract"
    
    Returns:
        Complete PubMed search term with qualifiers
    """
    term_parts = []
    
    # Apply field restriction to base query
    if base_query.strip():
        if field_restriction == "title":
            term_parts.append(f"({base_query}[Title])")
        elif field_restriction == "title_abstract":
            term_parts.append(f"({base_query}[Title/Abstract])")
        else:  # all fields
            term_parts.append(f"({base_query})")
    
    # Add filters
    if journal:
        term_parts.append(f'"{journal}"[Journal]')
    
    if author:
        term_parts.append(f'"{author}"[Author]')
    
    if language:
        term_parts.append(f"{language}[Language]")
    
    if has_abstract:
        term_parts.append("hasabstract")
    
    if publication_types:
        for ptype in publication_types:
            term_parts.append(f'"{ptype}"[Publication Type]')
    
    return " AND ".join(term_parts) if term_parts else base_query


def esearch(
    term: str,
    retmax: int = 20,
    sort: str = "relevance",
    mindate: str = "",
    maxdate: str = "",
    reldate: int = 0,
    datetype: str = "pdat",
) -> list[str]:
    """
    Search PubMed using E-utilities esearch.
    
    Args:
        term: Search term/query
        retmax: Maximum number of results to return
        sort: Sort order ("relevance" or "pub_date")
        mindate: Minimum date (YYYY/MM/DD)
        maxdate: Maximum date (YYYY/MM/DD)
        reldate: Relative date in days (alternative to mindate/maxdate)
        datetype: Date type ("pdat" for publication date)
    
    Returns:
        List of PMIDs as strings
    """
    params = {
        "db": "pubmed",
        "term": term,
        "retmax": retmax,
        "retmode": "xml",
        "sort": sort,
        "datetype": datetype,
    }
    
    # Use either reldate OR mindate/maxdate
    if reldate > 0:
        params["reldate"] = reldate
    else:
        if mindate:
            params["mindate"] = mindate
        if maxdate:
            params["maxdate"] = maxdate
    
    try:
        response = requests.get(f"{EUTILS_BASE}/esearch.fcgi", params=params, timeout=10)
        response.raise_for_status()
        
        # Parse XML response
        root = ET.fromstring(response.content)
        pmids = [id_elem.text for id_elem in root.findall(".//Id") if id_elem.text]
        
        return pmids
    except Exception as e:
        raise RuntimeError(f"PubMed search failed: {str(e)}")


def efetch(pmids: list[str]) -> list[dict]:
    """
    Fetch article details for given PMIDs using E-utilities efetch.
    
    Args:
        pmids: List of PubMed IDs
    
    Returns:
        List of article dictionaries with metadata
    """
    if not pmids:
        return []
    
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
    }
    
    try:
        response = requests.get(f"{EUTILS_BASE}/efetch.fcgi", params=params, timeout=15)
        response.raise_for_status()
        
        # Parse XML response
        root = ET.fromstring(response.content)
        articles = []
        
        for article_elem in root.findall(".//PubmedArticle"):
            pmid_elem = article_elem.find(".//PMID")
            pmid = pmid_elem.text if pmid_elem is not None else "Unknown"
            
            # Title
            title_elem = article_elem.find(".//ArticleTitle")
            title = title_elem.text if title_elem is not None else "No title"
            
            # Abstract
            abstract_parts = article_elem.findall(".//AbstractText")
            abstract = " ".join([
                (ab.text or "") for ab in abstract_parts if ab.text
            ]) if abstract_parts else ""
            
            # Journal
            journal_elem = article_elem.find(".//Journal/Title")
            journal = journal_elem.text if journal_elem is not None else "Unknown"
            
            # Year
            year_elem = article_elem.find(".//PubDate/Year")
            year = year_elem.text if year_elem is not None else ""
            
            # Authors
            author_elems = article_elem.findall(".//Author")
            authors = []
            for author in author_elems:
                lastname = author.find("LastName")
                forename = author.find("ForeName")
                if lastname is not None:
                    name = lastname.text
                    if forename is not None:
                        name = f"{forename.text} {name}"
                    authors.append(name)
            
            articles.append({
                "pmid": pmid,
                "title": title,
                "abstract": abstract,
                "journal": journal,
                "year": year,
                "authors": authors,
                "url": f"{PUBMED_BASE}/{pmid}/",
            })
        
        return articles
    except Exception as e:
        raise RuntimeError(f"PubMed fetch failed: {str(e)}")


def search_pubmed(
    query: str,
    date_preset: str = "5years",
    max_results: int = 20,
    sort: str = "relevance",
    journal: str = "",
    author: str = "",
    language: str = "",
    has_abstract: bool = False,
    publication_types: Optional[list[str]] = None,
    field_restriction: str = "all",
    custom_mindate: str = "",
    custom_maxdate: str = "",
) -> list[dict]:
    """
    Search PubMed and fetch article details.
    
    Args:
        query: Base search query
        date_preset: Date filter preset ("2years", "5years", "10years", "custom", "all")
        max_results: Maximum number of results
        sort: Sort order ("relevance" or "pub_date")
        journal: Journal filter
        author: Author filter
        language: Language filter
        has_abstract: Require abstract
        publication_types: Publication type filters
        field_restriction: Field restriction ("all", "title", "title_abstract")
        custom_mindate: Custom minimum date (YYYY/MM/DD)
        custom_maxdate: Custom maximum date (YYYY/MM/DD)
    
    Returns:
        List of article dictionaries
    """
    # Build search term with filters
    term = build_term(
        query,
        journal=journal,
        author=author,
        language=language,
        has_abstract=has_abstract,
        publication_types=publication_types,
        field_restriction=field_restriction,
    )
    
    # Determine date filters
    reldate = 0
    mindate = ""
    maxdate = ""
    
    if date_preset == "2years":
        reldate = 730  # approximately 2 years
    elif date_preset == "5years":
        reldate = 1825  # approximately 5 years
    elif date_preset == "10years":
        reldate = 3650  # approximately 10 years
    elif date_preset == "custom":
        mindate = custom_mindate
        maxdate = custom_maxdate
    # "all" means no date restriction
    
    # Search for PMIDs
    pmids = esearch(
        term=term,
        retmax=max_results,
        sort=sort,
        mindate=mindate,
        maxdate=maxdate,
        reldate=reldate,
    )
    
    # Fetch article details
    articles = efetch(pmids)
    
    return articles
