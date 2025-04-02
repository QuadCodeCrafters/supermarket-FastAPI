from fastapi import FastAPI
import requests

app = FastAPI()

ESP32_IP = "http://192.168.1.186"  # Change to your ESP32's local IP

@app.get("/test")
async def test_led():
    try:
        response = requests.get(f"{ESP32_IP}/led_on")  # Send request to ESP32
        return {"message": "Command sent to ESP32", "esp_response": response.text}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


@app.get("/light_off")
async def light_off():
    try:
        response = requests.get(f"{ESP32_IP}/led_off")  # Send request to ESP32
        return {"message": "Turned OFF", "esp_response": response.text}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
