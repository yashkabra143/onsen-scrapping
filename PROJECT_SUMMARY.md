# 📊 Onsen Scraper - High-Level Project Summary (9-Spa Model)

## 🎯 Project Overview
This system scrapes competitor booking data from Onsen Hot Tubs in Wanaka, New Zealand, to support strategic business planning for hot tub and sauna resort operations. The data helps with pricing strategy, demand forecasting, and competitive analysis.

**Updated Business Model**: Now assumes **9 spas available for rental per hour slot** to model a larger operation scale.

## 💰 Revenue Model & Guest Segments

The code implements a sophisticated revenue model based on three guest segments:

### Guest Type Distribution:
```python
GUEST_TYPES = {
    'couples': {
        'price': 175,      # $175 per booking
        'guests': 2,       # 2 people
        'percentage': 0.6  # 60% of market
    },
    'groups': {
        'price': 260,      # $260 average per booking  
        'guests': 3.5,     # 3-4 adults average
        'percentage': 0.2  # 20% of market
    },
    'families': {
        'price': 235,      # $235 per booking
        'guests': 4,       # 4 people (2 adults + 2 children)
        'percentage': 0.2  # 20% of market
    }
}
```

### Time-Based Revenue Logic:
- **Before 6 PM**: All guest types can book (60% couples, 20% groups, 20% families)
- **After 6 PM**: Families excluded (75% couples, 25% groups) - adults only

### Revenue Calculation Example (9-Spa Model):
```python
# For a time slot with 6 out of 9 spas booked at 3 PM:
Revenue = (6 × 0.6 × $175) + (6 × 0.2 × $260) + (6 × 0.2 × $235) = $1,206

# For the same 6 bookings at 8 PM:
Revenue = (6 × 0.75 × $175) + (6 × 0.25 × $260) = $1,177.50

# Peak capacity (all 9 spas booked at 3 PM):
Revenue = (9 × 0.6 × $175) + (9 × 0.2 × $260) + (9 × 0.2 × $235) = $1,809
```

## 🕐 Seasonal Operating Hours

The code adjusts for seasonal variations:

### Spring Season (Aug 21 - Oct 31):
- **Hours**: 9:00 AM - 11:00 PM (14 hour slots)
- **Peak tourist season** with extended hours

### Winter/Other Seasons:
- **Hours**: 10:00 AM - 11:00 PM (13 hour slots)
- **Standard operating hours**

## 📈 Data Collection Strategy

### Multi-Horizon Approach:
1. **SameDay** - Current availability (operational decisions)
2. **SevenDays** - Next week (short-term planning)
3. **ThirtyDays** - Next month (medium-term forecasting)
4. **SixtyDays** - 2 months out (seasonal planning)
5. **NinetyDays** - 3 months out (strategic planning)

### Dual Data Storage:
1. **Snapshot Tabs** - Current state (replaced each run)
2. **Historical Data** - Time series (appended each run)

## 🏢 Business Modeling Features (9-Spa Scale)

### Capacity Assumptions:
- **Max capacity per slot**: 9 spas (updated from 4)
- **Availability range**: 0-9 spas per time slot
- **Revenue scaling**: Linear with number of bookings

### Mirror Data Generation:
- Creates comparison datasets with 5-10% lower bookings
- Helps model conservative scenarios
- Provides range estimates for business planning

### Competitive Benchmarking:
- **Competitor benchmark**: Onsen's performance scaled to 9-spa capacity
- **Conservative modeling**: Mirror data provides 5-10% lower projections

## 🔄 Scraping Schedule

Runs automatically on Railway:
- **Every 4 hours**: Captures booking velocity
- **Peak times**: 8 AM, 12 PM, 4 PM, 8 PM NZ time
- **Purpose**: Track how fast slots fill up throughout the day

## 📊 Key Metrics Captured (9-Spa Model)

1. **Occupancy Rate**: Percentage of 9 spas booked per slot
2. **Revenue per Slot**: Based on guest mix (up to $1,809 at full capacity)
3. **Booking Velocity**: How fast slots fill up
4. **Lead Time**: Days between booking and visit
5. **Seasonal Patterns**: Demand variations by season

## 💡 Strategic Insights Enabled

### Pricing Strategy:
- Compare revenue per guest type
- Identify premium time slots
- Optimize pricing by season

### Capacity Planning:
- Understand peak demand periods (up to 9 spas)
- Plan staffing requirements for larger operation
- Design operating hours for maximum utilization

### Marketing Focus:
- Target high-value segments (couples still 60%)
- Family-friendly hours (before 6 PM)
- Adult-only evening experiences

### Competitive Positioning:
- Scale competitor data to 9-spa operation
- Model various occupancy scenarios (50%, 75%, 90%)
- Focus on underserved time slots

## 🎯 Business Model Assumptions (9-Spa Scale)

Your resort modeling now uses:
```python
# Configurable parameters in Business Modeling tab
Number of Spas: 9            # Updated from 4
Max Capacity per Slot: 9     # 9 people maximum
Competitor Match %: 75%      # Achieve 75% of scaled competitor occupancy
Price Premium: 5%            # Price 5% higher than competitor
Fixed Costs/Month: $45,000   # Scaled for larger operation
Marketing Budget: $8,000     # Increased for 9-spa operation
Variable Cost %: 30%         # Remains consistent
```

## 📈 Revenue Projections (9-Spa Model)

Based on the updated model with 80% average occupancy:
- **Average Bookings per Slot**: 7.2 spas (80% of 9)
- **Afternoon Revenue per Slot**: ~$1,447 (families allowed)
- **Evening Revenue per Slot**: ~$1,413 (no families)
- **Daily Revenue Potential**: ~$18,500 (13 slots at 80% capacity)
- **Monthly Revenue Potential**: ~$555,000
- **Annual Revenue Potential**: ~$6,750,000

### Scaled Revenue Comparison:
- **4-Spa Model**: ~$768,690 annually
- **9-Spa Model**: ~$6,750,000 annually (8.8x scaling factor)

## 🔍 Data Quality Features

- **CSV Backups**: Every scrape saved with 9-spa notation
- **Error Handling**: Screenshots on failure
- **Historical Tracking**: Complete audit trail with capacity model noted
- **Timezone Aware**: Auckland/Pacific time
- **Capacity Validation**: All calculations bounded to 0-9 spa range

## 🚀 Implementation Changes

### Code Updates:
1. **MAX_CAPACITY_PER_SLOT = 9** (updated from 4)
2. **Availability calculations**: Now range 0-9 instead of 0-4
3. **Mirror data generation**: Scales to 9-spa capacity
4. **Revenue calculations**: Same percentages, larger absolute numbers
5. **Historical tab**: Now labeled "📈 Historical Data (9-Spa Model)"

### File Naming:
- **New scraper**: `onsen_scraper_v4_9spas.py`
- **CSV exports**: Include "_9spas" suffix
- **Error logs**: Include 9-spa notation

---

## 📝 Executive Summary:

**Purpose**: Model a 9-spa hot tub resort operation using competitor data from Onsen in Wanaka, NZ.

**Key Scaling**: Revenue potential scales from ~$769K annually (4 spas) to ~$6.75M annually (9 spas) at 80% capacity.

**Revenue Logic**: Maintains sophisticated guest segmentation (60% couples, 20% groups, 20% families) with time-based restrictions, now applied to 9-spa capacity.

**Conservative Approach**: Mirror data at 5-10% below competitor provides realistic targets even at larger scale.

**Operational Intelligence**: Tracks occupancy rates, booking velocity, and revenue patterns across multiple time horizons for a substantial spa operation.

This system now models a significantly larger operation while maintaining the same sophisticated approach to guest segmentation and revenue optimization! 🚀

## 🔄 Migration Notes

To switch from 4-spa to 9-spa model:
1. Use `onsen_scraper_v4_9spas.py` instead of `onsen_scraper_v4.py`
2. Historical data will be stored in separate tab to maintain data integrity
3. All new CSV exports will include 9-spa notation
4. Revenue calculations automatically scale to new capacity assumptions
