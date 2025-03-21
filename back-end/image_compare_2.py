import os
import numpy as np
from PIL import Image
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, TimeoutException
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity
from tensorflow.keras.applications import VGG16
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.vgg16 import preprocess_input
from sentence_transformers import SentenceTransformer
from collections import defaultdict
import re
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import nltk

nltk.download('stopwords')

visual_model = VGG16(weights='imagenet', include_top=False)
text_model = SentenceTransformer('all-MiniLM-L6-v2')

class VisualAnalyzer:
    def __init__(self):
        self.driver = self._initialize_driver()

    def _get_browser_options(self):
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--allow-insecure-localhost')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--ignore-ssl-errors=yes')
        options.add_argument('--disable-extensions')
        options.add_argument('--no-sandbox')
        return options

    def _initialize_driver(self):
        chrome_driver_path = r"C:\Users\draghi\Desktop\chromedriver-win64\chromedriver.exe"
        options = self._get_browser_options()
        service = Service(chrome_driver_path, log_path="chromedriver.log")
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(60)
        return driver

    def capture_screenshot(self, file_path, save_path, max_retries=3):
        for attempt in range(max_retries):
            try:
                self.driver.set_page_load_timeout(60)
                self.driver.get(f"file:///{os.path.abspath(file_path)}")
                self.driver.save_screenshot(save_path)
                return Image.open(save_path)
            except TimeoutException:
                print(f"Timeout: {file_path} took too long to load (attempt {attempt + 1}).")
            except WebDriverException as e:
                print(f"WebDriverException for {file_path} (attempt {attempt + 1}): {str(e)}")
            except Exception as e:
                print(f"Error capturing screenshot for {file_path}: {str(e)}")
                return None
        print(f"Failed to capture screenshot for {file_path} after {max_retries} attempts.")
        return None

    def extract_visual_features(self, img_path):
        try:
            img = image.load_img(img_path, target_size=(224, 224))
            x = image.img_to_array(img)
            x = preprocess_input(x)
            features = visual_model.predict(np.expand_dims(x, axis=0))
            return features.flatten()
        except Exception as e:
            print(f"Error extracting visual features from {img_path}: {str(e)}")
            return np.zeros((25088,))

    def close(self):
        self.driver.quit()

def extract_structure(html):
    soup = BeautifulSoup(html, 'html.parser')
    structure = []
    for tag in soup.find_all(True):
        depth = len(list(tag.parents))
        structure.append(f"{tag.name}:{depth}")
    return ' '.join(structure)

def extract_classes(html):
    soup = BeautifulSoup(html, 'html.parser')
    classes = set()
    for element in soup.find_all(class_=True):
        classes.update(element['class'])
    return classes

def extract_text(html):
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
    with open(file_path, 'r', encoding='utf-8') as f:
        html = f.read()
    return {
        'path': file_path,
        'structure': extract_structure(html),
        'classes': extract_classes(html),
        'text': extract_text(html)
    }

def get_text_embedding(text_str):
    return text_model.encode(text_str)

class WebsiteClusterer:
    def __init__(self):
        self.visual_analyzer = VisualAnalyzer()
        self.screenshot_dir = "website_screenshots_t2"
        os.makedirs(self.screenshot_dir, exist_ok=True)
        
    def process_website(self, file_path):
        try:
            data = process_file(file_path)
            screenshot_path = os.path.join(self.screenshot_dir, f"{os.path.basename(file_path)}.png")
            screenshot = self.visual_analyzer.capture_screenshot(file_path, screenshot_path)
            
            if screenshot is None:
                print(f"Skipping {file_path} due to screenshot capture failure.")
                return None
            
            data['visual_features'] = self.visual_analyzer.extract_visual_features(screenshot_path)
            data['text_embedding'] = get_text_embedding(data['text'])
            
            return data
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
            print("Restarting WebDriver...")
            self.visual_analyzer.close()
            self.visual_analyzer = VisualAnalyzer()
            return None

    def calculate_similarity(self, doc1, doc2):
        visual_sim = cosine_similarity([doc1['visual_features']], [doc2['visual_features']])[0][0]
        text_sim = cosine_similarity([doc1['text_embedding']], [doc2['text_embedding']])[0][0]
        class_set1 = set(doc1['classes'])
        class_set2 = set(doc2['classes'])
        class_sim = len(class_set1 & class_set2) / len(class_set1 | class_set2) if len(class_set1 | class_set2) > 0 else 0
        return 0.4 * visual_sim + 0.3 * text_sim + 0.3 * class_sim

    def cluster_websites(self, processed_data, similarity_threshold=0.7):
        features = np.array([d['visual_features'] for d in processed_data])
        clustering = DBSCAN(metric='cosine', eps=1-similarity_threshold, min_samples=1).fit(features)
        return clustering.labels_

    def close(self):
        self.visual_analyzer.close()

def save_clusters(clusters, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    for cluster_id, cluster in enumerate(clusters, 1):
        output_path = os.path.join(output_dir, f"cluster_{cluster_id:03d}.txt")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"Cluster {cluster_id} ({len(cluster)} documents)\n")
            f.write("=" * 40 + "\n")
            for doc in cluster:
                f.write(f"- {os.path.relpath(doc['path'], output_dir)}\n")
                
    print(f"Generated {len(clusters)} clusters in {output_dir}")

def main(input_dir, output_dir):
    if not os.path.exists(input_dir):
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    
    clusterer = WebsiteClusterer()
    
    processed_data = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                data = clusterer.process_website(file_path)
                if data:
                    processed_data.append(data)
    
    labels = clusterer.cluster_websites(processed_data)
    
    clusters = defaultdict(list)
    for idx, label in enumerate(labels):
        clusters[label].append(processed_data[idx])
    
    save_clusters(clusters.values(), output_dir)
    
    clusterer.close()

if __name__ == "__main__":
    INPUT_DIR = "../back-end/clones/tier2"
    OUTPUT_DIR = "../back-end/output_clusters_t2"
    main(INPUT_DIR, OUTPUT_DIR)
