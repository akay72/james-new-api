import urllib.parse
import undetected_chromedriver as uc
import time
import random
from bs4 import BeautifulSoup
import re
from selenium.webdriver.chrome.options import Options
import os
from selenium_stealth import stealth
from fuzzywuzzy import fuzz

# State code mapping for Allbiz
state_codes = {
    "Alabama": "US_AL", "Alaska": "US_AK", "Arizona": "US_AZ", "Arkansas": "US_AR", 
    "California": "US_CA", "Colorado": "US_CO", "Connecticut": "US_CT", "Delaware": "US_DE", 
    "Florida": "US_FL", "Georgia": "US_GA", "Hawaii": "US_HI", "Idaho": "US_ID", 
    "Illinois": "US_IL", "Indiana": "US_IN", "Iowa": "US_IA", "Kansas": "US_KS", 
    "Kentucky": "US_KY", "Louisiana": "US_LA", "Maine": "US_ME", "Maryland": "US_MD", 
    "Massachusetts": "US_MA", "Michigan": "US_MI", "Minnesota": "US_MN", 
    "Mississippi": "US_MS", "Missouri": "US_MO", "Montana": "US_MT", "Nebraska": "US_NE", 
    "Nevada": "US_NV", "New Hampshire": "US_NH", "New Jersey": "US_NJ", "New Mexico": "US_NM", 
    "New York": "US_NY", "North Carolina": "US_NC", "North Dakota": "US_ND", "Ohio": "US_OH", 
    "Oklahoma": "US_OK", "Oregon": "US_OR", "Pennsylvania": "US_PA", "Rhode Island": "US_RI", 
    "South Carolina": "US_SC", "South Dakota": "US_SD", "Tennessee": "US_TN", 
    "Texas": "US_TX", "Utah": "US_UT", "Vermont": "US_VT", "Virginia": "US_VA", 
    "Washington": "US_WA", "Washington, D.C.": "US_DC", "West Virginia": "US_WV", 
    "Wisconsin": "US_WI", "Wyoming": "US_WY"
}

# Function to construct the Allbiz URL
def construct_url(search_term, state_name):
    state_name = state_name.strip()
    state_code = state_codes.get(state_name.title())
    if not state_code:
        return f"Error: State '{state_name}' not found in mapping."
    search_term_encoded = urllib.parse.quote(search_term)
    url = f"https://www.allbiz.com/search?ssm=&ss={search_term_encoded}&ia={state_code}"
    return url

# Setup ChromeDriver with Heroku paths
def setup_chrome_driver():
    
        try:
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.140 Safari/537.36"
            chrome_options = uc.ChromeOptions()
            chrome_options.add_argument('--headless=new')
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("user-agent={}".format(user_agent))
            driver = uc.Chrome(options=chrome_options)
            stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True
            )
            return driver
        except Exception as e:
            print("Error in Driver: ",e)


# Function to fetch contact details and return JSON-like structure
def fetch_contact_info(search_term, state_name, target_street_address):
    url = construct_url(search_term, state_name)
    if "Error" in url:
        print(url)
        return

    driver = setup_chrome_driver()
    
    try:
        driver.get(url)
        time.sleep(random.uniform(2, 5))

        # Parse the page content with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Find 'result-b' class divs and collect the links and address information
        result_divs = soup.find_all("a", class_="res-link")
        
        for div in result_divs:
            link = div['href']
            business_title = div.find(class_='res-bname').get_text(strip=True)
            address_div = div.find("span", class_="res-addy-text")
            if address_div:
                # Method 1: Using get_text with strip
                address = address_div.get_text(strip=True)
                print("Address (get_text with strip):", address)

                # Method 2: Using .text with .strip()
                if not address:
                    address = address_div.text.strip()
                    print("Address (text with strip):", address)

                # Method 3: Using .contents (useful if there’s nested structure)
                if not address and address_div.contents:
                    address = ''.join([str(content).strip() for content in address_div.contents])
                    print("Address (using contents):", address)

            else:
                address=""
                print("Address div not found.")
            
            # Split address into components
            match = re.match(r"(.*), ([A-Z]{2}) (\d{5})", address)
            street_address = match.group(1) if match else ""
            print(street_address)
            state = match.group(2) if match else ""
            zip_code = match.group(3) if match else ""

            similarity = fuzz.partial_ratio(address.lower(), target_street_address.lower())
            # Check if this is the target address
            if similarity >= 70:
                # Visit the company page for detailed information
                driver.get(link)
                time.sleep(random.uniform(3, 7))

                contact_soup = BeautifulSoup(driver.page_source, "html.parser")

                if not state or not zip_code:
                    print("State and zip are not found on the main page; checking company page details.")
                    address_container = contact_soup.find("div", class_="fp rrv")
                    print("Address container content:", address_container)
                    
                    if address_container:
                        # Extract complete address text
                        address_text = address_container.get_text(separator=" ", strip=True).replace("\xa0", " ")
                        print("Complete address:", address_text)

                        # Updated regex pattern to capture street address, state, and zip only
                        match = re.search(r"(.*?),?\s+([A-Za-z\s]+),?\s+(\d{5})", address_text)

                        # Check if match is found and print for debugging
                        if match:
                            print("Match groups:", match.groups())
                            
                            street_address=match.group(1).strip()
                            state = match.group(2).strip()           # State (any length)
                            zip_code = match.group(3).strip()         # Zip code (five digits)

                            # Print the extracted details
                            print("Street Address:", street_address)
                            print("State:", state)
                            print("Zip Code:", zip_code)
                        else:
                            street_address=""
                            state = ""       
                            zip_code = ""   
                    else:
                        print("Address container not found.")
                                            


                contact_div = contact_soup.find("div", class_="mt16 ats prmyc")
                name = contact_div.find("strong").get_text(strip=True) if contact_div and contact_div.find("strong") else ""
                position = contact_div.find("span").get_text(strip=True) if contact_div and contact_div.find("span") else ""

                phones = []
                contact_email, company_email, website = "", "", ""
                employees, founded = "", ""

                for bl_div in contact_soup.find_all("div", class_="bl"):
                    label = bl_div.find("b")
                    if label:
                        label_text = label.get_text(strip=True)
                        if "Phone" in label_text:
                            phone = bl_div.find("a", href=True)
                            if phone:
                                phones.append(phone.get_text(strip=True))
                        elif "Email" in label_text:
                            email = bl_div.find("a", href=True)
                            if email:
                                if not contact_email:
                                    contact_email = email.get_text(strip=True)
                                else:
                                    company_email = email.get_text(strip=True)
                        elif "Web" in label_text:
                            web_link = bl_div.find("a", href=True)
                            if web_link:
                                website = web_link.get("href")

                for attri_div in contact_soup.find_all("div", class_="attri"):
                    label = attri_div.find("b")
                    if label:
                        label_text = label.get_text(strip=True)
                        if "Employees" in label_text:
                            employees = attri_div.get_text(strip=True).replace("Employees:", "").strip()
                        elif "Founded" in label_text:
                            founded = attri_div.get_text(strip=True).replace("Founded:", "").strip()

                phones_str = ", ".join(phones)

                # Return JSON-like data for the matching company
                return {
                    "Business Title": business_title,
                    "Address": street_address,
                    "State": state,
                    "Zip": zip_code,
                    "Contact Name": name,
                    "Position": position,
                    "Phone": phones_str,
                    "Contact Email": contact_email,
                    "Company Email": company_email,
                    "Web": website,
                    "Employees": employees,
                    "Founded": founded
                }

        print("No matching company found for the specified address.")
        
    except Exception as e:
        print("An error occurred:", e)
    finally:
        driver.quit()

    return None  # Return None if no matching company is found
