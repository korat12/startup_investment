# utils/db.py
import json
import streamlit as st
import pymysql
from pymysql.err import MySQLError


def _get_conn():
    conn = st.session_state.get("DB_CONN")
    if conn is None or not getattr(conn, "open", False):
        raise RuntimeError("Database connection not initialized in app.py")
    return conn


def run_query(query, params=None, fetch=False):
    conn = _get_conn()
    cursor = None
    try:
        cursor = conn.cursor()  # DictCursor already set in app.py
        cursor.execute(query, params or ())
        if fetch:
            return cursor.fetchall()
        else:
            conn.commit()
            return True
    except MySQLError as e:
        print("Query error:", e)
        raise
    finally:
        if cursor is not None:
            cursor.close()


def get_user_profile(email):
    q = "SELECT id, email, name, role FROM users WHERE email=%s LIMIT 1"
    rows = run_query(q, (email,), fetch=True)
    return rows[0] if rows else None


def has_preferences(user_id: int) -> bool:
    q = "SELECT 1 FROM user_preferences WHERE user_id=%s LIMIT 1"
    rows = run_query(q, (user_id,), fetch=True)
    return bool(rows)




def save_preferences(user_id, sectors, stages, geography, risk, invest_size, goals=None, budget=None, experience=None, insights_pref=None):
    sectors_json = json.dumps(sectors) if sectors else '[]'
    stages_json = json.dumps(stages) if stages else '[]'
    geography_json = json.dumps(geography) if geography else '[]'
    budget_json = json.dumps(budget) if budget else '[]'
    insights_json = json.dumps(insights_pref) if insights_pref else '[]'
    q = """
        INSERT INTO user_preferences 
        (user_id, sectors, stages, geography, risk_level, investment_size, investment_goals, budget_ranges, experience_level, preferred_insights)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        sectors=%s, stages=%s, geography=%s, risk_level=%s, investment_size=%s, 
        investment_goals=%s, budget_ranges=%s, experience_level=%s, preferred_insights=%s
    """
    params = (
        user_id, sectors_json, stages_json, geography_json, risk, invest_size, goals, budget_json, experience, insights_json,
        sectors_json, stages_json, geography_json, risk, invest_size, goals, budget_json, experience, insights_json
    )
    run_query(q, params)


def update_preferences(user_id, sectors, stages, geography, risk, invest_size):
    save_preferences(user_id, sectors, stages, geography, risk, invest_size)


def log_activity(user_id, action_type, target, page=None, session_id=None, metadata=None):
    metadata_json = json.dumps(metadata) if metadata else '{}'
    q = "INSERT INTO user_activity (user_id, action_type, target, page, session_id, metadata) VALUES (%s, %s, %s, %s, %s, %s)"
    run_query(q, (user_id, action_type, target, page, session_id, metadata_json))


def add_watchlist(user_id, company):
    q = "INSERT INTO watchlist (user_id, company) VALUES (%s, %s)"
    run_query(q, (user_id, company))


def get_watchlist(user_id):
    q = "SELECT company FROM watchlist WHERE user_id=%s"
    return run_query(q, (user_id,), fetch=True)


def remove_watchlist(user_id, company):
    q = "DELETE FROM watchlist WHERE user_id=%s AND company=%s"
    run_query(q, (user_id, company))


def submit_feedback(user_id, ftype, target, rating=None, comments=None):
    q = "INSERT INTO user_feedback (user_id, feedback_type, target, rating, comments) VALUES (%s, %s, %s, %s, %s)"
    run_query(q, (user_id, ftype, target, rating, comments))


def get_user_insights(user_id):
    q = "SELECT * FROM user_insights WHERE user_id=%s"
    res = run_query(q, (user_id,), fetch=True)
    return res[0] if res else None


def update_user_insights(user_id, top_sectors, top_companies, trends=None):
    top_sec_json = json.dumps(top_sectors) if top_sectors else '{}'
    top_comp_json = json.dumps(top_companies) if top_companies else '[]'
    q = """
        INSERT INTO user_insights (user_id, top_sectors, top_companies, recent_trends)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE top_sectors=%s, top_companies=%s, recent_trends=%s
    """
    run_query(q, (user_id, top_sec_json, top_comp_json, trends, top_sec_json, top_comp_json, trends))