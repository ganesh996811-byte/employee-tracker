import os
import sys
import time
import subprocess
import sqlite3
import urllib.request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configure database environment variable for testing
TEST_DB = "test_productivity.db"
os.environ["PRODUCTIVITY_DB"] = TEST_DB

def cleanup_test_db():
    """Removes the test database file if it exists."""
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
            print(f"Removed old test database: {TEST_DB}")
        except Exception as e:
            print(f"Failed to remove test database: {e}")

def wait_for_server(url, timeout=15):
    """Waits for the Streamlit server to become responsive."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen(url) as response:
                if response.status == 200:
                    print("Streamlit server is ready!")
                    return True
        except Exception:
            time.sleep(0.5)
    print("Streamlit server did not become responsive in time.")
    return False

def run_browser_test():
    cleanup_test_db()
    
    # Pre-populate database with test employee
    from database import init_db, add_employee
    init_db(TEST_DB)
    add_employee("Test Engineer", "test@company.com", "Developer", 50.0, 40, TEST_DB)
    
    # 1. Start Streamlit server as a subprocess
    print("Starting Streamlit server on port 8501...")
    server_process = subprocess.Popen(
        ["streamlit", "run", "app.py", "--server.port=8501", "--server.headless=true"],
        env=os.environ.copy()
    )
    
    # Ensure server process is terminated on exit
    try:
        if not wait_for_server("http://localhost:8501"):
            server_process.terminate()
            sys.exit(1)
            
        # 2. Configure Selenium Webdriver
        print("Configuring headless Chrome...")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        
        try:
            print("Opening http://localhost:8501...")
            driver.get("http://localhost:8501")
            
            # Wait for main container to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "app-title"))
            )
            print("Page loaded successfully.")
            
            # 3. Create a task via sidebar
            print("Locating task creation fields...")
            title_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Write code review...']"))
            )
            desc_input = driver.find_element(By.CSS_SELECTOR, "textarea[placeholder='Check performance metrics...']")
            submit_button = driver.find_element(By.XPATH, "//button[contains(., 'Create Task')]")
            
            print("Creating test task assigned to 'Test Engineer'...")
            title_input.send_keys("Selenium Test Task")
            desc_input.send_keys("This task was automatically created to verify timer logic.")
            submit_button.click()
            
            # Wait for task card to appear on workspace
            print("Verifying task creation on board...")
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Selenium Test Task')]"))
            )
            print("Task successfully created and rendered.")
            
            # 4. Start the active timer
            print("Starting timer for the task...")
            start_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Focus')]"))
            )
            start_button.click()
            
            # 5. Verify timer is active and ticking
            print("Checking active timer display...")
            time.sleep(3)  # Give components iframe time to render
            
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            print(f"Number of iframes found on page: {len(iframes)}")
            
            if not iframes:
                print("No iframes found. Waiting a bit longer...")
                time.sleep(3)
                iframes = driver.find_elements(By.TAG_NAME, "iframe")
                print(f"Number of iframes found after second wait: {len(iframes)}")
            
            if not iframes:
                raise TimeoutException("No iframe found for stopwatch component.")
            
            iframe = iframes[0]
            
            # Switch to iframe to read JS clock
            driver.switch_to.frame(iframe)
            timer_display = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "timer-display"))
            )
            
            initial_time = timer_display.text
            print(f"Initial timer text: {initial_time}")
            
            # Wait for ticking
            print("Waiting 5 seconds for timer to tick...")
            time.sleep(5)
            
            ticked_time = timer_display.text
            print(f"Ticked timer text: {ticked_time}")
            
            # Switch back to main page context
            driver.switch_to.default_content()
            
            assert initial_time != ticked_time, "Timer display text did not change/tick!"
            print("Timer is ticking correctly in browser!")
            
            # 6. Stop the timer
            print("Stopping active timer...")
            stop_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Stop Timer & Save Log')]"))
            )
            stop_button.click()
            
            print("Waiting for database update...")
            time.sleep(2)
            
            # 7. Test manual time logging on same task
            print("Expanding manual log form...")
            expander = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//summary[contains(., 'Add Time')]"))
            )
            expander.click()
            time.sleep(1) # Wait for animation
            
            print("Filing manual logging fields...")
            # Retrieve inputs inside this task expander container ONLY
            expander_parent = expander.find_element(By.XPATH, "..")
            minutes_input = expander_parent.find_element(By.CSS_SELECTOR, "input[type='number']")
            save_log_button = expander_parent.find_element(By.XPATH, ".//button[contains(., 'Save Log')]")
            
            # Overwrite Streamlit default number input value using select-all shortcut
            minutes_input.send_keys(Keys.CONTROL + "a")
            minutes_input.send_keys(Keys.BACKSPACE)
            minutes_input.send_keys("90")
            minutes_input.send_keys(Keys.ENTER)
            time.sleep(0.5)
            
            print("Clicking save log button...")
            save_log_button.click()
            
            print("Waiting for manual log update...")
            time.sleep(2)
            
            # 8. Check sqlite database for logged times and employee assignment
            print("Verifying SQLite records...")
            conn = sqlite3.connect(TEST_DB)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Verify employee assignment
            cursor.execute("SELECT employee_name FROM tasks WHERE title = 'Selenium Test Task'")
            task_row = cursor.fetchone()
            assert task_row is not None, "Task was not found in database!"
            print(f"Task employee assignment in database: {task_row['employee_name']}")
            assert task_row['employee_name'] == "Test Engineer", f"Incorrect employee assigned: {task_row['employee_name']}"
            
            # Verify stopwatch log exists
            cursor.execute("SELECT duration_minutes FROM time_logs ORDER BY id ASC LIMIT 1")
            stopwatch_log = cursor.fetchone()
            assert stopwatch_log is not None, "No active stopwatch time log found!"
            print(f"Recorded stopwatch duration: {stopwatch_log['duration_minutes']:.4f} minutes")
            assert stopwatch_log['duration_minutes'] > 0.0, "Stopwatch duration did not record correct time."
            
            # Verify manual log of 90 minutes exists
            cursor.execute("SELECT duration_minutes FROM time_logs WHERE duration_minutes = 90.0")
            manual_log = cursor.fetchone()
            assert manual_log is not None, "Manual log of 90 minutes was not written to database!"
            print("Recorded manual log duration: 90.0 minutes")
            
            conn.close()
            print("Database verification passed successfully! Timer logic and manual logs verified.")
            
        except Exception as e:
            print(f"\n[ERROR] Test failed: {e}")
            screenshot_path = "test_failure.png"
            try:
                driver.save_screenshot(screenshot_path)
                print(f"Screenshot saved to {screenshot_path}")
            except Exception as se:
                print(f"Failed to save screenshot: {se}")
            sys.exit(1)
        finally:
            print("Closing browser...")
            try:
                driver.quit()
            except Exception:
                pass
            
    finally:
        print("Stopping Streamlit server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
        print("Server stopped.")
        
        # Windows file unlock wait
        time.sleep(2)
        cleanup_test_db()
        
    print("\n[SUCCESS] All tests passed successfully!")
    sys.exit(0)

if __name__ == "__main__":
    run_browser_test()
