from flask import Flask, jsonify, request
from flask_cors import CORS
import cloudscraper
from bs4 import BeautifulSoup
import re
import json

app = Flask(__name__)
# السماح للمتصفح بالوصول للسيرفر (CORS)
CORS(app)

def get_tiktok_data(username):
    try:
        # محاكاة متصفح حقيقي لتجنب الحظر
        scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
        )
        url = f"https://www.tiktok.com/@{username}"
        response = scraper.get(url)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # تيك توك يضع بياناته في وسم Script بـ ID محدد
            script_tag = soup.find('script', id='__UNIVERSAL_DATA_FOR_REEHYDRATION__')
            
            if script_tag:
                data_json = json.loads(script_tag.string)
                # استخراج الإحصائيات من داخل هيكل JSON المعقد لتيك توك
                # ملاحظة: المسار قد يختلف قليلاً حسب تحديثات تيك توك، أضفت محاولتين للوصول
                try:
                    stats = data_json['__DEFAULT_SCOPE__']['webapp.user-detail']['userInfo']['stats']
                except KeyError:
                    # محاولة بديلة في حال تغير الهيكل
                    stats = data_json['__DEFAULT_SCOPE__']['webapp.user-detail']['stats']

                f_count = stats.get('followerCount', 0)
                h_count = stats.get('heartCount', 0)
                v_count = stats.get('videoCount', 0)
                
                # حساب نسبة التفاعل (الإعجابات مقارنة بالمتابعين)
                # نضرب في 5 كمعامل تقديري للحصول على نسبة مئوية منطقية
                engagement = round((h_count / f_count) * 5, 2) if f_count > 0 else 0
                
                return {
                    "followers": f_count,
                    "engagement": f"{engagement}%",
                    "views": h_count * 2, # تقدير للمشاهدات
                    "raw_engagement": engagement
                }
        return None
    except Exception as e:
        print(f"حدث خطأ أثناء جلب البيانات: {e}")
        return None

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    # تنظيف اسم المستخدم من المسافات أو الرموز
    username = data.get('username', '').replace('@', '').strip()
    
    if not username:
        return jsonify({"error": "No username provided"}), 400

    result = get_tiktok_data(username)
    
    if result:
        return jsonify(result)
    else:
        return jsonify({"error": "User not found or data hidden"}), 404

if __name__ == '__main__':
    # تشغيل السيرفر على المنفذ 5000
    app.run(debug=True, port=5000)
    