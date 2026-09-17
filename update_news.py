import json
import os
from datetime import datetime
import feedparser
from google import genai
from google.genai import types

# Initialize Gemini client using GitHub Secret
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Diverse RSS feeds covering different genres
FEEDS = {
    "السياسة الدولية (Politics)": "http://feeds.bbci.co.uk/news/politics/rss.xml",
    "الأخبار العالمية (World)": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "التكنولوجيا (Technology)": "https://feeds.bbci.co.uk/news/technology/rss.xml",
    "الأعمال والاقتصاد (Business)": "https://feeds.bbci.co.uk/news/business/rss.xml"
}

def fetch_and_translate():
    news_list = []
    
    # Load existing news if file exists
    if os.path.exists("news.json"):
        with open("news.json", "r", encoding="utf-8") as f:
            try:
                existing_data = json.load(f)
                if isinstance(existing_data, list):
                    news_list = existing_data
            except Exception:
                news_list = []

    new_articles = []

    for genre, url in FEEDS.items():
        feed = feedparser.parse(url)
        for entry in feed.entries[:2]: # 2 articles per genre (total 8 daily)
            title = entry.title
            summary = getattr(entry, 'summary', title)
            source = "BBC News"
            
            prompt = f"""
You are an expert translation professor. Translate the following English news snippet into professional, eloquent Arabic for translation students.

Title: {title}
Snippet: {summary}

Respond strictly with JSON format using these exact keys:
"arabic_title": "Arabic translated title",
"arabic_text": "Arabic translated text",
"glossary": "List 3-4 terms with Arabic translations as bullet points (e.g. • Term: المعنى)",
"translation_notes": "Brief pedagogical translation notes in Arabic"
"""

            try:
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    )
                )
                
                translation_data = json.loads(response.text)
                
                glossary_val = translation_data.get("glossary", "")
                if isinstance(glossary_val, list):
                    glossary_val = "\n".join([f"• {item}" for item in glossary_val])
                elif isinstance(glossary_val, dict):
                    glossary_val = "\n".join([f"• {k}: {v}" for k, v in glossary_val.items()])

                article_record = {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "genre": genre,
                    "source": source,
                    "original_title": title,
                    "original_text": summary,
                    "arabic_title": translation_data.get("arabic_title", ""),
                    "arabic_text": translation_data.get("arabic_text", ""),
                    "glossary": str(glossary_val),
                    "translation_notes": translation_data.get("translation_notes", "")
                }
                
                new_articles.append(article_record)
                print(f"Successfully processed: {title}")
            except Exception as e:
                print(f"Error processing article '{title}': {e}")

    if new_articles:
        news_list = new_articles + news_list
        news_list = news_list[:200]

        with open("news.json", "w", encoding="utf-8") as f:
            json.dump(news_list, f, ensure_ascii=False, indent=4)
        print("Saved articles successfully.")

if __name__ == "__main__":
    fetch_and_translate()
