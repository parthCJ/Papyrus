const API_BASE = 'http://localhost:8000/api/v1';

// File upload handling
const fileInput = document.getElementById('fileInput');
const uploadArea = document.getElementById('uploadArea');

uploadArea.addEventListener('click', () => fileInput.click());

uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('drag-over');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('drag-over');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('drag-over');
    
    const files = e.dataTransfer.files;
    if (files.length > 0 && files[0].type === 'application/pdf') {
        uploadFile(files[0]);
    } else {
        showStatus('uploadStatus', 'Please upload a PDF file', 'error');
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        uploadFile(e.target.files[0]);
    }
});

async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    showStatus('uploadStatus', `<span class="spinner"></span> Uploading ${file.name}...`, 'info');
    
    try {
        const startTime = Date.now();
        const response = await fetch(`${API_BASE}/upload/pdf`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        const uploadTime = ((Date.now() - startTime) / 1000).toFixed(2);
        
        if (response.ok) {
            showStatus('uploadStatus', 
                `Uploaded successfully! (${uploadTime}s)<br>` +
                `Document ID: ${data.document_id}<br>` +
                `Chunks: ${data.num_chunks}`, 
                'success'
            );
            loadDocuments();
            fileInput.value = '';
        } else {
            showStatus('uploadStatus', `Error: ${data.detail}`, 'error');
        }
    } catch (error) {
        showStatus('uploadStatus', `Upload failed: ${error.message}`, 'error');
    }
}

async function loadDocuments() {
    const docsList = document.getElementById('documentsList');
    docsList.innerHTML = '<p class="text-muted">Loading...</p>';
    
    try {
        const response = await fetch(`${API_BASE}/documents/`);
        const data = await response.json();
        
        if (data.documents && data.documents.length > 0) {
            docsList.innerHTML = data.documents.map(doc => `
                <div class="document-item">
                    <div class="document-info">
                        <h4>${doc.title || 'Untitled Document'}</h4>
                        <p>ID: ${doc.document_id} | Chunks: ${doc.num_chunks || 'N/A'}</p>
                        <p style="font-size: 0.85em; color: #999;">
                            Uploaded: ${new Date(doc.upload_date).toLocaleString()}
                        </p>
                    </div>
                    <div class="document-actions">
                        <button onclick="deleteDocument('${doc.document_id}')">
                            Delete
                        </button>
                    </div>
                </div>
            `).join('');
        } else {
            docsList.innerHTML = '<p class="text-muted">No documents uploaded yet</p>';
        }
    } catch (error) {
        docsList.innerHTML = `<p class="text-muted">Error loading documents: ${error.message}</p>`;
    }
}

async function deleteDocument(documentId) {
    if (!confirm('Are you sure you want to delete this document?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/documents/${documentId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showStatus('uploadStatus', 'Document deleted successfully', 'success');
            loadDocuments();
        } else {
            const data = await response.json();
            showStatus('uploadStatus', `Error: ${data.detail}`, 'error');
        }
    } catch (error) {
        showStatus('uploadStatus', `Delete failed: ${error.message}`, 'error');
    }
}

async function askQuestion() {
    const query = document.getElementById('queryInput').value.trim();
    const promptTemplate = document.getElementById('promptTemplate').value;
    const topK = parseInt(document.getElementById('topKInput').value);
    const bm25Weight = parseFloat(document.getElementById('bm25WeightValue').textContent);
    const vectorWeight = parseFloat(document.getElementById('vectorWeightValue').textContent);
    
    if (!query) {
        showStatus('queryStatus', 'Please enter a question', 'error');
        return;
    }
    
    const answerSection = document.getElementById('answerSection');
    const answerBox = document.getElementById('answerBox');
    const sourcesList = document.getElementById('sourcesList');
    const timingInfo = document.getElementById('timingInfo');
    
    answerSection.style.display = 'block';
    answerBox.innerHTML = '<span class="spinner"></span> Thinking...';
    sourcesList.innerHTML = '';
    timingInfo.innerHTML = '';
    
    showStatus('queryStatus', '<span class="spinner"></span> Processing your question...', 'info');
    
    try {
        const startTime = Date.now();
        const response = await fetch(`${API_BASE}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                top_k: topK,
                bm25_weight: bm25Weight,
                vector_weight: vectorWeight,
                prompt_template: promptTemplate
            })
        });
        
        const data = await response.json();
        const totalTime = ((Date.now() - startTime) / 1000).toFixed(2);
        
        if (response.ok) {
            answerBox.textContent = data.answer;
            
            timingInfo.innerHTML = `
                Retrieval: ${data.retrieval_time.toFixed(2)}s | 
                Generation: ${data.generation_time.toFixed(2)}s | 
                Total: ${totalTime}s
            `;
            
            if (data.sources && data.sources.length > 0) {
                sourcesList.innerHTML = data.sources.map((source, idx) => `
                    <div class="source-item">
                        <h4>Source ${idx + 1} (Score: ${source.score.toFixed(4)})</h4>
                        <div class="source-content">${source.content}</div>
                        <div class="source-meta">
                            <span>Chunk: ${source.chunk_id}</span>
                            ${source.page_number ? `<span>Page: ${source.page_number}</span>` : ''}
                        </div>
                    </div>
                `).join('');
            } else {
                sourcesList.innerHTML = '<p class="text-muted">No sources found</p>';
            }
            
            showStatus('queryStatus', `Answer generated in ${totalTime}s`, 'success');
        } else {
            answerBox.textContent = `Error: ${data.detail}`;
            showStatus('queryStatus', `Error: ${data.detail}`, 'error');
        }
    } catch (error) {
        answerBox.textContent = `Error: ${error.message}`;
        showStatus('queryStatus', `Query failed: ${error.message}`, 'error');
    }
}

function showStatus(elementId, message, type) {
    const element = document.getElementById(elementId);
    element.innerHTML = message;
    element.className = `status-message show ${type}`;
    
    if (type === 'success' || type === 'error') {
        setTimeout(() => {
            element.classList.remove('show');
        }, 5000);
    }
}

// Update top_k value display
function updateTopKValue(value) {
    document.getElementById('topKValue').textContent = value;
}

// Update weights with auto-balance
function updateWeights(bm25Value) {
    const bm25Weight = (bm25Value / 100).toFixed(2);
    const vectorWeight = ((100 - bm25Value) / 100).toFixed(2);
    
    document.getElementById('bm25WeightValue').textContent = bm25Weight;
    document.getElementById('vectorWeightValue').textContent = vectorWeight;
    document.getElementById('vectorWeightInput').value = 100 - bm25Value;
}

// Load documents on page load and setup event listeners
window.addEventListener('load', () => {
    loadDocuments();
    
    // Allow Enter key to submit query (Shift+Enter for new line)
    document.getElementById('queryInput').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            askQuestion();
        }
    });
});
