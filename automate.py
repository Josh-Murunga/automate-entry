from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import sys
import time
import traceback

# Configure logging
def log_error(message):
    with open("error_log.txt", "a") as f:
        f.write(f"{time.ctime()} - {message}\n")

try:
    df = pd.read_excel("icd11_concepts.xlsx")
    print("Excel file loaded successfully")
except Exception as e:
    print(f"Error loading Excel file: {str(e)}")
    log_error(f"Excel load error: {traceback.format_exc()}")
    sys.exit()

try:
    driver = webdriver.Chrome()
    print("Browser launched successfully")
except Exception as e:
    print(f"Failed to start browser: {str(e)}")
    log_error(f"Browser start error: {traceback.format_exc()}")
    sys.exit()

try:
    # Login process with explicit steps
    print("Attempting login...")
    driver.get("https://ba.kenyahmis.org/openmrs/spa/login")
    
    # Break down login steps
    username = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "username"))
    )
    continue_button = driver.find_element(By.XPATH, "//button[@type='submit']")
    username.send_keys("Quality")
    continue_button.click()
    print("Username entered")

    password = driver.find_element(By.ID, "password")
    password.send_keys("Quality123")
    print("Password entered")
    
    login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
    login_button.click()
    print("Login button clicked")
    
    # Verify login success
    WebDriverWait(driver, 30).until(
        EC.url_contains("/openmrs/spa/home")
    )
    print("Login successful")

    # Main workflow
    for index, row in df.iterrows():
        try:
            print(f"\nProcessing row {index+2}: {row['concept_name'][:20]}...")
            
            driver.get("https://ba.kenyahmis.org/openmrs/dictionary/concept.form")
            th_element = driver.find_element(By.XPATH, "//th[contains(text(), 'Fully Specified Name')]")
            is_visible = th_element.is_displayed()
            print("Concept form loaded")

            # Form interaction
            name_field = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "namesByLocale[en].name"))
            )
            name_field.clear()
            name_field.send_keys(row['concept_name'])
            print("Concept name entered")

            # Error handling
            try:
                error = WebDriverWait(driver, 2).until(
                    EC.visibility_of_element_located((By.XPATH, "//*[contains(text(), 'Fully specified name must be unique')]"))
                )
                print(f"Duplicate found at row {index+2} - skipping")
                df.at[index, 'concept_id'] = "DUPLICATE"
                df.at[index, 'uuid'] = "DUPLICATE"
                continue
            except:
                print("No duplicate error detected")

            # Dropdown handling
            Select(driver.find_element(By.ID, "conceptClass")).select_by_visible_text("Anatomy")
            print("Anatomy selected")
            Select(driver.find_element(By.ID, "datatype")).select_by_visible_text("N/A")
            print("N/A selected")

            # Save handling
            save_button = driver.find_element(By.XPATH, "//input[@type='submit' and @name='action' and @value='Save and Continue']")
            save_button.click()
            print("Save clicked")  

            time.sleep(2)    
            
            # Success handling
            concept_id = WebDriverWait(driver, 20).until(
                EC.visibility_of_element_located((By.XPATH, "//th[contains(text(), 'Id')]/following-sibling::td"))
            ).text
            uuid = driver.find_element(By.XPATH, 
                "//th[contains(text(), 'UUID')]/following-sibling::td"
            ).text
            print(f"Success! Concept ID: {concept_id}, UUID: {uuid[:8]}...")
            
            df.at[index, 'concept_id'] = concept_id
            df.at[index, 'uuid'] = uuid

            time.sleep(1)  # Small delay for page load

        except Exception as e:
            print(f"Error processing row {index+2}: {str(e)}")
            log_error(f"Row {index+2} error: {traceback.format_exc()}")
            df.at[index, 'concept_id'] = "ERROR"
            df.at[index, 'uuid'] = "ERROR"
            continue
        
except Exception as e:
    print(f"\nCRITICAL ERROR: {str(e)}")
    log_error(f"Main error: {traceback.format_exc()}")
    print("Full traceback saved to error_log.txt")

finally:
    print("\nCleaning up...")
    df.to_excel("updated_icd11_concepts.xlsx", index=False)
    print("Excel file saved")
    driver.quit()
    print("Browser closed")
    input("Press Enter to exit...")  # Keeps window open on Windows