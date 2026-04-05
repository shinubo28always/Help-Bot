import aiohttp
from bot.config import Config

class Anilist:
    def __init__(self):
        self.url = Config.ANILIST_URL

    async def search_anime(self, title: str):
        # Anilist ki GraphQL Query (Top 5 results mangne ke liye)
        query = """
        query ($search: String) {
          Page (page: 1, perPage: 5) {
            media (search: $search, type: ANIME) {
              id
              title {
                romaji
                english
              }
              episodes
              season
              format
            }
          }
        }
        """
        variables = {"search": title}

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.url, json={"query": query, "variables": variables}) as response:
                    data = await response.json()
                    
                    if "errors" in data or not data["data"]["Page"]["media"]:
                        return None # Agar kuch nahi mila
                    
                    return data["data"]["Page"]["media"] # Top 5 results ki list return karega
            except Exception as e:
                print(f"Anilist Error: {e}")
                return None

    # Title ko clean karke nikalne ka chota function
    def get_best_title(self, media_dict):
        # Agar english naam hai toh woh le lo, warna romaji le lo
        if media_dict["title"]["english"]:
            return media_dict["title"]["english"]
        return media_dict["title"]["romaji"]

    # Yeh function ID de kar Anime ki details mangwayega
    async def get_anime_by_id(self, anime_id: int):
        query = """
        query ($id: Int) {
          Media (id: $id, type: ANIME) {
            title {
              romaji
              english
            }
          }
        }
        """
        variables = {"id": anime_id}

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.url, json={"query": query, "variables": variables}) as response:
                    data = await response.json()
                    if "errors" in data or not data["data"]["Media"]:
                        return None
                    return data["data"]["Media"]
            except Exception as e:
                print(f"Anilist ID Search Error: {e}")
                return None

# Database object ki tarah iska bhi object bana lete hain
anilist_api = Anilist()
