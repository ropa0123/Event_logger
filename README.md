# Schedule Event Logging System - Web Application

A modern web-based schedule event logging system built with Flask, ready for deployment on Vercel.

## Features

- 🔐 User authentication (admin and regular users)
- 📅 Event management (create, read, update, delete)
- 📊 Dashboard with statistics
- 🔍 Filter events by date and client
- 📥 Export events to CSV
- 👥 User management (admin only)
- 📱 Responsive design
- 🔔 **Alert System:**
  - Sound alerts for upcoming events
  - Browser popup notifications
  - In-app modal alerts with full event details
  - Automatic polling every 30 seconds
  - Configurable alert timing (minutes before event)

## Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   python app.py
   ```

3. **Access the application:**
   - Open your browser and navigate to `http://localhost:5000`
   - Default credentials:
     - Admin: `admin` / `admin123`
     - User: `user` / `user123`

## Deployment to Vercel

### Prerequisites
- [Vercel account](https://vercel.com/signup)
- [Vercel CLI](https://vercel.com/docs/cli) (optional, for command-line deployment)

### Method 1: Deploy via Vercel CLI

1. **Install Vercel CLI:**
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel:**
   ```bash
   vercel login
   ```

3. **Deploy:**
   ```bash
   vercel
   ```

4. **Follow the prompts:**
   - Set up and deploy? `Y`
   - Which scope? (select your account)
   - Link to existing project? `N`
   - Project name: (enter your desired project name)
   - Directory: `./` (current directory)
   - Overwrite settings? `N`

5. **Set environment variable (important for production):**
   ```bash
   vercel env add SECRET_KEY
   ```
   Enter a secure random string when prompted.

6. **Production deployment:**
   ```bash
   vercel --prod
   ```

### Method 2: Deploy via Vercel Dashboard

1. **Push your code to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-github-repo-url>
   git push -u origin main
   ```

2. **Import project in Vercel:**
   - Go to [Vercel Dashboard](https://vercel.com/dashboard)
   - Click "Add New Project"
   - Import your GitHub repository
   - Vercel will auto-detect the Flask application

3. **Configure environment variables:**
   - In Project Settings → Environment Variables
   - Add `SECRET_KEY` with a secure random value

4. **Deploy:**
   - Click "Deploy"
   - Your app will be live at `https://your-project.vercel.app`

## Important Notes

### Data Persistence

⚠️ **Warning:** Vercel serverless functions have read-only file systems. The current implementation stores data in JSON files (`users.json` and `schedule_log.json`), which **will not persist** across deployments in a serverless environment.

For production use, you should integrate a database:

**Recommended options:**
- **Vercel Postgres** (PostgreSQL)
- **MongoDB Atlas** (free tier available)
- **Supabase** (PostgreSQL with real-time features)
- **PlanetScale** (MySQL-compatible)

### Environment Variables

Set these environment variables in Vercel:

- `SECRET_KEY` (required): A secure random string for session encryption
  ```bash
  # Generate a secure key:
  python -c "import secrets; print(secrets.token_hex(32))"
  ```

## Project Structure

```
.
├── app.py                 # Main Flask application
├── templates/             # HTML templates
│   ├── base.html         # Base template with navigation
│   ├── login.html        # Login page
│   ├── dashboard.html    # Dashboard with stats
│   ├── events.html       # Events list
│   ├── add_event.html    # Add event form
│   ├── edit_event.html   # Edit event form
│   └── users.html        # User management (admin)
├── users.json            # User data (not persistent on Vercel)
├── schedule_log.json     # Event data (not persistent on Vercel)
├── requirements.txt      # Python dependencies
├── vercel.json           # Vercel configuration
├── .vercelignore        # Files to ignore in deployment
└── README.md            # This file
```

## Migrating from Desktop GUI

This web application replaces the previous `web_app.py` desktop GUI application. Key differences:

- **Access:** Browser-based instead of desktop application
- **Multi-user:** Multiple users can access simultaneously
- **No installation:** No need to install customtkinter or plyer
- **Cloud deployment:** Can be accessed from anywhere
- **Enhanced Alerts:** Web-based browser notifications + sound + in-app modals (better than desktop notifications)

## How Alerts Work

The application automatically checks for upcoming events every 30 seconds and displays alerts when an event is approaching:

1. **Browser Notifications:** Desktop/mobile notifications (requires permission)
2. **Sound Alert:** Plays an audio notification
3. **Modal Popup:** Shows a detailed popup with event information

**To enable alerts:**
- When you first log in, click anywhere on the page to grant notification permissions
- Keep the browser tab open (alerts work even if tab is not focused)
- Set the "Alert Minutes Before" field when creating events (default: 5 minutes)

**Note:** Browser notifications only work when the browser tab is open. For production use with always-on alerts, consider integrating with services like:
- Twilio for SMS alerts
- SendGrid for email notifications
- Slack/Discord webhooks
- Push notification services (OneSignal, Firebase)

## Security Recommendations

1. **Change default passwords** immediately after deployment
2. **Use a strong SECRET_KEY** in production
3. **Enable HTTPS** (Vercel provides this by default)
4. **Implement database storage** for production use
5. **Add rate limiting** for login attempts
6. **Regular backups** of data if using file-based storage

## Support

For issues or questions about deployment, consult:
- [Vercel Documentation](https://vercel.com/docs)
- [Flask Documentation](https://flask.palletsprojects.com/)

## License

This project is provided as-is for internal use.
