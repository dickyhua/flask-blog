from werkzeug.security import generate_password_hash

from app import app, db, User
import os

def reset_db():
    # 确保在应用上下文中运行
    with app.app_context():
        # 删除数据库文件
        db_file = 'blog.db'
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"已删除旧的数据库文件: {db_file}")
        
        # 删除所有表
        print("删除所有表...")
        db.drop_all()
        
        # 创建所有表
        db.create_all()
        print("已创建新的数据库表")

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
        
        print("数据库已重置完成！")

if __name__ == '__main__':
    reset_db()
