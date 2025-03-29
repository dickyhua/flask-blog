from app import app, db, User
from werkzeug.security import generate_password_hash

def reset_admin_password(username, new_password):
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if user:
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            print(f"已成功重置用户 {username} 的密码")
        else:
            print(f"找不到用户: {username}")

# 重置 admin 用户的密码为 "admin123"
reset_admin_password('admin', 'admin123')
