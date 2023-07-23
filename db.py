import sqlite3

def check_database_contents():
    # 連接到tags.db資料庫
    connection = sqlite3.connect('tags.db')
    cursor = connection.cursor()

    try:
        cursor.execute("PRAGMA table_info('modules')")
        modules_headers = cursor.fetchall()
        
        cursor.execute('SELECT * FROM modules')
        modules_rows = cursor.fetchall()        
        
        cursor.execute("PRAGMA table_info('words')")
        words_headers = cursor.fetchall()        
        
        cursor.execute('SELECT * FROM words')
        words_rows = cursor.fetchall()
        
        # 檢查modules資料表內容
        print("Modules Table Contents:\n================================================================")
        for header in modules_headers:
            print(header[1], end=' ')  # The column name is at index 1
        print("\n================================================================")
        for row in modules_rows:
            print(row)
            

        # 檢查words資料表內容
        print("\nWords Table Contents:\n================================================================")
        for header in words_headers:
            print(header[1], end=' ')  # The column name is at index 1
        print("\n================================================================")
        for row in words_rows:
            print(row)

    except sqlite3.Error as e:
        print("Error:", e)

    finally:
        # 關閉資料庫連接
        connection.close()

if __name__ == "__main__":
    check_database_contents()
