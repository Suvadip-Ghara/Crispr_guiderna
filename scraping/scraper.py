from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

def scrape_idtdna(sequence):
    options = Options()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Path to chromedriver installed in your environment
    service = Service("/usr/bin/chromedriver")  # Adjust path as needed

    driver = webdriver.Chrome(service=service, options=options)
    driver.get("https://sg.idtdna.com/site/order/designtool/index/CRISPR_SEQUENCE")

    try:
        # Open the IDT DNA website
        driver.get("https://sg.idtdna.com/site/order/designtool/index/CRISPR_SEQUENCE")

        # Wait for the species dropdown and select "Danio rerio"
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "speciesDropdown"))
        )
        species_dropdown = driver.find_element(By.ID, "speciesDropdown")
        species_dropdown.click()
        danio_rerio_option = driver.find_element(By.XPATH, "//option[contains(text(), 'Danio rerio')]")
        danio_rerio_option.click()

        # Enter the FASTA sequence
        sequence_input = driver.find_element(By.ID, "sequenceInput")
        sequence_input.clear()
        sequence_input.send_keys(fasta_sequence)

        # Submit the form
        submit_button = driver.find_element(By.ID, "submitButton")
        submit_button.click()

        # Wait for results to load
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "resultsTable"))
        )

        # Scrape the results
        results_table = driver.find_element(By.ID, "resultsTable")
        rows = results_table.find_elements(By.TAG_NAME, "tr")
        results = []
        for row in rows:
            columns = row.find_elements(By.TAG_NAME, "td")
            results.append([col.text for col in columns])

        return results

    except Exception as e:
        print("Error:", e)
        return None

    finally:
        driver.quit()
