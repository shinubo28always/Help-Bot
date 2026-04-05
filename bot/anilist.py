import aiohttp
from bot.config import Config

class Anilist:
    def __init__(self):
        self.url = Config.ANILIST_URL

    async def search_anime(self, title: str):
        # Anilist ki GraphQL Query
        query = """
        query ($search: String) {
          Page (page: 1, perPage: 5) {
            media (search: $search, type: ANIME) {
              id
              title {
                romaji
                english
              }
              coverImage {
                large
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
                        return None
                    
                    return data["data"]["Page"]["media"]
            except Exception as e:
                print(f"Anilist Error: {e}")
                return None

    def get_best_title(self, media_dict):
        if media_dict["title"]["english"]:
            return media_dict["title"]["english"]
        return media_dict["title"]["romaji"]

    async def get_anime_by_id(self, anime_id: int):
        query = """
        query ($id: Int) {
          Media (id: $id, type: ANIME) {
            id
            title {
              romaji
              english
            }
            coverImage {
              large
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

anilist_api = Anilist()
