import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from urllib.parse import urljoin

def get_soup(url, params=None, headers=None):
    """Get BeautifulSoup object from URL"""
    if headers is None:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    return BeautifulSoup(response.text, 'html.parser')

def get_post_links(base_url, max_pages=None):
    """Extract all post links from the bulletin board"""
    post_links = []
    page = 1
    
    while True:
        if max_pages and page > max_pages:
            break
            
        params = {'page': page}
        soup = get_soup(base_url, params=params)
        
        # Find all post rows in the table
        rows = soup.select('table.board_list tbody tr')
        if not rows:
            break
            
        for row in rows:
            link = row.select_one('td.title a')
            if link and 'href' in link.attrs:
                post_links.append(urljoin(base_url, link['href']))
        
        # Check if there's a next page
        next_page = soup.select_one('a.next')
        if not next_page or 'disabled' in next_page.get('class', []):
            break
            
        page += 1
        time.sleep(1)  # Be nice to the server
    
    return post_links

def get_post_content(post_url):
    """Extract content from a single post"""
    soup = get_soup(post_url)
    
    # Extract post details
    title = soup.select_one('div.view_title h2').get_text(strip=True) if soup.select_one('div.view_title h2') else ''
    date = soup.select_one('div.view_info span.date').get_text(strip=True) if soup.select_one('div.view_info span.date') else ''
    content = soup.select_one('div.view_cont').get_text('\n', strip=True) if soup.select_one('div.view_cont') else ''
    
    return {
        'title': title,
        'date': date,
        'content': content,
        'url': post_url
    }

def main():
    base_url = 'https://overseas.mofa.go.kr/us-ko/brd/m_4525/list.do'
    output_file = 'mofa_notices.csv'
    
    print("Collecting post links...")
    post_links = get_post_links(base_url)
    print(f"Found {len(post_links)} posts.")
    
    posts_data = []
    for i, link in enumerate(post_links, 1):
        print(f"Processing post {i}/{len(post_links)}: {link}")
        try:
            post_data = get_post_content(link)
            posts_data.append(post_data)
            time.sleep(1)  # Be nice to the server
        except Exception as e:
            print(f"Error processing {link}: {str(e)}")
    
    # Save to CSV
    if posts_data:
        df = pd.DataFrame(posts_data)
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"Data saved to {output_file}")
    else:
        print("No data was collected.")

if __name__ == "__main__":
    main()