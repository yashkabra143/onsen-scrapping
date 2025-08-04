#!/usr/bin/env python3
"""
4-Spa Mirror Data Creator - PRODUCTION VERSION
Creates realistic 4-spa projections for client based on 9-spa competitor data
"""

import sys
import os

# Add project directory to path
sys.path.append('/Users/yashkabra/Desktop/onsen-scraper-deploy')

def main():
    print("🚀 4-Spa Mirror Data Creator - PRODUCTION")
    print("=" * 50)
    
    try:
        # Import required libraries
        import gspread
        from google.oauth2.service_account import Credentials
        from datetime import datetime
        print("✅ Libraries imported successfully")
        
        # Configuration
        SHEET_ID = "1xFtJvQLeI65YD2-twrGzh8g0c5pGTwODe8i5XFK7bZ0"
        CREDENTIALS_FILE = "onsen-scraping-e41c80c00b93.json"
        
        # Check credentials file
        if not os.path.exists(CREDENTIALS_FILE):
            print(f"❌ Credentials file not found: {CREDENTIALS_FILE}")
            return False
        
        print("✅ Credentials file found")
        
        # Connect to Google Sheets
        print("\n🔐 Connecting to Google Sheets...")
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(SHEET_ID)
        
        print(f"✅ Connected to: {spreadsheet.title}")
        
        # Business model constants
        COMPETITOR_SPAS = 9
        CLIENT_SPAS = 4
        PERFORMANCE_FACTOR = 0.85  # Conservative 85% performance
        
        print(f"\n🏢 Business Model:")
        print(f"   • Competitor capacity: {COMPETITOR_SPAS} spas")
        print(f"   • Client capacity: {CLIENT_SPAS} spas")
        print(f"   • Performance factor: {PERFORMANCE_FACTOR:.0%}")
        
        # Process each horizon
        horizons = ['SameDay', 'SevenDays', 'ThirtyDays', 'SixtyDays', 'NinetyDays']
        success_count = 0
        
        for horizon in horizons:
            print(f"\n🎯 Processing {horizon}...")
            
            try:
                # Get competitor data
                worksheet = spreadsheet.worksheet(horizon)
                data = worksheet.get_all_records()
                
                if not data:
                    print(f"   ⚠️ No data found in {horizon}")
                    continue
                
                print(f"   📊 Found {len(data)} records")
                
                # Create 4-spa projections
                mirror_data = []
                
                for row in data:
                    mirror_row = {}
                    
                    # Copy basic fields
                    for key, value in row.items():
                        mirror_row[key] = value
                    
                    # Scale bookings
                    if 'Slots Booked' in row:
                        try:
                            original_bookings = int(float(str(row['Slots Booked']).replace('', '0')))
                            
                            # Calculate scaled bookings
                            occupancy_rate = original_bookings / COMPETITOR_SPAS
                            client_occupancy = occupancy_rate * PERFORMANCE_FACTOR
                            new_bookings = min(round(client_occupancy * CLIENT_SPAS), CLIENT_SPAS)
                            
                            mirror_row['Slots Booked'] = new_bookings
                            mirror_row['Slots Available'] = CLIENT_SPAS - new_bookings
                            mirror_row['Competitor_Bookings_9Spa'] = original_bookings
                            mirror_row['Occupancy_Rate_Client'] = f"{(new_bookings/CLIENT_SPAS)*100:.1f}%"
                            mirror_row['Occupancy_Rate_Competitor'] = f"{occupancy_rate*100:.1f}%"
                            
                        except (ValueError, TypeError):
                            mirror_row['Slots Booked'] = 0
                            mirror_row['Slots Available'] = CLIENT_SPAS
                    
                    # Scale revenue
                    if 'Revenue' in row:
                        try:
                            original_revenue = float(str(row['Revenue']).replace('', '0'))
                            scaling_factor = CLIENT_SPAS / COMPETITOR_SPAS
                            new_revenue = original_revenue * scaling_factor * PERFORMANCE_FACTOR
                            
                            mirror_row['Revenue'] = round(new_revenue, 2)
                            mirror_row['Competitor_Revenue_9Spa'] = original_revenue
                            mirror_row['Revenue_Scaling'] = f"{scaling_factor:.1%} × {PERFORMANCE_FACTOR:.0%}"
                            
                        except (ValueError, TypeError):
                            mirror_row['Revenue'] = 0
                    
                    # Add metadata
                    mirror_row['Data_Source'] = '4Spa_Client_Projection'
                    mirror_row['Created_Date'] = datetime.now().strftime('%Y-%m-%d')
                    mirror_row['Methodology'] = f'{PERFORMANCE_FACTOR:.0%}_performance_vs_competitor'
                    
                    mirror_data.append(mirror_row)
                
                # Write to new tab
                new_tab_name = f"{horizon}_4Spa_Client"
                
                try:
                    # Try to access existing worksheet
                    new_worksheet = spreadsheet.worksheet(new_tab_name)
                    new_worksheet.clear()
                    print(f"   📝 Cleared existing {new_tab_name}")
                except:
                    # Create new worksheet
                    new_worksheet = spreadsheet.add_worksheet(
                        title=new_tab_name, rows=1000, cols=25
                    )
                    print(f"   📄 Created new {new_tab_name}")
                
                # Prepare data for sheets
                if mirror_data:
                    headers = list(mirror_data[0].keys())
                    values = [headers]
                    
                    for row in mirror_data:
                        values.append([str(row.get(h, '')) for h in headers])
                    
                    # Write to sheet
                    new_worksheet.update('A1', values)
                    print(f"   ✅ Wrote {len(mirror_data)} rows to {new_tab_name}")
                    
                    # Calculate summary
                    total_bookings = sum(
                        int(float(str(row.get('Slots Booked', 0)))) 
                        for row in mirror_data 
                        if str(row.get('Slots Booked', '')).replace('.', '').isdigit()
                    )
                    
                    total_revenue = sum(
                        float(str(row.get('Revenue', 0))) 
                        for row in mirror_data 
                        if str(row.get('Revenue', '')).replace('.', '').replace('-', '').isdigit()
                    )
                    
                    print(f"   📊 Summary: {total_bookings} bookings, ${total_revenue:,.2f} revenue")
                    success_count += 1
                
            except Exception as e:
                print(f"   ❌ Error processing {horizon}: {e}")
                continue
        
        # Final summary
        print(f"\n{'='*50}")
        print(f"🎉 4-Spa Mirror Creation Complete!")
        print(f"✅ Successfully created {success_count} out of {len(horizons)} projections")
        
        if success_count > 0:
            print(f"\n📋 New tabs created:")
            for horizon in horizons:
                print(f"   • {horizon}_4Spa_Client")
            
            print(f"\n💡 Key Features:")
            print(f"   • Conservative {PERFORMANCE_FACTOR:.0%} performance vs competitor")
            print(f"   • Realistic {CLIENT_SPAS}-spa capacity scaling")
            print(f"   • Side-by-side comparison data")
            print(f"   • Ready for financial modeling")
            
            print(f"\n🎯 Tell your client:")
            print(f"   'Added 4-spa mirror data showing realistic projections'")
            print(f"   'Based on {PERFORMANCE_FACTOR:.0%} performance vs 9-spa competitor'")
            print(f"   'New tabs show hour-by-hour projections for your resort'")
        
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🚀 SUCCESS! 4-spa mirror data is ready for your client.")
        else:
            print("\n💥 FAILED! Check the errors above.")
        
        print("\nNext step: Create professional charts using the new 4-spa data!")
        
    except KeyboardInterrupt:
        print("\n⏹️ Cancelled by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
