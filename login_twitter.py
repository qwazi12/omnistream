import os
import time
from playwright.sync_api import sync_playwright

def get_netscape_cookies(context):
    """Convert Playwright cookies to Netscape format (required by yt-dlp)"""
    cookies = context.cookies()
    netscape_lines = ["# Netscape HTTP Cookie File"]
    
    for cookie in cookies:
        domain = cookie['domain']
        flag = 'TRUE' if domain.startswith('.') else 'FALSE'
        path = cookie['path']
        secure = 'TRUE' if cookie['secure'] else 'FALSE'
        expiration = int(cookie['expires']) if 'expires' in cookie else 0
        name = cookie['name']
        value = cookie['value']
        
        netscape_lines.append(
            f"{domain}\t{flag}\t{path}\t{secure}\t{expiration}\t{name}\t{value}"
        )
        
    return "\n".join(netscape_lines)

def main():
    print("="*60)
    print("🐦 OmniStream Twitter/X Login Helper")
    print("="*60)
    print("1. A browser window will open.")
    print("2. Please log in to X.com (Twitter).")
    print("3. Once you reach the HOME page, the script will capture cookies.")
    print("4. The window will close automatically.")
    print("="*60)
    
    with sync_playwright() as p:
        # Launch visible browser (so user can login)
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
             viewport={'width': 1280, 'height': 800}
        )
        page = context.new_page()
        
        try:
            print("\n🚀 Opening X.com/login...")
            page.goto("https://x.com/login")
            
            print("⏳ Waiting for you to log in...")
            
            # Smart wait: Check for 'home' in URL or specific home elements
            # Timeout after 300 seconds (5 mins)
            # We poll every second
            start_time = time.time()
            logged_in = False
            
            while time.time() - start_time < 300:
                url = page.url
                if "x.com/home" in url or "twitter.com/home" in url:
                    logged_in = True
                    break
                
                # Also check for specific element that implies login (e.g. valid nav bar)
                try:
                    if page.is_visible('[data-testid="AppTabBar_Home_Link"]'):
                        logged_in = True
                        break
                except: pass
                
                time.sleep(1)
            
            if logged_in:
                print("\n✅ Login detected!")
                print("🍪 Capturing cookies...")
                time.sleep(2) # Wait a sec for all cookies to set
                
                cookie_content = get_netscape_cookies(context)
                
                # Save to cookies.txt
                with open("cookies.txt", "w") as f:
                    f.write(cookie_content)
                
                print(f"✓ Saved to: {os.path.abspath('cookies.txt')}")
                print("\n🎉 You can now run the Twitter downloader!")
            else:
                print("\n❌ Timeout: Login not detected within 5 minutes.")
                
        except Exception as e:
            print(f"\n❌ process interrupted: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    main()
