from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
import psycopg2.extras
import os
import urllib.parse
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'

# 数据库连接配置
DB_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'user': 'gaussdb',
    'password': 'openGauss@123',
    'database': 'library_db',
    'client_encoding': 'utf8'
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def init_db():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        # 创建用户表
        cur.execute('''
            CREATE TABLE IF NOT EXISTS "user" (
                id SERIAL PRIMARY KEY,
                username VARCHAR(80) UNIQUE NOT NULL,
                password_hash VARCHAR(120) NOT NULL,
                role VARCHAR(20) NOT NULL DEFAULT 'student'
            )
        ''')
        
        # 创建图书表
        cur.execute('''
            CREATE TABLE IF NOT EXISTS book (
                id SERIAL PRIMARY KEY,
                title VARCHAR(100) NOT NULL,
                author VARCHAR(100) NOT NULL,
                isbn VARCHAR(13) UNIQUE NOT NULL,
                status VARCHAR(20) DEFAULT 'available',
                total_copies INTEGER NOT NULL,
                available_copies INTEGER NOT NULL
            )
        ''')

        # 创建借阅记录表
        cur.execute('''
            CREATE TABLE IF NOT EXISTS borrowing_record (
                id SERIAL PRIMARY KEY,
                book_id INTEGER REFERENCES book(id),
                user_id INTEGER REFERENCES "user"(id),
                borrow_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                return_date TIMESTAMP,
                status VARCHAR(20) DEFAULT 'borrowed'
            )
        ''')
        
        conn.commit()
    except Exception as e:
        print(f"初始化数据库时出错: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        try:
            cur.execute('SELECT * FROM "user" WHERE username = %s', (username,))
            user = cur.fetchone()
            
            if user and check_password_hash(user['password_hash'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user['role']
                flash('登录成功', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('用户名或密码错误', 'error')
        except Exception as e:
            print(f"登录时发生错误: {e}")
            flash('登录失败，请稍后重试', 'error')
        finally:
            cur.close()
            conn.close()
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        
        if not username or not password or not role:
            flash('请填写所有必填字段')
            return redirect(url_for('register'))
        
        if role not in ['student', 'admin']:
            flash('无效的角色选择')
            return redirect(url_for('register'))
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        try:
            # 检查用户名是否已存在
            cur.execute('SELECT 1 FROM "user" WHERE username = %s', (username,))
            if cur.fetchone():
                flash('用户名已存在')
                return redirect(url_for('register'))
            
            # 创建新用户
            password_hash = generate_password_hash(password)
            cur.execute(
                'INSERT INTO "user" (username, password_hash, role) VALUES (%s, %s, %s)',
                (username, password_hash, role)
            )
            conn.commit()
            flash('注册成功，请登录')
            return redirect(url_for('login'))
        except Exception as e:
            print(f"注册时出错: {e}")
            conn.rollback()
            flash('注册时发生错误')
        finally:
            cur.close()
            conn.close()
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # 获取用户信息
        cur.execute('SELECT * FROM "user" WHERE id = %s', (session['user_id'],))
        user = cur.fetchone()
        
        # 获取图书列表
        cur.execute('''
            SELECT b.*, 
                   COUNT(br.id) as borrow_count
            FROM book b
            LEFT JOIN borrowing_record br ON b.id = br.book_id
            GROUP BY b.id
            ORDER BY b.id
        ''')
        books = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return render_template('dashboard.html', user=user, books=books)
    except Exception as e:
        print(f"获取图书列表时发生错误: {e}")
        flash('获取图书列表失败，请稍后重试', 'error')
        return redirect(url_for('login'))

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('权限不足')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        isbn = request.form.get('isbn')
        quantity = int(request.form.get('quantity', 1))
        
        if quantity < 1:
            flash('副本数量必须大于0')
            return render_template('add_book.html')
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        try:
            cur.execute(
                'INSERT INTO book (title, author, isbn, total_copies, available_copies) VALUES (%s, %s, %s, %s, %s)',
                (title, author, isbn, quantity, quantity)
            )
            conn.commit()
            flash('图书添加成功')
            return redirect(url_for('dashboard'))
        except psycopg2.IntegrityError:
            conn.rollback()
            flash('ISBN已存在')
        except Exception as e:
            print(f"添加图书时出错: {e}")
            conn.rollback()
            flash('添加图书时发生错误')
        finally:
            cur.close()
            conn.close()
    return render_template('add_book.html')

@app.route('/delete/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    if 'user_id' not in session:
        flash('请先登录', 'error')
        return redirect(url_for('login'))
    
    if session.get('role') != 'admin':
        flash('只有管理员可以删除图书', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # 检查图书是否存在
        cur.execute('SELECT * FROM book WHERE id = %s', (book_id,))
        book = cur.fetchone()
        
        if not book:
            flash('图书不存在', 'error')
            return redirect(url_for('dashboard'))
        
        # 获取要删除的副本数量
        delete_quantity = int(request.form.get('quantity', 1))
        if delete_quantity < 1:
            flash('删除数量必须大于0', 'error')
            return redirect(url_for('dashboard'))
        
        # 检查是否有未归还的借阅记录
        cur.execute('''
            SELECT COUNT(*) FROM borrowing_record 
            WHERE book_id = %s AND status = 'borrowed'
        ''', (book_id,))
        
        borrowed_count = cur.fetchone()[0]
        available_copies = book['available_copies']
        
        if delete_quantity > available_copies:
            flash(f'只能删除{available_copies}本可用的副本', 'error')
            return redirect(url_for('dashboard'))
        
        # 开始事务
        cur.execute('BEGIN')
        
        try:
            # 更新图书数量
            cur.execute('''
                UPDATE book 
                SET total_copies = total_copies - %s,
                    available_copies = available_copies - %s
                WHERE id = %s
            ''', (delete_quantity, delete_quantity, book_id))
            
            # 如果所有副本都被删除，则删除图书记录
            cur.execute('SELECT total_copies FROM book WHERE id = %s', (book_id,))
            remaining_copies = cur.fetchone()['total_copies']
            
            if remaining_copies <= 0:
                # 删除借阅记录
                cur.execute('DELETE FROM borrowing_record WHERE book_id = %s', (book_id,))
                # 删除图书
                cur.execute('DELETE FROM book WHERE id = %s', (book_id,))
            
            # 提交事务
            cur.execute('COMMIT')
            flash(f'成功删除{delete_quantity}本图书', 'success')
            
        except Exception as e:
            # 回滚事务
            cur.execute('ROLLBACK')
            raise e
            
    except Exception as e:
        print(f"删除图书时发生错误: {e}")
        flash('删除图书失败，请稍后重试', 'error')
    finally:
        cur.close()
        conn.close()
    
    return redirect(url_for('dashboard'))

@app.route('/borrow/<int:book_id>', methods=['POST'])
def borrow_book(book_id):
    if 'user_id' not in session:
        flash('请先登录', 'error')
        return redirect(url_for('login'))
    
    if session.get('role') != 'student':
        flash('只有学生可以借阅图书', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # 验证用户是否存在
        cur.execute('SELECT * FROM "user" WHERE id = %s', (session['user_id'],))
        user = cur.fetchone()
        
        if not user:
            session.clear()  # 清除无效的会话
            flash('用户信息无效，请重新登录', 'error')
            return redirect(url_for('login'))
        
        # 检查图书是否存在且可借
        cur.execute('SELECT * FROM book WHERE id = %s', (book_id,))
        book = cur.fetchone()
        
        if not book:
            flash('图书不存在', 'error')
            return redirect(url_for('dashboard'))
        
        if book['available_copies'] <= 0:
            flash('该图书已无可借副本', 'error')
            return redirect(url_for('dashboard'))
        
        # 检查用户是否已经借阅过这本书且未归还
        cur.execute('''
            SELECT * FROM borrowing_record 
            WHERE book_id = %s AND user_id = %s AND status = 'borrowed'
        ''', (book_id, session['user_id']))
        
        if cur.fetchone():
            flash('您已经借阅过这本书且未归还', 'error')
            return redirect(url_for('dashboard'))
        
        # 开始事务
        cur.execute('BEGIN')
        
        try:
            # 更新图书可借数量
            cur.execute('''
                UPDATE book 
                SET available_copies = available_copies - 1 
                WHERE id = %s AND available_copies > 0
            ''', (book_id,))
            
            if cur.rowcount == 0:
                raise Exception('图书可借数量更新失败')
            
            # 创建借阅记录
            cur.execute('''
                INSERT INTO borrowing_record (book_id, user_id, borrow_date, status)
                VALUES (%s, %s, CURRENT_TIMESTAMP, 'borrowed')
            ''', (book_id, session['user_id']))
            
            # 提交事务
            cur.execute('COMMIT')
            flash('借阅成功', 'success')
            
        except Exception as e:
            # 回滚事务
            cur.execute('ROLLBACK')
            raise e
            
    except Exception as e:
        print(f"借书时发生错误: {e}")
        flash('借书失败，请稍后重试', 'error')
    finally:
        cur.close()
        conn.close()
    
    return redirect(url_for('dashboard'))

@app.route('/return/<int:book_id>', methods=['POST'])
def return_book(book_id):
    if 'user_id' not in session:
        flash('请先登录')
        return redirect(url_for('login'))
    
    if session['role'] != 'student':
        flash('只有学生可以还书')
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        # 检查是否有未归还的借阅记录
        cur.execute('''
            SELECT id FROM borrowing_record 
            WHERE book_id = %s AND user_id = %s AND status = 'borrowed'
        ''', (book_id, session['user_id']))
        
        record = cur.fetchone()
        if not record:
            flash('您没有借阅这本书')
            return redirect(url_for('dashboard'))
        
        # 开始归还流程
        cur.execute('BEGIN')
        
        # 更新图书可用数量
        cur.execute('''
            UPDATE book 
            SET available_copies = available_copies + 1 
            WHERE id = %s
        ''', (book_id,))
        
        # 更新借阅记录
        cur.execute('''
            UPDATE borrowing_record 
            SET return_date = CURRENT_TIMESTAMP, status = 'returned'
            WHERE id = %s
        ''', (record['id'],))
        
        conn.commit()
        flash('归还成功')
        
    except Exception as e:
        print(f"还书时出错: {e}")
        conn.rollback()
        flash('还书失败，请稍后重试')
    finally:
        cur.close()
        conn.close()
    
    return redirect(url_for('my_books'))

@app.route('/my_books')
def my_books():
    if 'user_id' not in session:
        flash('请先登录')
        return redirect(url_for('login'))
    
    if session['role'] != 'student':
        flash('只有学生可以查看借阅记录')
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute('''
            SELECT b.*, br.borrow_date, br.return_date, br.status as borrow_status
            FROM book b
            JOIN borrowing_record br ON b.id = br.book_id
            WHERE br.user_id = %s
            ORDER BY br.borrow_date DESC
        ''', (session['user_id'],))
        books = cur.fetchall()
    except Exception as e:
        print(f"获取借阅记录时出错: {e}")
        books = []
    finally:
        cur.close()
        conn.close()
    
    return render_template('my_books.html', books=books)

@app.route('/search')
def search():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    query = request.args.get('query', '') or request.args.get('search', '')
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        if session.get('role') == 'admin':
            cur.execute('''
                SELECT b.*, 
                       COUNT(br.id) as borrow_count
                FROM book b
                LEFT JOIN borrowing_record br ON b.id = br.book_id
                WHERE b.title ILIKE %s 
                OR b.author ILIKE %s 
                OR b.isbn ILIKE %s
                GROUP BY b.id
                ORDER BY b.id
            ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
        else:
            cur.execute('''
                SELECT b.*, 
                       COUNT(br.id) as borrow_count
                FROM book b
                LEFT JOIN borrowing_record br ON b.id = br.book_id
                WHERE (b.title ILIKE %s 
                OR b.author ILIKE %s 
                OR b.isbn ILIKE %s)
                AND b.available_copies > 0
                GROUP BY b.id
                ORDER BY b.id
            ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
        books = cur.fetchall()
        return render_template('search_results.html', books=books, query=query)
    except Exception as e:
        print(f"搜索图书时出错: {e}")
        flash('搜索图书时发生错误')
        return render_template('search_results.html', books=[], query=query)
    finally:
        cur.close()
        conn.close()

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/statistics')
def statistics():
    if 'user_id' not in session:
        flash('请先登录')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        # 获取总藏书量
        cur.execute('SELECT SUM(total_copies) as total FROM book')
        total_books = cur.fetchone()['total'] or 0
        
        # 获取可借图书数量
        cur.execute('SELECT SUM(available_copies) as available FROM book')
        available_books = cur.fetchone()['available'] or 0
        
        # 获取已借出图书数量
        borrowed_books = total_books - available_books
        
        # 获取当前借阅人数
        cur.execute('''
            SELECT COUNT(DISTINCT user_id) as active_borrowers 
            FROM borrowing_record 
            WHERE status = 'borrowed'
        ''')
        active_borrowers = cur.fetchone()['active_borrowers']
        
        # 获取最受欢迎的图书（借阅次数最多的前5本）
        cur.execute('''
            SELECT b.title, b.author, b.total_copies, b.available_copies,
                   COUNT(br.id) as borrow_count
            FROM book b
            LEFT JOIN borrowing_record br ON b.id = br.book_id
            GROUP BY b.id, b.title, b.author, b.total_copies, b.available_copies
            ORDER BY borrow_count DESC
            LIMIT 5
        ''')
        popular_books = cur.fetchall()
        
        # 获取最近借阅的图书
        cur.execute('''
            SELECT b.title, b.author, br.borrow_date, u.username
            FROM borrowing_record br
            JOIN book b ON br.book_id = b.id
            JOIN "user" u ON br.user_id = u.id
            ORDER BY br.borrow_date DESC
            LIMIT 5
        ''')
        recent_borrows = cur.fetchall()
        
        return render_template('statistics.html',
                             total_books=total_books,
                             available_books=available_books,
                             borrowed_books=borrowed_books,
                             active_borrowers=active_borrowers,
                             popular_books=popular_books,
                             recent_borrows=recent_borrows)
                             
    except Exception as e:
        print(f"获取统计数据时出错: {e}")
        flash('获取统计数据时发生错误')
        return redirect(url_for('dashboard'))
    finally:
        cur.close()
        conn.close()

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        flash('请先登录', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not current_password or not new_password or not confirm_password:
            flash('请填写所有字段', 'error')
            return redirect(url_for('change_password'))
        
        if new_password != confirm_password:
            flash('两次输入的新密码不一致', 'error')
            return redirect(url_for('change_password'))
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        try:
            # 验证当前密码
            cur.execute('SELECT password_hash FROM "user" WHERE id = %s', (session['user_id'],))
            user = cur.fetchone()
            
            if not user or not check_password_hash(user['password_hash'], current_password):
                flash('当前密码错误', 'error')
                return redirect(url_for('change_password'))
            
            # 更新密码
            new_password_hash = generate_password_hash(new_password)
            cur.execute(
                'UPDATE "user" SET password_hash = %s WHERE id = %s',
                (new_password_hash, session['user_id'])
            )
            conn.commit()
            flash('密码修改成功', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            print(f"修改密码时出错: {e}")
            conn.rollback()
            flash('修改密码失败，请稍后重试', 'error')
        finally:
            cur.close()
            conn.close()
    
    return render_template('change_password.html')

@app.route('/increase/<int:book_id>', methods=['POST'])
def increase_book_copy(book_id):
    if 'user_id' not in session:
        flash('请先登录', 'error')
        return redirect(url_for('login'))
    if session.get('role') != 'admin':
        flash('只有管理员可以增加图书副本', 'error')
        return redirect(url_for('dashboard'))
    try:
        quantity = int(request.form.get('quantity', 1))
        if quantity < 1:
            flash('增加数量必须大于0', 'error')
            return redirect(url_for('dashboard'))
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        # 检查图书是否存在
        cur.execute('SELECT * FROM book WHERE id = %s', (book_id,))
        book = cur.fetchone()
        if not book:
            flash('图书不存在', 'error')
            return redirect(url_for('dashboard'))
        # 增加副本
        cur.execute('''
            UPDATE book 
            SET total_copies = total_copies + %s,
                available_copies = available_copies + %s
            WHERE id = %s
        ''', (quantity, quantity, book_id))
        conn.commit()
        flash(f'成功增加{quantity}本图书', 'success')
    except Exception as e:
        print(f"增加图书副本时发生错误: {e}")
        conn.rollback()
        flash('增加图书副本失败，请稍后重试', 'error')
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True) 