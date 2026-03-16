from publication.models import Publication


def search_publications(query):

    pubs = Publication.objects.filter(
        title__icontains=query
    ).order_by("-citation_count")[:5]

    return [
        {
            "title": p.title,
            "year": p.publication_year,
            "citations": p.citation_count
        }
        for p in pubs
    ]
def highest_cited_publications(limit=5):

    pubs = Publication.objects.order_by("-citation_count")[:limit]

    return [
        {
            "title": p.title,
            "year": p.publication_year,
            "citations": p.citation_count
        }
        for p in pubs
    ]