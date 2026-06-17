from .models import FeedbackEntry


def analyze_comment_sentiment(comment):
    """
    Placeholder for the future sentiment model.

    Sentiment must be inferred from the free-text comment only. Do not map the
    user's selected experience rating to positive, neutral, or negative because
    satisfaction ratings and comment sentiment are separate signals.
    """
    if not comment:
        return FeedbackEntry.PENDING

    # TODO: Replace this with the trained sentiment model prediction.
    return FeedbackEntry.PENDING
