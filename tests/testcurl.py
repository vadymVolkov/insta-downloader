import requests


def test_download_video(instagram_url):
    response = requests.post("http://localhost:8000/api/download/", json={"url": instagram_url})
    return response.json()

data = test_download_video("https://www.instagram.com/reel/DPFJiwpDiBL/")
print(data)

