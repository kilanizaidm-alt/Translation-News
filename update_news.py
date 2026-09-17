import json
import os
from datetime import datetime
import feedparser
from google import genai

# Initialize Gemini client using GitHub Secret
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Diverse RSS feeds covering different genres
FEEDS = {
    "Politics": "http://feeds.bbci.co.uk/news/politics/rss.xml",
    "World": "https://www.reutersagency.com/feed/?best-topics=political-general&post_type=best",
    "Technology": "https://feeds.bbci.co.uk/news/technology/rss.xml",
    "Business": "https://feeds.bbci.co.uk/news/business/rss.xml"
}

def fetch_and_translate():
    news_list = []
    
    # Load existing news if file exists so history is preserved
    if os.path.exists("news.json"):
        with open("news.json", "r", encoding="utf-8") as f:
            try:
                news_list = json.load(f)
            except json.JSONDecodeError:
                news_list = []

    # Fetch 2-3 articles per genre to reach at least 10 total
    for genre, url in FEEDS.items():
        feed = feedparser.parse(url)
        count = 0
        for entry in feed.entries[:3]: 
            title = entry.title
            summary = getattr(entry, 'summary', title)
            source = url.split("//")[1].split("/")[0]
            
            # Prompt Gemini for professional translation and translation student notes
            prompt = f"""
            You are an expert translation instructor. Translate the following English news snippet into professional, eloquent Arabic suitable for translation students.
            Also provide 2 key lexical or stylistic notes in Arabic (explaining how specific terms or structures were handled).
            
            Title: {title}
            Snippet: {summary}
            
            Format your output strictly as valid JSON with these keys:
            "arabic_title": "...",
            "arabic_text": "...",
            "translation_notes": "..."
            """
            
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                )
                # Clean response text and parse JSON
                res_text = response.text.replace("```json", "").replace("```", "").strip()
                translation_data = json.loads(res_text)
                
                article_record = {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "genre": genre,
                    "source": source,
                    "original_title": title,
                    "original_text": summary,
                    "arabic_title": translation_data.get("arabic_title"),
                    "arabic_text": translation_data.get("arabic_text"),
                    "translation_notes": translation_data.get("translation_notes")
                }
                
                # Prepend to keep latest on top
                news_list.insert(0, article_record)
                count += 1
            except Exception as e:
                print(f"Error processing article: {e}")

    # Keep a permanent record capped at the last 200 articles to avoid bloating
    news_list = news_list[:200]

    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(news_list, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    fetch_and_translate()
