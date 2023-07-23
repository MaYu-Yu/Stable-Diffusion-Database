import sqlite3
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# 建立SQLite資料庫連接
def connect_db():
    return sqlite3.connect('AI_prompt.db')

# 創建資料表（如果資料表不存在）
def create_table():
    with connect_db() as connection:
        cursor = connection.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS modules (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY,
                module_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                word TEXT NOT NULL,
                FOREIGN KEY (module_id) REFERENCES modules (id)
            )
        ''')
        connection.commit()

# 預先加入 default Module
def init_db():
    with connect_db() as connection:
        cursor = connection.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS modules (id INTEGER PRIMARY KEY, name TEXT)')
        
        # 檢查是否已經存在模組
        cursor.execute('SELECT COUNT(*) FROM modules')
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.execute('INSERT INTO modules (name) VALUES (?)', ('default Module',))

        connection.commit()

# 初始化資料庫
@app.before_request
def setup():
    create_table()
    init_db()

# 主頁
@app.route('/')
def index():
    with connect_db() as connection:
        cursor = connection.cursor()
        cursor.execute('SELECT name FROM modules')
        modules = [row[0] for row in cursor.fetchall()]
    return render_template('index.html', modules=modules)

# 獲取模組資料
@app.route('/get_module_data', methods=['POST'])
def get_module_data():
    module_name = request.form['module_name']
    with connect_db() as connection:
        cursor = connection.cursor()
        cursor.execute('SELECT id FROM modules WHERE name = ?', (module_name,))
        module_id = cursor.fetchone()[0]

        cursor.execute('SELECT word FROM words WHERE module_id = ? AND type = ?', (module_id, 'prompt'))
        prompts = [row[0] for row in cursor.fetchall()]

        cursor.execute('SELECT word FROM words WHERE module_id = ? AND type = ?', (module_id, 'negative_prompt'))
        negative_prompts = [row[0] for row in cursor.fetchall()]

    return jsonify({
        'prompts': prompts,
        'negative_prompts': negative_prompts
    })

# 新增模組
@app.route('/add_module', methods=['POST'])
def add_module():
    module_name = request.form['module_name'].strip()
    with connect_db() as connection:
        cursor = connection.cursor()

        # 檢查模組是否已存在於資料庫中
        cursor.execute('SELECT name FROM modules WHERE name = ?', (module_name,))
        existing_module = cursor.fetchone()

        if existing_module:
            return 'Module already exists'

        cursor.execute('INSERT INTO modules (name) VALUES (?)', (module_name,))
        connection.commit()

    return 'success'

# 刪除模組
@app.route('/delete_module', methods=['POST'])
def delete_module():
    module_name = request.form['module_name']
    with connect_db() as connection:
        cursor = connection.cursor()
        cursor.execute('SELECT id FROM modules WHERE name = ?', (module_name,))
        module_id = cursor.fetchone()[0]

        # 先刪除模組下的prompt
        cursor.execute('DELETE FROM words WHERE module_id = ?', (module_id,))

        # 刪除模組
        cursor.execute('DELETE FROM modules WHERE name = ?', (module_name,))
        connection.commit()

    return 'success'

# 新增單詞
@app.route('/add_words', methods=['POST'])
def add_words():
    module_name = request.form['module_name']
    word_type = request.form['word_type']
    words = request.form['words'].split(',')

    with connect_db() as connection:
        cursor = connection.cursor()
        cursor.execute('SELECT id FROM modules WHERE name = ?', (module_name,))
        module_id = cursor.fetchone()[0]

        # 檢查是否有重複的單詞，若有則忽略
        existing_words = set()
        cursor.execute('SELECT word FROM words WHERE module_id = ? AND type = ?', (module_id, word_type))
        for row in cursor.fetchall():
            existing_words.add(row[0])

        # 加入新的單詞
        new_words = []
        for word in words:
            word = word.strip()  # 清除最前方和最後方的空格
            if word and word not in existing_words:
                new_words.append((module_id, word_type, word))
                existing_words.add(word)

        if new_words:
            cursor.executemany('INSERT INTO words (module_id, type, word) VALUES (?, ?, ?)', new_words)
            connection.commit()

    return 'success'

# 移除單詞
@app.route('/remove_word', methods=['POST'])
def remove_word():
    module_name = request.form['module_name']
    word_type = request.form['word_type']
    word = request.form['word']

    with connect_db() as connection:
        cursor = connection.cursor()
        cursor.execute('SELECT id FROM modules WHERE name = ?', (module_name,))
        module_id = cursor.fetchone()[0]

        # 從db中移除
        cursor.execute('DELETE FROM words WHERE module_id = ? AND type = ? AND word = ?', (module_id, word_type, word))
        connection.commit()

    return 'success'

if __name__ == '__main__':
    app.run()
