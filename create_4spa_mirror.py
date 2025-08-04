#!/usr/bin/env python3
"""
Create 4-Spa Mirror Data for Client's Planned Resort
Takes 9-spa competitor data and creates realistic 4-spa projections
"""

import gspread
import pandas as pd
from datetime import datetime
from google.oauth2.service_account import Credentials
import os
import time

class FourSpaMirrorCreator:
    def __init__(self, sheet_id, credentials_file):
        """Initialize the 4-spa mirror creator"""
        self.sheet_id = sheet_id
        self.credentials_file = credentials_file
        self.client = None
        self.spreadsheet = None
        
        # Business model constants
        self.COMPETITOR_SPAS = 9  # Onsen's current capacity
        self.CLIENT_SPAS = 4      # Client's planned capacity
        self.SCALING_FACTOR = self.CLIENT_SPAS / self.COMPETITOR_SPAS  # 44.4%
        
        # Conservative performance assumption (client will perform 85% as well as competitor)
        self.PERFORMANCE_FACTOR = 0.85
        
        # Guest type pricing (same as competitor)
        self.GUEST_TYPES = {
            'couples': {'price': 175, 'guests': 2, 'percentage': 0.6},
            'groups': {'price': 260, 'guests': 3.5, 'percentage': 0.2},
            'families': {'price': 235, 'guests': 4, 'percentage': 0.2}
        }
        
        self.authenticate()
    
    def authenticate(self):
        """Authenticate with Google Sheets API"""
        try:
            scope = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            
            creds = Credentials.from_service_account_file(
                self.credentials_file, scopes=scope
            )
            self.client = gspread.authorize(creds)
            self.spreadsheet = self.client.open_by_key(self.sheet_id)
            print("✅ Successfully authenticated with Google Sheets")
            
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            raise
    
    def get_competitor_data(self, tab_name):
        """Get competitor data from existing tabs"""
        try:
            worksheet = self.spreadsheet.worksheet(tab_name)
            data = worksheet.get_all_records()
            return pd.DataFrame(data) if data else pd.DataFrame()
        except Exception as e:
            print(f"❌ Error reading {tab_name}: {e}")
            return pd.DataFrame()
    
    def calculate_4spa_revenue(self, slots_booked, time_slot):
        """Calculate revenue for 4-spa model with guest type distribution"""
        if pd.isna(slots_booked) or slots_booked == 0:
            return 0.0
        
        # Extract hour from time slot (handle different formats)
        try:
            if '–' in str(time_slot):
                hour_str = str(time_slot).split('–')[0].split(':')[0]
            elif ':' in str(time_slot):
                hour_str = str(time_slot).split(':')[0]
            else:
                hour_str = '12'  # Default to noon
            
            hour = int(hour_str)
        except:
            hour = 12  # Default to noon if parsing fails
        
        # Apply guest type distribution based on time
        if hour < 18:  # Before 6 PM - all guest types allowed
            couples_bookings = slots_booked * self.GUEST_TYPES['couples']['percentage']
            groups_bookings = slots_booked * self.GUEST_TYPES['groups']['percentage']
            families_bookings = slots_booked * self.GUEST_TYPES['families']['percentage']
        else:  # After 6 PM - no families (adults only)
            couples_percentage = self.GUEST_TYPES['couples']['percentage'] / (1 - self.GUEST_TYPES['families']['percentage'])
            groups_percentage = self.GUEST_TYPES['groups']['percentage'] / (1 - self.GUEST_TYPES['families']['percentage'])
            
            couples_bookings = slots_booked * couples_percentage
            groups_bookings = slots_booked * groups_percentage
            families_bookings = 0
        
        # Calculate total revenue
        revenue = (
            couples_bookings * self.GUEST_TYPES['couples']['price'] +
            groups_bookings * self.GUEST_TYPES['groups']['price'] +
            families_bookings * self.GUEST_TYPES['families']['price']
        )
        
        return round(revenue, 2)
    
    def create_4spa_projection(self, competitor_data, horizon_name):
        """Create 4-spa projection from 9-spa competitor data"""
        if competitor_data.empty:
            return pd.DataFrame()
        
        # Create copy for client data
        client_data = competitor_data.copy()
        
        # Add identification columns
        client_data['Data_Source'] = 'Client_4Spa_Projection'
        client_data['Competitor_Reference'] = '9Spa_Onsen'
        client_data['Scaling_Method'] = f'{self.SCALING_FACTOR:.1%}_capacity_+_{self.PERFORMANCE_FACTOR:.0%}_performance'
        
        # Scale bookings: (Competitor bookings ÷ 9) × 4 × performance factor
        if 'Slots Booked' in client_data.columns:
            # Convert to occupancy rate first, then scale to 4-spa capacity
            competitor_occupancy = pd.to_numeric(client_data['Slots Booked'], errors='coerce') / self.COMPETITOR_SPAS
            
            # Apply performance factor (client performs 85% as well as competitor)
            client_occupancy = competitor_occupancy * self.PERFORMANCE_FACTOR
            
            # Convert back to actual bookings for 4-spa setup
            client_data['Slots Booked'] = (client_occupancy * self.CLIENT_SPAS).round().astype(int)
            
            # Ensure we don't exceed 4-spa capacity
            client_data['Slots Booked'] = client_data['Slots Booked'].clip(upper=self.CLIENT_SPAS)
            
            # Recalculate availability
            client_data['Slots Available'] = self.CLIENT_SPAS - client_data['Slots Booked']
            
            # Add performance metrics
            client_data['Occupancy_Rate'] = (client_data['Slots Booked'] / self.CLIENT_SPAS * 100).round(1)
            client_data['Competitor_Occupancy_Rate'] = (pd.to_numeric(competitor_data['Slots Booked'], errors='coerce') / self.COMPETITOR_SPAS * 100).round(1)
            
        # Recalculate revenue using 4-spa model
        if 'Time Slot' in client_data.columns:
            client_data['Revenue'] = client_data.apply(
                lambda row: self.calculate_4spa_revenue(
                    row['Slots Booked'], 
                    row['Time Slot']
                ), axis=1
            )
        
        # Add comparison metrics
        if 'Revenue' in competitor_data.columns:
            competitor_revenue = pd.to_numeric(competitor_data['Revenue'], errors='coerce')
            client_data['Competitor_Revenue_9Spa'] = competitor_revenue
            client_data['Revenue_Scaling_Factor'] = (
                client_data['Revenue'] / competitor_revenue * 100
            ).round(1)
        
        # Add timestamp
        client_data['Projection_Created'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        client_data['Horizon'] = horizon_name
        
        return client_data
    
    def write_to_sheet(self, df, sheet_name):
        """Write DataFrame to Google Sheet"""
        try:
            # Try to get existing worksheet
            try:
                worksheet = self.spreadsheet.worksheet(sheet_name)
                worksheet.clear()
                print(f"  📝 Cleared existing {sheet_name}")
            except:
                # Create new worksheet if it doesn't exist
                worksheet = self.spreadsheet.add_worksheet(
                    title=sheet_name, rows=1000, cols=30
                )
                print(f"  📄 Created new worksheet: {sheet_name}")
            
            # Convert DataFrame to list format for Google Sheets
            if not df.empty:
                # Replace NaN values with empty strings
                df_clean = df.fillna('')
                values = [df_clean.columns.tolist()] + df_clean.values.tolist()
                
                # Write data
                worksheet.update('A1', values)
                print(f"  ✅ Updated {sheet_name} with {len(df)} rows")
            else:
                print(f"  ⚠️ No data to write to {sheet_name}")
            
        except Exception as e:
            print(f"  ❌ Error updating {sheet_name}: {e}")
    
    def create_all_4spa_mirrors(self):
        """Create 4-spa mirror data for all time horizons"""
        print("🔧 Creating 4-Spa Mirror Data for Client's Planned Resort")
        print("=" * 60)
        
        # Time horizons to process
        horizons = ['SameDay', 'SevenDays', 'ThirtyDays', 'SixtyDays', 'NinetyDays']
        
        success_count = 0
        
        for horizon in horizons:
            print(f"\n🎯 Processing {horizon}...")
            
            # Get competitor data
            competitor_data = self.get_competitor_data(horizon)
            
            if competitor_data.empty:
                print(f"  ⚠️ No competitor data found for {horizon}")
                continue
            
            print(f"  📊 Found {len(competitor_data)} competitor time slots")
            
            # Create 4-spa projection
            client_projection = self.create_4spa_projection(competitor_data, horizon)
            
            if not client_projection.empty:
                # Write to new tab
                client_tab_name = f"{horizon}_4Spa_Client"
                self.write_to_sheet(client_projection, client_tab_name)
                
                # Show summary
                total_competitor_bookings = competitor_data['Slots Booked'].sum() if 'Slots Booked' in competitor_data.columns else 0
                total_client_bookings = client_projection['Slots Booked'].sum() if 'Slots Booked' in client_projection.columns else 0
                total_client_revenue = client_projection['Revenue'].sum() if 'Revenue' in client_projection.columns else 0
                
                print(f"  📈 Summary for {horizon}:")
                print(f"     Competitor (9-spa): {total_competitor_bookings} total bookings")
                print(f"     Client (4-spa): {total_client_bookings} projected bookings")
                print(f"     Client revenue: ${total_client_revenue:,.2f} NZD")
                
                if total_competitor_bookings > 0:
                    performance_ratio = (total_client_bookings / self.CLIENT_SPAS) / (total_competitor_bookings / self.COMPETITOR_SPAS)
                    print(f"     Performance vs competitor: {performance_ratio:.1%}")
                
                success_count += 1
            
            # Add delay to avoid API rate limits
            time.sleep(1)
        
        print("\n" + "=" * 60)
        print(f"🎉 4-Spa Mirror Data Creation Complete!")
        print(f"✅ Successfully created {success_count} out of {len(horizons)} projections")
        
        if success_count > 0:
            print("\n📋 New tabs created:")
            for horizon in horizons:
                print(f"   • {horizon}_4Spa_Client")
            
            print("\n🏢 Business Model Summary:")
            print(f"   • Competitor capacity: {self.COMPETITOR_SPAS} spas")
            print(f"   • Client capacity: {self.CLIENT_SPAS} spas ({self.SCALING_FACTOR:.1%} of competitor)")
            print(f"   • Performance assumption: {self.PERFORMANCE_FACTOR:.0%} of competitor performance")
            print(f"   • Revenue model: Couples (60%), Groups (20%), Families (20%)")
            
            print("\n💡 Key Features Added:")
            print("   • Realistic occupancy scaling (not just 44% of competitor)")
            print("   • Conservative performance factor (85% of competitor)")
            print("   • Guest-type based revenue calculations")
            print("   • Comparison metrics vs competitor")
            print("   • Hour-by-hour projections")
        
        return success_count > 0

def main():
    """Main function to create 4-spa mirror data"""
    
    # Configuration
    SHEET_ID = "1xFtJvQLeI65YD2-twrGzh8g0c5pGTwODe8i5XFK7bZ0"
    CREDENTIALS_FILE = "onsen-scraping-e41c80c00b93.json"
    
    print("🚀 4-Spa Mirror Data Creator")
    print("Creating realistic projections for client's 4-spa resort...")
    print()
    
    # Check if credentials file exists
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"❌ Credentials file not found: {CREDENTIALS_FILE}")
        print("Please ensure the Google service account JSON file is in the current directory.")
        return False
    
    try:
        # Initialize creator
        creator = FourSpaMirrorCreator(SHEET_ID, CREDENTIALS_FILE)
        
        # Create all 4-spa mirror data
        success = creator.create_all_4spa_mirrors()
        
        if success:
            print("\n🎯 Next Steps for Client:")
            print("1. Review the new 4-spa projection tabs")
            print("2. Compare with competitor data to validate assumptions")
            print("3. Adjust performance factor if needed (currently 85%)")
            print("4. Use projections for business planning and financial modeling")
            
        return success
        
    except Exception as e:
        print(f"\n❌ Error during 4-spa mirror creation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ 4-Spa mirror data created successfully!")
    else:
        print("\n❌ 4-Spa mirror data creation failed.")
