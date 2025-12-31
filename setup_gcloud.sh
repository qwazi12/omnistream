#!/bin/bash
# OmniStream - Automated Google Cloud Setup
# Uses gcloud CLI to configure all APIs and credentials

set -e  # Exit on error

PROJECT_ID="manhwa-engine"
SERVICE_ACCOUNT_NAME="omnistream-bot"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "=========================================="
echo "🚀 OmniStream GCloud Setup"
echo "=========================================="
echo "Project: $PROJECT_ID"
echo ""

# Step 1: Install gcloud (if needed)
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found!"
    echo ""
    echo "Install with:"
    echo "  brew install google-cloud-sdk"
    echo ""
    echo "Or download from:"
    echo "  https://cloud.google.com/sdk/docs/install-sdk"
    exit 1
fi

echo "✅ gcloud CLI found: $(gcloud --version | head -1)"
echo ""

# Step 2: Authenticate
echo "🔐 Authenticating..."
gcloud auth login --brief

# Step 3: Set project
echo "📁 Setting project to: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# Step 4: Enable required APIs
echo ""
echo "🔧 Enabling APIs..."
APIs=(
    "youtube.googleapis.com"
    "sheets.googleapis.com"
    "drive.googleapis.com"
    "generativelanguage.googleapis.com"
)

for api in "${APIs[@]}"; do
    echo "  Enabling $api..."
    gcloud services enable $api --quiet
done

echo "✅ All APIs enabled"

# Step 5: Create service account
echo ""
echo "👤 Creating service account: $SERVICE_ACCOUNT_NAME"

if gcloud iam service-accounts describe $SERVICE_ACCOUNT_EMAIL &>/dev/null; then
    echo "  ⚠️  Service account already exists"
else
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
        --display-name="OmniStream Automation Bot" \
        --description="Service account for OmniStream automated posting"
    echo "  ✅ Service account created"
fi

# Step 6: Grant permissions
echo ""
echo "🔑 Granting permissions..."
# Note: Service accounts don't get project-level Drive/Sheets permissions
# They get access when you share specific files/folders with them
echo "  ⚠️  Service account will need access to specific files:"
echo "     Share your Google Sheet with: $SERVICE_ACCOUNT_EMAIL"
echo "     Share your Drive folder with: $SERVICE_ACCOUNT_EMAIL"
echo ""
echo "  For now, granting basic permissions..."

# Grant service account basic permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/serviceusage.serviceUsageConsumer" \
    --quiet

echo "✅ Basic permissions granted"

# Step 7: Generate credentials
echo ""
echo "🔐 Generating service account credentials..."
CREDS_FILE="service_account.json"

if [ -f "$CREDS_FILE" ]; then
    echo "  ⚠️  $CREDS_FILE already exists. Backing up..."
    mv "$CREDS_FILE" "${CREDS_FILE}.backup.$(date +%s)"
fi

gcloud iam service-accounts keys create $CREDS_FILE \
    --iam-account=$SERVICE_ACCOUNT_EMAIL

echo "✅ Credentials saved to: $CREDS_FILE"

# Step 8: Setup YouTube OAuth
echo ""
echo "📺 YouTube OAuth Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "For YouTube uploads, you need OAuth credentials:"
echo ""
echo "1. Go to: https://console.cloud.google.com/apis/credentials"
echo "2. Create OAuth 2.0 Client ID"
echo "3. Application type: Desktop app"
echo "4. Name: OmniStream YouTube"
echo "5. Download and save as: youtube_credentials.json"
echo ""
read -p "Press ENTER when you have youtube_credentials.json ready..."

if [ -f "youtube_credentials.json" ]; then
    echo "✅ Found youtube_credentials.json"
else
    echo "⚠️  youtube_credentials.json not found - you'll need this for YouTube posting"
fi

# Step 9: Get Gemini API Key
echo ""
echo "🤖 Gemini AI Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "For AI metadata generation, you need a Gemini API key:"
echo ""
echo "1. Go to: https://aistudio.google.com/app/apikey"
echo "2. Create API key for project: $PROJECT_ID"
echo "3. Copy the key"
echo ""
read -p "Paste your Gemini API key: " GEMINI_KEY

if [ -n "$GEMINI_KEY" ]; then
    echo "export GEMINI_API_KEY='$GEMINI_KEY'" >> ~/.zshrc
    echo "export GEMINI_API_KEY='$GEMINI_KEY'" >> ~/.bashrc
    export GEMINI_API_KEY="$GEMINI_KEY"
    echo "✅ Gemini API key saved to shell config"
else
    echo "⚠️  No API key provided - AI metadata generation will not work"
fi

# Step 10: Summary
echo ""
echo "=========================================="
echo "✅ SETUP COMPLETE!"
echo "=========================================="
echo ""
echo "Created files:"
echo "  • service_account.json (for Sheets/Drive)"
if [ -f "youtube_credentials.json" ]; then
    echo "  • youtube_credentials.json (for YouTube)"
fi
echo ""
echo "Environment variables:"
echo "  • GEMINI_API_KEY (for AI metadata)"
echo ""
echo "Next steps:"
echo "  1. Install Python dependencies:"
echo "     pip install -r requirements.txt"
echo ""
echo "  2. Setup Google Sheet:"
echo "     python3 sheets_manager.py --setup"
echo ""
echo "  3. Setup Facebook (optional):"
echo "     python3 facebook_poster.py --setup"
echo ""
echo "  4. Test connections:"
echo "     python3 post_manager.py --test"
echo ""
echo "🎉 Ready to start auto-posting!"
echo "=========================================="
