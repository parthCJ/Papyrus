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
    
    const conversationSection = document.getElementById('conversationSection');
    const conversationContainer = document.getElementById('conversationContainer');
    
    conversationSection.style.display = 'block';
    
    // Create conversation item
    const conversationItem = document.createElement('div');
    conversationItem.className = 'conversation-item';
    
    // Add question
    const questionHtml = `
        <div class="conversation-question">
            <div class="conversation-question-label">Question</div>
            <div class="conversation-question-text">${escapeHtml(query)}</div>
        </div>
    `;
    
    // Add loading answer
    const answerHtml = `
        <div class="conversation-answer">
            <div class="conversation-answer-label">
                Answer
                <span class="conversation-timing" id="timing-${Date.now()}"></span>
            </div>
            <div class="conversation-answer-text">
                <span class="spinner"></span> Thinking...
            </div>
        </div>
    `;
    
    conversationItem.innerHTML = questionHtml + answerHtml;
    conversationContainer.appendChild(conversationItem);
    
    // Scroll to bottom
    conversationItem.scrollIntoView({ behavior: 'smooth', block: 'end' });
    
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
            // Update answer
            const answerDiv = conversationItem.querySelector('.conversation-answer');
            const timingSpan = conversationItem.querySelector('.conversation-timing');
            
            timingSpan.textContent = `Retrieval: ${data.retrieval_time.toFixed(2)}s | Generation: ${data.generation_time.toFixed(2)}s | Total: ${totalTime}s`;
            
            answerDiv.innerHTML = `
                <div class="conversation-answer-label">
                    Answer
                    <span class="conversation-timing">${timingSpan.textContent}</span>
                </div>
                <div class="conversation-answer-text">${renderMarkdown(data.answer)}</div>
            `;
            
            showStatus('queryStatus', `Answer generated in ${totalTime}s`, 'success');
            
            // Clear query input
            document.getElementById('queryInput').value = '';
            
            // Save to history
            addToHistory({
                query: query,
                answer: data.answer,
                sources: data.sources || [],
                top_k: topK,
                bm25_weight: bm25Weight,
                vector_weight: vectorWeight,
                prompt_template: promptTemplate,
                response_time: parseFloat(totalTime)
            });
            
            // Scroll to bottom
            conversationItem.scrollIntoView({ behavior: 'smooth', block: 'end' });
        } else {
            const answerDiv = conversationItem.querySelector('.conversation-answer-text');
            answerDiv.textContent = `Error: ${data.detail}`;
            showStatus('queryStatus', `Error: ${data.detail}`, 'error');
        }
    } catch (error) {
        const answerDiv = conversationItem.querySelector('.conversation-answer-text');
        answerDiv.textContent = `Error: ${error.message}`;
        showStatus('queryStatus', `Query failed: ${error.message}`, 'error');
    }
}

// Clear conversation
function clearConversation() {
    if (confirm('Are you sure you want to clear the conversation?')) {
        const conversationContainer = document.getElementById('conversationContainer');
        conversationContainer.innerHTML = '';
        document.getElementById('conversationSection').style.display = 'none';
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
    loadHistory();
    
    // Allow Enter key to submit query (Shift+Enter for new line)
    document.getElementById('queryInput').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            askQuestion();
        }
    });
});

// ===== QUERY HISTORY MANAGEMENT =====

const HISTORY_KEY = 'researchrag_query_history';
const MAX_HISTORY_ITEMS = 100;

// Load history from localStorage
function loadHistory() {
    const history = getHistory();
    displayHistory(history);
}

// Get history from localStorage
function getHistory() {
    const stored = localStorage.getItem(HISTORY_KEY);
    return stored ? JSON.parse(stored) : [];
}

// Save history to localStorage
function saveHistory(history) {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
}

// Add new query to history
function addToHistory(queryData) {
    let history = getHistory();
    
    const historyItem = {
        id: Date.now(),
        query: queryData.query,
        answer: queryData.answer,
        sources: queryData.sources,
        timestamp: Date.now(),
        settings: {
            top_k: queryData.top_k,
            bm25_weight: queryData.bm25_weight,
            vector_weight: queryData.vector_weight,
            prompt_template: queryData.prompt_template
        },
        response_time: queryData.response_time,
        favorite: false
    };
    
    history.unshift(historyItem);
    
    if (history.length > MAX_HISTORY_ITEMS) {
        history = history.slice(0, MAX_HISTORY_ITEMS);
    }
    
    saveHistory(history);
    displayHistory(history);
}

// Toggle favorite status
function toggleFavorite(id) {
    const history = getHistory();
    const item = history.find(h => h.id === id);
    if (item) {
        item.favorite = !item.favorite;
        saveHistory(history);
        displayHistory(history);
    }
}

// Delete history item
function deleteHistoryItem(id) {
    let history = getHistory();
    history = history.filter(h => h.id !== id);
    saveHistory(history);
    displayHistory(history);
}

// Clear all history
function clearHistory() {
    if (confirm('Are you sure you want to clear all search history?')) {
        localStorage.removeItem(HISTORY_KEY);
        displayHistory([]);
    }
}

// Load query from history
function loadFromHistory(id) {
    const history = getHistory();
    const item = history.find(h => h.id === id);
    
    if (item) {
        document.getElementById('queryInput').value = item.query;
        document.getElementById('topKInput').value = item.settings.top_k;
        document.getElementById('topKValue').textContent = item.settings.top_k;
        
        const bm25Percent = Math.round(item.settings.bm25_weight * 100);
        document.getElementById('bm25WeightInput').value = bm25Percent;
        updateWeights(bm25Percent);
        
        document.getElementById('promptTemplate').value = item.settings.prompt_template;
        
        closeHistory();
        document.getElementById('queryInput').focus();
    }
}

// Display history in sidebar
function displayHistory(history) {
    const container = document.getElementById('historyContent');
    
    if (!history || history.length === 0) {
        container.innerHTML = '<p class="text-muted" style="text-align: center; padding: 20px;">No search history yet</p>';
        return;
    }
    
    const favorites = history.filter(h => h.favorite);
    const today = history.filter(h => isToday(h.timestamp) && !h.favorite);
    const yesterday = history.filter(h => isYesterday(h.timestamp) && !h.favorite);
    const older = history.filter(h => !isToday(h.timestamp) && !isYesterday(h.timestamp) && !h.favorite);
    
    let html = '';
    
    if (favorites.length > 0) {
        html += renderHistoryGroup('Favorites', favorites);
    }
    if (today.length > 0) {
        html += renderHistoryGroup('Today', today);
    }
    if (yesterday.length > 0) {
        html += renderHistoryGroup('Yesterday', yesterday);
    }
    if (older.length > 0) {
        html += renderHistoryGroup('Older', older);
    }
    
    container.innerHTML = html;
}

// Render history group
function renderHistoryGroup(title, items) {
    const itemsHtml = items.map(item => `
        <div class="history-item ${item.favorite ? 'favorite' : ''}" onclick="loadFromHistory(${item.id})">
            <div class="history-item-header">
                <div class="history-item-query">${escapeHtml(item.query)}</div>
                <div class="history-item-actions">
                    <button class="favorite-btn ${item.favorite ? 'active' : ''}" 
                            onclick="event.stopPropagation(); toggleFavorite(${item.id})" 
                            title="${item.favorite ? 'Remove from favorites' : 'Add to favorites'}">
                        ${item.favorite ? '★' : '☆'}
                    </button>
                    <button onclick="event.stopPropagation(); deleteHistoryItem(${item.id})" 
                            title="Delete">
                        ×
                    </button>
                </div>
            </div>
            <div class="history-item-answer">${escapeHtml(item.answer.substring(0, 150))}...</div>
            <div class="history-item-meta">
                <span>${formatTimestamp(item.timestamp)}</span>
                <span>${item.response_time.toFixed(1)}s</span>
                <span>${item.settings.top_k} chunks</span>
            </div>
        </div>
    `).join('');
    
    return `
        <div class="history-group">
            <div class="history-group-title">${title}</div>
            ${itemsHtml}
        </div>
    `;
}

// Filter history by search term
function filterHistory(searchTerm) {
    const history = getHistory();
    
    if (!searchTerm.trim()) {
        displayHistory(history);
        return;
    }
    
    const filtered = history.filter(item => 
        item.query.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.answer.toLowerCase().includes(searchTerm.toLowerCase())
    );
    
    displayHistory(filtered);
}

// Toggle history sidebar
function toggleHistory() {
    const sidebar = document.getElementById('historySidebar');
    const overlay = document.getElementById('historyOverlay');
    
    if (!overlay) {
        const newOverlay = document.createElement('div');
        newOverlay.id = 'historyOverlay';
        newOverlay.className = 'history-overlay';
        newOverlay.onclick = closeHistory;
        document.body.appendChild(newOverlay);
    }
    
    sidebar.classList.toggle('open');
    document.getElementById('historyOverlay').classList.toggle('show');
}

function closeHistory() {
    document.getElementById('historySidebar').classList.remove('open');
    const overlay = document.getElementById('historyOverlay');
    if (overlay) {
        overlay.classList.remove('show');
    }
}

// Helper functions
function isToday(timestamp) {
    const today = new Date();
    const date = new Date(timestamp);
    return date.toDateString() === today.toDateString();
}

function isYesterday(timestamp) {
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const date = new Date(timestamp);
    return date.toDateString() === yesterday.toDateString();
}

function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    
    if (isToday(timestamp)) {
        return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    } else if (isYesterday(timestamp)) {
        return 'Yesterday ' + date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    } else {
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Simple markdown to HTML converter
function renderMarkdown(text) {
    if (!text) return '';
    
    let html = text;
    
    // Remove source citations like [Source 1], [Source 2], etc.
    html = html.replace(/\[Source\s+\d+\]/gi, '');
    
    // Escape HTML first
    html = html.replace(/&/g, '&amp;')
               .replace(/</g, '&lt;')
               .replace(/>/g, '&gt;');
    
    // Headers
    html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
    html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');
    
    // Bold
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    
    // Italic
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
    
    // Code blocks
    html = html.replace(/```([\s\S]+?)```/g, '<pre><code>$1</code></pre>');
    
    // Inline code
    html = html.replace(/`(.+?)`/g, '<code>$1</code>');
    
    // Lists (unordered)
    html = html.replace(/^\s*[-*+]\s+(.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    
    // Lists (ordered)
    html = html.replace(/^\s*\d+\.\s+(.+)$/gm, '<li>$1</li>');
    
    // Line breaks
    html = html.replace(/\n\n/g, '</p><p>');
    html = html.replace(/\n/g, '<br>');
    
    // Wrap in paragraph if not already wrapped
    if (!html.startsWith('<h') && !html.startsWith('<ul') && !html.startsWith('<ol') && !html.startsWith('<pre')) {
        html = '<p>' + html + '</p>';
    }
    
    return html;
}

