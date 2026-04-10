"""
初回 superadmin ユーザーを作成するスクリプト。

使い方:
    cd backend
    uv run python create_superadmin.py

環境変数で上書き可能:
    VAM_SUPERADMIN_EMAIL=xxx uv run python create_superadmin.py
"""

import os
import sys

from app.database import SessionLocal
from app.models.user import User
from app.auth.jwt import hash_password

EMAIL = os.environ.get("VAM_SUPERADMIN_EMAIL", "superadmin@vam.local")
USERNAME = os.environ.get("VAM_SUPERADMIN_USERNAME", "superadmin")
PASSWORD = os.environ.get("VAM_SUPERADMIN_PASSWORD", "changeme123")


def main() -> None:
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.role == "superadmin").first()
        if existing:
            print(f"[SKIP] superadmin already exists: {existing.email}")
            sys.exit(0)

        if db.query(User).filter(User.email == EMAIL).first():
            print(f"[ERROR] Email already in use: {EMAIL}")
            sys.exit(1)

        if db.query(User).filter(User.username == USERNAME).first():
            print(f"[ERROR] Username already in use: {USERNAME}")
            sys.exit(1)

        user = User(
            email=EMAIL,
            username=USERNAME,
            hashed_password=hash_password(PASSWORD),
            role="superadmin",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        print("=" * 40)
        print("[OK] superadmin created")
        print(f"  email   : {user.email}")
        print(f"  username: {user.username}")
        print(f"  password: {PASSWORD}")
        print(f"  id      : {user.id}")
        print("=" * 40)
        print("[!] 本番環境では必ずパスワードを変更してください")

    finally:
        db.close()


if __name__ == "__main__":
    main()
