import os
import csv
import json
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify, render_template
import time  
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- PART 1: AI CONFIGURATION ---
...
GOOGLE_AI_API_KEY = "You thought!!!"


try:
    import google.generativeai as genai
    if GOOGLE_AI_API_KEY != "YOUR_API_KEY_HERE":
        genai.configure(api_key=GOOGLE_AI_API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash')
        # model = genai.GenerativeModel('gemini-1.0-pro')
        print("Google AI model configured.")
    else:
        print("WARNING: GOOGLE_AI_API_KEY not set. AI will be mocked.")
        model = None
except ImportError:
    print("Google AI library not found. AI functions will be mocked.")
    genai = None
    model = None



# --- PART 2: FLASK APP SETUP ---
app = Flask(__name__)


# Load our commodity codes from the CSV
def load_commodity_codes():
    codes = []
    try:
        with open('codes.csv', mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            # Skip the header row ("Class","Item","Description")
            header = next(reader, None)
            
            for row in reader:
                # row[0] is Class, row[1] is Item, row[2] is Description
                if row and len(row) >= 3: 
                    # This is our new, smarter code: "Class-Item"
                    combined_code = f"{row[0].strip()}-{row[1].strip()}" 
                    description = row[2].strip()
                    codes.append({"code": combined_code, "description": description})

    except FileNotFoundError:
        print("WARNING: 'codes.csv' not found. Using placeholder codes.")
        return [{"code": "915", "description": "CATERING SERVICES"}]
    except Exception as e:
        print(f"Error loading codes.csv: {e}")
        return [{"code": "ERROR", "description": "CSV Error"}]
    
    print(f"Successfully loaded {len(codes)} commodity codes.")
    return codes


COMMODITY_CODES = load_commodity_codes()
# Create a simple text block for the AI prompt
COMMODITY_CODES_TEXT = "\n".join([f"{c['code']}: {c['description']}" for c in COMMODITY_CODES])


# --- PART 3: CORE LOGIC  ---

def get_ai_matched_codes(description):
    '''
    Uses AI to match a user's description to our commodity codes.
    '''
    if not model:
        print("AI model not configured. Returning mock data.")
        return [{"code": "915-00", "description": "Mock AI Code (e.g., Catering)"}]

    prompt = f"""
    You are a procurement expert for the City of Memphis. I will give you a user's simple business description and a list of official commodity codes. 
    Your job is to return a JSON array of the top 10-15 codes that are the best match.

    HERE IS THE LIST OF CODES:
    {COMMODITY_CODES_TEXT}

    HERE IS THE USER'S DESCRIPTION:
    "{description}"

    Return *only* the JSON array of matching codes (with "code" and "description" keys). Do not add any other text or "```json" markers.
    """
    
    try:
        response = model.generate_content(prompt)
        # Clean up the response just in case
        json_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(json_text)
    except Exception as e:
        print(f"Error calling AI: {e}")
        return [{"code": "ERROR", "description": f"AI call failed: {e}"}]


def get_live_rfps():
    '''
    Scrapes the BeaconBid portal.
    This is the FINAL, correct version, built by inspecting page_source.html.
    It finds the "title" div and the "view" link separately and pairs them.
    '''
    url = "https://www.beaconbid.com/solicitations/city-of-memphis-95/open"
    rfps = []
    
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = None
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(url)
        
        wait = WebDriverWait(driver, 10)
        
        # This is the selector for the *title* div
        title_selector = (By.CSS_SELECTOR, 'div.overflow-hidden.text-ellipsis')
        
        # We are telling it to wait until at least one element is present
        wait.until(EC.presence_of_element_located(title_selector))
        

        solicitation_blocks = driver.find_elements(By.CSS_SELECTOR, 'div.p-20px.border-b')
        
        print(f"SELENIUM_SCRAPER: Found {len(solicitation_blocks)} solicitation blocks.")

        for block in solicitation_blocks:
            try:
                # Find the title text within this block
                title_element = block.find_element(By.CSS_SELECTOR, 'div.overflow-hidden.text-ellipsis')
                title = title_element.text.strip()
                
                # Find the "View" button link within this block
                link_element = block.find_element(By.CSS_SELECTOR, 'a[role="button"]')
                href = link_element.get_attribute('href')
                
                if title and href:
                    if not href.startswith('http'):
                        href = f"https://www.beaconbid.com{href}"
                
                    rfps.append({"title": title, "url": href})
                    
            except Exception as e:
                print(f"Scraper skipping a block: {e}")
                pass
                
        if not rfps:
             print("SELENIUM_SCRAPER_FAILURE: Found blocks but couldn't parse title/link.")
             return []
        
        print(f"SELENIUM_SCRAPER_SUCCESS: Found and parsed {len(rfps)} links from BeaconBid.")
        return rfps
        
    except Exception as e:
        print(f"Error scraping BeaconBid with Selenium: {e}")
        return [] # Return an EMPTY LIST
    finally:
        if driver:
            driver.quit() 
            
def get_ai_matched_rfps(ai_codes, live_rfps):
    '''
    Uses a second AI call to match the codes to the RFPs.
    This version is more robust.
    '''
    if not model:
        return [] 
        

    if not live_rfps:
        print("AI_MATCHER: No live RFPs to match against.")
        return [] 

    codes_text = "\n".join([f"- {c['code']}: {c['description']}" for c in ai_codes])
    rfps_text = "\n".join([f"- {rfp['title']}" for rfp in live_rfps])

    prompt = f"""
    You are a procurement expert. I will give you a list of "Service Codes" that a business provides. I will also give you a list of "Open Contracts" from the city.

    Your job is to identify which "Open Contracts" are a good match for the "Service Codes".
    HERE ARE THE BUSINESS'S SERVICE CODES:
    {codes_text}

    HERE ARE THE LIVE, OPEN CONTRACTS:
    {rfps_text}

    Please analyze both lists and return a JSON array of *only* the matching "Open Contracts".
    Each item in the array should be an object with a "title" and a "url" (from the list I gave you).
    
    If no contracts match, you MUST return an empty array [].
    Return *only* the JSON array.
    """
    
    try:
        response = model.generate_content(prompt)
        json_text = response.text.strip().replace("```json", "").replace("```", "")
        
        if not json_text:
            json_text = "[]"
            
        ai_matches = json.loads(json_text)
        
        final_rfps = []
        for ai_match in ai_matches:
            for live_rfp in live_rfps:
                # Match on title (be a bit flexible with whitespace)
                if ai_match['title'].strip() == live_rfp['title'].strip():
                    final_rfps.append(live_rfp)
                    break
        return final_rfps
        
    except Exception as e:
        print(f"Error in AI Matcher (json.loads failed?): {e}")
        return [] 
    

def get_ai_profile(biz_name, description, ai_codes):
    '''
    Uses a third AI call to write a professional profile.
    (SMART FORM VERSION)
    '''
    if not model:
        return "ERROR: AI model not configured."

    codes_text = "\n".join([f"- {c['code']}: {c['description']}" for c in ai_codes])

    prompt = f"""
    You are a professional business writer helping a small business write their official profile for a City of Memphis vendor application.

    I will give you the business's name, their description, and their official Commodity Codes.

    Your job is to combine all this into a polished, professional profile.
    The profile must sound confident and MUST mention that they are available for "subcontractor opportunities".

    BUSINESS NAME:
    "{biz_name}"

    USER'S DESCRIPTION:
    "{description}"

    THEIR CODES:
    {codes_text}

    Return *only* the single paragraph of text for their new profile.
    """

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error calling AI Profile Builder: {e}")
        return "Error generating profile."
    
# --- PART 4: OUR FLASK ROUTES (THE "SERVER") ---

@app.route('/')
def index():
    '''
    Serves our main index.html page.
    '''
    # 'index.html' must be in a folder named 'templates'
    return render_template('index.html')


@app.route('/api/find_contracts', methods=['POST'])
def api_find_contracts():
    '''
    This is our one and only API endpoint. (FINAL SMART FORM VERSION)
    '''
    data = request.json
    biz_name = data.get('name')
    biz_services = data.get('services')
    biz_specs = data.get('specialties')
    biz_other = data.get('other', '') 

    description = f"Main Services: {biz_services}. Specialties: {biz_specs}. Other Details: {biz_other}."

    print(f"\n--- NEW REQUEST ---")
    print(f"USER INPUT (SMART FORM): {description}")

    if not biz_services:
        return jsonify({"error": "No services provided."}), 400

    # 1. Get AI Codes (Call #1)
    ai_codes = get_ai_matched_codes(description)
    print(f"AI CODES FOUND: {ai_codes}")

    # 2. Get Live RFPs (Scraper)
    live_rfps = get_live_rfps()
    print(f"LIVE RFPS FOUND: {len(live_rfps)} links")

    # 3. Get AI-Matched RFPs (Call #2)
    matched_rfps = get_ai_matched_rfps(ai_codes, live_rfps)
    print(f"AI MATCHES FOUND: {matched_rfps}")

    # 4. Get AI-Generated Profile (Call #3)
    ai_profile = get_ai_profile(biz_name, description, ai_codes)
    print(f"AI PROFILE GENERATED: {ai_profile}")

    # 5. Return!
    return jsonify({
        "codes": ai_codes,
        "rfps": matched_rfps,
        "profile": ai_profile
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)