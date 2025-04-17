// Configuration
const config = {
    width: 800,
    height: 600,
    padding: 50,
    nodeRadius: 8,
    colors: d3.schemeCategory10
};

// Initialize visualization
let svg, simulation;
let posts = [];
let clusters = [];
let currentAlgorithm = 'kmeans';

// Fetch blog posts and initialize visualization
async function initialize() {
    try {
        const response = await fetch('/api/blog-posts');
        posts = await response.json();
        
        // Process posts and create embeddings
        const processedPosts = await processPosts(posts);
        
        // Initialize visualization
        setupVisualization();
        
        // Perform initial clustering
        updateClustering();
        
        // Add event listeners
        document.getElementById('numClusters').addEventListener('input', updateClustering);
        document.getElementById('algorithm').addEventListener('change', (e) => {
            currentAlgorithm = e.target.value;
            updateClustering();
        });
    } catch (error) {
        console.error('Error initializing visualization:', error);
    }
}

// Process blog posts and create embeddings
async function processPosts(posts) {
    // The backend already provides embeddings, so we can just return the posts
    return posts;
}

// Setup D3 visualization
function setupVisualization() {
    const container = d3.select('#cluster-graph');
    svg = container.append('svg')
        .attr('width', config.width)
        .attr('height', config.height);
    
    // Add zoom behavior
    const zoom = d3.zoom()
        .scaleExtent([0.5, 4])
        .on('zoom', (event) => {
            svg.attr('transform', event.transform);
        });
    
    svg.call(zoom);
}

// Update clustering based on current settings
async function updateClustering() {
    const numClusters = parseInt(document.getElementById('numClusters').value);
    document.getElementById('clusterValue').textContent = numClusters;
    
    // Perform clustering
    clusters = await performClustering(posts, numClusters, currentAlgorithm);
    
    // Update visualization
    updateVisualization();
}

// Perform clustering using the selected algorithm
async function performClustering(posts, numClusters, algorithm) {
    try {
        const response = await fetch('/api/cluster', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                posts: posts,
                n_clusters: numClusters,
                algorithm: algorithm
            })
        });
        
        if (!response.ok) {
            throw new Error('Clustering failed');
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error performing clustering:', error);
        return posts; // Fallback to original posts if clustering fails
    }
}

// Update the visualization with new clustering results
function updateVisualization() {
    // Clear existing visualization
    svg.selectAll('*').remove();
    
    // Create force simulation
    simulation = d3.forceSimulation(clusters)
        .force('charge', d3.forceManyBody().strength(-30))
        .force('center', d3.forceCenter(config.width / 2, config.height / 2))
        .force('collision', d3.forceCollide().radius(config.nodeRadius * 2));
    
    // Create nodes
    const nodes = svg.selectAll('.node')
        .data(clusters)
        .enter()
        .append('circle')
        .attr('class', 'cluster-node')
        .attr('r', config.nodeRadius)
        .attr('fill', d => config.colors[d.cluster % config.colors.length])
        .on('click', showPostDetails);
    
    // Add labels
    const labels = svg.selectAll('.label')
        .data(clusters)
        .enter()
        .append('text')
        .attr('class', 'label')
        .text(d => d.title)
        .attr('font-size', '10px')
        .attr('dx', config.nodeRadius + 5)
        .attr('dy', 3);
    
    // Update positions on each tick
    simulation.on('tick', () => {
        nodes
            .attr('cx', d => d.x)
            .attr('cy', d => d.y);
        
        labels
            .attr('x', d => d.x)
            .attr('y', d => d.y);
    });
}

// Show post details when a node is clicked
function showPostDetails(post) {
    const detailsContainer = document.getElementById('post-content');
    detailsContainer.innerHTML = `
        <h4>${post.title}</h4>
        <p>${post.excerpt || 'No excerpt available'}</p>
        <a href="${post.url}" class="btn btn-primary">Read More</a>
    `;
}

// Initialize when the page loads
document.addEventListener('DOMContentLoaded', initialize); 