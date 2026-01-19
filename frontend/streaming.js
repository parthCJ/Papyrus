// Streaming query handler
async function askQuestionStream(query, topK, bm25Weight, vectorWeight, promptTemplate, conversationItem) {
    const startTime = Date.now();
    
    const response = await fetch(`${API_BASE}/query/stream`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            query: query,
            top_k: topK,
            bm25_weight: bm25Weight,
            vector_weight: vectorWeight,
            prompt_template: promptTemplate,
            include_sources: false
        })
    });
    
    if (!response.ok || !response.body) {
        throw new Error('Streaming not supported');
    }
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let fullAnswer = '';
    let retrievalTime = 0;
    let generationTime = 0;
    
    const answerTextDiv = conversationItem.querySelector('.conversation-answer-text');
    const timingSpan = conversationItem.querySelector('.conversation-timing');
    answerTextDiv.innerHTML = '';
    
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
            if (line.startsWith('data: ')) {
                try {
                    const data = JSON.parse(line.substring(6));
                    
                    if (data.type === 'metadata') {
                        retrievalTime = data.retrieval_time;
                    } else if (data.type === 'answer') {
                        fullAnswer += data.content;
                        answerTextDiv.innerHTML = renderMarkdown(fullAnswer);
                        conversationItem.scrollIntoView({ behavior: 'smooth', block: 'end' });
                    } else if (data.type === 'timing') {
                        generationTime = data.generation_time;
                        const totalTime = ((Date.now() - startTime) / 1000).toFixed(2);
                        timingSpan.textContent = `Retrieval: ${retrievalTime.toFixed(2)}s | Generation: ${generationTime.toFixed(2)}s | Total: ${totalTime}s`;
                    } else if (data.type === 'done') {
                        showStatus('queryStatus', `Answer generated in ${((Date.now() - startTime) / 1000).toFixed(2)}s`, 'success');
                        
                        // Clear query input
                        document.getElementById('queryInput').value = '';
                        
                        // Save to history
                        addToHistory({
                            query: query,
                            answer: fullAnswer,
                            sources: [],
                            top_k: topK,
                            bm25_weight: bm25Weight,
                            vector_weight: vectorWeight,
                            prompt_template: promptTemplate,
                            response_time: parseFloat(((Date.now() - startTime) / 1000).toFixed(2))
                        });
                    } else if (data.type === 'error') {
                        answerTextDiv.textContent = `Error: ${data.message}`;
                        showStatus('queryStatus', `Error: ${data.message}`, 'error');
                    }
                } catch (e) {
                    // Skip invalid JSON
                }
            }
        }
    }
}
