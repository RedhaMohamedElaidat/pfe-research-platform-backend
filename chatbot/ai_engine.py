from .semantic_search import semantic_search
from .clustering import cluster_publications
from .services import highest_cited_publications


def process_question(question):

    q = question.lower()
    if "highest cited" in q or "most cited" in q:
        return highest_cited_publications()
    if "theme" in q or "research area" in q:
        return cluster_publications()

    if "publication" in q or "paper" in q or "research" in q:
        return semantic_search(question)

    return {
        "message": "I did not understand the question"
    }
   