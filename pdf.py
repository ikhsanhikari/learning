import requests
import subprocess
import json
import os
import re
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def get_channel_playlists(api_key, channel_id):
    base_url = "https://www.googleapis.com/youtube/v3/playlists"
    params = {
        'part': 'snippet',
        'channelId': channel_id,
        'maxResults': 50,  # Sesuaikan sesuai kebutuhan
        'key': api_key
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        playlists_data = response.json()

        
        # Process the playlists data
        for item in playlists_data.get('items', []):
            snippet = item.get('snippet', {})
            title = snippet.get('title', '')
            playlist_id = item.get('id', '')
            print(f"Title: {title}, Playlist ID: {playlist_id}")
            get_youtube_playlist(api_key,playlist_id,title)
            

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from YouTube API: {e}")



def get_youtube_playlist(api_key, playlist_id,folder):
    base_url = "https://www.googleapis.com/youtube/v3/playlistItems"
    page_token = None

    while True:
        params = {
            'part': 'snippet',
            'maxResults': 50,
            'playlistId': playlist_id,
            'key': api_key,
            'pageToken': page_token
        }

        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            playlist_data = response.json()

            # Process the playlist data
            for item in playlist_data.get('items', []):
                snippet = item.get('snippet', {})
                title = snippet.get('title', '')
                video_id = snippet.get('resourceId', {}).get('videoId', '')
                #print(f"Title: {title}, Video ID: {video_id}")

                # Check if the video has subtitles
                if has_subtitles(video_id):
                    # Get subtitles for the video
                    subtitles = get_subtitles(video_id)

                    # Save subtitles to PDF
                    save_to_pdf(video_id, title, subtitles,folder)
                else:
                    print(f"Video ID {video_id} does not have subtitles.")

            if 'nextPageToken' in playlist_data:
                page_token = playlist_data['nextPageToken']
            else:
                break

        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from YouTube API: {e}")
            break


def has_subtitles(video_id):
    command = f"youtube_transcript_api {video_id} --list --format json"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    if result.returncode == 0:
        try:
            json_data = result.stdout
            return bool(json.loads(json_data))
        except json.decoder.JSONDecodeError as e:
            print(f"Error decoding JSON for Video ID {video_id}: {e}")
            return False
    else:
        print(f"Error checking subtitles for Video ID {video_id}: {result.stderr}")
        return False

def get_subtitles(video_id):
    command = f"youtube_transcript_api {video_id} --language id --format json"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    if result.returncode == 0:
        try:
            json_data = result.stdout
            data = json.loads(json_data)[0]
            text = "\n".join(item['text'] for item in data)
            return text
        except json.decoder.JSONDecodeError as e:
            print(f"Error decoding subtitles JSON for Video ID {video_id}: {e}")
            return None
    else:
        print(f"Error getting subtitles for Video ID {video_id}: {result.stderr}")
        return None

def clean_filename(filename):
    # Menghapus karakter yang tidak diizinkan dalam nama file
    return re.sub(r'[\/:*?"<>|]', '', filename)
    
def save_to_pdf(video_id, title, subtitles,folder):
    pdf_folder = folder.replace(" ","_")
    
    # Membuat folder "loa" jika belum ada
    if not os.path.exists(pdf_folder):
        os.makedirs(pdf_folder)
    
    clean_title = clean_filename(title)
    clean_title = clean_title.replace(" ","_")

    pdf_filename = os.path.join(pdf_folder, f"{clean_title}.pdf")
    if os.path.exists(pdf_filename):
        print(f"File {pdf_filename} already exists. Skipping...")
        return

    try:
        with open(pdf_filename, 'wb') as pdf_file:
            pdf = canvas.Canvas(pdf_file, pagesize=letter)
            pdf.setFont("Helvetica-Bold", 16)  # Judul dengan teks bold
            pdf.setTitle(title)

            # Tambahkan judul ke PDF di halaman pertama
            pdf.drawString(50, 750, title)

            # Tambahkan subtitle ke PDF dengan spasi antar baris
            lines = subtitles.split('\n')
            y_position = 700
            line_height = 15  # Tinggi setiap baris
            max_lines_per_page = 45  # Jumlah maksimal baris per halaman
            first_page = True

            for line in lines:
                pdf.setFont("Helvetica", 9)  # Gunakan teks reguler untuk isi

                # Jika mencapai batas baris per halaman, lanjutkan ke halaman berikutnya
                if y_position < 50:
                    pdf.showPage()
                    y_position = 750  # Atur posisi ulang ke atas halaman
                    first_page = False

                pdf.drawString(50, y_position, line)
                y_position -= line_height

            pdf.save()
            print(f"Subtitles saved to {pdf_filename}")

    except Exception as e:
        print(f"Error saving subtitles to PDF for Video ID {video_id}: {e}")




if __name__ == "__main__":
    # Masukkan API key dan ID playlist Anda di sini
    api_key = ""
    channel_id = "UCl9J4WO7n4Zj4GqzeSnW5GQ"

    get_channel_playlists(api_key,channel_id)
