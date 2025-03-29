from app import app, db, User
from werkzeug.security import generate_password_hash

def init_db():
    with app.app_context():
        # 创建所有表
        db.create_all()
        
        # 检查是否已存在管理员用户
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            # 创建管理员用户
            admin = User(
                username='admin',
                password_hash=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print("已创建管理员用户 (用户名: admin, 密码: admin123)")
        else:
            print("管理员用户已存在，跳过创建")

if __name__ == '__main__':
    init_db()
