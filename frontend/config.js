// Configuration for backend API URL
const API_CONFIG = {
    // Change this to your Hugging Face Space URL after deployment
    BACKEND_URL: window.location.hostname === 'localhost' 
        ? 'http://localhost:8000'
        : 'https://YOUR-HF-SPACE-NAME.hf.space',
    API_V1: '/api/v1'
};

// Get full API URL
function getApiUrl(endpoint) {
    return `${API_CONFIG.BACKEND_URL}${API_CONFIG.API_V1}${endpoint}`;
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { API_CONFIG, getApiUrl };
}
