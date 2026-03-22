from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import cloudscraper
import re
import json
import os

app = Flask(__name__, static_folder='.')
CORS(app)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

def get_tiktok_data(username):
    try:
        # إنشاء متصفح يحاكي الواقع تماماً
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        
        url = f"https://www.tiktok.com/@{username}"
        # إضافة Headers لمحاكاة متصفح حقيقي
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        }
        
        response = scraper.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            html_text = response.text
            
            # محاولة 1: استخراج الأرقام عبر البحث النصي المباشر (أسرع وأضمن)
            f_count = 0
            h_count = 0
            
            follower_match = re.search(r'"followerCount":(\d+)', html_text)
            heart_match = re.search(r'"heartCount":(\d+)', html_text)
            
            if follower_match:
                f_count = int(follower_match.group(1))
            if heart_match:
                h_count = int(heart_match.group(1))
                
            # محاولة 2: إذا فشلت المحاولة الأولى نستخدم الطريقة التقليدية
            if f_count == 0:
                data_match = re.search(r'id="__UNIVERSAL_DATA_FOR_REEHYDRATION__">([^<]+)', html_text)
                if data_match:
                    data = json.loads(data_match.group(1))
                    stats = data['__DEFAULT_SCOPE__']['webapp.user-detail']['userInfo']['stats']
                    f_count = stats.get('followerCount', 0)
                    h_count = stats.get('heartCount', 0)

            # حساب النتائج
            engagement = round((h_count / f_count) * 5, 2) if f_count > 0 else 0
            
            return {
                "followers": f_count,
                "engagement": f"{engagement}%",
                "views": h_count * 3, # معامل تقديري للمشاهدات
                "raw_engagement": engagement
            }
        else:
            print(f"Failed with status: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Error occurred: {e}")
        return None

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    username = data.get('username', '').replace('@', '').strip()
    
    if not username:
        return jsonify({"error": "Empty username"}), 400
        
    result = get_tiktok_data(username)
    if result:
        return jsonify(result)
    
    return jsonify({"error": "تعذر جلب البيانات. قد يكون الحساب خاصاً أو محظوراً"}), 404

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
