import wikipedia
import csv

def scrape_wikipedia_articles():
    # Set up categories
    categories = {
        'Sport': ['Basketball', 'Football', 'Baseball', 'Soccer'],
        'Technology': ['Artificial intelligence', 'Robotics', 'Blockchain', 'Virtual reality'],
        'Climate': ['Climate change', 'Global warming', 'Renewable energy', 'Carbon footprint']
    }

    # Get articles from Wikipedia
    articles = []
    for category, topics in categories.items():
        for topic in topics:
            try:
                page = wikipedia.page(topic)
                content = page.content
                sentences = content.split('. ')
                for i in range(100):
                    sentence = sentences[i].strip()
                    articles.append([sentence])
            except:
                pass

    # Write to CSV file
    with open('articles.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Sentence'])
        for article in articles:
            writer.writerow(article)
