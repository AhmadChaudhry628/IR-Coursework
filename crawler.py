import requests
from bs4 import BeautifulSoup
import time
import json
import schedule
import re
import math
import csv
# Initialize empty index dictionary
index = {}

# Load existing index from file, if it exists
try:
    with open("index.json", "r") as f:
        index = json.load(f)
except FileNotFoundError:
    pass

def scrape_csm_members():
    csm_members_url = "https://pureportal.coventry.ac.uk/en/organisations/research-centre-for-computational-science-and-mathematical-modell/persons/"
    csm_members_page = requests.get(csm_members_url)
    csm_members_soup = BeautifulSoup(csm_members_page.content, "html.parser")
    csm_member_links = [link['href'] for link in csm_members_soup.select('ul.grid-results li.grid-result-item div.result-container div.rendering_person_short h3.title a.link.person')]

    with open("csm_members.csv", "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Name", "URL"])
        for member_link in csm_member_links:
            member_page = requests.get(member_link)
            member_soup = BeautifulSoup(member_page.content, "html.parser")
            csm_member_name = member_soup.select_one("div.header.person-details h1").text.strip()
            writer.writerow([csm_member_name, member_link])

def scrape_publications(url):
    headers = {
        "User-Agent": "My Web Crawler 1.0"
    }

    publications = []

    page_num = 0

    while True:
        print(f"Scraping page {page_num + 1}...")
        response = requests.get(url, params={"page": page_num}, headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")

        results = soup.find("ul", class_="list-results")

        if not results:
            print("No results found.")
            break

        publication_items = results.find_all("li", class_="list-result-item")

        if not publication_items:
            print("No more publications found.")
            break

        for item in publication_items:
            title = item.find("h3", class_="title").text.strip()
            author_elements = item.find_all("a", rel="Person")
            authors = [a.text.strip() for a in author_elements]
            urls = [a["href"] for a in author_elements]
            date = item.find("span", class_="date").text.strip()
            link = item.find("a", class_="link")["href"]

            publication = {
                "title": title,
                "authors": authors,
                "urls": urls,
                "date": date,
                "link": link
            }

            publications.append(publication)

        page_num += 1
        time.sleep(5)

    return publications

def filter_publications_by_csm(publications, csm_members_file_path):
    csm_members = []
    with open(csm_members_file_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            csm_members.append({
                'name': row[0],
                'url': row[1]
            })

    filtered_publications = []
    for publication in publications:
        authors = publication['urls']
        csm_author_names = []
        csm_author_urls = []
        flag = False
        for author in authors:
            csm_member = next((m for m in csm_members if m['url'] == author), None)
            if csm_member:
                flag = True
                csm_author_names.append(csm_member['name'])
                csm_author_urls.append(csm_member['url'])

        if flag:
            filtered_publications.append({
                'title': publication['title'],
                'authors': csm_author_names,
                'urls': csm_author_urls,
                'date': publication['date'],
                'link': publication['link']
            })

    return filtered_publications

def update_index(title, authors, date, publication_link, author_urls, index):
    # Update index with new publication
    for word in title.split() + authors:
        if word.lower() not in index:
            index[word.lower()] = []
        if publication_link not in [pub["Publication Link"] for pub in index[word.lower()]]:
            index[word.lower()].append({
                "Title": title,
                "Authors": authors,
                "Date": date,
                "Publication Link": publication_link,
                "Author URLs": author_urls
            })

def print_num_publications_by_author(publications):
    num_publications_by_author = {}
    for pub in publications:
        authors = pub["authors"]
        for author in authors:
            if author not in num_publications_by_author:
                num_publications_by_author[author] = 1
            else:
                num_publications_by_author[author] += 1
    sorted_authors = sorted(num_publications_by_author.items(), key=lambda x: x[1], reverse=True)
    for author, num_publications in sorted_authors:
        print(f"{author}: {num_publications}")

def scrape_and_update(csm_members_file_path, index_file_path):
    # Scrape and filter publications
    publications = scrape_publications("https://pureportal.coventry.ac.uk/en/organisations/research-centre-for-computational-science-and-mathematical-modell/publications/")
    filtered_publications = filter_publications_by_csm(publications, csm_members_file_path)
    print_num_publications_by_author(filtered_publications)

    # Load index
    try:
        with open(index_file_path) as f:
            index = json.load(f)
    except FileNotFoundError:
        index = {}

    # Update index with filtered publications
    for publication in filtered_publications:
        title = publication['title']
        authors = publication['authors']
        date = publication['date']
        publication_link = publication['link']
        author_urls = publication['urls']
        update_index(title, authors, date, publication_link, author_urls, index)

    # Save updated index
    with open(index_file_path, 'w') as f:
        json.dump(index, f)

    print(f"Updated index file at {index_file_path} with {len(filtered_publications)} new publications")

def preprocess_text(text):
    # Convert to lowercase
    text = text.lower()

    # Remove non-alphanumeric characters
    text = re.sub(r"[^\w\s]", "", text)

    # Remove extra whitespaces
    text = re.sub(r"\s+", " ", text)

    # Strip leading and trailing whitespaces
    text = text.strip()

    return text



def search(query):
    query = preprocess_text(query)
    keywords = query.split()
    matches = []
    
    # Calculate the IDF for each keyword in the query
    idf_scores = {}
    for keyword in keywords:
        num_publications_with_keyword = sum(1 for publications in index.values() if keyword in publications)
        if num_publications_with_keyword > 0:
            idf_scores[keyword] = math.log(len(index) / num_publications_with_keyword)
        else:
            idf_scores[keyword] = 0.001
    
    for publications in index.values():
        for publication in publications:
            # Calculate the TF-IDF score for each keyword in the query and the publication's title/authors
            tfidf_sum = 0
            for keyword in keywords:
                tf = publication['Title'].lower().count(keyword) + sum(author.lower().count(keyword) for author in publication['Authors'])
                tfidf_sum += tf * idf_scores[keyword]
            
            # Add the publication to the matches if the TF-IDF score is above a threshold
            if tfidf_sum > 0:
                if publication not in matches:
                    matches.append(publication)


    # Sort matches by date
    matches.sort(key=lambda x: x["Date"], reverse=True)
    print(matches)
    return matches

# Schedule to run every 7 days at 00:00
schedule.every(7).days.at("00:00").do(scrape_and_update, 'csm_members.csv', 'index.json')

scrape_and_update('csm_members.csv','index.json')
