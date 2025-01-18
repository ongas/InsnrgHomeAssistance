# Project README

## Installation Instructions

### Step 1: Install Samba Share

1. Navigate to **Settings** -> **Add-ons** -> **ADD-ON STORE**.
2. Search for "Samba share" and install it.
3. After installation, go to the **Configuration** tab and enter your **Username**, **Password**, and **Workgroup name**.
4. Return to the **Info** tab and click **Start**.

### Step 2: Install Insnrg Integration

1. Open **File Explorer** and enter `\\<HOME_ASSISTANT_IP_ADDRESS>\` in the address bar.
2. Open the **config** folder. If it doesn't exist, create it.
3. Inside the **config** folder, locate the **custom_components** folder. If it doesn't exist, create it.
4. Copy the **insnrg** folder into the **custom_components** folder.
5. Restart Home Assistant by navigating to **Settings** -> **System**, clicking the power button in the top right corner, and selecting **Restart Home Assistant**.

### Step 3: Activate Insnrg Integration

1. Go to **Settings** -> **Devices & Services** -> **Add integration**.
2. Search for "Insnrg" and enter your **Username** and **Password**.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

**Note:** By using this code to access the Insnrg 3rd party API, you agree to Insnrg's Terms and Conditions.
