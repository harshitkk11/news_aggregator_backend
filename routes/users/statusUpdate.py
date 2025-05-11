from flask import Blueprint, request, jsonify
from config.db import get_db_connection

update_status_bp = Blueprint("update_status", __name__)  

@update_status_bp.route("/update-status", methods=["PATCH"])
def update_user_status():
    try:
        data = request.get_json()
        user_id = data.get("userId")

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute('SELECT "isNew" FROM users WHERE "userId" = %s', (user_id,))
        result = cur.fetchone()

        if result is None:
            return jsonify({"success": False, "message": "User not found."}), 404

        is_new = result[0]

        if is_new:
            cur.execute('UPDATE users SET "isNew" = FALSE WHERE "userId" = %s', (user_id,))
            conn.commit()
            message = "Status updated."
        else:
            message = "User is not new."

        cur.close()
        conn.close()

        return jsonify({"success": True, "message": message}), 200

    except Exception as e:
        print("Update Status Error:", str(e))
        return jsonify({"success": False, "message": "Unexpected error"}), 500
