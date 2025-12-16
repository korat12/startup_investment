import pandas as pd
import json
import pymysql

# ---------------------------------------
# 1) Direct DB connection (no Streamlit)
# ---------------------------------------
try:
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="12082004",
        database="startup_app",
        port=3306,
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor,
    )
    print("✅ DB connected directly via PyMySQL")
except Exception as e:
    print("❌ DB connection failed:", e)
    exit(1)

print("🔄 Starting insights update...")

# ---------------------------------------
# 2) Fetch all active users
# ---------------------------------------
users_query = "SELECT id FROM users WHERE is_active = TRUE"
users = pd.read_sql(users_query, conn)

if users.empty:
    print("No active users found.")
    conn.close()
    exit(0)

# ---------------------------------------
# 3) Process each user
# ---------------------------------------
for _, user in users.iterrows():
    user_id = user["id"]
    print(f"Processing user {user_id}...")

    activity_query = """
        SELECT target, action_type, COUNT(*) as score
        FROM user_activity
        WHERE user_id = %s AND timestamp > DATE_SUB(NOW(), INTERVAL 30 DAY)
        GROUP BY target, action_type
        ORDER BY score DESC
    """
    act_df = pd.read_sql(activity_query, conn, params=(user_id,))

    if act_df.empty:
        print(f"  → No recent activity for user {user_id}. Skipping.")
        continue

    # Top sectors: any action_type containing 'sector'
    sector_df = act_df[act_df["action_type"].str.contains("sector", case=False, na=False)]
    top_sectors = dict(sector_df.head(5)[["target", "score"]].values)

    # Top companies: action_type == 'view_company'
    company_df = act_df[act_df["action_type"] == "view_company"]
    top_companies = company_df.head(5)["target"].tolist()

    # Simple trend text
    trends = f"Your top sector {list(top_sectors.keys())[0] if top_sectors else 'N/A'} saw 15% funding growth recently."

    # ---------------------------------------
    # 4) Update user_insights directly
    # ---------------------------------------
    with conn.cursor() as cursor:
        upsert_query = """
            INSERT INTO user_insights (user_id, top_sectors, top_companies, recent_trends)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
              top_sectors=%s,
              top_companies=%s,
              recent_trends=%s
        """
        cursor.execute(
            upsert_query,
            (
                user_id,
                json.dumps(top_sectors),
                json.dumps(top_companies),
                trends,
                json.dumps(top_sectors),
                json.dumps(top_companies),
                trends,
            ),
        )

    print(f"  → Updated: {len(top_sectors)} sectors, {len(top_companies)} companies.")

print("✅ All insights updated successfully.")
conn.close()
