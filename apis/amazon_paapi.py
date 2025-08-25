# apis/amazon_paapi.py
from typing import List, Dict
from amazon_paapi5 import AmazonApi  # or any wrapper you choose

class AmazonPaapiAdapter:
    def __init__(self, access_key, secret_key, partner_tag, marketplace="www.amazon.com"):
        self.client = AmazonApi(access_key, secret_key, partner_tag, marketplace=marketplace)

    def search(self, keyword: str, page: int=1) -> List[Dict]:
        # ask only for the fields you need to reduce payload (per best practices)
        items = self.client.search_items(keywords=keyword, item_page=page, resources=[
            "ItemInfo.Title","Offers.Listings.Price","Images.Primary.Small","BrowseNodeInfo.BrowseNodes"
        ])
        out = []
        for it in items:
            out.append({
                "Title": it.title,
                "Price": it.prices and it.prices.current_price and it.prices.current_price,
                "Rating": "", "Sold": "", "Seller": "",
                "SKU": it.asin, "ImageURL": it.image and it.image.url, "URL": it.detail_page_url
            })
        return out
