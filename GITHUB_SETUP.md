# HR Course Automation - GitHub Actions Setup

This automation runs every 4 hours to register new course participants and track them in Google Sheets.

## 🚀 Quick Setup Guide

### 1. Create a GitHub Repository
```bash
cd /Volumes/DataHD/runs/hr_automation
git init
git add .
git commit -m "Initial commit: HR automation"
```

Create a new repository on GitHub, then:
```bash
git remote add origin https://github.com/YOUR_USERNAME/hr-automation.git
git push -u origin main
```

### 2. Add Secrets to GitHub

Go to your repository on GitHub → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add these 4 secrets:

| Secret Name | Value | Description |
|------------|-------|-------------|
| `HR_USERNAME` | `ЖЯ87101312` | Your HR system username |
| `HR_PASSWORD` | `MqameaSd63WMrqd` | Your HR system password |
| `SPREADSHEET_ID` | `1iKkOvTrujkfvShB0npGnyNktIBVuZU6iU9RBgc4DZME` | Google Sheets ID |
| `GOOGLE_CREDENTIALS_JSON` | *[Full JSON content]* | Service account credentials |

#### How to get `GOOGLE_CREDENTIALS_JSON`:
1. Open your `credentials.json` file
2. Copy the **entire content** (it's a JSON object)
3. Paste it directly as the secret value (GitHub will handle it)

Example format:
```json
{
  "type": "service_account",
  "project_id": "your-project",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "...",
  "client_id": "...",
  "auth_uri": "...",
  "token_uri": "...",
  "auth_provider_x509_cert_url": "...",
  "client_x509_cert_url": "..."
}
```

### 3. Enable GitHub Actions

1. Go to your repository → **Actions** tab
2. GitHub will detect the workflow file automatically
3. Click **"I understand my workflows, go ahead and enable them"**

### 4. Test the Automation

**Option A: Wait for scheduled run** (next 4-hour mark: 00:00, 04:00, 08:00, 12:00, 16:00, 20:00 UTC)

**Option B: Manual trigger**
1. Go to **Actions** tab
2. Click **"HR Course Automation"** workflow
3. Click **"Run workflow"** → **"Run workflow"**

### 5. Monitor Execution

- Go to **Actions** tab to see workflow runs
- Click on any run to see detailed logs
- Check your Google Sheet for new participants

## 📅 Schedule

The automation runs **6 times per day** (every 4 hours):
- 00:00 UTC (8:00 AM Mongolia time)
- 04:00 UTC (12:00 PM Mongolia time)
- 08:00 UTC (4:00 PM Mongolia time)
- 12:00 UTC (8:00 PM Mongolia time)
- 16:00 UTC (12:00 AM Mongolia time)
- 20:00 UTC (4:00 AM Mongolia time)

> **Note:** UTC is 8 hours behind Mongolia time (ULAT)

## 🔧 Customizing the Schedule

Edit `.github/workflows/automation.yml` and change the cron expression:

```yaml
schedule:
  - cron: '0 0,4,8,12,16,20 * * *'  # Current: every 4 hours
  # - cron: '0 */4 * * *'            # Alternative: every 4 hours
  # - cron: '0 0,8,16 * * *'         # Every 8 hours (3 times/day)
  # - cron: '0 0 * * *'              # Once daily at midnight UTC
```

[Cron syntax reference](https://crontab.guru/)

## 📊 View Results

Your Google Sheet: https://docs.google.com/spreadsheets/d/1iKkOvTrujkfvShB0npGnyNktIBVuZU6iU9RBgc4DZME

## 🐛 Troubleshooting

### Workflow fails with "Permission denied"
- Check that all 4 secrets are added correctly
- Verify `GOOGLE_CREDENTIALS_JSON` is valid JSON

### No participants found
- The script only processes newly registered participants
- If all participants are already registered, it will skip them

### Chrome/ChromeDriver errors
- GitHub Actions automatically installs compatible versions
- If issues persist, check the Actions logs for details

## 💰 GitHub Actions Usage

- **Free tier:** 2,000 minutes/month for private repos
- **Public repos:** Unlimited
- **This workflow:** ~3-5 minutes per run
- **Monthly usage:** ~540-900 minutes (well within free tier)

## 📝 Files Structure

```
hr_automation/
├── main.py                    # Main automation script
├── requirements.txt           # Python dependencies
├── credentials.json           # Google service account (local only, not pushed)
├── .github/
│   └── workflows/
│       └── automation.yml     # GitHub Actions workflow
└── README.md                  # This file
```

## 🔒 Security Notes

- Never commit `credentials.json` to GitHub
- All sensitive data is stored in GitHub Secrets (encrypted)
- Add `credentials.json` to `.gitignore`

## 🎉 Done!

Your automation is now running in the cloud, completely independent of your local computer.
