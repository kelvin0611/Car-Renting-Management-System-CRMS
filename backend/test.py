import os

import mysql.connector
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

def connect_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "p2p_car_rental"),
    )

def create_user(cursor, userType, name, gmail, identityNo, address):
    sql = """
        INSERT INTO `User` (`userType`, `name`, `gmail`, `identityNo`, `address`)
        VALUES (%s, %s, %s, %s, %s)
    """
    cursor.execute(sql, (userType, name, gmail, identityNo, address))

def read_users(cursor):
    cursor.execute("SELECT * FROM `User`")
    return cursor.fetchall()

def update_user(cursor, user_id, new_userType, new_name, new_gmail, new_identityNo, new_address):
    try:
        # Parameterized query (safe method)
        sql = "UPDATE `User` SET `userType`=%s, `name`=%s, `gmail`=%s, `identityNo`=%s, `address`=%s WHERE `user_id`=%s"
        params = (new_userType, new_name, new_gmail, new_identityNo, new_address, user_id)
        cursor.execute(sql, params)
        return True
    except Exception as e:
        print(f"Failed to update user: {e}")
        return False

def show_tables(cursor):
    cursor.execute("SHOW TABLES;")
    return cursor.fetchall()

def get_user_columns(cursor):
    """Get column information for User table"""
    cursor.execute("DESCRIBE `User`;")
    return cursor.fetchall()

def main():
    try:
        db = connect_db()
        print("Database connection successful!")
        cursor = db.cursor()

        # Show all tables
        print("\nTables in database:")
        for table in show_tables(cursor):
            print(table[0])

        # Show User table structure
        print("\nUser table structure:")
        columns = get_user_columns(cursor)
        for column in columns:
            print(column)

        # --------------------------
        # Test Case: CRUD Operations Demo
        # --------------------------

        print("\n[Test] Inserting new user...")
        create_user(cursor, "renter", "Bob", "bob@gmail.com", "C999888777", "Hong Kong")
        db.commit()

        print("\n[Test] Querying all users...")
        users = read_users(cursor)
        for user in users:
            print(user)

        print("\n[Test] Updating user information...")
        if users:
            # Find Bob user
            bob_user = None
            for user in users:
                if user[2] == "Bob":  # name is in third column
                    bob_user = user
                    break
            
            if bob_user:
                user_id = bob_user[0]
                
                # Use parameterized query for update
                success = update_user(cursor, user_id, "owner", "Bob_updated", "bob_new@gmail.com", "D111222333", "Updated Address")
                
                if success:
                    db.commit()
                    print("User update successful!")
                else:
                    print("User update failed")

        print("\n[Test] Querying all users (after update)...")
        users = read_users(cursor)
        for user in users:
            print(user)

    except mysql.connector.Error as err:
        print(f"Connection failed: {err}")
    finally:
        if 'db' in locals() and db.is_connected():
            cursor.close()
            db.close()
            print("\nConnection closed")

if __name__ == "__main__":
    main()