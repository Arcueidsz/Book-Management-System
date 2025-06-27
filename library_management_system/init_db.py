import psycopg2
import psycopg2.extras
from werkzeug.security import generate_password_hash

# 数据库连接配置
DB_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'user': 'gaussdb',
    'password': 'openGauss@123',
    'database': 'library_db',
    'client_encoding': 'utf8'
}

# 初始图书数据
INITIAL_BOOKS = [
    {
        'title': '三体',
        'author': '刘慈欣',
        'isbn': '9787536692930',
        'total_copies': 5,
        'available_copies': 5
    },
    {
        'title': '活着',
        'author': '余华',
        'isbn': '9787506365437',
        'total_copies': 3,
        'available_copies': 3
    },
    {
        'title': '百年孤独',
        'author': '加西亚·马尔克斯',
        'isbn': '9787544253994',
        'total_copies': 4,
        'available_copies': 4
    },
    {
        'title': '围城',
        'author': '钱钟书',
        'isbn': '9787020090006',
        'total_copies': 3,
        'available_copies': 3
    },
    {
        'title': '平凡的世界',
        'author': '路遥',
        'isbn': '9787530216781',
        'total_copies': 4,
        'available_copies': 4
    },
    {
        'title': '红楼梦',
        'author': '曹雪芹',
        'isbn': '9787020002207',
        'total_copies': 6,
        'available_copies': 6
    },
    {
        'title': '白鹿原',
        'author': '陈忠实',
        'isbn': '9787530216782',
        'total_copies': 3,
        'available_copies': 3
    },
    {
        'title': '追风筝的人',
        'author': '卡勒德·胡赛尼',
        'isbn': '9787532726173',
        'total_copies': 4,
        'available_copies': 4
    },
    {
        'title': '挪威的森林',
        'author': '村上春树',
        'isbn': '9787532725694',
        'total_copies': 5,
        'available_copies': 5
    },
    {
        'title': '1984',
        'author': '乔治·奥威尔',
        'isbn': '9787530210291',
        'total_copies': 3,
        'available_copies': 3
    },
    {
        'title': '人类简史',
        'author': '尤瓦尔·赫拉利',
        'isbn': '9787508647357',
        'total_copies': 4,
        'available_copies': 4
    },
    {
        'title': '时间简史',
        'author': '史蒂芬·霍金',
        'isbn': '9787535732309',
        'total_copies': 3,
        'available_copies': 3
    },
    {
        'title': '小王子',
        'author': '圣埃克苏佩里',
        'isbn': '9787532745441',
        'total_copies': 5,
        'available_copies': 5
    },
    {
        'title': '解忧杂货店',
        'author': '东野圭吾',
        'isbn': '9787544270878',
        'total_copies': 4,
        'available_copies': 4
    },
    {
        'title': '月亮与六便士',
        'author': '毛姆',
        'isbn': '9787532739547',
        'total_copies': 3,
        'available_copies': 3
    },
    {
        'title': '傲慢与偏见',
        'author': '简·奥斯汀',
        'isbn': '9787532736564',
        'total_copies': 4,
        'available_copies': 4
    },
    {
        'title': '简爱',
        'author': '夏洛蒂·勃朗特',
        'isbn': '9787532736565',
        'total_copies': 3,
        'available_copies': 3
    },
    {
        'title': '战争与和平',
        'author': '列夫·托尔斯泰',
        'isbn': '9787532736566',
        'total_copies': 5,
        'available_copies': 5
    },
    {
        'title': '罪与罚',
        'author': '陀思妥耶夫斯基',
        'isbn': '9787532736567',
        'total_copies': 3,
        'available_copies': 3
    },
    {
        'title': '老人与海',
        'author': '海明威',
        'isbn': '9787532736568',
        'total_copies': 4,
        'available_copies': 4
    },
    {
        'title': '动物农场',
        'author': '乔治·奥威尔',
        'isbn': '9787532736569',
        'total_copies': 3,
        'available_copies': 3
    },
    {
        'title': '麦田里的守望者',
        'author': 'J.D.塞林格',
        'isbn': '9787532736570',
        'total_copies': 4,
        'available_copies': 4
    },
    {
        'title': '百年孤独',
        'author': '加西亚·马尔克斯',
        'isbn': '9787532736571',
        'total_copies': 3,
        'available_copies': 3
    },
    {
        'title': '霍乱时期的爱情',
        'author': '加西亚·马尔克斯',
        'isbn': '9787532736572',
        'total_copies': 4,
        'available_copies': 4
    },
    {
        'title': '追忆似水年华',
        'author': '马塞尔·普鲁斯特',
        'isbn': '9787532736573',
        'total_copies': 5,
        'available_copies': 5
    },
    {
        'title': '悲惨世界',
        'author': '维克多·雨果',
        'isbn': '9787532736574',
        'total_copies': 3,
        'available_copies': 3
    },
    {
        'title': '巴黎圣母院',
        'author': '维克多·雨果',
        'isbn': '9787532736575',
        'total_copies': 4,
        'available_copies': 4
    },
    {
        'title': '复活',
        'author': '列夫·托尔斯泰',
        'isbn': '9787532736576',
        'total_copies': 3,
        'available_copies': 3
    },
    {
        'title': '安娜·卡列尼娜',
        'author': '列夫·托尔斯泰',
        'isbn': '9787532736577',
        'total_copies': 4,
        'available_copies': 4
    },
    {
        'title': '茶花女',
        'author': '小仲马',
        'isbn': '9787532736578',
        'total_copies': 3,
        'available_copies': 3
    }
]

# 初始用户数据
INITIAL_USERS = [
    {
        'username': 'admin',
        'password': 'admin123',
        'role': 'admin'
    },
    {
        'username': 'student',
        'password': 'student123',
        'role': 'student'
    }
]

def init_db():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        # 删除现有表（如果存在）
        cur.execute('DROP TABLE IF EXISTS borrowing_record CASCADE')
        cur.execute('DROP TABLE IF EXISTS book CASCADE')
        cur.execute('DROP TABLE IF EXISTS "user" CASCADE')
        print("已删除现有表")

        # 创建用户表
        cur.execute('''
            CREATE TABLE "user" (
                id SERIAL PRIMARY KEY,
                username VARCHAR(80) UNIQUE NOT NULL,
                password_hash VARCHAR(120) NOT NULL,
                role VARCHAR(20) NOT NULL DEFAULT 'student'
            )
        ''')
        print("已创建用户表")
        
        # 创建图书表
        cur.execute('''
            CREATE TABLE book (
                id SERIAL PRIMARY KEY,
                title VARCHAR(100) NOT NULL,
                author VARCHAR(100) NOT NULL,
                isbn VARCHAR(13) UNIQUE NOT NULL,
                total_copies INTEGER NOT NULL DEFAULT 1,
                available_copies INTEGER NOT NULL DEFAULT 1
            )
        ''')
        print("已创建图书表")

        # 创建借阅记录表
        cur.execute('''
            CREATE TABLE borrowing_record (
                id SERIAL PRIMARY KEY,
                book_id INTEGER REFERENCES book(id),
                user_id INTEGER REFERENCES "user"(id),
                borrow_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                return_date TIMESTAMP,
                status VARCHAR(20) DEFAULT 'borrowed'
            )
        ''')
        print("已创建借阅记录表")

        # 插入初始用户数据
        for user in INITIAL_USERS:
            password_hash = generate_password_hash(user['password'])
            cur.execute(
                'INSERT INTO "user" (username, password_hash, role) VALUES (%s, %s, %s)',
                (user['username'], password_hash, user['role'])
            )
        print("已创建初始用户账户")

        # 插入初始图书数据
        for book in INITIAL_BOOKS:
            cur.execute(
                'INSERT INTO book (title, author, isbn, total_copies, available_copies) VALUES (%s, %s, %s, %s, %s)',
                (book['title'], book['author'], book['isbn'], book['total_copies'], book['available_copies'])
            )
        print("已添加初始图书数据")
        
        conn.commit()
        print("数据库初始化完成")
        print("\n初始账户信息：")
        print("管理员账户：")
        print("  用户名：admin")
        print("  密码：admin123")
        print("\n学生账户：")
        print("  用户名：student")
        print("  密码：student123")
        
    except Exception as e:
        print(f"初始化数据库时出错: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    init_db() 