# Quick Deployment Guide

## ✅ What's Been Created

Your desktop GUI application has been successfully converted to a modern Flask web application with **sound and popup alerts**.

## 🎯 New Features

### Alert System (Triple Notification)
When an event is approaching, users receive:
1. **🔊 Sound Alert** - Audio notification plays automatically
2. **💬 Browser Notification** - OS-level desktop notification
3. **📋 Modal Popup** - Detailed in-app alert with full event information

### Other Features
- Modern responsive UI with gradient design
- User authentication (admin/user roles)
- Full CRUD for events
- Statistics dashboard
- CSV export
- User management (admin only)

## 🚀 Testing Locally

1. **Start the server:**
   ```bash
   python app.py
   ```

2. **Open browser:**
   - Go to `http://localhost:5000`
   - Login with: `admin` / `admin123`

3. **Test alerts:**
   - Create an event with time slot starting in 6 minutes (e.g., if it's 2:00 PM, set "14:06-15:00")
   - Set "Alert Minutes Before" to 5
   - Click anywhere on the page to grant notification permissions
   - Wait 1 minute - you should see the alert!

## 📦 Deploy to Vercel

### Option 1: Vercel CLI (Fastest)

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy
vercel

# Set secret key
vercel env add SECRET_KEY
# (paste a secure random string)

# Production deployment
vercel --prod
```

### Option 2: GitHub + Vercel Dashboard

1. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Flask event logger with alerts"
   git branch -M main
   git remote add origin YOUR_GITHUB_REPO_URL
   git push -u origin main
   ```

2. **Deploy on Vercel:**
   - Go to https://vercel.com/dashboard
   - Click "Add New Project"
   - Import your GitHub repository
   - Add environment variable: `SECRET_KEY` = (generate secure key)
   - Click "Deploy"

## ⚠️ Important Notes

### Data Persistence
The app currently uses JSON files which **won't persist on Vercel** serverless. For production:
- Integrate a database (Vercel Postgres, MongoDB Atlas, Supabase)
- Or use persistent storage service

### Alert Limitations
- Browser notifications only work when tab is open
- For always-on alerts, integrate:
  - Twilio (SMS)
  - SendGrid (Email)
  - Slack/Discord webhooks
  - Push notification services

### Security
1. Change default passwords immediately
2. Use strong `SECRET_KEY` in production
3. Enable HTTPS (Vercel provides this)
4. Add rate limiting for login

## 📁 File Structure

```
templates/
├── app.py                    # Main Flask application
├── templates/                # HTML templates
│   ├── base.html            # Base with alert system
│   ├── login.html           # Login page
│   ├── dashboard.html       # Dashboard
│   ├── events.html          # Events list
│   ├── add_event.html       # Add event form
│   ├── edit_event.html      # Edit event form
│   └── users.html           # User management
├── users.json               # User data
├── schedule_log.json        # Event data
├── vercel.json              # Vercel config
├── requirements.txt         # Dependencies
├── .vercelignore           # Deployment exclusions
└── README.md               # Full documentation
```

## 🧪 Testing the Alert System

### Create a Test Event
1. Login as admin
2. Click "Add Event"
3. Fill in:
   - Time Slot: (Current time + 6 minutes, e.g., "14:06-15:00")
   - Client Name: "Test Client"
   - Delivery Type: "Online"
   - Alert Minutes Before: 5
4. Create event
5. Wait ~1 minute
6. You should see:
   - Sound plays
   - Browser notification appears
   - Modal popup shows event details

## 🔧 Troubleshooting

### No sound playing?
- Check browser permissions
- Unmute the browser tab
- Try clicking on page first (browsers block auto-play)

### No browser notifications?
- Click anywhere on the page to trigger permission request
- Check browser notification settings
- Ensure notifications aren't blocked for localhost

### Alerts not triggering?
- Check that event time is in future
- Verify "Alert Minutes Before" is set
- Check browser console for errors (F12)
- Alerts poll every 30 seconds, so wait up to 30s

## 📚 Next Steps

1. ✅ Test locally
2. ✅ Deploy to Vercel
3. ⚠️ Integrate database for production
4. ⚠️ Change default passwords
5. ⚠️ Set strong SECRET_KEY
6. 🎯 Optional: Add SMS/Email alerts for 24/7 notifications

## 🆘 Support

- Flask docs: https://flask.palletsprojects.com/
- Vercel docs: https://vercel.com/docs
- Web Notifications API: https://developer.mozilla.org/en-US/docs/Web/API/Notifications_API

---

**Ready to deploy!** 🚀
