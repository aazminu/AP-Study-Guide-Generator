import os

# Check size of the FAISS index
index_size = os.path.getsize("faiss_index.index")
print(f"FAISS index size: {index_size / (1024*1024):.2f} MB")

# Check size of the metadata
metadata_size = os.path.getsize("metadata.json")
print(f"Metadata size: {metadata_size / (1024*1024):.2f} MB")

# Total size
total_size = index_size + metadata_size
print(f"Total database size: {total_size / (1024*1024):.2f} MB")