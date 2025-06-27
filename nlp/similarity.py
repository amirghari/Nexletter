from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def score_title_similarity(new_title, liked_titles):
    if not liked_titles:
        return 0.0

    titles = liked_titles + [new_title]
    tfidf = TfidfVectorizer(stop_words='english').fit_transform(titles)
    similarity_matrix = cosine_similarity(tfidf[-1], tfidf[:-1])
    return similarity_matrix.max()