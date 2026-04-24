# test_setup.py
import streamlit as st
import onnxruntime as ort
import cv2
import googlemaps
import requests
import langgraph
import sqlite3

print("✅ All imports successful!")

# Test ONNX Runtime
print(f"ONNX Runtime version: {ort.__version__}")

# Test Google Maps (requires key)
gmaps = googlemaps.Client(key="AIzaSyAvTQ4zuaDWojP2_Qp5DUoW5FaXF5YTYqg")
print("✅ Google Maps client created")

# Test Open-Meteo (free weather)
resp = requests.get("https://api.open-meteo.com/v1/forecast?latitude=3.139&longitude=101.6869&current_weather=true")
print(f"✅ Weather API status: {resp.status_code}")