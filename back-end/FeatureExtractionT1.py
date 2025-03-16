import os
from bs4 import BeautifulSoup
from simhash import Simhash
from datasketch import MinHash, MinHashLSH
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import re

# Ensure NLTK resources are downloaded
import nltk
nltk.download('stopwords')

def extract_structure(html):
    """Extract DOM structure with tag names and depths"""
    soup = BeautifulSoup(html, 'html.parser')
    structure = []
    for tag in soup.find_all(True):
        depth = len(list(tag.parents))
        structure.append(f"{tag.name}:{depth}")
    return ' '.join(structure)

def extract_classes(html):
    """Extract all unique CSS classes"""
    soup = BeautifulSoup(html, 'html.parser')
    classes = set()
    for element in soup.find_all(class_=True):
        classes.update(element['class'])
    return classes

def extract_text(html):
    """Clean and process text content"""
    soup = BeautifulSoup(html, 'html.parser')
    for script in soup(["script", "style"]):
        script.decompose()
    text = soup.get_text()
    text = re.sub(r'[^\w\s]', '', text.lower())
    tokens = text.split()
    stop_words = set(stopwords.words('english'))
    ps = PorterStemmer()
    filtered = [ps.stem(word) for word in tokens if word not in stop_words]
    return ' '.join(filtered)

def process_file(file_path):
    """Process a single HTML file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        html = f.read()
    return {
        'path': file_path,
        'structure': extract_structure(html),
        'classes': extract_classes(html),
        'text': extract_text(html)
    }

def get_structure_simhash(structure_str):
    """Generate SimHash for DOM structure"""
    return Simhash(structure_str.split())

def get_class_minhash(classes_set, num_perm=128):
    """Generate MinHash for CSS classes"""
    minhash = MinHash(num_perm=num_perm)
    for cls in classes_set:
        minhash.update(cls.encode('utf-8'))
    return minhash

def get_text_simhash(text_str):
    """Generate SimHash for text content"""
    return Simhash(text_str.split())

def cluster_documents(input_dir):
    """Main clustering function with adjustable thresholds"""
    processed_data = []
    
    # Process all HTML files in input directory
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.html'):
                path = os.path.join(root, file)
                try:
                    data = process_file(path)
                    # Retain the original hash objects for computation
                    data['structure_simhash'] = get_structure_simhash(data['structure'])
                    data['class_minhash'] = get_class_minhash(data['classes'])
                    data['text_simhash'] = get_text_simhash(data['text'])
                    processed_data.append(data)
                except Exception as e:
                    print(f"Error processing {path}: {str(e)}")
    
    if not processed_data:
        print("No HTML files processed.")
        return []
    
    # Build LSH index for class similarities
    lsh_class = MinHashLSH(threshold=0.3, num_perm=128)
    for idx, data in enumerate(processed_data):
        lsh_class.insert(f"c{idx}", data['class_minhash'])
    
    # Adjustable parameters
    COMBINED_THRESHOLD = 0.7   # Increase overall threshold for precision
    MIN_STRUCTURE_SIM = 0.65   # Minimum structure similarity (0-1 scale)
    MIN_TEXT_SIM = 0.65        # Minimum text similarity (0-1 scale)
    STRUCT_WEIGHT = 0.5
    CLASS_WEIGHT = 0.3  # Note: class similarity is indirectly used by LSH query
    TEXT_WEIGHT = 0.2

    clusters = []
    for doc in processed_data:
        added = False
        # Query similar documents based on class MinHash similarity
        class_candidates = lsh_class.query(doc['class_minhash'])
        candidate_indices = [int(cid[1:]) for cid in class_candidates]
        candidates = [processed_data[i] for i in candidate_indices]
        
        for candidate in candidates:
            if candidate['path'] == doc['path']:
                continue
            
            # Compute similarity using Simhash distance (64-bit)
            struct_dist = doc['structure_simhash'].distance(candidate['structure_simhash'])
            struct_sim = 1 - (struct_dist / 64)
            text_dist = doc['text_simhash'].distance(candidate['text_simhash'])
            text_sim = 1 - (text_dist / 64)
            
            # Only consider candidate if structure and text individually pass minimum thresholds
            if struct_sim < MIN_STRUCTURE_SIM or text_sim < MIN_TEXT_SIM:
                continue
            
            combined = STRUCT_WEIGHT * struct_sim + CLASS_WEIGHT * 1.0 + TEXT_WEIGHT * text_sim
            
            if combined >= COMBINED_THRESHOLD:
                for cluster in clusters:
                    if candidate['path'] in [d['path'] for d in cluster]:
                        cluster.append(doc)
                        added = True
                        break
                if added:
                    break
        if not added:
            clusters.append([doc])
    
    # Merge overlapping clusters
    merged_clusters = []
    for cluster in clusters:
        merged = False
        for mc in merged_clusters:
            if any(doc['path'] in [d['path'] for d in mc] for doc in cluster):
                mc.extend(cluster)
                merged = True
                break
        if not merged:
            merged_clusters.append(cluster)
    
    # Deduplicate final clusters
    final_clusters = []
    for cluster in merged_clusters:
        unique = []
        seen = set()
        for doc in cluster:
            if doc['path'] not in seen:
                seen.add(doc['path'])
                unique.append(doc)
        final_clusters.append(unique)
    
    return final_clusters

def save_clusters(clusters, output_dir):
    """Save clustering results to output directory"""
    os.makedirs(output_dir, exist_ok=True)
    
    for cluster_id, cluster in enumerate(clusters, 1):
        output_path = os.path.join(output_dir, f"cluster_{cluster_id:03d}.txt")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"Cluster {cluster_id} ({len(cluster)} documents)\n")
            f.write("=" * 40 + "\n")
            for doc in cluster:
                f.write(f"- {os.path.relpath(doc['path'], output_dir)}\n")
                
    print(f"Generated {len(clusters)} clusters in {output_dir}")

if __name__ == "__main__":
    # Configure paths (MODIFY THESE)
    INPUT_DIR = "clones/tier1"  # Folder with your 100 HTML files
    OUTPUT_DIR = "output_clusters_t1"   # Where to save cluster results
    
    # Validate input path
    if not os.path.exists(INPUT_DIR):
        raise FileNotFoundError(f"Input directory not found: {INPUT_DIR}")
    
    # Run clustering and save results
    clusters = cluster_documents(INPUT_DIR)
    save_clusters(clusters, OUTPUT_DIR)
