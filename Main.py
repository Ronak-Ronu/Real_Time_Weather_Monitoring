import streamlit as stl
import requests
import time
from datetime import datetime,timezone
import pytz 
from dotenv import load_dotenv
import os
import folium
from streamlit_folium import st_folium
import sqlite3
from collections import Counter

load_dotenv()


local_timezone = pytz.timezone('Asia/Kolkata')
interval = 10 #seconds
alert_cities = ['Delhi', 'Mumbai', 'Chennai', 'Bangalore', 'Kolkata', 'Hyderabad']

stl.set_page_config(page_title="WEATHER_APP ",page_icon='⚡',menu_items={       
        'About': """ Hello User, This is Ronak .
         Github: https://github.com/Ronak-Ronu LinkedIn: www.linkedin.com/in/ronak-suthar-2532a4202 """})

api_key= os.getenv('API_KEY')

# Database connection for storing daily summaries
conn = sqlite3.connect('weather_summary.db')
c = conn.cursor()
# Create a table for storing daily summaries
c.execute('''
    CREATE TABLE IF NOT EXISTS daily_summary (
        city TEXT,
        date TEXT,
        avg_temp REAL,
        max_temp REAL,
        min_temp REAL,
        dominant_condition TEXT
    )
''')
conn.commit()

stl.title('Real-Time Data Processing System for :blue[WEATHER] Monitoring 🌥')




current_date= datetime.now(local_timezone)



def kelvin_to_celsius(temp_kelvin):
    return temp_kelvin - 273.15

def kelvin_to_fahrenheit(temp_kelvin):
    return (temp_kelvin - 273.15) * 9/5 + 32

stl.markdown("<h5>Select Temperature Unit:</h5>",unsafe_allow_html=True
)
temp_unit = stl.radio(
                "Select temperature unit",
                ('Celsius (°C)', 'Fahrenheit (°F)'),

    )


def get_weather_data(city_name):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={api_key}&lang={language}"
    try:
            response = requests.get(url)
            response.raise_for_status() 
            return response.json()
    except requests.exceptions.RequestException as e:
            print(f"Error fetching data for {city_name}: {e}")
            return None

language= stl.selectbox("Choose your preferable Language 🔠",(

    'ar','bg','da','de','el','en','fr','hi','hu','id','it','ja','kr','nl','pt','sp','th','tr','ua','zh_cn'
   
    ), index=None,
   placeholder="Selected language - english" )

city_name = stl.text_input('City 🌆',max_chars=30,placeholder="Find Your Location Weather ⚡")
threshold_temp = stl.number_input("Set Temperature Threshold (°C):", min_value=-50, max_value=50, value=35)
consecutive_updates = stl.number_input("Set Consecutive Updates for Alert:", min_value=1, max_value=10, value=2)

# Keep track of consecutive updates exceeding the threshold
exceed_threshold_count = 0
def check_temperature_alert(current_temp, threshold_temp, consecutive_updates):
    global exceed_count
    if current_temp > threshold_temp:
        exceed_threshold_count += 1
    else:
        exceed_threshold_count = 0
    
    # If the threshold is exceeded for consecutive updates, trigger an alert
    if exceed_threshold_count >= consecutive_updates:
        return True
    return False


def aggregate_daily_data(city, weather_data_list):
    temps = [data['main']['feels_like'] for data in weather_data_list]
    max_temps = [data['main']['temp_max'] for data in weather_data_list]
    min_temps = [data['main']['temp_min'] for data in weather_data_list]
    conditions = [data['weather'][0]['main'] for data in weather_data_list]

    avg_temp = sum(temps) / len(temps)
    max_temp = max(max_temps)
    min_temp = min(min_temps)
    
    # Get the most frequent weather condition
    dominant_condition = Counter(conditions).most_common(1)[0][0]

    # Store daily summary in the database
    today = datetime.now(local_timezone).strftime("%Y-%m-%d")
    c.execute('''
        INSERT INTO daily_summary (city, date, avg_temp, max_temp, min_temp, dominant_condition)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (city, today, avg_temp, max_temp, min_temp, dominant_condition))
    print(f"Inserting into DB: city={city}, date={today}, avg_temp={avg_temp}, max_temp={max_temp}, min_temp={min_temp}, dominant_condition={dominant_condition}")

    conn.commit()



if city_name:
    json_data = get_weather_data(city_name)

def display_weather_data(weather_data, city):
    if weather_data:
        sunrise = datetime.fromtimestamp(weather_data['sys']['sunrise'], tz=timezone.utc)
        sunset = datetime.fromtimestamp(weather_data['sys']['sunset'], tz=timezone.utc)
        temp_kelvin = weather_data['main']['feels_like']
        humidity = weather_data['main']['humidity']
        weather = weather_data['weather'][0]['main']
        weather_description = weather_data['weather'][0]['description']
        wind_speed = weather_data['wind']['speed']
        latitude = weather_data['coord']['lat']
        longitude = weather_data['coord']['lon']
        formatted_date = current_date.strftime("%A, %I:%M %p")

        # Convert temperature based on user preference
        if temp_unit == 'Celsius (°C)':
            temp = kelvin_to_celsius(temp_kelvin)
            temp_display = f"{temp:.2f}°C"
        else:
            temp = kelvin_to_fahrenheit(temp_kelvin)
            temp_display = f"{temp:.2f}°F"

        # Create a new column for each city
        col1, col2 = stl.columns([2, 3]) 

        with col1:
           

            stl.markdown(f'<div style="border: 1px solid #ccc; border-radius: 5px; padding: 10px; margin: 10px 0; background-color: #f9f9f9;">'
                          f'<h4>{city}</h4>'
                          f'<p><strong>Weather:</strong> {weather} 🌈</p>'
                          f'<p><strong>Description:</strong> {weather_description}</p>'
                          f'<p><strong>Humidity:</strong> {humidity}%</p>'
                          f'<p><strong>Feels like:</strong> {temp_display}🌡️</p>'
                          f'<p><strong>Sunrise:</strong> {sunrise.astimezone(local_timezone).strftime("%H:%M:%S")} 🌅</p>'
                          f'<p><strong>Sunset:</strong> {sunset.astimezone(local_timezone).strftime("%H:%M:%S")} 🌇</p>'
                          f'<p><strong>Wind Speed:</strong> {wind_speed} km/h 🌪</p>'
                          f'<p><strong>Time:</strong> {formatted_date} </p>'
                          '</div>', unsafe_allow_html=True)

        # Display map for each city
        m = folium.Map(location=(latitude, longitude), zoom_start=10)
        with col2:
            st_folium(m, width=700, height=350, key="map_" + city)

# Collect weather data throughout the day and aggregate it
weather_data_list = []

def monitor_weather(city_name=None):
    weather_data = get_weather_data(city_name)
    if weather_data:
        weather_data_list.append(weather_data)
        temp_cel=kelvin_to_celsius(weather_data['main']['feels_like'])
        alert_triggered = check_temperature_alert(temp_cel, threshold_temp, consecutive_updates)
        if alert_triggered:
            stl.warning(f"Alert! The temperature in {city_name} has exceeded {threshold_temp}°C for {consecutive_updates} consecutive updates.")

        display_weather_data(weather_data, city_name)


        # If the day ends (for simplicity, at midnight), aggregate and store daily data
        if datetime.now(local_timezone).minute % 1 ==0:
            aggregate_daily_data(city_name, weather_data_list)
            weather_data_list.clear()


def display_daily_summary(city):
    today = datetime.now(local_timezone).strftime("%Y-%m-%d")
    c.execute('SELECT * FROM daily_summary WHERE city = ? AND date = ?', (city, today))
    summary = c.fetchone()

    if summary:
        city, date, avg_temp, max_temp, min_temp, dominant_condition = summary
        stl.write(f"### {city} - Daily Summary for {date}")
        stl.write(f"**Average Temperature:** {avg_temp:.2f}°C")
        stl.write(f"**Maximum Temperature:** {max_temp:.2f}°C")
        stl.write(f"**Minimum Temperature:** {min_temp:.2f}°C")
        stl.write(f"**Dominant Weather Condition:** {dominant_condition}")
    else:
        weather_data = get_weather_data(city_name)
        weather_data_list.append(weather_data)
        aggregate_daily_data(city_name, weather_data_list)
        stl.write(f"No data available for {city} today.")


def monitor_weather(city_name=None):
            weather_data = get_weather_data(city_name)
            display_weather_data(weather_data,city_name)
            stl.session_state.current_city = city_name

def monitor_all_weather():
    while True:
                for city in alert_cities:
                    weather_data = get_weather_data(city)
                    if weather_data:
                        display_weather_data(weather_data,city)
                        
                time.sleep(interval)

                stl.rerun()  

if city_name:
    monitor_weather(city_name)
    display_daily_summary(city_name)

monitor_all_weather()

if len(weather_data_list) > 0:
    aggregate_daily_data(city_name, weather_data_list)
    weather_data_list.clear()


# stl.header(":blue[DEVELOPER] SECTION 👨‍💻")
# stl.write("API 📡")

# code1 = ''' # GET WEATHER DATA BY CITY_NAME
#  https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={api_key}'''
# stl.code(code1,language="python")
# code2 = ''' # GET WEATHER DATA BY CITY_NAME WITH PREFERABLE LANGUAGE
#  https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={api_key}&lang={language}'''

# stl.code(code2,language="python")


# Kelvin to Celsius: Celsius = Kelvin - 273.15
# Kelvin to Fahrenheit: Fahrenheit = (Kelvin - 273.15) * 9/5 + 32


