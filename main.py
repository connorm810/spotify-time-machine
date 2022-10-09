import os
import requests
import spotipy
import re
from tqdm import tqdm
from bs4 import BeautifulSoup
from spotipy.oauth2 import SpotifyOAuth

# --- IDs from Spotify Developer Dashboard --- #
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
REDIRECT_URI = "https://open.spotify.com/search"


# --- Removal Loop Function --- #
def remove_from_list(item: str, rem_list: list):
    while item in rem_list:
        rem_list.remove(item)


def main():
    # --- Spotify Authentication --- #
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
                                                   redirect_uri=REDIRECT_URI, scope="playlist-modify-private",
                                                   show_dialog=True, cache_path="token.txt"))
    user_id = sp.current_user()["id"]

    # --- User Input and Web Scraping --- #
    user_date = input("Which year do you want to travel to? Type the data in this format YYYY-MM-DD: ")
    # user_date = "2000-08-12"

    response = requests.get(f"https://www.billboard.com/charts/hot-100/{user_date}/")
    soup = BeautifulSoup(response.text, "html.parser")

    song_tags = soup.find_all("h3", id="title-of-a-story")
    artists_tags = soup.find_all("span", class_="c-label")

    # --- Cleans Song and Artist Lists --- #
    pattern = '[0-9]'
    artists_names = [re.sub(pattern, '', name.get_text().strip().replace("-", '').replace("NEW", '')
                            .replace("Featuring", "feat.")) for name in artists_tags]
    remove_from_list('', artists_names)
    print(artists_names)

    song_names = [song.get_text().strip().replace("Songwriter(s):", '').replace("Producer(s):", '')
                  .replace("Imprint/Promotion Label:", '') for song in song_tags]
    remove_from_list('', song_names)
    print(song_names[3:103])

    # --- Finds Song URIs to Allow Addition to Playlist --- #
    passed = 0
    skipped = 0
    song_uris = []
    for song in tqdm(song_names[3:103], colour="blue", desc="Searching for URIs", leave=False):
        try:
            result = sp.search(q=f"artist: {artists_names[song_names[3:103].index(song)]} track: {song}", limit=50)
            song_uris.append(result["tracks"]["items"][0]["uri"])
            passed += 1
        except IndexError:
            skipped += 1
        except requests.exceptions.HTTPError:
            skipped += 1
        except spotipy.exceptions.SpotifyException:
            skipped += 1

    print(f"Finished Search | Out of {len(song_names[3:103])} songs, {passed} were found and {skipped} were not.")

    # --- Add Songs to new Playlist --- #
    print("Adding songs to new playlist...")
    try:
        playlist_id = sp.user_playlist_create(user_id, f"{user_date} Billboard 100", public=False,
                                              description=f"Top songs from {user_date}")["id"]
        sp.playlist_add_items(playlist_id, song_uris)
        print("Playlist created successfully!")
    except NameError:
        print("Failed to create playlist, please ensure your spotify login was correct.")


if __name__ == "__main__":
    main()
