import re
import joblib
from pathlib import Path
from nltk.stem import SnowballStemmer

from .models import FeedbackEntry

_ML_DIR = Path(__file__).resolve().parent / 'ml'
_MODEL_PATH = _ML_DIR / 'random_forest_sentiment.pkl'
_STOPWORDS_PATH = _ML_DIR / 'stopwords_en.txt'

_model = None
_stemmer = SnowballStemmer('english')

_STOP_WORDS = set()
if _STOPWORDS_PATH.exists():
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


def _get_model():
    global _model
    if _model is None and _MODEL_PATH.exists():
        try:
            _model = joblib.load(_MODEL_PATH)
        except Exception:
            _model = False
    return _model if _model is not False else None


def _preprocess_light(text):
    if not isinstance(text, str):
        return ""
    # Strip form section header prefixes (e.g., "Comments: ", "Commendation: ")
    text = re.sub(r'^(Comments|Commendation|Comments & Suggestions):\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\|\s*(Comments|Commendation|Comments & Suggestions):\s*', ' ', text, flags=re.IGNORECASE)
    text = text.lower()
    text = re.sub(r'[^a-z\s]', '', text)
    tokens = text.split()
    filtered_tokens = [
        _stemmer.stem(word)
        for word in tokens
        if word not in _STOP_WORDS
    ]
    return " ".join(filtered_tokens)


def _experience_to_sentiment(experience):
    if experience == FeedbackEntry.VERY_SATISFACTORY:
        return FeedbackEntry.POSITIVE
    elif experience == FeedbackEntry.UNSATISFACTORY:
        return FeedbackEntry.NEGATIVE
    elif experience == FeedbackEntry.SATISFACTORY:
        return FeedbackEntry.NEUTRAL
    return FeedbackEntry.PENDING


def analyze_comment_sentiment(comment, experience=None):
    if not comment or not comment.strip():
        return FeedbackEntry.PENDING
    model = _get_model()
    cleaned = _preprocess_light(comment)
    
    if model and cleaned:
        try:
            predicted_label = model.predict([cleaned])[0]
            normalized_label = (
                predicted_label.strip().lower()
                if isinstance(predicted_label, str)
                else predicted_label
            )
            sentiment = _LABEL_MAP.get(normalized_label, FeedbackEntry.PENDING)
            if sentiment != FeedbackEntry.PENDING:
                return sentiment
        except Exception:
            pass

    # Fallback to user experience rating if ML model returned irrelevant/pending or failed
    if experience:
        fallback = _experience_to_sentiment(experience)
        if fallback != FeedbackEntry.PENDING:
            return fallback

    return FeedbackEntry.PENDING


def reanalyze_pending_entries(force=False):
    qs = FeedbackEntry.objects.exclude(comment='')
    if not force:
        qs = qs.filter(sentiment=FeedbackEntry.PENDING)

    total = qs.count()
    processed = 0

    for entry in qs.iterator(chunk_size=200):
        new_sentiment = analyze_comment_sentiment(entry.comment, experience=entry.experience)
        if new_sentiment != entry.sentiment:
            entry.sentiment = new_sentiment
            entry.save(update_fields=['sentiment', 'updated_at'])
            processed += 1

    return total, processed
