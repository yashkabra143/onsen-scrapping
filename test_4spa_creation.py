#!/usr/bin/env python3
"""
Simple test to verify Google Sheets access and create basic 4-spa mirror
"""

import sys
import os
sys.path.append('/Users/yashkabra/Desktop/onsen-scraper-deploy')

try:
    import gspread
    from google.oauth2.service_account import Credentials
    print("✅ Required libraries imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Configuration
SHEET_ID = "1xFtJvQLeI65YD2-twrGzh8g0c5pGTwODe8i5XFK7bZ0"
CREDENTIALS_FILE = "onsen-scraping-e41c80c00b93.json"

def test_connection():
    """Test Google Sheets connection"""
    try:
        print("🔐 Testing Google Sheets authentication...")
        
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(SHEET_ID)
        
        print("✅ Successfully connected to Google Sheets")
        print(f"📊 Spreadsheet title: {spreadsheet.title}")
        
        # List existing worksheets
        worksheets = spreadsheet.worksheets()
        print(f"📄 Found {len(worksheets)} existing worksheets:")
        for ws in worksheets:
            print(f"   • {ws.title}")
        
        return client, spreadsheet
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None, None

def get_sample_data(spreadsheet, tab_name):
    """Get sample data from a tab"""
    try:
        worksheet = spreadsheet.worksheet(tab_name)
        data = worksheet.get_all_records()
        print(f"✅ Successfully read {len(data)} records from {tab_name}")
        
        if data:
            print(f"📋 Sample data from {tab_name}:")
            keys = list(data[0].keys()) if data else []
            print(f"   Columns: {keys}")
            
            if len(data) > 0:
                first_row = data[0]
                print(f"   First row: {first_row}")
        
        return data
        
    except Exception as e:
        print(f"❌ Error reading {tab_name}: {e}")
        return []

def create_simple_4spa_mirror(spreadsheet, competitor_data, tab_name):
    """Create simple 4-spa mirror data"""
    try:
        print(f"\n🔧 Creating 4-spa mirror for {tab_name}...")
        
        if not competitor_data:
            print("⚠️ No competitor data to process")
            return False
        
        # Simple scaling: competitor has 9 spas, client will have 4
        scaling_factor = 4 / 9  # 44.4%
        performance_factor = 0.85  # Conservative: client performs 85% as well
        
        mirror_data = []
        
        for row in competitor_data:
            mirror_row = row.copy()
            
            # Scale bookings
            if 'Slots Booked' in row:
                original_bookings = int(row['Slots Booked']) if str(row['Slots Booked']).isdigit() else 0
                
                # Scale to 4-spa capacity with performance factor
                occupancy_rate = original_bookings / 9
                client_occupancy = occupancy_rate * performance_factor
                new_bookings = min(int(client_occupancy * 4), 4)
                
                mirror_row['Slots Booked'] = new_bookings
                mirror_row['Slots Available'] = 4 - new_bookings
                mirror_row['Original_9Spa_Bookings'] = original_bookings
                mirror_row['Scaling_Applied'] = f"{scaling_factor:.1%} capacity, {performance_factor:.0%} performance"
            
            # Scale revenue (simple method)
            if 'Revenue' in row:
                original_revenue = float(row['Revenue']) if str(row['Revenue']).replace('.','').isdigit() else 0
                new_revenue = original_revenue * scaling_factor * performance_factor
                mirror_row['Revenue'] = round(new_revenue, 2)
                mirror_row['Original_9Spa_Revenue'] = original_revenue
            
            mirror_row['Data_Type'] = '4Spa_Client_Projection'
            mirror_row['Created_At'] = '2025-07-12'
            
            mirror_data.append(mirror_row)
        
        # Write to new tab
        new_tab_name = f"{tab_name}_4Spa_Mirror"
        
        try:
            # Try to get existing worksheet
            worksheet = spreadsheet.worksheet(new_tab_name)
            worksheet.clear()
            print(f"  📝 Cleared existing {new_tab_name}")
        except:
            # Create new worksheet
            worksheet = spreadsheet.add_worksheet(title=new_tab_name, rows=1000, cols=20)
            print(f"  📄 Created new worksheet: {new_tab_name}")
        
        # Prepare data for Google Sheets
        if mirror_data:
            headers = list(mirror_data[0].keys())
            values = [headers]
            
            for row in mirror_data:
                values.append([row.get(h, '') for h in headers])
            
            # Write to sheet
            worksheet.update('A1', values)
            print(f"  ✅ Successfully wrote {len(mirror_data)} rows to {new_tab_name}")
            
            # Show summary
            total_bookings = sum(int(row['Slots Booked']) for row in mirror_data if str(row['Slots Booked']).isdigit())
            total_revenue = sum(float(row['Revenue']) for row in mirror_data if str(row['Revenue']).replace('.','').isdigit())
            
            print(f"  📊 Summary: {total_bookings} total bookings, ${total_revenue:,.2f} revenue")
            
        return True
        
    except Exception as e:
        print(f"❌ Error creating 4-spa mirror: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🚀 Simple 4-Spa Mirror Data Creator")
    print("=" * 50)
    
    # Test connection
    client, spreadsheet = test_connection()
    if not client:
        return False
    
    # Try to process main data tabs
    horizons = ['SameDay', 'SevenDays', 'ThirtyDays', 'SixtyDays', 'NinetyDays']
    success_count = 0
    
    for horizon in horizons:
        print(f"\n🎯 Processing {horizon}...")
        
        # Get competitor data
        data = get_sample_data(spreadsheet, horizon)
        
        # Create 4-spa mirror
        if data:
            success = create_simple_4spa_mirror(spreadsheet, data, horizon)
            if success:
                success_count += 1
        else:
            print(f"⚠️ No data found for {horizon}")
    
    print(f"\n🏁 Completed! Successfully created {success_count} out of {len(horizons)} mirrors")
    return success_count > 0

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✅ 4-spa mirror data creation completed!")
        else:
            print("\n❌ 4-spa mirror data creation failed!")
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        import traceback
        traceback.print_exc()
