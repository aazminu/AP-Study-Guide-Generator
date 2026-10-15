
import os
import csv
import time
import requests
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def create_webdriver(headless=True):
    """
    Create and return a configured Selenium Chrome WebDriver instance.
    """
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--log-level=3")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    return webdriver.Chrome(options=options)

def gather_links(driver, base_url):
    """
    Gather all valid links from the current Selenium-loaded page.
    """
    valid_links = set()
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "a"))
        )
        elements = driver.find_elements(By.TAG_NAME, "a")
        for element in elements:
            link = element.get_attribute("href")
            if link and is_valid_link(link, base_url):
                valid_links.add(link)
    except Exception as e:
        print(f"Warning: Could not gather links. Reason: {e}")
    return valid_links

def is_valid_link(link, base_url):
    """
    Check if the link is on the same domain and is not a typical static resource
    we want to skip. PDFs are allowed.
    """
    parsed_url = urlparse(link)
    return (
        base_url in link
        and not link.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".bmp",
                                       ".svg", ".webp", ".js", ".css"))
        and "/wp-content/" not in link
        and "/wp-json/" not in link
        and parsed_url.scheme in ["http", "https"]
    )

def download_file(url, session, download_dir="downloaded_files"):
    """
    Download a file (e.g., PDF) to the specified directory.
    """
    os.makedirs(download_dir, exist_ok=True)
    local_filename = url.split('/')[-1] or "file"
    local_filepath = os.path.join(download_dir, local_filename)
    try:
        with session.get(url, stream=True, timeout=15) as r:
            r.raise_for_status()
            with open(local_filepath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"Downloaded: {local_filepath}")
    except Exception as e:
        print(f"Failed to download {url}. Reason: {e}")

def process_website(driver, session, website):
    """
    Process a single website:
    1. Open the page in Selenium.
    2. Collect links on the page.
    3. Download PDFs from the collected links.
    """
    try:
        print(f"Processing: {website}")
        driver.get(website)

        # Determine base domain for link filtering
        base_domain = website.split("//")[-1].split('/')[0]
        links = gather_links(driver, base_domain)

        # Download only PDF files
        for link in links:
            if link.lower().endswith(".pdf"):
                download_file(link, session)
                
        return True
    except Exception as e:
        print(f"Error processing {website}: {e}")
        return False

def run_web_scraper(csv_file="input_websites.csv"):
    """
    Process all websites from a CSV file.
    
    Parameters:
        csv_file (str): Path to the CSV file containing websites.
    """
    # Prepare requests session
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/91.0.4472.124 Safari/537.36'
    })
    
    # Launch Selenium WebDriver
    driver = create_webdriver(headless=True)
    
    try:
        with open(csv_file, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if not row:
                    continue  # skip empty rows
                website = row[0].strip()
                if website:
                    process_website(driver, session, website)
    except FileNotFoundError:
        print(f"CSV file '{csv_file}' not found.")
    except Exception as e:
        print(f"Error reading CSV file: {e}")
    finally:
        driver.quit()

# Command-line execution
if __name__ == "__main__":
    import sys
    # Allow a CSV filename to be passed as a parameter, otherwise default
    csv_file = sys.argv[1] if len(sys.argv) > 1 else "input_websites.csv"
    run_web_scraper(csv_file)
