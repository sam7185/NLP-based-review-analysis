import analyze
import scrape

# hotel_url = 'https://www.booking.com/hotel/in/trident-nariman-point.html'

def main():
    hotel_url = 'https://www.booking.com/hotel/in/trident-nariman-point.html'
    scrape.scrape_hotel_reviews(hotel_url)
    print("Scraping completed. Now running analysis pipeline...")
    # analyze.run_pipeline('Trident_Nariman_Point_filtered')