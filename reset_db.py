from app import app, db
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
        
        print("数据库已重置完成！")

if __name__ == '__main__':
    reset_db()
