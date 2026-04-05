from bot.regex_parser import RegexParser

test_files = [
    "[SubsPlease] Fairy Tail - 100 Years Quest - 03 (1080p).mkv",
    "Fairy Tail S01E01 720p.mp4",
    "One Piece - 1100 [1080p].mkv",
    "[AniReal - Anime] S1E03 Fairy Tail 1080p.mkv"
]

for f in test_files:
    data = RegexParser.parse_filename(f)
    print(f"File: {f}")
    print(f"Parsed: {data}")
    print("-" * 20)
