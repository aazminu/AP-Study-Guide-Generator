# PDF Scraper and Retrieval-Augmented Generator (RAG) System


This project automates the pipeline for scraping AP (Advanced Placement) exam PDFs, extracting their content, splitting the text into semantic chunks, generating vector embeddings, and storing them in a searchable vector store (MongoDB Atlas). The system integrates with OpenAI's GPT models to enable **Retrieval-Augmented Generation (RAG)**, allowing users to query the dataset and receive grounded, contextualized answers.
 It uses **Poetry** for dependency management.

## How It Works

1. **Initial Setup**
   - The user provides a list of AP website URLs in `input_websites.csv`.
   - The project’s main script, `main.py`, orchestrates the entire workflow by calling two modules:
     - **Web Scraping Module:** Downloads PDFs from the provided AP websites.
     - **PDF Processing Module:** Extracts text from the downloaded PDFs, chunks the text, converts each chunk into a vector embedding using a SentenceTransformer model, and indexes these embeddings in a FAISS vector database.
   - Ensure that the required folder structure is in place (e.g., folders for downloaded PDFs, saved indexes, and metadata).

2. **Web Scraping**
   - The web scraping code loads each URL from `input_websites.csv`, navigates the site using Selenium, and downloads any PDF files found on those pages.
   - Downloaded PDFs are saved in the designated folder (e.g., `downloaded_files/`).

3. **PDF Processing and Vector Indexing**
   - The PDF processing module reads the downloaded PDFs and extracts text using PyPDF2.
   - The extracted text is split into manageable chunks to preserve context.
   - Each text chunk is converted into a vector embedding using a pre-trained model (e.g., `all-MiniLM-L6-v2` from SentenceTransformer).

4. **Vector Database (MongoDB Atlas)**
   - Each chunk, along with its embedding and metadata (e.g., source PDF, chunk index), is stored in a **MongoDB collection**.
   - A sample document in the database includes:
     ```json
     {
       "pdf_file": "2020_APUSH_DBQ.pdf",
       "chunk_index": 3,
       "chunk_text": "...",
       "embedding": [0.021, -0.004, ..., 0.108]
     }
     ```

5. **Retrieval-Augmented Generation (RAG)**
   - When a user submits a query, the system:
     - Embeds the query using the same SentenceTransformer model.
     - Retrieves top-matching chunks from MongoDB using cosine similarity.
     - Sends the chunks and the user query to OpenAI’s GPT model (e.g., `gpt-4o-mini`) to generate a context-aware response.


## Setup Instructions

1. **Install Dependencies**

   Ensure you have **Poetry** installed. In the project directory, run:

   ```bash
   poetry install
   ```

2. **Folder Structure**

   Ensure that the following folders exist (or are created automatically by the scripts):
   - `downloaded_files/` – for storing scraped PDF files.
   - (Optional) `faiss_index.index` and `metadata.json` – will be created after processing.

3. **Running the Project**

   To start the process—scraping the AP websites for PDFs, processing the PDFs, and building the vector database—run:

   ```bash
   poetry run python main.py
   ```

   This command will:
   - Scrape the URLs in `input_websites.csv` and download available PDFs.
   - Process the PDFs by extracting their content, chunking the text, generating vector embeddings, and storing the results in a FAISS vector index.

## Notes
- **Demo Video:**
  We have also uploaded a demo video on our github to demonstrate our fully functional web app!
- **PDF Warnings:**  
  You may see warnings such as `unknown widths` or `ignore '/Perms' verify failed` during PDF processing. These are common with PyPDF2 when encountering non-standard PDF structures or permission entries. They can typically be ignored unless they affect the text extraction quality.

- **Modularity:**  
  The project has been modularized so that web scraping and PDF processing are contained in separate modules. This makes it easier to test, maintain, and extend the functionality.

- **Customization:**  
  You can customize parameters such as the maximum chunk size or the model used for vector embeddings by modifying the respective modules.
