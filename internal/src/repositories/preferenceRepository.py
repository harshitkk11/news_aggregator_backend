from internal.src.db.connection import get_connection
class PreferenceRepository:
    def __init__(self):
        self.conn = get_connection()

    async def get_user_preference_count(self, user_id: str) -> int:
        query = """
        SELECT COUNT(*) FROM user_preferences WHERE user_id = %s;
        """
        with self.conn.cursor() as cursor:
            cursor.execute(query, (user_id,))
            (count,) = cursor.fetchone()
        return count

    async def populate_default_preferences(self, user_id: str):
        query = """
        INSERT INTO user_preferences (user_id, preference_item_id, status)
        SELECT %s, id, true FROM preference_items WHERE deleted_at IS NULL;
        """
        with self.conn.cursor() as cursor:
            cursor.execute(query, (user_id,))
        self.conn.commit()

    async def get_active_preference_items(self):
        query = """
        SELECT id, category FROM preference_items WHERE deleted_at IS NULL ORDER BY id ASC;
        """
        with self.conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            return [{"id": row[0], "category": row[1]} for row in rows]

    async def get_existing_preferences(self, user_id: str):
        query = """
        SELECT preference_item_id, status FROM user_preferences WHERE user_id = %s;
        """
        with self.conn.cursor() as cursor:
            cursor.execute(query, (user_id,))
            rows = cursor.fetchall()
            return [{"preference_item_id": row[0], "status": row[1]} for row in rows]
