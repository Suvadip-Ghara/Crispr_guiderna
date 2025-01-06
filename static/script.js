document.addEventListener('DOMContentLoaded', () => {
    const navLinks = document.querySelectorAll('.nav-item a'); // Updated selector
    const content = document.getElementById('content');
  
    navLinks.forEach(link => {
      link.addEventListener('click', async (event) => {
        event.preventDefault();
        const section = link.getAttribute('data-section');
        await loadSection(section);
      });
    });
  
    async function loadSection(section) {
      try {
        const response = await fetch(`/static/${section}.html`);
        if (!response.ok) {
          throw new Error(`Failed to load section: ${section}`);
        }
        const html = await response.text();
        content.innerHTML = html;
        initializeInteractiveFeatures();
      } catch (error) {
        console.error(error);
      }
    }

    // Load the default section
    loadSection('about');

    function initializeInteractiveFeatures() {
        const analyzeForm = document.getElementById("analyze-form");
        const designForm = document.getElementById("design-form");
        const loadingSpinner = document.getElementById("loading-spinner");
        const resultsDiv = document.getElementById("results");
        const downloadLink = document.getElementById("download-link");

        if (analyzeForm) {
            handleFormSubmission(analyzeForm, "/analyze");
        }

        if (designForm) {
            handleFormSubmission(designForm, "/design");
        }

        function handleFormSubmission(form, action) {
            form.addEventListener("submit", async (event) => {
                event.preventDefault();
                
                // Show loading state
                if (loadingSpinner) loadingSpinner.style.display = "block";
                if (resultsDiv) resultsDiv.innerHTML = "";
                if (downloadLink) downloadLink.style.display = "none";

                try {
                    const formData = new FormData(event.target);
                    const response = await fetch(action, {
                        method: "POST",
                        body: formData,
                    });

                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }

                    const contentType = response.headers.get("content-type");
                    if (contentType && contentType.includes("text/html")) {
                        const html = await response.text();
                        if (resultsDiv) resultsDiv.innerHTML = html;
                        if (downloadLink) downloadLink.style.display = "block";
                        initializeInteractiveFeatures(); // Initialize features after loading results
                    } else {
                        throw new Error("Unexpected response format");
                    }
                } catch (error) {
                    if (resultsDiv) resultsDiv.innerHTML = `<div class="error-message">Error: ${error.message}</div>`;
                    if (downloadLink) downloadLink.style.display = "none";
                } finally {
                    if (loadingSpinner) loadingSpinner.style.display = "none";
                }
            });

            // Add sequence validation
            const sequenceInput = form.querySelector('textarea[name="sequence"]') || form.querySelector('textarea[name="dna-sequence"]');
            if (sequenceInput) {
                sequenceInput.addEventListener('input', (e) => {
                    const text = e.target.value;
                    const lines = text.split('\n');
                    
                    // Allow first line to start with '>' (FASTA header)
                    const headerValid = lines[0].startsWith('>');
                    // Check sequence lines contain only valid DNA bases
                    const sequenceValid = lines.slice(1).every(line => 
                        /^[ATCG\s]*$/.test(line.toUpperCase())
                    );
                    
                    e.target.setCustomValidity(
                        (headerValid && sequenceValid) ? '' : 
                        'Invalid format. First line must start with > and sequence must contain only A, T, C, G bases'
                    );
                });
            }
        }
    }

    // Function to create visual results display
    function createResultsDisplay(data) {
        if (!data.results) return '<div class="error-message">No results available</div>';
        
        const { sequence, on_target_score, off_target_score } = data.results;
        const overallScore = (on_target_score + off_target_score) / 2;
        
        return `
            <div class="results-card">
                <h3>Analysis Results</h3>
                <div class="sequence-display">
                    <label>Guide Sequence:</label>
                    <div class="sequence-text">
                        <code>${sequence}</code>
                        <button class="copy-btn" data-sequence="${sequence}" title="Copy sequence">
                            <i class="fas fa-copy"></i>
                        </button>
                    </div>
                </div>
                <div class="scores-container">
                    <div class="score-item">
                        <label>On-Target Score:</label>
                        <div class="score-bar-container">
                            <div class="score-bar" style="width: ${on_target_score * 100}%"></div>
                            <span class="score-value">${(on_target_score * 100).toFixed(1)}%</span>
                        </div>
                    </div>
                    <div class="score-item">
                        <label>Off-Target Score:</label>
                        <div class="score-bar-container">
                            <div class="score-bar" style="width: ${off_target_score * 100}%"></div>
                            <span class="score-value">${(off_target_score * 100).toFixed(1)}%</span>
                        </div>
                    </div>
                    <div class="score-item">
                        <label>Overall Quality:</label>
                        <div class="score-bar-container">
                            <div class="score-bar" style="width: ${overallScore * 100}%"></div>
                            <span class="score-value">${(overallScore * 100).toFixed(1)}%</span>
                        </div>
                    </div>
                </div>
                <div class="action-buttons">
                    <button class="download-btn" onclick="downloadResults('csv')">
                        Download CSV
                    </button>
                    <button class="download-btn" onclick="downloadResults('json')">
                        Export JSON
                    </button>
                </div>
            </div>
        `;
    }

    // Initialize interactive features
    function initializeInteractiveFeatures() {
        // Copy button functionality
        document.querySelectorAll('.copy-btn').forEach(button => {
            button.addEventListener('click', () => {
                const sequence = button.dataset.sequence;
                navigator.clipboard.writeText(sequence).then(() => {
                    showToast('Sequence copied to clipboard!');
                });
            });
        });
    }

    // Toast notification
    function showToast(message) {
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(() => {
            toast.classList.add('show');
            setTimeout(() => {
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 300);
            }, 2000);
        }, 100);
    }

    // Download functionality
    window.downloadResults = function(format) {
        const data = {
            sequence: document.querySelector('.sequence-text code').textContent,
            onTargetScore: parseFloat(document.querySelector('.score-item:nth-child(1) .score-value').textContent) / 100,
            offTargetScore: parseFloat(document.querySelector('.score-item:nth-child(2) .score-value').textContent) / 100,
            overallScore: parseFloat(document.querySelector('.score-item:nth-child(3) .score-value').textContent) / 100
        };

        let content, filename, type;
        if (format === 'csv') {
            content = `Sequence,On-Target Score,Off-Target Score,Overall Score\n${data.sequence},${data.onTargetScore},${data.offTargetScore},${data.overallScore}`;
            filename = 'crispr-analysis.csv';
            type = 'text/csv';
        } else {
            content = JSON.stringify(data, null, 2);
            filename = 'crispr-analysis.json';
            type = 'application/json';
        }

        const blob = new Blob([content], { type });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        showToast(`Downloaded ${filename}`);
    };
});