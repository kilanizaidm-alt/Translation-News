import json
import os
from datetime import datetime
import feedparser
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")
print(f"API Key exists: {bool(api_key)}")

client = genai.Client(api_key=api_key)

FEEDS = {
    "الأخبار العالمية (World)": "https://feeds.bbci.co.uk/news/world/rss.xml"
}

def run():
    news_list = []
    feed = feedparser.parse(FEEDS["الأخبار العالمية (World)"])
    
    for entry in feed.entries[:3]:
        title = entry.title
        summary = getattr(entry, 'summary', title)
        
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=f"Translate this news title and snippet to professional Arabic and give a glossary of 3 terms: Title: {title} - Snippet: {summary}. Return JSON with keys: arabic_title, arabic_text, glossary, translation_notes"
            )
            res_text = response.text.replace("```json", "").replace("```", "").strip()
            data = json.loads(res_text)
            
            news_list.append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "genre": "الأخبار العالمية",
                "source": "BBC",
                "original_title": title,
                "original_text": summary,
                "arabic_title": data.get("arabic_title", title),
                "arabic_text": data.get("arabic_text", summary),
                "glossary": data.get("glossary", "• مصطلح: شرح"),
                "translation_notes": data.get("translation_notes", "ملاحظة أسلوبية")
            })
        except Exception as e:
            print(f"Error: {e}")

    if news_list:
        with open("news.json", "w", encoding="utf-8") as f:
            json.dump(news_list, f, ensure_ascii=False, indent=4)
        print("Saved successfully!")

if __name__ == "__main__":
    run()
