# Stable Diffusion WebUI 教學

* ## 架設環境
    ### 測試環境 
    - Windows 11 22H2
    - Python 3.9.13
    ### 環境架設
    - git clone https://github.com/MaYu-Yu/AI-Stable-Diffusion-DB.git
    - pip freeze > requirements.txt
    ### 開啟WebUI
    - python app.py
    - 進入網頁: http://127.0.0.1:5000
    ### civitai 網站來找自己喜歡的圖片類型之模組
    ### 按下download下載模組
    ### 從civitai的圖片按下info中的Copy Generation Data複製該張圖片參數
    - ![2](https://github.com/MaYu-Yu/AI-Stable-Diffusion-DB/assets/59922656/d0783a1f-8c83-48ad-9df0-f80c42f477e1)
    ### 選擇一鍵匯入可以從civitai直接套用所有設定
    - ![1](https://github.com/MaYu-Yu/AI-Stable-Diffusion-DB/assets/59922656/99904731-3168-4f72-991c-446d2c7d0702)
    ### 也可以各部分個別輸入(請遵守stable diffusion格式)
    - ![2](https://github.com/MaYu-Yu/AI-Stable-Diffusion-DB/assets/59922656/1641d8a2-f686-46aa-bff8-6caf09dd83d7)
    ### 選取上方小方塊就會在下方Output Box出現，直接複製就能用!一鍵複製可以如同civitai複製整張參數，到Stable-Diffusion WebUI直接貼在prompt區就好
    - ![3](https://github.com/MaYu-Yu/AI-Stable-Diffusion-DB/assets/59922656/7e0299cb-2d56-4325-bc50-f4e9cc18f930)
* ## 參考網站
- Stable Diffusion - https://github.com/CompVis/stable-diffusion, https://github.com/CompVis/taming-transformers, https://github.com/AUTOMATIC1111/stable-diffusion-webui
- 圖片參考 - https://civitai.com/models/36520?modelVersionId=76907
- 美觀 - https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css
