import re
import joblib
from pathlib import Path
from nltk.stem import SnowballStemmer

from .models import FeedbackEntry

_ML_DIR = Path(__file__).resolve().parent / 'ml'
_MODEL_PATH = _ML_DIR / 'random_forest_sentiment.pkl'
_STOPWORDS_PATH = _ML_DIR / 'stopwords_en.txt'

_model = joblib.load(_MODEL_PATH)
_stemmer = SnowballStemmer('english')

with open(_STOPWORDS_PATH, 'r') as f:
    _STOP_WORDS = frozenset(line.strip() for line in f if line.strip())

_LABEL_MAP = {
    0: FeedbackEntry.NEGATIVE,
    1: FeedbackEntry.NEUTRAL,
    2: FeedbackEntry.POSITIVE,
    'negative': FeedbackEntry.NEGATIVE,
    'neutral': FeedbackEntry.NEUTRAL,
    'positive': FeedbackEntry.POSITIVE,
    'irrelevant': FeedbackEntry.PENDING,
}


def _preprocess_light(text):
    """
    Must stay byte-for-byte identical to the preprocess_light() used during
    training (lowercase -> strip non a-z/space -> split -> stopword filter
    -> stem), or predictions will silently diverge from what the model
    learned. Stopwords are loaded from ml/stopwords_en.txt, a frozen
    snapshot of nltk.corpus.stopwords.words('english') verified to match
    the live nltk fetch exactly.
    """
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'[^a-z\s]', '', text)
    tokens = text.split()
    filtered_tokens = [
        _stemmer.stem(word)
        for word in tokens
        if word not in _STOP_WORDS
    ]
    return " ".join(filtered_tokens)


def analyze_comment_sentiment(comment):
    """
    Sentiment must be inferred from the free-text comment only. Do not map
    the user's selected experience rating to positive, neutral, or
    negative because satisfaction ratings and comment sentiment are
    separate signals.
    """
    if not comment:
        return FeedbackEntry.PENDING
    cleaned = _preprocess_light(comment)
    if not cleaned:
        return FeedbackEntry.PENDING
    predicted_label = _model.predict([cleaned])[0]
    normalized_label = (
        predicted_label.strip().lower()
        if isinstance(predicted_label, str)
        else predicted_label
    )
    return _LABEL_MAP.get(normalized_label, FeedbackEntry.PENDING)

def reanalyze_pending_entries(force=False):
    """
    Runs sentiment analysis on feedback entries.

    By default, only entries with a non-blank comment that are still
    PENDING are processed — anything already categorized (pos/neu/neg)
    is left untouched. Pass force=True to reprocess every entry with a
    comment regardless of its current sentiment (intended for after
    retraining the model with new data, not for routine use).

    Returns (total_scanned, processed_count).
    """
    qs = FeedbackEntry.objects.exclude(comment='')
    if not force:
        qs = qs.filter(sentiment=FeedbackEntry.PENDING)

    total = qs.count()
    processed = 0

    for entry in qs.iterator(chunk_size=200):
        new_sentiment = analyze_comment_sentiment(entry.comment)
        if new_sentiment != entry.sentiment:
            entry.sentiment = new_sentiment
            entry.save(update_fields=['sentiment', 'updated_at'])
            processed += 1

    return total, processed
