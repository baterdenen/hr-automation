import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoAlertPresentException, ElementClickInterceptedException
import time
import logging
from datetime import datetime
from pathlib import Path

# Google Sheets
try:
    import gspread
    from google.oauth2.service_account import Credentials
    SHEETS_AVAILABLE = True
except ImportError:
    SHEETS_AVAILABLE = False

class CourseAutomation:
    def __init__(self, spreadsheet_id=None):
        # Browser setup
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 10)
        
        # Logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
        # Google Sheets setup
        self.sheets_client = None
        self.spreadsheet_id = spreadsheet_id
        if spreadsheet_id and SHEETS_AVAILABLE:
            self.setup_sheets()

    def setup_sheets(self):
        """Setup Google Sheets connection"""
        self.logger.info("Attempting to set up Google Sheets...")
        try:
            # Check for credentials in environment variable first (for GitHub Actions)
            creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
            if creds_json:
                import json
                import tempfile
                # Write credentials to temp file
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
                    f.write(creds_json)
                    creds_file = f.name
            else:
                # Fall back to local credentials.json file
                creds_file = Path(__file__).parent / "credentials.json"
                if not creds_file.exists():
                    self.logger.error("FATAL: credentials.json not found in the script directory.")
                    self.sheets_client = None
                    return
                creds_file = str(creds_file)
            
            self.logger.info("Found credentials. Authorizing...")
            creds = Credentials.from_service_account_file(
                creds_file, 
                scopes=gspread.auth.DEFAULT_SCOPES
            )
            self.sheets_client = gspread.authorize(creds)
            self.logger.info("✓ Google Sheets connected successfully")
        except Exception as e:
            self.logger.error(f"FATAL: Google Sheets setup failed. Error: {e}")
            self.sheets_client = None

    def login(self, username, password):
        """Login to HR system"""
        self.logger.info("Logging in...")
        self.driver.get("https://hr.hdc.gov.mn/login")
        time.sleep(2)
        
        self.wait.until(EC.element_to_be_clickable((By.NAME, "username"))).send_keys(username)
        self.wait.until(EC.element_to_be_clickable((By.NAME, "password"))).send_keys(password)
        self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))).click()
        time.sleep(3)
        self.logger.info("✓ Login successful")

    def click_safe(self, element):
        """Safe click with JS fallback"""
        try:
            element.click()
            return True
        except:
            try:
                self.driver.execute_script("arguments[0].click();", element)
                return True
            except:
                return False

    def close_modal(self):
        """Close any open modal"""
        try:
            WebDriverWait(self.driver, 2).until_not(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".modal.fade.in, .modal.show"))
            )
            time.sleep(0.3)
        except:
            pass

    def register_participant(self, checkbox):
        """Register a participant"""
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)
            time.sleep(0.5)
            
            if not self.click_safe(checkbox):
                return False
            
            time.sleep(1)
            confirm_btn = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.ID, "confirm_btn"))
            )
            
            if not self.click_safe(confirm_btn):
                return False
            
            time.sleep(1)
            
            # Handle alerts
            try:
                alert = WebDriverWait(self.driver, 2).until(EC.alert_is_present())
                alert.accept()
            except:
                pass
            
            self.close_modal()
            return True
        except Exception as e:
            self.logger.error(f"Registration failed: {e}")
            return False

    def extract_email(self, user_link):
        """Extract email from user profile"""
        name = "N/A"
        try:
            name = user_link.text.strip()
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", user_link)
            time.sleep(0.3)
            
            if not self.click_safe(user_link):
                self.logger.warning("  ✗ Failed to click user link")
                self.close_modal()
                return name, None
            
            time.sleep(2)  # Simple delay to let modal content load
            
            # Find email input
            email = None
            try:
                email_input = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'input[value*="@"]'))
                )
                email_value = email_input.get_attribute('value')
                if email_value and '@' in email_value:
                    email = email_value.replace('"', '').replace("'", '').strip()
            except TimeoutException:
                self.logger.warning(f"  ✗ No email input found for {name}")

            # Close modal
            try:
                close_btn = self.driver.find_element(By.CSS_SELECTOR, 'button.close')
                self.click_safe(close_btn)
            except:
                pass
            
            self.close_modal()
            return name, email
        except Exception as e:
            self.logger.error(f"  ✗ Email extraction failed for {name}: {e}")
            self.close_modal()
            return name, None

    def save_to_sheets(self, sheet_name, course_id, participants):
        """Save participants to Google Sheets, avoiding duplicates."""
        if not self.sheets_client or not participants:
            self.logger.info("No participants or Sheets client available to save.")
            return
        
        try:
            spreadsheet = self.sheets_client.open_by_key(self.spreadsheet_id)
            
            # Get or create sheet
            try:
                sheet = spreadsheet.worksheet(sheet_name)
            except gspread.WorksheetNotFound:
                self.logger.info(f"Worksheet '{sheet_name}' not found. Creating it.")
                sheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=10)
                headers = ['Course ID', 'Name', 'Email', 'Status', 'Date', 'Email Sent']
                sheet.update('A1:F1', [headers])

            # Get existing emails to prevent duplicates. Filter out empty strings.
            existing_emails = set(filter(None, sheet.col_values(3)))

            # Filter for new participants
            new_participants = [p for p in participants if p['email'] and p['email'] not in existing_emails]
            
            if not new_participants:
                self.logger.info("✓ No new participants to add to Google Sheets (all found are already present).")
                return

            # Prepare data for new participants
            rows = [[
                str(p['course_id']),
                p['name'],
                p['email'],
                p['status'],
                p['date'],
                'Pending'
            ] for p in new_participants]
            
            # Append
            sheet.append_rows(rows)
            self.logger.info(f"✓ Saved {len(rows)} new participants to Google Sheets")
            
        except Exception as e:
            self.logger.error(f"Failed to save to Sheets: {e}")

    def process_course(self, course_id, sheet_name):
        """Process a single course: register new participants and extract all emails."""
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"Processing Course: {course_id} (Sheet: {sheet_name})")
        self.logger.info(f"{'='*60}")
        
        url = f"https://hr.hdc.gov.mn/trainings/{course_id}?accordion=student"
        self.driver.get(url)
        time.sleep(3)
        
        participants = []
        
        # --- Step 1: Register all pending participants efficiently (with pagination sweeps) ---
        self.logger.info("--- Checking for pending participants to register (with pagination) ---")

        def click_page(page_number):
            """Click a pagination button by its pagenumber attribute."""
            # Strategy 1: Direct Page Number
            try:
                btn = WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located((
                        By.CSS_SELECTOR,
                        f".page-navigation input.number-button[pagenumber='{page_number}']"
                    ))
                )
                if btn.is_enabled() and btn.get_attribute("disabled") is None:
                    self.click_safe(btn)
                    time.sleep(3)
                    return True
            except TimeoutException:
                pass # Fall through to Strategy 2
            except Exception:
                pass

            # Strategy 2: "Next" button (if page number button is hidden/missing)
            try:
                # Look for inputs with value ">" or "Next"
                inputs = self.driver.find_elements(By.CSS_SELECTOR, ".page-navigation input")
                for inp in inputs:
                    val = inp.get_attribute("value")
                    if val and (">" in val or "Next" in val):
                        if inp.is_enabled() and inp.get_attribute("disabled") is None:
                            self.logger.info(f"  Using 'Next' button to reach page {page_number}...")
                            self.click_safe(inp)
                            time.sleep(3)
                            return True
            except Exception:
                pass
                
            return False

        initial_pending_count = 0

        while True:
            any_registered_in_sweep = False

            # Try pages 1,2,3,... in this sweep
            page_number = 1
            while True:
                # For page 1, reload the course URL to be safe
                if page_number == 1:
                    self.driver.get(url)
                    time.sleep(2)
                else:
                    if not click_page(page_number):
                        break

                self.logger.info(f"Processing page {page_number} for pending participants...")

                while True:
                    pending_icons = self.driver.find_elements(
                        By.CSS_SELECTOR,
                        'i.icon-checkbox-checked2[onclick*="single"]'
                    )

                    if not pending_icons:
                        self.logger.info("  ✓ No more pending participants on this page.")
                        break

                    pending_icon = pending_icons[0]
                    self.logger.info(
                        f"  Registering participant on page {page_number} "
                        f"(remaining on this page: {len(pending_icons)})..."
                    )

                    # Find the table row for this participant
                    try:
                        row = pending_icon.find_element(By.XPATH, "./ancestor::tr")
                        user_link = row.find_element(By.CSS_SELECTOR, 'a[onclick*="dialogUserInfo"]')
                    except Exception as e:
                        self.logger.warning(f"    ✗ Could not find row/user link for pending participant: {e}")
                        user_link = None

                    # Extract email FIRST (before registration invalidates the row)
                    name, email = "N/A", None
                    if user_link:
                        name, email = self.extract_email(user_link)
                    
                    # Re-fetch pending icon to avoid StaleElementReferenceException
                    # (The modal opening/closing might have refreshed the DOM)
                    try:
                        pending_icons = self.driver.find_elements(
                            By.CSS_SELECTOR,
                            'i.icon-checkbox-checked2[onclick*="single"]'
                        )
                        if not pending_icons:
                            break
                        pending_icon = pending_icons[0]
                    except:
                        pass

                    if self.register_participant(pending_icon):
                        initial_pending_count += 1
                        any_registered_in_sweep = True
                        self.logger.info("    ✓ Registered successfully.")
                        time.sleep(1)

                        if email:
                            participants.append({
                                'course_id': course_id,
                                'name': name,
                                'email': email,
                                'status': 'NEW',
                                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })
                            self.logger.info(f"    ✓ Email captured: {name} - {email}")
                        else:
                            self.logger.warning(f"    ✗ Email not found for: {name}")

                        # After registration on page 2, the site jumps to page 1.
                        # Break so the outer logic can restart the sweep.
                        break
                    else:
                        self.logger.warning("    ✗ Registration failed for this participant. Refreshing course page.")
                        self.driver.get(url)
                        time.sleep(3)
                        break

                # If we registered someone, page state likely changed; restart sweep.
                if any_registered_in_sweep:
                    break

                page_number += 1

            # If a full sweep registered nobody, we're done.
            if not any_registered_in_sweep:
                break

        if initial_pending_count == 0:
            self.logger.info("✓ No pending participants to register across all pages.")
        else:
            self.logger.info(
                f"✓ All pending participants have been processed across pages. "
                f"Total registered: {initial_pending_count}."
            )
            # Ensure we are on page 1 before email extraction
            click_page(1)
            time.sleep(2)

        # --- Step 2: Extract emails from ONLY newly registered participants ---
        self.logger.info("\n--- Email extraction performed during registration; skipping separate pass ---")
        # No extra extraction here.

        # --- Step 3: Save unique participants to Google Sheets ---
        if participants:
            self.save_to_sheets(sheet_name, course_id, participants)
        
        self.logger.info(f"\n✅ Course {course_id} Complete: Found {len(participants)} total participants.")
        return participants

    def close(self):
        """Close browser"""
        self.driver.quit()

def main():
    # ========== CONFIGURATION ==========
    # Get credentials from environment variables (for GitHub Actions) or use defaults
    USERNAME = os.getenv('HR_USERNAME', "ЖЯ87101312")
    PASSWORD = os.getenv('HR_PASSWORD', "MqameaSd63WMrqd")
    SPREADSHEET_ID = os.getenv('SPREADSHEET_ID', "1iKkOvTrujkfvShB0npGnyNktIBVuZU6iU9RBgc4DZME")
    COURSES = {
        8473: "Chest pain",
        8469: "Antibiotic",
        8472: "Kidney",
        8474: "ECG",
        8470: "Zurkh em",
        8475: "Glucocorticoid",
        8471: "Hypertension"

    }
    # ===================================
    
    automation = CourseAutomation(spreadsheet_id=SPREADSHEET_ID)
    
    try:
        automation.login(USERNAME, PASSWORD)
        
        all_participants = []
        for course_id, sheet_name in COURSES.items():
            try:
                participants = automation.process_course(course_id, sheet_name)
                all_participants.extend(participants)
            except Exception as e:
                automation.logger.error(f"Course {course_id} failed: {e}")
        
        # Summary
        print("\n" + "="*60)
        print("🎉 ALL COURSES PROCESSED")
        print("="*60)
        print(f"Total new participants found across all courses: {len(all_participants)}")
        if SPREADSHEET_ID:
            print(f"📊 View: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
        print("="*60)
        
    except Exception as e:
        automation.logger.error(f"Fatal error: {e}")
    finally:
        time.sleep(2)
        automation.close()

if __name__ == "__main__":
    main()
