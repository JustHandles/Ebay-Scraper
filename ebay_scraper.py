from bs4 import BeautifulSoup
import requests
from currency_converter import CurrencyConverter
from datetime import datetime
from ebay_images import get_ebay_image_urls





def parse_sold_date(sold_date_str):
    # Clean up the date string by removing unnecessary text
    sold_date_str = sold_date_str.replace('Sold ', '').strip()
    # List of possible date formats
    date_formats = ['%d %b %Y', '%b %d, %Y']

    #Canadian and American ebay display sold dates differently. Must check for the different formats
    for date_format in date_formats:
        try:
            sold_date = datetime.strptime(sold_date_str, date_format)
            return sold_date
        except ValueError:
            # Try the next format if current format fails
            continue  
    
    print(f"Skipping item due to invalid date: {sold_date_str}")
    return None


#Main Scraping Function
def scrape_ebay(ebay_url, headers):
    #send request using correct set of Headers depending on .CA or .COM
    r = requests.get(ebay_url, headers=headers)
    if r.status_code != 200:
        print(f"Error: Could not fetch page (status code: {r.status_code})")
        return []
    #parse the html returned by the request
    soup = BeautifulSoup(r.text, 'html.parser')
    #initialize products list
    productslist = []
    #find all the search results of the query
    results = soup.find_all('div', {'class': "s-item__info clearfix"})
    # go through every search result and assign its attributes
    image_wrappers = soup.find_all("div", class_="s-item__image-wrapper")
    for item in results:
        soldDate = item.find('span', {'class': "s-item__caption--signal POSITIVE"}).text if item.find('span', {'class': "s-item__caption--signal POSITIVE"}) else "N/A"
        
        if soldDate == "N/A":
            continue

        # Attempt to parse the date
        sold_date = parse_sold_date(soldDate)
        
        # If parsing fails, skip this item
        if not sold_date:
            continue
        #get number of bids
        bids = item.find('span', {'class': "s-item__bids"})
        bids = bids.text if bids else "N/A"

        # Handle price, check for price ranges
        price_text = item.find('span', {'class': "s-item__price"}).text.replace('C', '').replace('$', '').replace(',', '').strip()
        if ' to ' in price_text:
            price_text = price_text.split(' to ')[0].strip()

        try:
            price = float(price_text)
        except ValueError:
            print(f"Skipping item due to invalid price: {price_text}")
            continue

        # Try extracting the image URL
        link = item.find('a', {'class': "s-item__link"})['href'] if item.find('a', {'class': "s-item__link"}) else "#"
        for wrapper in image_wrappers:
            img = wrapper.find("img")
            if img and img.get("src", "").endswith(".webp"):
                image_url = img["src"]
            else:
                image_url = "NONE"
        #image_url = soup.find("img", {"src": lambda x: x and x.endswith(".webp")}) #"https://i.ebayimg.com/images/g/klkAAOSw3oVoE9H2/s-l1600.webp" #get_ebay_image_urls(link) if link != "#" else []
        #assign the dictionary to store details about the item
        product = {
            'TITLE': item.find('div', {'class': "s-item__title"}).text,
            'Date of Sale': sold_date,
            'Price': price,
            '|-Number of Bids-|': bids,
            'link': item.find('a', {'class': "s-item__link"})['href'] if item.find('a', {'class': "s-item__link"}) else "#",
            'image_url': image_url
            }
        productslist.append(product)
    #return full list of items
    return productslist

#search_ebay function that allows for scraping US and Canadian ebay
def search_ebay(query):
    #replace the whitespace in the query to match the original form in the url
    query= query.replace(" ", "+")
    #create the different urls
    ebay_ca_url = f"https://www.ebay.ca/sch/i.html?_from=R40&_nkw={query}&_sacat=0&LH_Sold=1&LH_Complete=1&rt=nc&LH_Auction=1"
    ebay_com_url = f"https://www.ebay.com/sch/i.html?_from=R40&_nkw={query}&_sacat=0&LH_Sold=1&LH_Complete=1&rt=nc&LH_Auction=1"
    #create Country specific headers to bypass their attempt at blocking scraping scripts
    headers_com = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Referer': 'https://www.ebay.com/'
    }
    headers_ca = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Referer': 'https://www.ebay.ca/'
    }
    # Scrape both eBay.ca and eBay.com
    ca_results = scrape_ebay(ebay_ca_url, headers_ca)
    com_results = scrape_ebay(ebay_com_url, headers_com)
    c = CurrencyConverter()
    
    #format the price to always be in CAD using currency converter. the exchange rate is updated once a day
    for item in com_results:
       item['Price'] = multiplier = c.convert(item['Price'],'USD', 'CAD')

    #remove duplicate items based on title, date of sale, and number of bids
    for item in com_results:
        com_item = item["TITLE"] + item["Date of Sale"].strftime('%d %b %Y') + item["|-Number of Bids-|"]
        for item2 in ca_results:
            cad_item = item2["TITLE"] + item["Date of Sale"].strftime('%d %b %Y') + item["|-Number of Bids-|"]
            if com_item == cad_item:
                ca_results.remove(item2)
    #combine both countries results
    combined_results = ca_results + com_results

    #sort the list by date to return most recent sales first
    combined_results.sort(key=lambda x: x['Date of Sale'], reverse=True)
    #format the date back to a more comprehensible string rather than date time object
    for item in combined_results:
        item["Date of Sale"] = item["Date of Sale"].strftime('%d %b %Y')
    #final return of combined results 
    return combined_results
