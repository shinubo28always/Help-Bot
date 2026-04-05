import re

class RegexParser:
    @staticmethod
    def parse_filename(filename: str):
        # Default empty data
        data = {
            "title": None,
            "season": "1", # Default season 1 hota hai
            "episode": None,
            "quality": None
        }

        # 1. Quality nikalna (1080p, 720p, 480p)
        quality_match = re.search(r'(1080p|720p|480p|2160p|4k)', filename, re.IGNORECASE)
        if quality_match:
            data["quality"] = quality_match.group(1).lower()

        # 2. Brackt hatana aur Quality hatana title ke liye
        # Sab se pehle quality hatayen taake woh title ka hissa na banay
        clean_name = re.sub(r'(?i)(1080p|720p|480p|2160p|4k)', '', filename)

        # Extension hatana
        clean_name = re.sub(r'\.(mkv|mp4|avi|webm)', '', clean_name)

        # Bracket wala kachra saaf karna (e.g. [SubsPlease], (Web-rip))
        clean_name = re.sub(r'\[.*?\]|\(.*?\)', '', clean_name)

        # 3. Season Nikalna (S01, S1, Season 1)
        season_match = re.search(r'(?i)(?:S|Season\s*)(\d+)', clean_name)
        if season_match:
            data["season"] = str(int(season_match.group(1))) # 01 ko 1 bana dega
            clean_name = re.sub(r'(?i)(?:S|Season\s*)\d+', '', clean_name) # Season wala text hata do

        # 4. Episode Nikalna (E01, Ep 12, - 15)
        # Regex jo "E12", "Ep 12", ya "- 12" ko pakdega
        episode_match = re.search(r'(?i)(?:E|Ep|Episode\s*|-)\s*(\d+)', clean_name)
        if episode_match:
            data["episode"] = str(int(episode_match.group(1)))
            # Episode wala hissa aur uske baad ka sab hata do
            clean_name = re.sub(r'(?i)(?:E|Ep|Episode\s*|-)\s*\d+.*$', '', clean_name)
        
        # 5. Bacha hua text hamara Title hai
        title = clean_name.replace('_', ' ').replace('.', ' ').strip()
        # Faltu characters hatana jo titles ke end me reh jate hain
        title = re.sub(r'\s+', ' ', title).strip('- ').strip()
        data["title"] = title

        return data

# Test karne ke liye:
# print(RegexParser.parse_filename("[SubsPlease] Fairy Tail - 100 Years Quest - 03 (1080p).mkv"))
