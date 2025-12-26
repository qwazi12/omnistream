# JDownloader 2 Installation Guide for macOS

## 📥 Download JDownloader 2

The download page is already open in your browser. Choose the appropriate version:

### Recommended Download (for most modern Macs)
**macOS Catalina, Big Sur, Monterey, Ventura, Sonoma**

Click the download link on the page for your macOS version.

---

## 🔧 Installation Steps

### 1. Download the Installer
- Click the download link for your macOS version
- The `.dmg` file will download to your Downloads folder

### 2. Install JDownloader
1. Open the downloaded `.dmg` file
2. Drag **JDownloader 2.app** to your Applications folder
3. Eject the DMG

### 3. First Launch
1. Open **Applications** folder
2. Right-click **JDownloader 2.app** → **Open**
3. Click **Open** when macOS warns about unidentified developer
4. JDownloader will start and may download updates

---

## 🔗 Connect to MyJDownloader (Required for OmniStream)

OmniStream uses the MyJDownloader API to communicate with JDownloader.

### Step 1: Create MyJDownloader Account
1. Go to: https://my.jdownloader.org/
2. Click **Register**
3. Create account with:
   - Email
   - Password
   - Username

### Step 2: Link JDownloader to Your Account
1. In JDownloader app, go to: **Settings** → **MyJDownloader**
2. Enter your credentials:
   - **Email:** your MyJDownloader email
   - **Password:** your MyJDownloader password
3. Click **Connect**
4. Wait for status to show: **"Connected"** ✅

### Step 3: Verify Connection
1. Go to https://my.jdownloader.org/
2. Login with your credentials
3. You should see your device listed

---

## ⚙️ Configure OmniStream to Use JDownloader

OmniStream will automatically detect JDownloader if it's running.

### Verify Detection
1. Keep JDownloader running
2. Restart OmniStream: `./run.sh`
3. Check the header - you should see:
   - **"📦 JDownloader: Connected"** (green) ✅

Instead of:
   - **"📦 JDownloader: Not Running"** (orange) ⚠️

---

## 🧪 Test JDownloader Integration

### Test with a File Host URL

Try downloading from a file hosting site:

**Example URLs to test:**
- Mega: `https://mega.nz/file/...`
- MediaFire: `https://www.mediafire.com/file/...`
- Google Drive: `https://drive.google.com/file/d/...`

**Steps:**
1. Paste a file host URL in OmniStream
2. Click **START DOWNLOAD**
3. OmniStream will automatically route to JDownloader
4. Check console log for: **"Selected engine: JDOWNLOADER"**

---

## 🔍 Troubleshooting

### "JDownloader: Not Running"

**Solution:**
1. Make sure JDownloader 2 app is open
2. Check it's not just in the menu bar - open the main window
3. Restart OmniStream

### "JDownloader API: Not Configured"

**Solution:**
1. Open JDownloader
2. Go to: **Settings** → **MyJDownloader**
3. Verify credentials are entered
4. Click **Connect** again
5. Wait for "Connected" status

### "Connection Failed"

**Solution:**
1. Check internet connection
2. Verify MyJDownloader account is active
3. Try disconnecting and reconnecting in JDownloader settings
4. Restart JDownloader app

---

## 📋 What JDownloader Enables

With JDownloader installed, OmniStream can now download from:

✅ **File Hosting Services:**
- Mega.nz
- MediaFire
- RapidGator
- Uploaded.net
- 1fichier.com
- Zippyshare
- And 100+ more!

✅ **Cloud Storage:**
- Google Drive (public links)
- Dropbox (public links)
- OneDrive (public links)

**Without JDownloader**, these sites would fail or require manual download.

---

## 🎯 Quick Reference

**JDownloader Status in OmniStream:**
- 🟢 **Connected** - Ready to use
- 🟠 **Not Running** - Start JDownloader app
- 🔴 **Not Configured** - Set up MyJDownloader

**Keep JDownloader running in the background for best results!**

---

## ✅ Installation Complete Checklist

- [ ] Downloaded JDownloader 2 for macOS
- [ ] Installed to Applications folder
- [ ] Created MyJDownloader account
- [ ] Connected JDownloader to MyJDownloader
- [ ] Verified "Connected" status
- [ ] Restarted OmniStream
- [ ] Confirmed green "JDownloader: Connected" in OmniStream

**Ready to download from file hosting sites! 🚀**
