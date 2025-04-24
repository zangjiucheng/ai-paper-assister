import faiss
import pickle
import numpy as np

# Check index.faiss
try:
    index = faiss.read_index("index.faiss")
    print(f"FAISS Index: {index.__class__.__name__}")
    print(f"Vector count: {index.ntotal}")
    print(f"Vector dimension: {index.d}")

    # Test search
    query = np.random.random((1, index.d)).astype('float32')
    distances, indices = index.search(query, k=5)
    print(f"Sample search indices: {indices}")
except Exception as e:
    print(f"Error with index.faiss: {e}")

# Check index.pkl
try:
    with open("index.pkl", "rb") as f:
        data = pickle.load(f)
    print(f"Pickle data type: {type(data)}")
    print(f"Entry count: {len(data)}")
    print(f"Sample data: {list(data.items())[:2] if isinstance(data, dict) else data[:2]}")
except Exception as e:
    print(f"Error with index.pkl: {e}")

# Cross-check
if index.ntotal == len(data):
    print("FAISS and pickle counts match!")
else:
    print("Mismatch detected!")