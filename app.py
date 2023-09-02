import sqlite3, os, re
from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)
# 初始化圖片
app.config['UPLOAD_FOLDER'] = 'static/img/'
upload_folder = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
os.makedirs(upload_folder, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
# 相對應 PARA_COL_NAMES 、 paraId 
PARA_COL_NAMES = {
    'Steps': 'para-1',
    'Size': 'para-2',
    'Seed': 'para-3',
    'Model': 'para-4',
    'Version': 'para-5',
    'Sampler': 'para-6',
    'CFG_scale': 'para-7',
    'Clip_skip': 'para-8',
    'Model_hash': 'para-9',
    'Hires_steps': 'para-10',
    'Hires_upscale': 'para-11',
    'Hires_upscaler': 'para-12',
    'Denoising_strength': 'para-13'
}

# 建立SQLite資料庫連接
def connect_db():
    return sqlite3.connect('AI_prompt.db')

# 預先加入 default Picture
def init_db():
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pictures (
                picture_name TEXT NOT NULL UNIQUE PRIMARY KEY,
                picture_path TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS words (
                picture_name TEXT NOT NULL,
                type TEXT NOT NULL,
                word TEXT NOT NULL,
                FOREIGN KEY (picture_name) REFERENCES pictures (picture_name)
            )
        ''')
        
        create_table_query = '''
            CREATE TABLE IF NOT EXISTS para (
                picture_name TEXT NOT NULL,
        '''
        # 使用PARA_COL_NAMES的key建立
        for key in PARA_COL_NAMES.keys():
            create_table_query += f'{key} TEXT, '
        # 增加外來鍵
        create_table_query += '''
            FOREIGN KEY (picture_name) REFERENCES pictures (picture_name)
        )
        '''

        # 执行创建表格的查询
        cursor.execute(create_table_query)
        
        # 檢查是否已經存在圖片
        cursor.execute('SELECT COUNT(*) FROM pictures')
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.execute('INSERT INTO pictures (picture_name) VALUES (?)', ('default',)) # 預設一張圖片 以防出錯

        conn.commit()
        
def get_picture_names():
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT picture_name FROM pictures')
        picture_names = [row[0] for row in cursor.fetchall()]
        conn.commit()
    return picture_names

# 初始化資料庫
@app.before_request
def setup():
    init_db()
    
# 主頁
@app.route('/')
def index():
    picture_names = get_picture_names()
    return render_template('index.html', picture_names=picture_names, selected_picture='')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 上傳圖片
@app.route('/upload', methods=['POST'])
def upload():
    if request.method == 'POST':
        selected_picture = request.form.get('selected_picture')
        file = request.files['picture']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            # 初始化 unique_filename
            unique_filename = None

            # 生成唯一的文件名
            suffix = 1
            while os.path.exists(filepath):
                base_name, ext = os.path.splitext(filename)
                unique_filename = f"{base_name}_{suffix}{ext}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                suffix += 1

            file.save(filepath)

            # 检查是否成功生成唯一的文件名
            if unique_filename is not None:
                with connect_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE pictures SET picture_path = ? WHERE picture_name = ?', (unique_filename, selected_picture))
                    conn.commit()

            picture_names = get_picture_names()
            return render_template('index.html', picture_names=picture_names, selected_picture=selected_picture)
    return redirect(url_for('index'))

# 獲取圖片資料
@app.route('/get_picture_data', methods=['POST'])
def get_picture_data():
    picture_name = request.form['picture_name']
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT word FROM words WHERE picture_name = ? AND type = ?', (picture_name, 'prompt')) # 獲取 prompt
        prompts = [row[0] for row in cursor.fetchall()]

        cursor.execute('SELECT word FROM words WHERE picture_name = ? AND type = ?', (picture_name, 'negative_prompt')) # 獲取 negative_prompt
        negative_prompts = [row[0] for row in cursor.fetchall()]
        
        cursor.execute('SELECT * FROM para WHERE picture_name = ?', (picture_name,)) # 獲取 para
        para_rows = cursor.fetchall()
        
        cursor.execute('SELECT picture_path FROM pictures WHERE picture_name = ?', (picture_name,)) # 獲取 圖片位置
        picture_path = cursor.fetchall()
        
        if len(para_rows) != 0:
            para_words = para_rows[0][1:]
        else:
            para_words = []

    return jsonify({
        'prompts': prompts,
        'negative_prompts': negative_prompts,
        'para_words': para_words,
        'picture_path': picture_path
    })

# 更新參數至資料庫
@app.route('/update_para', methods=['POST'])
def update_para():
    picture_name = request.json['picture_name']
    updated_values = request.json['updated_values']
    
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT picture_name FROM para WHERE picture_name = ?', (picture_name,))
        picture_name_is_exists = cursor.fetchone()
        
        if picture_name_is_exists is not None:
            # 更新para query
            update_query = 'UPDATE para SET '
            update_values = [] # query使用參數
            for col_name, para_key in PARA_COL_NAMES.items():
                value = updated_values.get(para_key, '') # 前端para id
                update_query += f'{col_name}=?, '
                update_values.append(value)

            update_query = update_query.rstrip(', ')
            update_query += ' WHERE picture_name=?'
            update_values.append(picture_name)

            cursor.execute(update_query, update_values)
        else:
            # 插入para query
            insert_query = 'INSERT INTO para (picture_name, ' + ', '.join(PARA_COL_NAMES.keys()) + ') VALUES (?, ' + ', '.join(['?'] * len(PARA_COL_NAMES)) + ')'
            insert_values = [picture_name]

            for para_key in PARA_COL_NAMES.values():
                insert_values.append(updated_values.get(para_key, ''))

            cursor.execute(insert_query, insert_values)

        conn.commit()

    return jsonify({})

# 新增圖片
@app.route('/add_picture', methods=['POST'])
def add_picture():
    picture_name = request.form['picture_name'].strip()
    with connect_db() as conn:
        cursor = conn.cursor()

        # 檢查圖片是否已存在於資料庫中
        cursor.execute('SELECT * FROM pictures WHERE picture_name = ?', (picture_name,))
        existing_picture = cursor.fetchone()

        if existing_picture:
            # 生成唯一的後綴
            suffix = 1
            while True:
                unique_picture_name = f"{picture_name}_{suffix}"
                cursor.execute('SELECT * FROM pictures WHERE picture_name = ?', (unique_picture_name,))
                existing_unique_picture = cursor.fetchone()
                if not existing_unique_picture:
                    break
                suffix += 1
            picture_name = unique_picture_name
        cursor.execute('INSERT INTO pictures (picture_name) VALUES (?)', (picture_name,))
        conn.commit()
    picture_names = get_picture_names()
    return render_template('index.html', picture_names=picture_names, selected_picture=picture_name)
# 刪除圖片
@app.route('/delete_picture', methods=['POST'])
def delete_picture():
    picture_name = request.form['picture_name']
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT picture_path FROM pictures WHERE picture_name = ?', (picture_name,))
        filepath = cursor.fetchone()[0]
        # 刪除資料庫相關資料
        cursor.execute('DELETE FROM words WHERE picture_name = ?', (picture_name,))
        cursor.execute('DELETE FROM para WHERE picture_name = ?', (picture_name,))
        cursor.execute('DELETE FROM pictures WHERE picture_name = ?', (picture_name,))
        conn.commit()

    if filepath is not None:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filepath)) # 刪除圖片
        except OSError:
            # 刪除失敗
            pass
    picture_names = get_picture_names()
    return render_template('index.html', picture_names=picture_names, selected_picture='')

# Prompt字串整理
def word_split(text):
    words = []
    current_part = ''
    stack = []

    for char in text:
        if char == '[' or char == '(':
            stack.append(char)
            current_part += char
        elif char == ']' or char == ')':
            if stack:
                stack.pop()
                current_part += char
                if not stack:
                    words.append(current_part)
                    current_part = ''
        elif char == ',':
            if not stack:
                words.append(current_part.strip())
                current_part = ''
            else:
                current_part += char
        else:
            current_part += char

    if current_part.strip():
        words.append(current_part.strip())
    return words
@app.route('/add_words', methods=['POST'])
def add_words():
    picture_name = request.form['picture_name']
    word_type = request.form['word_type']
    words = word_split(request.form['words'])

    with connect_db() as conn:
        cursor = conn.cursor()
        # 檢查是否有重複的單詞，若有則忽略
        existing_words = set()
        cursor.execute('SELECT word FROM words WHERE picture_name = ? AND type = ?', (picture_name, word_type))
        for row in cursor.fetchall():
            existing_words.add(row[0])

        # 加入新的單詞
        new_words = []
        for word in words:
            word = word.strip()
            if word and word not in existing_words:
                new_words.append((picture_name, word_type, word))
                existing_words.add(word)

        if new_words:
            cursor.executemany('INSERT INTO words (picture_name, type, word) VALUES (?, ?, ?)', new_words)
            conn.commit()
    return 'success'

# 移除單詞
@app.route('/remove_word', methods=['POST'])
def remove_word():
    picture_name = request.form['picture_name']
    word_type = request.form['word_type']
    word = request.form['word']

    with connect_db() as conn:
        cursor = conn.cursor()
        # 從db中移除
        cursor.execute('DELETE FROM words WHERE picture_name = ? AND type = ? AND word = ?', (picture_name, word_type, word))
        conn.commit()

    return 'success'

# 一鍵匯入
@app.route('/import_words', methods=['POST'])
def import_words():
    words = request.form['words']
    prompt_words = ""
    negative_words = []
    para_words = {}
    para_values = []
    non_para_words = []
    para_part = ""
    if words:  
        # 分成四部分 Prompt、Negative Prompt、參數、非參數值
        if "Negative prompt:" in words:
            prompt_part, negative_part = words.split("Negative prompt:", 1)
            prompt_words = word_split(prompt_part)
            
            if "Steps:" in negative_part:
                negative_part, para_part = negative_part.split("Steps:", 1)
                negative_words = word_split(negative_part)
                para_part = "Steps:" + para_part
                para_part = para_part.split(',')
                
                special_characters = '()<>{}[]' # 可能出現符號
                for item in para_part:
                    if ':' in item and not any(char in item for char in special_characters.replace(':', '')):
                        key, value = item.split(':', 1) # 參數輸入類型 key:value 
                        para_words[key.strip()] = value.strip()
                        
                    else:
                        non_para_words.append(item)
            else:
                negative_words = word_split(words)
        else:
            if "Steps:" in words:
                prompt_words, para_part = words.split("Steps:", 1)
                prompt_words = word_split(prompt_words)
                para_part = "Steps:" + para_part
                para_part = para_part.split(',')
            else:
                prompt_words = word_split(words)
                
        special_characters = '()<>{}[]' # 可能出現符號
        for item in para_part:
            if ':' in item and not any(char in item for char in special_characters.replace(':', '')):
                key, value = item.split(':', 1) # 參數輸入類型 key:value 
                para_words[key.strip()] = value.strip()
                
            else:
                non_para_words.append(item)
            # 前端不需要key
        for col_name in PARA_COL_NAMES:
            col_name = col_name.replace('_', ' ')
            if col_name in para_words:
                para_values.append(para_words[col_name])
            else:
                para_values.append(None) 
                
    return jsonify({
        'prompt_words': prompt_words,
        'negative_words': negative_words,
        'para_words': para_values,
        'non_para_words': non_para_words
    })

if __name__ == '__main__':
    app.run()