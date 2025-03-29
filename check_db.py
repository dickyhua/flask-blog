from app import app, db, User

with app.app_context():
    users = User.query.all()
    print("\n=== 用户列表 ===")
    for user in users:
        print(f"用户名: {user.username}")
        print(f"是否管理员: {user.is_admin}")
        print("-" * 20)
