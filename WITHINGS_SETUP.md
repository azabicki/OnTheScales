# Withings Integration Setup

This guide will help you set up Withings integration for your BouskiOnTheScales app.

## Prerequisites

1. A Withings account
2. A Withings developer account (free)

## Step 1: Create a Withings App

1. Go to [Withings Developer Portal](https://developer.withings.com/)
2. Sign in with your Withings account
3. Click "Create an App"
4. Fill in the required information:
   - **App Name**: BouskiOnTheScales (or any name you prefer)
   - **Description**: Health data sync for weight tracking
   - **Redirect URI**: `http://localhost:8501/manage_users` (for local development)
   - **Scope**: Select `user.metrics` to access weight and body composition data
5. Submit the form and note down your **Client ID** and **Client Secret**

## Step 2: Configure Your App

### Using Streamlit Secrets (Recommended)

1. Create a `.streamlit` folder in your project root if it doesn't exist
2. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`
3. Edit `.streamlit/secrets.toml` and add your credentials:

```toml
[withings]
client_id = "your_actual_client_id"
client_secret = "your_actual_client_secret"
redirect_uri = "http://localhost:8501/manage_users"
```

## Step 3: Deploy Your App (Optional)

If you're deploying your app to a cloud service:

1. Update the redirect URI in your Withings app settings to match your deployed URL
2. Update the `redirect_uri` in your configuration accordingly

## Step 4: Connect Users

1. Start your Streamlit app
2. Go to the "Manage Users" page
3. Select a user
4. In the "Withings Integration" section, click "Connect to Withings"
5. Complete the OAuth flow
6. The user's token will be saved automatically

## Step 5: Sync Data

1. Go to the "Measurements" page
2. Select the connected user
3. In the "Withings Data Sync" section:
   - Choose a date range
   - Click "Fetch Withings Data"
   - Select the measurements you want to import
   - Click "Import Selected"

## Features

- **Automatic Token Refresh**: Tokens are automatically refreshed when they expire
- **Import Tracking**: The app tracks which dates have been imported to avoid duplicates
- **Selective Import**: Choose which measurements to import using checkboxes
- **Data Conversion**: Withings absolute values are converted to percentages where appropriate

## Troubleshooting

### "Withings API credentials not configured"
- Make sure you've set up your credentials in either `.streamlit/secrets.toml` or environment variables
- Check that the file path and variable names are correct

### "Failed to authenticate with Withings"
- Verify your Client ID and Client Secret are correct
- Check that your redirect URI matches exactly (including protocol and port)
- Ensure your Withings app is approved and active

### "No measurements found"
- Check that you have measurements in your Withings account for the selected date range
- Verify that your Withings device is properly synced
- Make sure the date range includes dates when you took measurements

### Token Issues
- If tokens keep expiring, check your system clock is correct
- You can manually refresh tokens in the "Manage Users" page
- If all else fails, disconnect and reconnect the user

## Security Notes

- Never commit your actual credentials to version control
- Use environment variables or Streamlit secrets for production
- Tokens are stored locally in the `withings/tokens/` directory
- Consider encrypting token storage for production use

## API Limits

Withings API has rate limits. The app handles this gracefully, but if you encounter issues:
- Don't fetch data too frequently
- Use reasonable date ranges
- Contact Withings support if you need higher limits
