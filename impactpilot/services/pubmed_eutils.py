"""PubMed E-utilities API wrapper for searching and fetching articles."""

import requests
import xml.etree.ElementTree as ET
from typing import Optional
from urllib.parse import quote_plus

EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
ESEARCH_URL = f"{EUTILS_BASE}/esearch.fcgi"
EFETCH_URL = f"{EUTILS_BASE}/efetch.fcgi"


def build_term(
    base_query: str,
    journal: str = "",
    author: str = "",
    language: str = "",
    has_abstract: bool = True,
    publication_types: Optional[list[str]] = None,
    field_restriction: str = ""
) -> str:
    """
    Build a PubMed search term with optional qualifiers.
    
    Args:
        base_query: The main query string
        journal: Journal name qualifier
        author: Author name qualifier
        language: Language code (e.g., "eng")
        has_abstract: Require abstract present
        publication_types: List of publication types (e.g., ["Clinical Trial", "Review"])
        field_restriction: Restrict search to specific field (e.g., "tiab" for title/abstract)
        
    Returns:
        Complete PubMed search term with qualifiers
    """
    term_parts = []
    
    # Base query with optional field restriction
    if base_query:
        if field_restriction:
            term_parts.append(f"({base_query}[{field_restriction}])")
        else:
            term_parts.append(base_query)
    
    # Add qualifiers
    if journal:
        term_parts.append(f'"{journal}"[Journal]')
    
    if author:
        term_parts.append(f'"{author}"[Author]')
    
    if language:
        term_parts.append(f"{language}[Language]")
    
    if has_abstract:
        term_parts.append("hasabstract")
    
    if publication_types:
        for pub_type in publication_types:
            term_parts.append(f'"{pub_type}"[Publication Type]')
    
    return " AND ".join(term_parts)


def esearch(
    term: str,
    retmax: int = 20,
    sort: str = "relevance",
    mindate: str = "",
    maxdate: str = "",
    reldate: str = "",
    datetype: str = "pdat"
) -> list[str]:
    """
    Execute PubMed eSearch to get PMIDs.
    
    Args:
        term: PubMed search term
        retmax: Maximum number of results
        sort: Sort order ("relevance", "pub_date", "Most Recent")
        mindate: Min date (YYYY/MM/DD or YYYY)
        maxdate: Max date (YYYY/MM/DD or YYYY)
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
        "datetype": datetype
    }
    
    if reldate:
        params["reldate"] = reldate
    elif mindate and maxdate:
        params["mindate"] = mindate
        params["maxdate"] = maxdate
    
    try:
        response = requests.get(ESEARCH_URL, params=params, timeout=10)
        response.raise_for_status()
        
        # Parse XML response
        root = ET.fromstring(response.content)
        pmids = [id_elem.text for id_elem in root.findall(".//Id") if id_elem.text]
        return pmids
    except Exception as e:
        print(f"eSearch error: {e}")
        return []


def efetch(pmids: list[str]) -> list[dict]:
    """
    Fetch article details for given PMIDs.
    
    Args:
        pmids: List of PubMed IDs
        
    Returns:
        List of article dictionaries with keys:
        pmid, title, abstract, journal, year, authors, url
    """
    if not pmids:
        return []
    
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml"
    }
    
    try:
        response = requests.get(EFETCH_URL, params=params, timeout=15)
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
            abstract_parts = []
            for abstract_text in article_elem.findall(".//AbstractText"):
                label = abstract_text.get("Label", "")
                text = abstract_text.text or ""
                if label:
                    abstract_parts.append(f"{label}: {text}")
                else:
                    abstract_parts.append(text)
            abstract = " ".join(abstract_parts) if abstract_parts else "No abstract available"
            
            # Journal
            journal_elem = article_elem.find(".//Journal/Title")
            journal = journal_elem.text if journal_elem is not None else "Unknown"
            
            # Year
            year_elem = article_elem.find(".//PubDate/Year")
            year = year_elem.text if year_elem is not None else "N/A"
            
            # Authors
            author_elems = article_elem.findall(".//Author")
            authors = []
            for author in author_elems[:3]:  # First 3 authors
                lastname = author.find("LastName")
                forename = author.find("ForeName")
                if lastname is not None:
                    name = lastname.text
                    if forename is not None:
                        name = f"{forename.text} {name}"
                    authors.append(name)
            author_str = ", ".join(authors)
            if len(author_elems) > 3:
                author_str += " et al."
            
            # URL
            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            
            articles.append({
                "pmid": pmid,
                "title": title,
                "abstract": abstract,
                "journal": journal,
                "year": year,
                "authors": author_str if author_str else "Unknown",
                "url": url
            })
        
        return articles
    except Exception as e:
        print(f"eFetch error: {e}")
        return []


def search_pubmed(
    query: str,
    date_preset: str = "5years",
    max_results: int = 20,
    sort: str = "relevance",
    journal: str = "",
    author: str = "",
    language: str = "",
    has_abstract: bool = True,
    publication_types: Optional[list[str]] = None,
    field_restriction: str = ""
) -> list[dict]:
    """
    Complete PubMed search workflow: search + fetch.
    
    Args:
        query: Base search query
        date_preset: Date range preset ("2years", "5years", "10years", "all")
        max_results: Maximum number of results
        sort: Sort order
        journal: Journal filter
        author: Author filter
        language: Language filter
        has_abstract: Require abstract
        publication_types: Publication type filters
        field_restriction: Field restriction
        
    Returns:
        List of article dictionaries
    """
    # Build the full search term
    term = build_term(
        base_query=query,
        journal=journal,
        author=author,
        language=language,
        has_abstract=has_abstract,
        publication_types=publication_types,
        field_restriction=field_restriction
    )
    
    # Determine date range
    reldate = ""
    if date_preset == "2years":
        reldate = "730"  # ~2 years in days
    elif date_preset == "5years":
        reldate = "1825"  # ~5 years in days
    elif date_preset == "10years":
        reldate = "3650"  # ~10 years in days
    # else: "all" means no date restriction
    
    # Execute search
    pmids = esearch(
        term=term,
        retmax=max_results,
        sort=sort,
        reldate=reldate
    )
    
    # Fetch article details
    if pmids:
        return efetch(pmids)
    
    return []
