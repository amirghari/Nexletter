import pytest
from unittest.mock import MagicMock
from recommender.scorer import calculate_score

@pytest.fixture
def mock_conn_with_liked_titles():
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cursor
    cursor.fetchall.return_value = [
        ("Crypto Short Sellers Took A Hit Following De-escalation Of Conflict Between Israel and Iran",)
    ]
    return conn

def test_score_full_preference_match(mock_conn_with_liked_titles):
    article = (1, "AI beats humans at chess", "USA", ["technology"])
    user_profile = {
        "preferred_countries": ["USA"],
        "preferred_categories": ["technology"],
        "liked_categories": {},
        "liked_countries": {}
    }
    time_spent_map = {1: 1000}
    user_id = 1

    result = calculate_score(article, user_profile, time_spent_map, mock_conn_with_liked_titles, user_id)
    assert result["score"] >= 13  # includes 5 + 5 + 5, maybe more from NLP

def test_score_with_liked_category_and_country(mock_conn_with_liked_titles):
    article = (2, "Breaking crypto news", "USA", ["crypto"])
    user_profile = {
        "preferred_countries": [],
        "preferred_categories": [],
        "liked_categories": {"crypto": 4},
        "liked_countries": {"usa": 3}
    }
    time_spent_map = {2: 200}
    user_id = 1

    result = calculate_score(article, user_profile, time_spent_map, mock_conn_with_liked_titles, user_id)
    assert result["score"] >= 7  # 4 + 3 from liked fields

def test_score_with_time_spent_bonus(mock_conn_with_liked_titles):
    article = (3, "EU economy news", "France", ["economy"])
    user_profile = {
        "preferred_countries": [],
        "preferred_categories": [],
        "liked_categories": {},
        "liked_countries": {}
    }
    user_id = 1

    result1 = calculate_score(article, user_profile, {3: 650}, mock_conn_with_liked_titles, user_id)
    result2 = calculate_score(article, user_profile, {3: 1000}, mock_conn_with_liked_titles, user_id)
    result3 = calculate_score(article, user_profile, {3: 300}, mock_conn_with_liked_titles, user_id)

    assert result1["score"] >= 2
    assert result2["score"] >= 5
    assert result3["score"] >= 0