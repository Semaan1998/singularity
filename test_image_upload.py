import requests

with open("test.png", "rb") as f:
    res = requests.post("http://localhost:8000/analyze-image/", files={"file": f})
    print(res.json())
