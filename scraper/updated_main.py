from web_scraper import run_web_scraper
import store_pdf_mongo

def main():
    # Configuration
    csv_file      = "input_websites.csv"
    pdf_directory = "downloaded_files"
    chunk_size    = 2000

    # 1. Scrape and download PDFs
    print("Starting web scraping…")
    run_web_scraper(csv_file)

    # 2. Process PDFs, index into MongoDB, then enter RAG query loop
    print("\nProcessing PDFs and building the MongoDB-backed index…")
    store_pdf_mongo.run_pdf_indexing(pdf_directory, chunk_size)

if __name__ == "__main__":
    main()
