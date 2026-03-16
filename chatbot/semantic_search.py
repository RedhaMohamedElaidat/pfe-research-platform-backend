from sentence_transformers import SentenceTransformer # type: ignore
from sklearn.metrics.pairwise import cosine_similarity # type: ignore
from publication.models import Publication
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")


def semantic_search(query, top_k=5):

    pubs = list(Publication.objects.all())   # IMPORTANT

    titles = [p.title for p in pubs]

    if not titles:
        return []

    embeddings = model.encode(titles)
    query_embedding = model.encode([query])

    similarities = cosine_similarity(query_embedding, embeddings)[0]

    top_indices = np.argsort(similarities)[-top_k:][::-1]

    results = []

    for idx in top_indices:

        p = pubs[int(idx)]

        results.append({
            "title": p.title,
            "year": p.publication_year,
            "citations": p.citation_count
        })

    return results