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

        # 1. Quality nikalna
        quality_match = re.search(r'(1080p|720p|480p|2160p|4k)', filename, re.IGNORECASE)
        if quality_match:
            data["quality"] = quality_match.group(1).lower()

        # 2. Season Nikalna
        season_match = re.search(r'(?i)(?:S|Season\s*)(\d+)', filename)
        if season_match:
            data["season"] = str(int(season_match.group(1)))

        # 3. Episode Nikalna
        # Prioritize "E01", "Ep 01" style
        episode_match = re.search(r'(?i)(?:E|Ep|Episode\s*)\s*(\d+)', filename)
        if not episode_match:
             # Try matching something that looks like an episode number at the end or after a dash
             episode_match = re.search(r'(?<!\d)(\d{1,4})(?!\d)', re.sub(r'\[.*?\]|\(.*?\)', '', filename).split('.')[-2] if '.' in filename else filename)
             # Wait, the above is complex. Let's simplify.
             episode_match = re.search(r'(?i)-\s*(\d+)', filename)

        if episode_match:
            data["episode"] = str(int(episode_match.group(1)))

        # 4. Title Extraction
        # Sabse pehle brackets aur extensions hata lo
        clean = re.sub(r'\[.*?\]|\(.*?\)', '', filename)
        clean = re.sub(r'\.(mkv|mp4|avi|webm|ts)$', '', clean, flags=re.IGNORECASE)
        
        # Quality markers hatao title search ke liye
        clean = re.sub(r'(?i)(1080p|720p|480p|2160p|4k)', '', clean)

        # Season/Episode markers hatao (e.g. S01E01, Ep 01)
        # Match them as standalone parts or after space/dash
        clean = re.sub(r'(?i)\b(?:S|Season\s*)?\d+(?:E|Ep|Episode\s*)\s*\d+\b', '', clean)
        clean = re.sub(r'(?i)\b(?:S|Season\s*)\d+\b', '', clean)
        clean = re.sub(r'(?i)\b(?:E|Ep|Episode\s*)\s*\d+\b', '', clean)

        # For the "- 01" style, if it's the last part of the filename
        clean = re.sub(r'-\s*\d+\s*$', '', clean)

        # Clean up remaining string
        title = clean.replace('_', ' ').replace('.', ' ').strip()
        title = re.sub(r'\s+', ' ', title).strip('- ').strip()

        # SPECIAL CASE: If it's a long string with multiple dashes, take everything before the last dash if it was an episode
        # But our current regex for Fairy Tail - 100 Years Quest - 03 is keeping the title correct.

        # If title is empty, use the original filename without extension/brackets as fallback
        if not title:
            title = re.sub(r'\[.*?\]|\(.*?\)', '', filename)
            title = re.sub(r'\.(mkv|mp4|avi|webm|ts)$', '', title, flags=re.IGNORECASE).strip()

        data["title"] = title
        return data
