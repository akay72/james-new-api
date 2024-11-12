import urllib.parse
import undetected_chromedriver as uc
import time
import random
from bs4 import BeautifulSoup
import re
from selenium.webdriver.chrome.options import Options
import os

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
def fetch_contact_info(search_term, state_name):
    url = construct_url(search_term, state_name)
    if "Error" in url:
        return {"error": url}

    driver = setup_chrome_driver()
    data = []

    try:
        driver.get(url)
        time.sleep(random.uniform(2, 5))
        soup = BeautifulSoup(driver.page_source, "html.parser")

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Find 'result-b' class divs and collect the links and address information
        result_divs = soup.find_all("a", class_="res-link")
        links = []
        for div in result_divs:
            link = div['href']
            business_title = div.find(class_='res-bname').get_text(strip=True)
            address_div = div.find("span", class_="res-addy-text")
            address = address_div.get_text(strip=True) if address_div else ""
            
            # Split address into components
            match = re.match(r"(.*), ([A-Z]{2}) (\d{5})", address)
            street_address = match.group(1) if match else ""
            state = match.group(2) if match else ""
            zip_code = match.group(3) if match else ""
            
            # Add to links list for further processing
            links.append((link, business_title, street_address, state, zip_code))
        
        print("Found links:", links)

        # Visit each link and extract contact details
        for link, business_title, street_address, state, zip_code in links:
            print(f"Visiting link: {link}")
            driver.get(link)
            time.sleep(random.uniform(3, 7))  # Random cooldown between visits

            # Parse the contact page
            contact_soup = BeautifulSoup(driver.page_source, "html.parser")

            # Extract contact name and position from 'mt16 ats prmyc' divs
            contact_div = contact_soup.find("div", class_="mt16 ats prmyc")
            if contact_div:
                name = contact_div.find("strong").get_text(strip=True) if contact_div.find("strong") else ""
                position = contact_div.find("span").get_text(strip=True) if contact_div.find("span") else ""
            else:
                name, position = "", ""

            # Collect phones, contact email, company email, website, employees, and founded year
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
                            if not contact_email:  # First email as contact email
                                contact_email = email.get("href").replace("mailto:", "")
                            else:  # Second email as company email, extract visible text
                                company_email = email.get_text(strip=True)
                    elif "Web" in label_text:
                        web_link = bl_div.find("a", href=True)
                        if web_link:
                            website = web_link.get("href")

            # Find the Employees and Founded information
            for attri_div in contact_soup.find_all("div", class_="attri"):
                label = attri_div.find("b")
                if label:
                    label_text = label.get_text(strip=True)
                    if "Employees" in label_text:
                        employees = attri_div.get_text(strip=True).replace("Employees:", "").strip()
                    elif "Founded" in label_text:
                        founded = attri_div.get_text(strip=True).replace("Founded:", "").strip()

            # Join all collected phone numbers into a single string
            phones_str = ", ".join(phones)

            # Append the information as a dictionary to the data list
            data.append({
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
            })

    except Exception as e:
        print()
    finally:
        driver.quit()
    
    return data  # Return the data as JSON-like structure
