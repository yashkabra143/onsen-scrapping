# 🏊 Onsen Hot Tub Scraper - 9 Spa Business Model

Automated web scraper for tracking Onsen hot tub booking data in Wanaka, NZ. Built to support competitive analysis and business planning for a new 4-spa resort.

## 🎯 Purpose

This system scrapes competitor booking data from Onsen (9 hot tubs) to inform:
- Pricing strategy
- Demand forecasting  
- Capacity planning
- Marketing decisions

## 💰 Business Model

### Guest Segmentation
- **Couples**: 60% of market @ $175 (2 guests)
- **Groups**: 20% of market @ $260 (3-4 guests)
- **Families**: 20% of market @ $235 (4 guests, pre-6pm only)

### Key Assumptions
- Onsen operates with **9 hot tubs** available per hour
- Your planned resort: 4 hot tubs (44% of competitor capacity)
- Operating hours vary by season:
  - Spring (Aug 21 - Oct 31): 9am-11pm
  - Winter/Other: 10am-11pm

## 📊 Data Collection

### Multi-Horizon Tracking
- **SameDay**: Current availability
- **SevenDays**: 1 week ahead
- **ThirtyDays**: 1 month ahead  
- **SixtyDays**: 2 months ahead
- **NinetyDays**: 3 months ahead

### Data Storage
1. **Snapshot Tabs**: Current state (replaced each run)
2. **Historical Data**: Time series (appended each run)
3. **Mirror Data**: Conservative estimates (5-10% reduction)

## 🚀 Deployment

### Railway Setup
1. Connect GitHub repo to Railway
2. Add environment variables (if any)
3. Deploy - Railway will use `railway.toml` config

### Local Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Test scraper (visible browser)
python onsen_scraper_v4_9spas.py

# Production mode (headless)
python onsen_scraper_v4_9spas.py --production
```

### Scheduling
Runs automatically via Railway cron:
- Every 4 hours
- Additional runs at 8am & 8pm NZ time

## 📁 Project Structure

```
onsen/
├── onsen_scraper_v4_9spas.py    # Main scraper (9-spa model)
├── sheets_writer.py              # Google Sheets integration
├── scheduler_fixed.py            # Scheduler for continuous runs
├── railway.toml                  # Railway deployment config
├── requirements.txt              # Python dependencies
├── onsen-scraping-*.json         # Google service account key
└── onsen_exports/               # CSV backup files
```

## 📈 Key Metrics Tracked

- **Occupancy Rate**: % of slots booked
- **Revenue per Slot**: Based on guest mix
- **Booking Velocity**: How fast slots fill
- **Seasonal Patterns**: Demand by season
- **Lead Time**: Days between booking and visit

## 🔧 Configuration

Edit `onsen_scraper_v4_9spas.py` to adjust:
- `MAX_CAPACITY_PER_SLOT`: Number of spas (currently 9)
- `GUEST_TYPES`: Pricing and distribution
- `SHEET_ID`: Google Sheets destination

## 📊 Google Sheets Structure

The scraper populates these tabs:
- **SameDay**, **SevenDays**, etc.: Current snapshots
- **SameDay_Mirror**, etc.: Conservative estimates
- **📈 Historical Data (9-Spa Model)**: All data over time

## 🛠️ Troubleshooting

1. **No data appearing**: Check `fallback_logs/` for screenshots
2. **Authentication errors**: Verify service account JSON file
3. **Railway issues**: Check deployment logs in Railway dashboard

## 📝 Notes

- All times in Auckland/Pacific timezone
- Revenue calculations account for time-based guest restrictions
- Mirror data provides conservative planning scenarios
- CSV backups saved locally for data recovery

---

Built for strategic planning of a 4-spa hot tub resort in Wanaka, NZ 🇳🇿
