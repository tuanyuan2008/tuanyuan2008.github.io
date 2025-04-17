from flask import Flask, jsonify, request
from flask_cors import CORS
import numpy as np
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.manifold import TSNE
from sentence_transformers import SentenceTransformer
import os

app = Flask(__name__)
CORS(app)

# Initialize the sentence transformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

def get_blog_posts():
    """Get all blog posts from the _posts directory"""
    posts = []
    posts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), '_posts')
    
    for filename in os.listdir(posts_dir):
        if filename.endswith('.md'):
            with open(os.path.join(posts_dir, filename), 'r') as f:
                content = f.read()
                # Extract front matter and content
                parts = content.split('---')
                if len(parts) >= 3:
                    front_matter = parts[1]
                    post_content = parts[2]
                    
                    # Parse front matter (simplified)
                    title = filename.replace('.md', '')
                    date = filename[:10]  # Assuming filename starts with date
                    
                    posts.append({
                        'title': title,
                        'date': date,
                        'content': post_content,
                        'url': f'/blog/{date}-{title}'
                    })
    
    return posts

def create_embeddings(posts):
    """Create embeddings for blog posts"""
    texts = [post['content'] for post in posts]
    embeddings = model.encode(texts)
    return embeddings

def perform_clustering(embeddings, n_clusters, algorithm):
    """Perform clustering using the specified algorithm"""
    if algorithm == 'kmeans':
        clusterer = KMeans(n_clusters=n_clusters, random_state=42)
    elif algorithm == 'dbscan':
        clusterer = DBSCAN(eps=0.5, min_samples=2)
    elif algorithm == 'hierarchical':
        clusterer = AgglomerativeClustering(n_clusters=n_clusters)
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")
    
    clusters = clusterer.fit_predict(embeddings)
    return clusters

def reduce_dimensions(embeddings):
    """Reduce dimensions for visualization using t-SNE"""
    tsne = TSNE(n_components=2, random_state=42)
    reduced = tsne.fit_transform(embeddings)
    return reduced

@app.route('/api/blog-posts', methods=['GET'])
def get_posts():
    posts = get_blog_posts()
    embeddings = create_embeddings(posts)
    reduced = reduce_dimensions(embeddings)
    
    # Add coordinates and initial clustering to posts
    for i, post in enumerate(posts):
        post['x'] = float(reduced[i, 0])
        post['y'] = float(reduced[i, 1])
        post['embedding'] = embeddings[i].tolist()
    
    return jsonify(posts)

@app.route('/api/cluster', methods=['POST'])
def cluster_posts():
    data = request.json
    posts = data['posts']
    n_clusters = data['n_clusters']
    algorithm = data['algorithm']
    
    embeddings = np.array([post['embedding'] for post in posts])
    clusters = perform_clustering(embeddings, n_clusters, algorithm)
    
    # Update posts with new cluster assignments
    for i, post in enumerate(posts):
        post['cluster'] = int(clusters[i])
    
    return jsonify(posts)

if __name__ == '__main__':
    app.run(debug=True) 