import json
import os
from datetime import datetime
import feedparser
from google import genai

# Initialize Gemini client using GitHub Secret
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Diverse RSS feeds covering different genres
FEEDS = {
    "السياسة الدولية (Politics)": "http://feeds.bbci.co.uk/news/politics/rss.xml",
    "الأخبار العالمية (World)": "https://www.reutersagency.com/feed/?best-topics=political-general&post_type=best",
    "التكنولوجيا (Technology)": "https://feeds.bbci.co.uk/news/technology/rss.xml",
    "الأعمال والاقتصاد (Business)": "https://feeds.bbci.co.uk/news/business/rss.xml"
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

    # Fetch articles per genre
    for genre, url in FEEDS.items():
        feed = feedparser.parse(url)
        count = 0
        for entry in feed.entries[:3]: 
            title = entry.title
            summary = getattr(entry, 'summary', title)
            source = url.split("//")[1].split("/")[0]
            
            # Prompt Gemini for professional translation, terminology glossary, and stylistic notes
            prompt = f"""
            You are an expert translation professor. Analyze and translate the following English news text into professional, eloquent journalistic Arabic suited for undergraduate translation seminar students.
            
            Title: {title}
            Snippet: {summary}
            
            Provide your response strictly in valid JSON format with the following keys:
            - "arabic_title": The professional Arabic translation of the title.
            - "arabic_text": The professional Arabic translation of the snippet.
            - "glossary": A detailed list of 3 to 4 key professional terms, idioms, or political/economic expressions extracted from the text, formatted clearly with their English term and Arabic equivalent/explanation.
            - "translation_notes": Brief pedagogical notes explaining the stylistic choices, register, or syntactic adaptation used in the translation.
            """
            
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                )
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
                    "glossary": translation_data.get("glossary"),
                    "translation_notes": translation_data.get("translation_notes")
                }
                
                news_list.insert(0, article_record)
                count += 1
            except Exception as e:
                print(f"Error processing article: {e}")

    news_list = news_list[:200]

    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(news_list, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    fetch_and_translate()
