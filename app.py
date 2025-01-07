from flask import Flask, render_template, request, jsonify
import logging
import re
import os
from scraping.scraper import scrape_idtdna

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__, 
    template_folder=os.path.abspath('templates'),
    static_folder=os.path.abspath('static')
)

def validate_sequence(sequence):
    """Validate FASTA format and sequence content"""
    lines = sequence.strip().split('\n')
    if not lines:
        return False, "Empty sequence"
    if not lines[0].startswith('>'):
        return False, "First line must start with > (FASTA format)"
    if len(lines) < 2:
        return False, "No sequence provided after header"
    sequence = ''.join(lines[1:]).replace('\r', '').replace('\n', '').upper()
    if not re.match('^[ATCG]+$', sequence):
        return False, "Sequence must contain only A, T, C, G bases"
    if len(sequence) < 20:
        return False, "Sequence must be at least 20 base pairs"
    return True, sequence

def find_guide_rnas(dna_sequence):
    """Find guide RNAs in the DNA sequence"""
    guide_rnas = []
    # Updated PAM pattern for exact 20bp guide RNA + NGG PAM
    pam_pattern = re.compile(r'(?=(.{20})([ATCG]GG))')
    
    def is_valid_guide_rna(sequence):
        """Check if the guide RNA sequence is valid (not repetitive)"""
        # Check for repetitive sequences
        if re.match(r'^(A+|T+|C+|G+)$', sequence):
            return False
        # Check for alternating patterns like ATATATAT
        if re.match(r'^(?:AT|TA|GC|CG)+$', sequence):
            return False
        return True
    
    # Search for PAM on the sense strand
    for match in pam_pattern.finditer(dna_sequence):
        spacer = match.group(1)  # Exact 20bp guide RNA
        pam = match.group(2)     # NGG PAM sequence
        
        if not is_valid_guide_rna(spacer):
            continue
            
        gc_content = (spacer.count('G') + spacer.count('C')) / 20 * 100
        # Filter out guides with GC content outside 40-60%
        if not (40 <= gc_content <= 60):
            continue
            
        guide_rnas.append({
            'sequence': spacer,
            'pam': pam,
            'start_position': match.start() + 1,
            'end_position': match.start() + 22,
            'strand': 'Sense',
            'gc_content': round(gc_content, 2)
        })
    
    # Search for PAM on the antisense strand
    reverse_complement = dna_sequence.translate(str.maketrans('ATCG', 'TAGC'))[::-1]
    for match in pam_pattern.finditer(reverse_complement):
        spacer = match.group(1)  # Exact 20bp guide RNA
        pam = match.group(2)     # NGG PAM sequence
        
        if not is_valid_guide_rna(spacer):
            continue
            
        gc_content = (spacer.count('G') + spacer.count('C')) / 20 * 100
        # Filter out guides with GC content outside 40-60%
        if not (40 <= gc_content <= 60):
            continue
            
        guide_rnas.append({
            'sequence': spacer,
            'pam': pam,
            'start_position': len(dna_sequence) - match.start() - 22 + 1,
            'end_position': len(dna_sequence) - match.start(),
            'strand': 'Antisense',
            'gc_content': round(gc_content, 2)
        })
    
    # Sort guide RNAs by strand (Sense first, then Antisense) and position
    guide_rnas.sort(key=lambda x: (x['strand'] != 'Sense', x['start_position']))
    
    return guide_rnas

@app.route("/")
def index():
    logger.info("Accessing index page")
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        sequence = request.form.get("sequence", "")
        species = request.form.get("species", "human")
        
        if not sequence:
            return render_template('results.html', error="No sequence provided")
        
        # Validate sequence
        is_valid, result = validate_sequence(sequence)
        if not is_valid:
            return render_template('results.html', error=result)
            
        # Get scraping results
        results = scrape_idtdna(result, species)
        
        if 'error' in results:
            return render_template('results.html', error=results['error'])
            
        # Pass results as a dictionary
        return render_template('results.html', guide_rnas=results)
                             
    except Exception as e:
        return render_template('results.html', error=f"An error occurred during analysis: {str(e)}")

@app.route("/design", methods=["POST"])
def design():
    try:
        logger.info("Starting guide RNA design...")
        dna_sequence = request.form.get("dna-sequence", "")
        logger.info(f"Received DNA sequence: {dna_sequence}")
        
        if not dna_sequence:
            logger.error("No DNA sequence provided")
            return render_template('design_results.html', error="No DNA sequence provided")
        
        # Validate DNA sequence
        is_valid, result = validate_sequence(dna_sequence)
        if not is_valid:
            logger.error(f"Invalid DNA sequence: {result}")
            return render_template('design_results.html', error=result)
        
        # Find guide RNAs
        guide_rnas = find_guide_rnas(result)
        logger.info(f"Found {len(guide_rnas)} guide RNAs")
        
        # Render results template
        return render_template('design_results.html', guide_rnas=guide_rnas)
    
    except Exception as e:
        logger.error(f"Error during guide RNA design: {str(e)}")
        return render_template('design_results.html', 
                             error=f"An error occurred during guide RNA design: {str(e)}")

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {str(e)}")
    return render_template('results.html', 
                         error="Internal server error. Please try again later.")

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)