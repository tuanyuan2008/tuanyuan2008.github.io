from flask import Flask, jsonify, request
from flask_cors import CORS
import numpy as np
from sklearn.cluster import KMeans
import os
import logging
import gc
import re
import traceback
from collections import Counter

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configure CORS with the correct origin
CORS(app, origins=["http://localhost:4000"], supports_credentials=True)

@app.route('/cluster', methods=['POST'])
def cluster_posts():
    try:
        logger.debug("Received clustering request")
        data = request.get_json()
        logger.debug(f"Request data: {data}")
        
        if not data or 'n_clusters' not in data:
            logger.error("Invalid request: missing n_clusters parameter")
            return jsonify({'error': 'Missing n_clusters parameter'}), 400
            
        n_clusters = int(data['n_clusters'])
        if n_clusters < 1:
            logger.error(f"Invalid n_clusters value: {n_clusters}")
            return jsonify({'error': 'n_clusters must be at least 1'}), 400
            
        logger.info(f"Received clustering request with {n_clusters} clusters")
        
        # Get all posts
        posts = get_blog_posts()
        if not posts:
            logger.error("No posts found")
            return jsonify({'error': 'No posts found'}), 404
            
        # Create similarity matrix
        similarity_matrix = create_similarity_matrix(posts)
        if similarity_matrix is None:
            logger.error("Failed to create similarity matrix")
            return jsonify({'error': 'Failed to create similarity matrix'}), 500
            
        # Perform clustering
        clusters = perform_clustering(similarity_matrix, n_clusters)
        if clusters is None:
            logger.error("Failed to perform clustering")
            return jsonify({'error': 'Failed to perform clustering'}), 500
            
        # Group posts by cluster
        cluster_groups = {}
        for i, cluster_id in enumerate(clusters):
            if cluster_id not in cluster_groups:
                cluster_groups[cluster_id] = []
            cluster_groups[cluster_id].append(posts[i])
        
        # Prepare response
        result = {
            'clusters': []
        }
        
        for cluster_id, cluster_posts in cluster_groups.items():
            # Get top keywords for this cluster
            all_words = []
            for post in cluster_posts:
                all_words.extend(post['processed_content'])
            
            word_counts = Counter(all_words)
            top_keywords = [word for word, _ in word_counts.most_common(5)]
            
            result['clusters'].append({
                'id': int(cluster_id),
                'posts': [{'title': p['title'], 'date': p['date'], 'url': p['url']} for p in cluster_posts],
                'top_keywords': top_keywords
            })
        
        logger.info(f"Successfully prepared response with {len(result['clusters'])} clusters")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in cluster_posts: {e}\n{traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500
    finally:
        gc.collect()

def preprocess_text(text):
    """Preprocess text by removing special characters and converting to lowercase"""
    try:
        # Remove special characters and convert to lowercase
        text = re.sub(r'[^\w\s]', '', text.lower())
        # Split into words and remove short words
        words = [word for word in text.split() if len(word) > 3]
        logger.debug(f"Processed text into {len(words)} words")
        return set(words)
    except Exception as e:
        logger.error(f"Error in preprocess_text: {e}\n{traceback.format_exc()}")
        return set()

def jaccard_similarity(set1, set2):
    """Calculate Jaccard similarity between two sets"""
    try:
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        similarity = intersection / union if union > 0 else 0
        logger.debug(f"Jaccard similarity: {similarity}")
        return similarity
    except Exception as e:
        logger.error(f"Error in jaccard_similarity: {e}\n{traceback.format_exc()}")
        return 0

def get_blog_posts():
    """Get all blog posts from the _posts directory"""
    try:
        posts = []
        posts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '_posts')
        
        if not os.path.exists(posts_dir):
            logger.error(f"Posts directory not found: {posts_dir}")
            return []
        
        logger.info(f"Reading posts from {posts_dir}")
        for filename in os.listdir(posts_dir):
            if filename.endswith('.md'):
                try:
                    file_path = os.path.join(posts_dir, filename)
                    logger.debug(f"Processing file: {file_path}")
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Extract front matter and content
                        parts = content.split('---')
                        if len(parts) >= 3:
                            front_matter = parts[1]
                            post_content = parts[2]
                            
                            # Parse front matter (simplified)
                            title = filename.replace('.md', '')
                            date = filename[:10]  # Assuming filename starts with date
                            
                            # Preprocess content
                            processed_content = preprocess_text(post_content)
                            
                            posts.append({
                                'title': title,
                                'date': date,
                                'content': post_content,
                                'processed_content': processed_content,
                                'url': f'/blog/{date}-{title}'
                            })
                            logger.debug(f"Added post: {title} with {len(processed_content)} processed words")
                except Exception as e:
                    logger.error(f"Error processing file {filename}: {e}\n{traceback.format_exc()}")
                    continue
        
        logger.info(f"Loaded {len(posts)} posts")
        return posts
    except Exception as e:
        logger.error(f"Error in get_blog_posts: {e}\n{traceback.format_exc()}")
        return []

def create_similarity_matrix(posts):
    """Create similarity matrix using Jaccard similarity"""
    try:
        n_posts = len(posts)
        logger.debug(f"Creating similarity matrix for {n_posts} posts")
        similarity_matrix = np.zeros((n_posts, n_posts))
        
        for i in range(n_posts):
            for j in range(i+1, n_posts):
                similarity = jaccard_similarity(
                    posts[i]['processed_content'],
                    posts[j]['processed_content']
                )
                similarity_matrix[i][j] = similarity
                similarity_matrix[j][i] = similarity
        
        # Set diagonal to 1
        np.fill_diagonal(similarity_matrix, 1)
        
        logger.info("Similarity matrix created successfully")
        return similarity_matrix
    except Exception as e:
        logger.error(f"Error in create_similarity_matrix: {e}\n{traceback.format_exc()}")
        return None
    finally:
        gc.collect()

def perform_clustering(similarity_matrix, n_clusters):
    """Perform clustering using KMeans on similarity matrix"""
    try:
        if similarity_matrix is None:
            raise Exception("No similarity matrix available")
            
        logger.info(f"Performing clustering with {n_clusters} clusters")
        clusterer = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = clusterer.fit_predict(similarity_matrix)
        logger.info(f"Clustering completed. Cluster assignments: {clusters}")
        return clusters
    except Exception as e:
        logger.error(f"Error in perform_clustering: {e}\n{traceback.format_exc()}")
        return None
    finally:
        gc.collect()

if __name__ == '__main__':
    app.run(debug=True, port=5050, use_reloader=False) 