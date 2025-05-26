#!/usr/bin/env python3
"""
Admin Management Script
======================
Unified script for managing admin users and database setup.
"""

import sqlite3
import os
import sys

DB_PATH = 'database.db'

def check_admin_status(email):
    """Check if a user exists and their admin status."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT email, role FROM users WHERE email = ?', (email,))
        result = cursor.fetchone()
        
        if result:
            print(f"✅ User found: {result[0]} (Role: {result[1]})")
            return result[1] == 'admin'
        else:
            print(f"❌ User not found: {email}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking admin status: {e}")
        return False
    finally:
        conn.close()

def set_admin_role(email):
    """Set a user as admin."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        if not cursor.fetchone():
            print(f"❌ User {email} does not exist")
            return False
        
        # Update role to admin
        cursor.execute('UPDATE users SET role = ? WHERE email = ?', ('admin', email))
        conn.commit()
        
        if cursor.rowcount > 0:
            print(f"✅ User {email} is now an admin")
            return True
        else:
            print(f"❌ Failed to update user {email}")
            return False
            
    except Exception as e:
        print(f"❌ Error setting admin role: {e}")
        return False
    finally:
        conn.close()

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python admin_manager.py check <email>")
        print("  python admin_manager.py set <email>")
        return
    
    action = sys.argv[1]
    
    if action == "check" and len(sys.argv) == 3:
        email = sys.argv[2]
        check_admin_status(email)
    elif action == "set" and len(sys.argv) == 3:
        email = sys.argv[2]
        set_admin_role(email)
    else:
        print("Invalid arguments")
        print("Usage:")
        print("  python admin_manager.py check <email>")
        print("  python admin_manager.py set <email>")

if __name__ == "__main__":
    main()
