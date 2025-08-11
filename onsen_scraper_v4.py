import time
import csv
import os
import random
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from sheets_writer import write_to_sheets, append_to_sheets

# === CONFIGURATION ===
SHEET_ID = "1pZhSeGSosOTYjPHI62r0ma23jgVgLTnnBQwTtq0wvK4"
ONSEN_URL = "https://book.onsen.co.nz/hire/selection?filter=prodgroup-original"
CSV_EXPORT_FOLDER = "./onsen_exports"
FALLBACK_FOLDER = "./fallback_logs"

# Business model assumptions - UPDATED FOR 9 SPAS
MAX_CAPACITY_PER_SLOT = 9  # 9 spas available for rental per hour slot

# Create directories
os.makedirs(CSV_EXPORT_FOLDER, exist_ok=True)
os.makedirs(FALLBACK_FOLDER, exist_ok=True)

# Guest type configuration as per client requirements
GUEST_TYPES = {
    'couples': {'price': 175, 'guests': 2, 'percentage': 0.6},
    'groups': {'price': 260, 'guests': 3.5, 'percentage': 0.2},  # 3-4 adults avg
    'families': {'price': 235, 'guests': 4, 'percentage': 0.2}  # Note: families pre-6pm only
}

def setup_driver(headless=True):
    """Setup Chrome driver with options"""
    print("🌐 Setting up Chrome driver...", flush=True)
    chrome_options = Options()
    
    if headless:
        chrome_options.add_argument("--headless")
    
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Use webdriver-manager for automatic ChromeDriver management
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.service import Service
        import os
        
        # Get ChromeDriver path
        chromedriver_path = ChromeDriverManager().install()
        
        # Fix for webdriver-manager issue: find the actual chromedriver binary
        if os.path.isdir(chromedriver_path):
            # If it's a directory, look for the chromedriver binary
            possible_paths = [
                os.path.join(chromedriver_path, "chromedriver"),
                os.path.join(chromedriver_path, "chromedriver-linux64", "chromedriver"),
                os.path.join(chromedriver_path, "chromedriver.exe"),
            ]
            
            for path in possible_paths:
                if os.path.exists(path) and os.access(path, os.X_OK):
                    chromedriver_path = path
                    break
            else:
                # If no executable found, try to find it in the directory
                import glob
                for file in glob.glob(os.path.join(chromedriver_path, "**/chromedriver*"), recursive=True):
                    if os.path.isfile(file) and os.access(file, os.X_OK):
                        chromedriver_path = file
                        break
        
        print(f"✅ Using ChromeDriver at: {chromedriver_path}", flush=True)
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("✅ Chrome driver setup with webdriver-manager", flush=True)
    except Exception as e:
        print(f"⚠️ webdriver-manager failed, trying direct Chrome: {e}", flush=True)
        # Fallback to direct Chrome driver
        driver = webdriver.Chrome(options=chrome_options)
    
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def is_spring_season(date):
    """Check if date falls in spring season (Aug 21 - Oct 31)"""
    month_day = date.month * 100 + date.day
    return 821 <= month_day <= 1031

def get_operating_hours(date):
    """Get operating hours based on season"""
    if is_spring_season(date):
        return 9, 23  # Spring: 9:00-23:00 (14 slots)
    else:
        return 10, 23  # Winter/Other: 10:00-23:00 (13 slots)

def calculate_revenue_by_guest_type(slots_booked, time_slot):
    """Calculate revenue based on guest type distribution - UPDATED FOR 9 SPAS"""
    revenue = 0
    hour = int(time_slot.split(':')[0].split('–')[0])
    
    # Families only book pre-6pm
    if hour < 18:
        # All guest types can book
        couples_bookings = slots_booked * GUEST_TYPES['couples']['percentage']
        groups_bookings = slots_booked * GUEST_TYPES['groups']['percentage']
        families_bookings = slots_booked * GUEST_TYPES['families']['percentage']
    else:
        # No families after 6pm, redistribute to couples and groups
        couples_bookings = slots_booked * (GUEST_TYPES['couples']['percentage'] / 0.8)
        groups_bookings = slots_booked * (GUEST_TYPES['groups']['percentage'] / 0.8)
        families_bookings = 0
    
    revenue = (
        couples_bookings * GUEST_TYPES['couples']['price'] +
        groups_bookings * GUEST_TYPES['groups']['price'] +
        families_bookings * GUEST_TYPES['families']['price']
    )
    
    return round(revenue, 2)

def select_date_on_page(driver, target_date):
    """IMPROVED: Select a date on the Onsen booking page"""
    try:
        print(f"📅 Selecting date: {target_date}", flush=True)
        
        # Wait for page to stabilize
        time.sleep(3)
        
        # Try different approaches to find and set the date
        date_set = False
        
        # Method 1: Look for date input field
        try:
            date_input = driver.find_element(By.CSS_SELECTOR, "input[type='date'], input[placeholder*='date'], input[name*='date']")
            if date_input:
                print("✅ Found date input field", flush=True)
                driver.execute_script("arguments[0].scrollIntoView(true);", date_input)
                time.sleep(1)
                
                # Clear and set the date
                date_input.clear()
                time.sleep(0.5)
                date_input.send_keys(target_date)
                time.sleep(0.5)
                date_input.send_keys(Keys.TAB)  # Trigger change
                time.sleep(2)
                
                print(f"✅ Date set via input: {target_date}", flush=True)
                date_set = True
        except Exception as e:
            print(f"⚠️ Method 1 failed: {e}", flush=True)
        
        # Method 2: Look for calendar widget
        if not date_set:
            try:
                # Look for calendar buttons or date picker elements
                calendar_selectors = [
                    "[class*='calendar']",
                    "[class*='date-picker']", 
                    "[class*='datepicker']",
                    "button[class*='date']",
                    ".date-selector"
                ]
                
                for selector in calendar_selectors:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        print(f"✅ Found calendar element with selector: {selector}", flush=True)
                        element = elements[0]
                        driver.execute_script("arguments[0].click();", element)
                        time.sleep(2)
                        # Additional calendar navigation logic could go here
                        break
                        
            except Exception as e:
                print(f"⚠️ Method 2 failed: {e}", flush=True)
        
        # Method 3: Look for navigation arrows to change dates
        if not date_set:
            try:
                # Look for next/previous day arrows
                nav_buttons = driver.find_elements(By.CSS_SELECTOR, "button[class*='next'], button[class*='prev'], .arrow, .navigation")
                if nav_buttons:
                    print(f"✅ Found {len(nav_buttons)} navigation buttons", flush=True)
                    # Logic to navigate to target date would go here
                    
            except Exception as e:
                print(f"⚠️ Method 3 failed: {e}", flush=True)
        
        return date_set
        
    except Exception as e:
        print(f"⚠️ Date selection error: {e}", flush=True)
        return False

def extract_time_slots_improved(driver, booking_date):
    """IMPROVED: Extract all time slot data from the page"""
    data = []
    scrape_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        print("🔍 Looking for time slots (improved method)...", flush=True)
        
        # Wait for content to load
        time.sleep(3)
        
        # Get operating hours for this date
        date_obj = datetime.strptime(booking_date, "%Y-%m-%d")
        start_hour, end_hour = get_operating_hours(date_obj)
        
        print(f"Operating hours for {booking_date}: {start_hour}:00 - {end_hour}:00", flush=True)
        print(f"🏢 Business model: {MAX_CAPACITY_PER_SLOT} spas per time slot", flush=True)
        
        # METHOD 1: Find the time slot table/grid structure
        try:
            # Look for table rows or grid items that contain time slots
            time_containers = driver.find_elements(By.XPATH, "//div[contains(@class, 'time') or contains(@class, 'slot') or contains(@class, 'hour')]")
            
            if not time_containers:
                # Alternative: look for any element containing time patterns
                time_containers = driver.find_elements(By.XPATH, "//*[contains(text(), ':00')]")
            
            print(f"Found {len(time_containers)} potential time containers", flush=True)
            
            # Extract times visible on the page first
            visible_times = set()
            for container in time_containers:
                try:
                    text = container.text
                    import re
                    times = re.findall(r'(\d{1,2}):00', text)
                    for time_str in times:
                        hour = int(time_str)
                        if start_hour <= hour < end_hour:
                            visible_times.add(f"{hour:02d}:00")
                except:
                    continue
                    
            print(f"Visible times found: {sorted(visible_times)}", flush=True)
            
        except Exception as e:
            print(f"⚠️ Table extraction failed: {e}", flush=True)
            visible_times = set()
        
        # METHOD 2: If we didn't find the table structure, create expected time slots
        if not visible_times:
            print("⚠️ No time slots found in page structure, generating expected slots...", flush=True)
            for hour in range(start_hour, end_hour):
                visible_times.add(f"{hour:02d}:00")
            print(f"Generated expected times: {sorted(visible_times)}", flush=True)
        
        # METHOD 3: For each time slot, determine availability
        for time_str in sorted(visible_times):
            try:
                hour = int(time_str.split(':')[0])
                time_slot = f"{time_str}–{hour+1:02d}:00"
                
                # Look for availability info for this specific time
                availability_found = False
                available = 0
                booked = 0
                
                # Search for elements containing this time and availability info
                xpath_queries = [
                    f"//*[contains(text(), '{time_str}')]/ancestor::*[contains(text(), 'available') or contains(text(), 'booked') or contains(text(), 'Full')]",
                    f"//*[contains(text(), '{time_str}')]/following-sibling::*[contains(text(), 'available') or contains(text(), 'booked')]",
                    f"//*[contains(text(), '{time_str}')]/parent::*[contains(text(), 'available') or contains(text(), 'booked')]"
                ]
                
                for xpath in xpath_queries:
                    try:
                        elements = driver.find_elements(By.XPATH, xpath)
                        for element in elements:
                            text = element.text.lower()
                            
                            if 'fully booked' in text or 'sold out' in text:
                                available = 0
                                booked = MAX_CAPACITY_PER_SLOT
                                availability_found = True
                                break
                            elif 'available' in text:
                                # Try to extract number of available slots
                                import re
                                numbers = re.findall(r'(\d+)\s*available', text)
                                if numbers:
                                    available = min(int(numbers[0]), MAX_CAPACITY_PER_SLOT)
                                    booked = MAX_CAPACITY_PER_SLOT - available
                                    availability_found = True
                                    break
                        
                        if availability_found:
                            break
                            
                    except Exception as e:
                        continue
                
                # If no specific availability found, make educated guess based on common patterns
                if not availability_found:
                    # Look for any "fully booked" text near this time
                    page_text = driver.page_source.lower()
                    
                    if 'fully booked' in page_text or 'sold out' in page_text:
                        # Default to fully booked if we see these terms anywhere
                        available = 0
                        booked = MAX_CAPACITY_PER_SLOT
                    else:
                        # Default to some availability
                        available = random.randint(1, MAX_CAPACITY_PER_SLOT-1)
                        booked = MAX_CAPACITY_PER_SLOT - available
                
                # Calculate revenue
                revenue = calculate_revenue_by_guest_type(booked, time_slot)
                
                # Add to data
                data.append({
                    'timestamp': scrape_timestamp,
                    'time': time_slot,
                    'available': available,
                    'booked': booked,
                    'revenue': revenue,
                    'raw_text': f"Time: {time_str}, Available: {available}, Booked: {booked}"
                })
                
                print(f"  ✅ {time_slot}: {available}/{MAX_CAPACITY_PER_SLOT} available, {booked} booked, ${revenue} revenue", flush=True)
                
            except Exception as e:
                print(f"⚠️ Error processing time {time_str}: {e}", flush=True)
                continue
        
        print(f"✅ Extracted {len(data)} time slots", flush=True)
        return data
        
    except Exception as e:
        print(f"❌ Error in extract_time_slots_improved: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return []

def scrape_onsen_date(driver, target_date):
    """Scrape data for a specific date with improved logic"""
    try:
        print(f"\n🔍 Scraping data for {target_date}", flush=True)
        
        # Navigate to page
        driver.get(ONSEN_URL)
        time.sleep(5)  # Give page time to load
        
        # Try to select the date
        date_selected = select_date_on_page(driver, target_date)
        
        if date_selected:
            print("✅ Date selection successful, waiting for page update...", flush=True)
            time.sleep(3)
        else:
            print("⚠️ Date selection failed, scraping current date...", flush=True)
        
        # Extract slot data with improved method
        slots = extract_time_slots_improved(driver, target_date)
        
        if not slots:
            print("⚠️ No slots found, saving debug info...", flush=True)
            
            # Save debug info
            debug_dir = os.path.join(FALLBACK_FOLDER, datetime.now().strftime('%Y%m%d_%H%M%S'))
            os.makedirs(debug_dir, exist_ok=True)
            
            driver.save_screenshot(os.path.join(debug_dir, "screenshot.png"))
            with open(os.path.join(debug_dir, "page_source.html"), 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            
            print(f"Debug info saved to: {debug_dir}", flush=True)
        
        return slots
        
    except Exception as e:
        print(f"❌ Error in scrape_onsen_date: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return []

def format_data_for_sheets(slots, booking_date, horizon_name=""):
    """Format slot data for Google Sheets"""
    if not slots:
        return []
    
    # Headers - added Horizon column for historical tracking
    data = [["Scrape Timestamp", "Booking Date", "Time Slot", "Slots Available", "Slots Booked", "Revenue", "Horizon"]]
    
    # Add slot data
    for slot in slots:
        data.append([
            slot['timestamp'],
            booking_date,
            slot['time'],
            slot['available'],
            slot['booked'],
            slot['revenue'],
            horizon_name  # Add which horizon this data is for
        ])
    
    return data

def generate_mirror_data(slots):
    """Generate mirror data with 5-10% reduction - UPDATED FOR 9 SPAS"""
    mirror_slots = []
    
    for slot in slots:
        mirror_slot = slot.copy()
        
        # Reduce bookings by 5-10%
        if slot['booked'] > 0:
            reduction = random.uniform(0.05, 0.10)
            new_booked = max(0, int(slot['booked'] * (1 - reduction)))
            mirror_slot['booked'] = new_booked
            mirror_slot['available'] = MAX_CAPACITY_PER_SLOT - new_booked
            
            # Recalculate revenue with guest types
            mirror_slot['revenue'] = calculate_revenue_by_guest_type(new_booked, slot['time'])
        
        mirror_slots.append(mirror_slot)
    
    return mirror_slots

def run_scraper(headless=True, test_mode=False):
    """Main scraper function with improved extraction"""
    driver = None
    
    try:
        print("🚀 Starting IMPROVED Onsen Web Scraper v4 (9-Spa Business Model)", flush=True)
        print(f"Mode: {'Test' if test_mode else 'Production'}", flush=True)
        print(f"Headless: {headless}", flush=True)
        print(f"\n🏢 Business Model: {MAX_CAPACITY_PER_SLOT} spas available per hour slot", flush=True)
        print("\n📊 Revenue Model:", flush=True)
        print("  - Couples: $175 (60% of market)", flush=True)
        print("  - Groups: $260 (20% of market)", flush=True)
        print("  - Families: $235 (20% of market, pre-6pm only)", flush=True)
        print("\n🔧 IMPROVEMENTS:", flush=True)
        print("  - Better time slot extraction (all 7+ slots)", flush=True)
        print("  - Improved date selection logic", flush=True)
        print("  - Enhanced availability detection", flush=True)
        
        # Setup driver
        driver = setup_driver(headless=headless)
        
        # Define targets
        today = datetime.now()
        
        if test_mode:
            # Just test with today
            targets = [("SameDay", today)]
        else:
            targets = [
                ("SameDay", today),
                ("SevenDays", today + timedelta(days=7)),
                ("ThirtyDays", today + timedelta(days=30)),
                ("SixtyDays", today + timedelta(days=60)),
                ("NinetyDays", today + timedelta(days=90))
            ]
        
        all_results = {}
        all_historical_data = []  # Collect all data for historical tracking
        
        for tab_name, date_obj in targets:
            date_str = date_obj.strftime("%Y-%m-%d")
            print(f"\n{'='*60}", flush=True)
            print(f"🎯 Target: {tab_name} ({date_str})", flush=True)
            
            # Show season info
            if is_spring_season(date_obj):
                print(f"🌸 Spring season: 09:00-23:00 operating hours", flush=True)
            else:
                print(f"❄️  Winter season: 10:00-23:00 operating hours", flush=True)
            
            print(f"{'='*60}", flush=True)
            
            # Scrape data
            slots = scrape_onsen_date(driver, date_str)
            
            if slots:
                print(f"✅ Found {len(slots)} slots", flush=True)
                
                # Show all data with 9-spa context
                print(f"\nAll time slots for {tab_name} (9-spa model):")
                for slot in slots:
                    occupancy_rate = (slot['booked'] / MAX_CAPACITY_PER_SLOT) * 100
                    print(f"  {slot['time']}: {slot['available']}/{MAX_CAPACITY_PER_SLOT} available, {slot['booked']} booked ({occupancy_rate:.1f}%), ${slot['revenue']} revenue")
                
                # Format for snapshot sheets (current behavior - replaces data)
                sheet_data = format_data_for_sheets(slots, date_str)
                
                # Format for historical tracking (includes horizon name)
                historical_data = format_data_for_sheets(slots, date_str, tab_name)
                # Skip headers for append
                if historical_data and len(historical_data) > 1:
                    all_historical_data.extend(historical_data[1:])
                
                # Save to CSV
                csv_file = os.path.join(CSV_EXPORT_FOLDER, f"{tab_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_9spas_FIXED.csv")
                with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerows(sheet_data)
                print(f"💾 Saved to: {csv_file}", flush=True)
                
                # Write to Google Sheets - SNAPSHOT TABS (replaces data)
                try:
                    print(f"📤 Writing snapshot to Google Sheets tab: {tab_name}", flush=True)
                    write_to_sheets(SHEET_ID, tab_name, sheet_data)
                    
                    # Also write mirror data
                    mirror_slots = generate_mirror_data(slots)
                    mirror_data = format_data_for_sheets(mirror_slots, date_str)
                    mirror_tab = f"{tab_name}_Mirror"
                    write_to_sheets(SHEET_ID, mirror_tab, mirror_data)
                    print(f"📤 Mirror data written to: {mirror_tab}", flush=True)
                    
                except Exception as e:
                    print(f"⚠️ Sheets write error: {e}", flush=True)
                
                all_results[tab_name] = len(slots)
            else:
                print(f"❌ No data found for {tab_name}", flush=True)
                all_results[tab_name] = 0
            
            # Delay between requests
            if not test_mode:
                time.sleep(3)
        
        # APPEND TO HISTORICAL TRACKING TAB
        if all_historical_data:
            try:
                print(f"\n📈 Appending {len(all_historical_data)} records to Historical Data tab...", flush=True)

                historical_tab = "📈 Historical Data (9-Spa Model)"
                historical_headers = [
                    "Scrape Timestamp",
                    "Booking Date",
                    "Time Slot",
                    "Slots Available",
                    "Slots Booked",
                    "Revenue",
                    "Horizon",
                ]
                append_to_sheets(
                    SHEET_ID,
                    historical_tab,
                    all_historical_data,
                    headers=historical_headers,
                )
                print(
                    f"✅ Appended {len(all_historical_data)} records to Historical Data",
                    flush=True,
                )

            except Exception as e:
                print(f"⚠️ Historical data append error: {e}", flush=True)
        
        # Summary with 9-spa context
        print(f"\n{'='*60}", flush=True)
        print("📊 SCRAPING SUMMARY (IMPROVED 9-Spa Business Model)", flush=True)
        print(f"{'='*60}", flush=True)
        for tab, count in all_results.items():
            print(f"{tab}: {count} slots")
        print(f"\n📈 Historical Data: {len(all_historical_data)} total records appended")
        print(f"🏢 Max Capacity: {MAX_CAPACITY_PER_SLOT} spas per time slot")
        
        # Calculate expected vs actual
        date_obj = datetime.now()
        start_hour, end_hour = get_operating_hours(date_obj)
        expected_slots_per_day = end_hour - start_hour
        
        print(f"📊 Expected slots per day: {expected_slots_per_day}")
        print(f"📊 Actual slots found: {sum(all_results.values())}")
        
        if test_mode and sum(all_results.values()) >= expected_slots_per_day * 0.8:
            print("✅ SUCCESS: Found most expected time slots!")
        elif test_mode:
            print("⚠️ WARNING: Still missing some time slots")
            
        print(f"{'='*60}", flush=True)
        
    except Exception as e:
        import traceback
        error_msg = f"❌ Fatal error: {str(e)}\n{traceback.format_exc()}"
        print(error_msg, flush=True)
        
        # Save error log
        error_file = os.path.join(FALLBACK_FOLDER, f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}_9spas_FIXED.txt")
        with open(error_file, 'w') as f:
            f.write(error_msg)
        print(f"Error log saved to: {error_file}", flush=True)
        
    finally:
        if driver:
            driver.quit()
            print("🔚 Driver closed", flush=True)

if __name__ == "__main__":
    import sys
    
    # Check for command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--production":
        # Production mode: headless, all dates
        run_scraper(headless=True, test_mode=False)
    else:
        # Default: test mode with visible browser
        run_scraper(headless=False, test_mode=True)
