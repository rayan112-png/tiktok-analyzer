from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import cloudscraper
from bs4 import BeautifulSoup
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
        scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
        )
        url = f"https://www.tiktok.com/@{username}"
        response = scraper.get(url)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            script_tag = soup.find('script', id='__UNIVERSAL_DATA_FOR_REEHYDRATION__')
            
            if script_tag:
                data_json = json.loads(script_tag.string)
                try:
                    stats = data_json['__DEFAULT_SCOPE__']['webapp.user-detail']['userInfo']['stats']
                except:
                    stats = data_json['__DEFAULT_SCOPE__']['webapp.user-detail']['stats']

                f_count = stats.get('followerCount', 0)
                h_count = stats.get('heartCount', 0)
                
                engagement = round((h_count / f_count) * 5, 2) if f_count > 0 else 0
                
                return {
                    "followers": f_count,
                    "engagement": f"{engagement}%",
                    "views": h_count * 2,
                    "raw_engagement": engagement
                }
        return None
    except Exception as e:
        return None

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    username = data.get('username', '').replace('@', '').strip()
    result = get_tiktok_data(username)
    if result:
        return jsonify(result)
    return jsonify({"error": "Not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)
