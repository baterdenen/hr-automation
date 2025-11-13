# HR Course Automation

Automatically registers new course participants and tracks emails in Google Sheets.

## 📁 Files

```
hr_automation/
├── main.py              # Main automation script
├── credentials.json     # Google Sheets credentials (you provide)
└── README.md           # This file
```

## 🚀 Quick Start

### 1. Setup Credentials

Place your `credentials.json` in this folder:
```bash
cp /path/to/credentials.json hr_automation/
```

### 2. Configure

Edit `main.py` lines 240-243:
```python
USERNAME = "your_username"
PASSWORD = "your_password"
SPREADSHEET_ID = "your_spreadsheet_id"
COURSE_IDS = [8469, 8475, 8471]  # Your course IDs
```

### 3. Run

```bash
cd /Volumes/DataHD/runs/hr_automation
/usr/bin/python3 main.py
```

## 📊 Google Sheets Setup

1. Create spreadsheet: https://sheets.google.com/
2. Name it: "HR Course Participants"
3. Share with: `hr-automation@chagnuur.iam.gserviceaccount.com`
4. Copy the spreadsheet ID from URL
5. Update `SPREADSHEET_ID` in `main.py`

## ⏰ Schedule Automation

### Run every 4 hours:

```bash
crontab -e
```

Add:
```
0 */4 * * * cd /Volumes/DataHD/runs/hr_automation && /usr/bin/python3 main.py >> logs.txt 2>&1
```

## 🔧 Requirements

```bash
pip install selenium gspread google-auth
```

## 📝 How It Works

1. Logs into HR system
2. Checks each course for NEW pending participants
3. Registers them automatically
4. Extracts their emails
5. Saves to Google Sheets with status "Pending"
6. You manage emails from Google Sheets

## 🎯 What Happens

- **First run:** Registers all pending → Saves emails
- **Next runs:** Only processes NEW pending participants
- **Result:** Time efficient! Only 5-10 people instead of 100+

## 📧 Email Management

After script runs:
1. Open your Google Sheet
2. See new participants in course tabs
3. Send emails using Google Sheets features
4. Update "Email Sent" column

## 🌐 Cloud Deployment (Optional)

For 24/7 automation without your laptop:
- Google Cloud Run (FREE tier)
- PythonAnywhere ($5/month)
- Deploy and forget!

## 📞 Support

- Email: nyam.bagi@gmail.com
- Work: info@chagnuur.mn

---

**Last Updated:** November 7, 2025
