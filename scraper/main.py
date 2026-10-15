from scraper.web_scraper import run_web_scraper
import scraper.store_pdf_mongo as store_pdf_mongo

def main():
    # Define any parameters if needed
    csv_file = "input_websites.csv"
    pdf_directory = "downloaded_files"
    chunk_size = 2000

    print("Starting web scraping...")
    run_web_scraper(csv_file)
    
    print("\nProcessing PDFs and building the index...")
    store_pdf_mongo.run_pdf_indexing(pdf_directory, chunk_size)

if __name__ == "__main__":
    main()
