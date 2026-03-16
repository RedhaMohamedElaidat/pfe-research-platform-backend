from sklearn.feature_extraction.text import TfidfVectorizer # type: ignore
from sklearn.cluster import KMeans # type: ignore
from publication.models import Publication

vectorizer = TfidfVectorizer(stop_words="english")


def cluster_publications(k=5):

    pubs = list(Publication.objects.all())

    texts = [p.title for p in pubs]

    if not texts:
        return {}

    X = vectorizer.fit_transform(texts)

    kmeans = KMeans(n_clusters=k, random_state=42)
    labels = kmeans.fit_predict(X)

    clusters = {}

    for pub, label in zip(pubs, labels):

        label = int(label)   # ⭐ conversion importante

        key = f"cluster_{label}"

        if key not in clusters:
            clusters[key] = []

        clusters[key].append({
            "title": pub.title,
            "year": pub.publication_year
        })

    return clusters