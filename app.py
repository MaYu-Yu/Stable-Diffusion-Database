import sqlite3, os
from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)
# 初始化圖片
app.config['UPLOAD_FOLDER'] = 'static/img/'
upload_folder = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
os.makedirs(upload_folder, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# 建立SQLite資料庫連接
def connect_db():
    return sqlite3.connect('AI_prompt.db')

# 創建資料表（如果資料表不存在）
def create_table():
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
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS para (
                picture_name TEXT NOT NULL,
                Steps TEXT,
                Size TEXT,
                Seed TEXT,
                Model TEXT,
                Version TEXT,
                Sampler TEXT,
                CFG_scale TEXT,
                Clip_skip TEXT,
                Model_hash TEXT,
                Hires_steps TEXT,
                Hires_upscale TEXT,
                Hires_upscaler TEXT,
                Denoising_strength TEXT,
                FOREIGN KEY (picture_name) REFERENCES pictures (picture_name)
            )
        ''')

        conn.commit()

# 預先加入 default Picture
def init_db():
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS pictures (picture_name TEXT NOT NULL UNIQUE PRIMARY KEY, picture_path TEXT)')
        
        # 檢查是否已經存在圖片
        cursor.execute('SELECT COUNT(*) FROM pictures')
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.execute('INSERT INTO pictures (picture_name) VALUES (?)', ('default Picture',))

        conn.commit()

# 初始化資料庫
@app.before_request
def setup():
    create_table()
    init_db()

# 主頁
@app.route('/')
def index():
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT picture_name FROM pictures')
        picture_names = [row[0] for row in cursor.fetchall()]
        
        cursor.execute('SELECT picture_path FROM pictures')
    return render_template('index.html', picture_names=picture_names)

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
            # 去掉static目录，只保存到UPLOAD_FOLDER
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            with connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE pictures SET picture_path = ? WHERE picture_name = ?', (filename, selected_picture))
                conn.commit()

            return redirect(url_for('index'))  # 重定向回主页
    return redirect(url_for('index'))

# 獲取圖片資料
@app.route('/get_picture_data', methods=['POST'])
def get_picture_data():
    picture_name = request.form['picture_name']
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT word FROM words WHERE picture_name = ? AND type = ?', (picture_name, 'prompt'))
        prompts = [row[0] for row in cursor.fetchall()]

        cursor.execute('SELECT word FROM words WHERE picture_name = ? AND type = ?', (picture_name, 'negative_prompt'))
        negative_prompts = [row[0] for row in cursor.fetchall()]
        
        cursor.execute('SELECT * FROM para WHERE picture_name = ?', (picture_name,))
        para_rows = cursor.fetchall()
        
        cursor.execute('SELECT picture_path FROM pictures WHERE picture_name = ?', (picture_name,))
        picture_path = cursor.fetchall()

        if len(para_rows) != 0:
            para_words = para_rows[0]
        else:
            para_words = None

    return jsonify({
        'prompts': prompts,
        'negative_prompts': negative_prompts,
        'para_words': para_words,
        'picture_path': picture_path
    })
    
@app.route('/update_para', methods=['POST'])
def update_para():
    picture_name = request.json['picture_name']
    updated_values = request.json['updated_values']
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT picture_name FROM para WHERE picture_name = ?', (picture_name,))
        picture_name_is_exists = cursor.fetchone()
        if picture_name_is_exists is not None:  
            update_query = '''
                UPDATE para
                SET Steps=?, Size=?, Seed=?, Model=?, Version=?, Sampler=?,
                    CFG_scale=?, Clip_skip=?, Model_hash=?, Hires_steps=?,
                    Hires_upscale=?, Hires_upscaler=?, Denoising_strength=?
                WHERE picture_name=?
            '''
            cursor.execute(update_query, (
                updated_values.get('para-1', ''),
                updated_values.get('para-2', ''),
                updated_values.get('para-3', ''),
                updated_values.get('para-4', ''),
                updated_values.get('para-5', ''),
                updated_values.get('para-6', ''),
                updated_values.get('para-7', ''),
                updated_values.get('para-8', ''),
                updated_values.get('para-9', ''),
                updated_values.get('para-10', ''),
                updated_values.get('para-11', ''),
                updated_values.get('para-12', ''),
                updated_values.get('para-13', ''),
                picture_name
            ))
        else: 
            insert_query = '''
                INSERT INTO para (picture_name, Steps, Size, Seed, Model, Version, Sampler,
                    CFG_scale, Clip_skip, Model_hash, Hires_steps,
                    Hires_upscale, Hires_upscaler, Denoising_strength)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            cursor.execute(insert_query, (
                picture_name,
                updated_values.get('para-1', ''),
                updated_values.get('para-2', ''),
                updated_values.get('para-3', ''),
                updated_values.get('para-4', ''),
                updated_values.get('para-5', ''),
                updated_values.get('para-6', ''),
                updated_values.get('para-7', ''),
                updated_values.get('para-8', ''),
                updated_values.get('para-9', ''),
                updated_values.get('para-10', ''),
                updated_values.get('para-11', ''),
                updated_values.get('para-12', ''),
                updated_values.get('para-13', '')
            ))
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
    return jsonify({
        'picture_name':picture_name
    })
# 刪除圖片
@app.route('/delete_picture', methods=['POST'])
def delete_picture():
    picture_name = request.form['picture_name']
    with connect_db() as conn:
        cursor = conn.cursor()
        # 先刪除圖片下的prompt
        cursor.execute('DELETE FROM words WHERE picture_name = ?', (picture_name,))
        # 先刪除圖片下的para
        cursor.execute('DELETE FROM para WHERE picture_name = ?', (picture_name,))
        # 刪除圖片
        cursor.execute('DELETE FROM pictures WHERE picture_name = ?', (picture_name,))
        conn.commit()

    return 'success'
    
# 新增單詞
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
            word = word.strip()  # 清除最前方和最後方的空格
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
    if words:  
        # 分成三部分 Prompt、Negative Prompt、參數
        prompt_words = ""
        negative_words = []
        para_words = {}
        
        if "Negative prompt:" in words:
            prompt_part, rest = words.split("Negative prompt:", 1)
            prompt_words = prompt_part.strip()
            
            if "Steps:" in rest:
                negative_part, para_temp = rest.split("Steps:", 1)
                negative_words = word_split(negative_part)
                
                para_temp = "Steps:" + para_temp
                para_temp = para_temp.split(',')
                for i, temp in enumerate(para_temp, start=1):
                    _, value = temp.split(":")
                    para_words[str(i)] = value.strip()
        return jsonify({
            'prompt_words': prompt_words,
            'negative_words': negative_words,
            'para_words': para_words
        })
        
    return jsonify({
        'prompt_words': '',
        'negative_words': [],
        'para_words': {}
    })

if __name__ == '__main__':
    app.run()
