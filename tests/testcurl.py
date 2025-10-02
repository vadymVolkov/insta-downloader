import requests


def test_download_video(instagram_url):
    response = requests.post("http://localhost:8000/api/download/", json={"url": instagram_url})
    return response.json()

link = 'https://www.instagram.com/p/DghfghfgOOFdyJjLbG/?img_index=10&igsutghfhfdhfdgh=MXRzgfhfdhgdHZ2cGVudGF5ZA=='
link2 = 'https://www.instagram.com/reel/DPFJiwpDiBL/'
link3 = 'https://chatgpt.com/c/68dda1d8-955c-8328-b797-fa358aca668c'
data = test_download_video(link)
print(data)

