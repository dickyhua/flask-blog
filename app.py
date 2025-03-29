from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import or_
from datetime import datetime
import os
import base64
import re
from io import BytesIO
from PIL import Image
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # 在生产环境中应该使用环境变量
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(os.path.dirname(os.path.abspath(__file__)), "blog.db")}'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上传文件大小为16MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# 确保上传文件夹存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# 用户模型
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True)
    is_admin = db.Column(db.Boolean, default=False)  # 新增管理员标识
    posts = db.relationship('Post', backref='author', lazy=True)

# 文章模型
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(255))  # 新增图片文件名字段
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload_image', methods=['POST'])
@login_required
def upload_image():
    try:
        print("Received upload request")  # 调试信息
        
        # 检查是否有文件
        if 'upload' not in request.files:
            print("No file part")  # 调试信息
            return jsonify({
                'error': {
                    'message': 'No file uploaded'
                }
            }), 400
        
        file = request.files['upload']
        
        # 检查文件名是否为空
        if file.filename == '':
            print("No selected file")  # 调试信息
            return jsonify({
                'error': {
                    'message': 'No file selected'
                }
            }), 400
        
        # 检查文件类型
        if not allowed_file(file.filename):
            print(f"Invalid file type: {file.filename}")  # 调试信息
            return jsonify({
                'error': {
                    'message': 'Invalid file type'
                }
            }), 400
        
        # 生成安全的文件名
        original_filename = secure_filename(file.filename)
        extension = original_filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{extension}"
        
        # 保存文件
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        print(f"File saved to: {filepath}")  # 调试信息
        
        # 返回文件URL
        file_url = url_for('static', filename=f'uploads/{filename}')
        print(f"File URL: {file_url}")  # 调试信息
        
        return jsonify({
            'url': file_url
        })
        
    except Exception as e:
        print(f"Error during upload: {str(e)}")  # 调试信息
        return jsonify({
            'error': {
                'message': str(e)
            }
        }), 500

# 首页路由
@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 5  # 每页显示5篇文章
    search_query = request.args.get('q', '')
    
    if search_query:
        # 搜索标题或作者名
        posts_query = Post.query.join(User).filter(
            or_(
                Post.title.contains(search_query),
                User.username.contains(search_query)
            )
        )
    else:
        posts_query = Post.query
    
    # 按创建时间倒序排序并分页
    pagination = posts_query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('index.html', 
                         posts=pagination.items,
                         pagination=pagination,
                         search_query=search_query)

# 注册路由
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not password:
            flash('用户名和密码不能为空')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('两次输入的密码不一致')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('用户名已存在')
            return redirect(url_for('register'))
        
        user = User(username=username)
        user.password_hash = generate_password_hash(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('注册成功！请登录')
            return redirect(url_for('login', username=username))
        except Exception as e:
            db.session.rollback()
            flash(f'注册失败：{str(e)}')
            return redirect(url_for('register'))
    
    return render_template('register.html')

# 登录路由
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('manage_posts'))
        flash('用户名或密码错误')
    return render_template('login.html')

# 注销路由
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('您已成功退出登录。', 'success')
    return redirect(url_for('index'))

# 发布新文章路由
@app.route('/new_post', methods=['GET', 'POST'])
@login_required
def new_post():
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            content = request.form.get('content')
            
            if not title or not content:
                flash('标题和内容不能为空')
                return redirect(url_for('new_post'))
            
            post = Post(
                title=title,
                content=content,
                author=current_user
            )
            db.session.add(post)
            db.session.commit()
            flash('文章发布成功！')
            return redirect(url_for('manage_posts'))
        except Exception as e:
            flash(f'发布失败：{str(e)}')
            return redirect(url_for('new_post'))
    
    return render_template('new_post.html')

# 编辑文章路由
@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    # 检查权限：管理员可以编辑所有文章，普通用户只能编辑自己的文章
    if not current_user.is_admin and post.author != current_user:
        flash('您没有权限编辑这篇文章')
        return redirect(url_for('manage_posts'))
    
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            content = request.form.get('content')
            
            if not title or not content:
                flash('标题和内容不能为空')
                return redirect(url_for('edit_post', post_id=post_id))
            
            post.title = title
            post.content = content
            post.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            flash('文章更新成功！')
            return redirect(url_for('manage_posts'))
        except Exception as e:
            flash(f'更新失败：{str(e)}')
            return redirect(url_for('edit_post', post_id=post_id))
    return render_template('edit_post.html', post=post)

# 删除文章路由
@app.route('/delete_post/<int:post_id>')
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if current_user.is_admin or post.author == current_user:
        db.session.delete(post)
        db.session.commit()
        flash('文章已删除')
    else:
        flash('你没有权限删除这篇文章')
    return redirect(url_for('manage_posts'))

# 文章详情页面路由
@app.route('/post/<int:post_id>')
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post_detail.html', post=post)

# 管理文章路由
@app.route('/manage_posts')
@login_required
def manage_posts():
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # 管理员可以看到所有文章，普通用户只能看到自己的文章
    if current_user.is_admin:
        posts = Post.query.order_by(Post.created_at.desc())
    else:
        posts = Post.query.filter_by(author=current_user).order_by(Post.created_at.desc())
    
    # 分页
    pagination = posts.paginate(page=page, per_page=per_page, error_out=False)
    return render_template('manage_posts.html', posts=pagination.items, pagination=pagination)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
