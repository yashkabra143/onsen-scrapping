#!/usr/bin/env python3
"""
Fix Revenue Calculation in 4-Spa Mirror Data
The revenue numbers are too high - need to debug and fix
"""

import sys
import os
sys.path.append('/Users/yashkabra/Desktop/onsen-scraper-deploy')

def fix_revenue_calculation():
    print("🔧 Fixing 4-Spa Revenue Calculations...")
    
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        
        # Configuration
        SHEET_ID = "1xFtJvQLeI65YD2-twrGzh8g0c5pGTwODe8i5XFK7bZ0"
        CREDENTIALS_FILE = "onsen-scraping-e41c80c00b93.json"
        
        # Connect
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(SHEET_ID)
        
        print("✅ Connected to Google Sheets")
        
        # Check original data first
        print("\n🔍 Investigating original competitor data...")
        original_tab = spreadsheet.worksheet('SameDay')
        original_data = original_tab.get_all_records()
        
        if original_data:
            print(f"📊 Original SameDay data sample:")
            first_row = original_data[0]
            for key, value in first_row.items():
                print(f"   {key}: {value}")
            
            # Check revenue values specifically
            revenue_values = [row.get('Revenue', 0) for row in original_data[:3]]
            print(f"\n💰 Sample revenue values from competitor: {revenue_values}")
        
        # Check the 4-spa mirror data
        print("\n🔍 Checking 4-spa mirror data...")
        mirror_tab = spreadsheet.worksheet('SameDay_4Spa_Client')
        mirror_data = mirror_tab.get_all_records()
        
        if mirror_data:
            print(f"📊 4-Spa mirror data sample:")
            first_row = mirror_data[0]
            for key, value in first_row.items():
                if 'revenue' in key.lower() or 'booking' in key.lower():
                    print(f"   {key}: {value}")
        
        # Calculate what revenue SHOULD be
        print("\n🧮 Calculating correct revenue...")
        
        # Business model for 4-spa
        GUEST_TYPES = {
            'couples': {'price': 175, 'percentage': 0.6},
            'groups': {'price': 260, 'percentage': 0.2},
            'families': {'price': 235, 'percentage': 0.2}
        }
        
        def calculate_correct_4spa_revenue(slots_booked, hour=12):
            """Calculate what 4-spa revenue should actually be"""
            if slots_booked == 0:
                return 0
            
            # Before 6 PM - all guest types
            if hour < 18:
                couples_bookings = slots_booked * GUEST_TYPES['couples']['percentage']
                groups_bookings = slots_booked * GUEST_TYPES['groups']['percentage']
                families_bookings = slots_booked * GUEST_TYPES['families']['percentage']
            else:
                # After 6 PM - no families
                couples_bookings = slots_booked * 0.75  # 75% of remaining
                groups_bookings = slots_booked * 0.25   # 25% of remaining
                families_bookings = 0
            
            revenue = (
                couples_bookings * GUEST_TYPES['couples']['price'] +
                groups_bookings * GUEST_TYPES['groups']['price'] +
                families_bookings * GUEST_TYPES['families']['price']
            )
            
            return round(revenue, 2)
        
        # Test the calculation
        test_revenue_4_bookings = calculate_correct_4spa_revenue(4, 14)  # 4 bookings at 2 PM
        test_revenue_4_evening = calculate_correct_4spa_revenue(4, 20)   # 4 bookings at 8 PM
        
        print(f"✅ Correct revenue for 4 bookings (afternoon): ${test_revenue_4_bookings}")
        print(f"✅ Correct revenue for 4 bookings (evening): ${test_revenue_4_evening}")
        
        # Now fix the data
        print("\n🔧 Fixing all 4-spa tabs...")
        
        fixed_count = 0
        tabs_to_fix = ['SameDay_4Spa_Client', 'SevenDays_4Spa_Client', 'ThirtyDays_4Spa_Client', 
                      'SixtyDays_4Spa_Client', 'NinetyDays_4Spa_Client']
        
        for tab_name in tabs_to_fix:
            try:
                print(f"\n🎯 Fixing {tab_name}...")
                
                # Get the data
                worksheet = spreadsheet.worksheet(tab_name)
                data = worksheet.get_all_records()
                
                # Fix each row
                fixed_data = []
                for row in data:
                    fixed_row = row.copy()
                    
                    # Get slots booked (should be 0-4 for 4-spa)
                    try:
                        slots_booked = int(float(str(row.get('Slots Booked', 0))))
                        # Ensure it's within 4-spa limits
                        slots_booked = min(max(slots_booked, 0), 4)
                        
                        # Extract hour from time slot
                        time_slot = str(row.get('Time Slot', '12:00'))
                        try:
                            hour = int(time_slot.split(':')[0])
                        except:
                            hour = 12
                        
                        # Calculate correct revenue
                        correct_revenue = calculate_correct_4spa_revenue(slots_booked, hour)
                        
                        # Update the row
                        fixed_row['Slots Booked'] = slots_booked
                        fixed_row['Slots Available'] = 4 - slots_booked
                        fixed_row['Revenue'] = correct_revenue
                        
                    except:
                        # If parsing fails, set safe defaults
                        fixed_row['Slots Booked'] = 0
                        fixed_row['Slots Available'] = 4
                        fixed_row['Revenue'] = 0
                    
                    fixed_data.append(fixed_row)
                
                # Write back to sheet
                if fixed_data:
                    headers = list(fixed_data[0].keys())
                    values = [headers]
                    
                    for row in fixed_data:
                        values.append([str(row.get(h, '')) for h in headers])
                    
                    # Clear and update
                    worksheet.clear()
                    worksheet.update(values, 'A1')
                    
                    # Calculate new summary
                    total_bookings = sum(int(float(str(row.get('Slots Booked', 0)))) for row in fixed_data)
                    total_revenue = sum(float(str(row.get('Revenue', 0))) for row in fixed_data)
                    
                    print(f"   ✅ Fixed {tab_name}")
                    print(f"   📊 New summary: {total_bookings} bookings, ${total_revenue:,.2f} revenue")
                    
                    fixed_count += 1
                
            except Exception as e:
                print(f"   ❌ Error fixing {tab_name}: {e}")
        
        print(f"\n🎉 Revenue Fix Complete!")
        print(f"✅ Fixed {fixed_count} out of {len(tabs_to_fix)} tabs")
        print(f"\n💡 Revenue should now show realistic amounts:")
        print(f"   • 4 full bookings (afternoon): ~${test_revenue_4_bookings}")
        print(f"   • 4 full bookings (evening): ~${test_revenue_4_evening}")
        print(f"   • Daily total (13 slots, 80% occupancy): ~$8,000-10,000")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = fix_revenue_calculation()
    if success:
        print("\n🚀 Revenue calculations fixed! Check your Google Sheets.")
    else:
        print("\n💥 Fix failed - check errors above.")
