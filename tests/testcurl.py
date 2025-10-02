import requests


def test_download_video(instagram_url):
    response = requests.post("http://localhost:8000/api/download/", json={"url": instagram_url})
    return response.json()

link = 'https://www.instagram.com/p/DOOFdyJjLbG/?img_index=10&igsh=MXRzdHZ2cGVudGF5ZA=='
link2 = 'https://www.instagram.com/reel/DPFJiwpDiBL/'
data = test_download_video(link)
print(data)

