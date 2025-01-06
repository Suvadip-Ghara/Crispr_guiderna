from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s', 
    handlers=[
        logging.FileHandler('scraping_debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Species XPaths dictionary
SPECIES_XPATH = {
    'human': "/html/body/div[3]/div[3]/div[3]/div/div[3]/div[4]/div/div[1]/div[1]/div[1]/form/div[3]/div/select/option[1]",
    'mouse': "/html/body/div[3]/div[3]/div[3]/div/div[3]/div[4]/div/div[1]/div[1]/div[1]/form/div[3]/div/select/option[2]", 
    'zebrafish': "/html/body/div[3]/div[3]/div[3]/div/div[3]/div[4]/div/div[1]/div[1]/div[1]/form/div[3]/div/select/option[4]"
}

def save_debug_info(driver, error_msg):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    debug_dir = 'debug_logs'
    os.makedirs(debug_dir, exist_ok=True)
    screenshot_path = os.path.join(debug_dir, f'error_{timestamp}.png')
    driver.save_screenshot(screenshot_path)
    logger.info(f"Screenshot saved: {screenshot_path}")
    source_path = os.path.join(debug_dir, f'page_source_{timestamp}.html')
    with open(source_path, 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    logger.info(f"Page source saved: {source_path}")
    logger.error(f"Error occurred: {error_msg}")
    logger.info(f"Current URL: {driver.current_url}")

def scrape_idtdna(sequence, species='human'):
    logger.info(f"Starting analysis for sequence with species: {species}")
    sequence = sequence.strip().upper()
    if len(sequence) != 20:
        return {"error": "Sequence must be exactly 20 base pairs"}
    fasta_sequence = f">sq\n{sequence}"
    
    # Chrome options for headless mode
    options = Options()
    options.add_argument("--headless=new")  # Enable new headless mode
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    try:
        logger.info("Launching Chrome browser in headless mode...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # Navigate to IDT website
        logger.info("Navigating to IDT website...")
        driver.get("https://sg.idtdna.com/site/order/designtool/index/CRISPR_SEQUENCE")
        
        # Wait for page load and handle cookie consent
        try:
            cookie_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div[8]/div[2]/div/div/div[2]/div/div/button"))
            )
            cookie_button.click()
            logger.info("Cookies accepted")
            time.sleep(2)
        except:
            logger.info("No cookie dialog found")

        # Handle design dialog
        try:
            design_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div[3]/div[3]/div[3]/div/div[3]/div[15]/div/div/div/div/div[3]/button"))
            )
            design_button.click()
            logger.info("Design button clicked")
            time.sleep(2)
        except Exception as e:
            logger.error(f"Error with design dialog: {e}")
            raise

        # Select species
        logger.info(f"Selecting species: {species}")
        try:
            species_dropdown = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div[3]/div[3]/div[3]/div/div[3]/div[4]/div/div[1]/div[1]/div[1]/form/div[3]/div/select"))
            )
            species_dropdown.click()
            time.sleep(1)
            
            species_option = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, SPECIES_XPATH[species]))
            )
            species_option.click()
            time.sleep(1)
            logger.info(f"{species} selected")
        except Exception as e:
            logger.error(f"Error selecting species: {e}")
            raise

        # Enter sequence
        logger.info("Entering sequence...")
        try:
            sequence_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "/html/body/div[3]/div[3]/div[3]/div/div[3]/div[4]/div/div[1]/div[2]/div[1]/div/div[1]/div/div/div/div/div/div[5]/textarea"))
            )
            sequence_input.clear()
            time.sleep(1)
            sequence_input.send_keys(fasta_sequence)
            logger.info(f"Sequence entered: {fasta_sequence}")
        except Exception as e:
            logger.error(f"Error entering sequence: {e}")
            raise

        # Analyze sequence
        logger.info("Analyzing sequence...")
        try:
            check_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div[3]/div[3]/div[3]/div/div[3]/div[4]/div/div[1]/div[1]/div[3]/button[1]"))
            )
            check_button.click()
            logger.info("Analysis started")
            
            # Wait for results
            logger.info("Waiting for results...")
            results = WebDriverWait(driver, 45).until(
                EC.presence_of_element_located((By.XPATH, "/html/body/div[3]/div[3]/div[3]/div/div[3]/div[8]/div[2]/div[2]/div[2]/div/div[1]/div[2]/div[1]/div[1]/table/tbody/tr/td[2]"))
            )
            time.sleep(2)
            logger.info("Results loaded")
            
            # Extract scores
            scores = {
                'sequence': sequence,
                'species': species,
                'on_target_score': None,
                'off_target_score': None
            }
            
            on_target = driver.find_element(By.XPATH, "/html/body/div[3]/div[3]/div[3]/div/div[3]/div[8]/div[2]/div[2]/div[2]/div/div[1]/div[2]/div[1]/div[1]/table/tbody/tr/td[2]").text
            off_target = driver.find_element(By.XPATH, "/html/body/div[3]/div[3]/div[3]/div/div[3]/div[8]/div[2]/div[2]/div[2]/div/div[1]/div[2]/div[1]/div[1]/table/tbody/tr/td[3]").text
            
            scores['on_target_score'] = float(on_target) / 100
            scores['off_target_score'] = float(off_target) / 100
            
            logger.info(f"Analysis complete: {scores}")
            return scores
            
        except Exception as e:
            logger.error(f"Error processing results: {e}")
            save_debug_info(driver, str(e))
            return {"error": str(e)}
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        if 'driver' in locals():
            save_debug_info(driver, str(e))
        return {"error": str(e)}
        
    finally:
        if 'driver' in locals():
            driver.quit()
            logger.info("Browser closed")