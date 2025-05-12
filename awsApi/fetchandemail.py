import requests
import matplotlib.pyplot as plt
from PIL import Image
from io import BytesIO
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from io import BytesIO
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import re
from getParameterAws import get_ssm_param
import json


def is_valid_email(email):
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None

def is_valid_lat_lon(lat, lon):
    try:
        lat = float(lat)
        lon = float(lon)
        return -90 <= lat <= 90 and -180 <= lon <= 180
    except ValueError:
        return False

api_key = get_ssm_param('api_key_weatherapp', with_decryption=True)
login = get_ssm_param('gmail_login', with_decryption=True)
password = get_ssm_param('gmail_password', with_decryption=True)
sender_email = get_ssm_param('gmail_login', with_decryption=True)
smtp_server_name = get_ssm_param('smtp_server_name', with_decryption=True)
subject = get_ssm_param('mail_subject', with_decryption=True)

class WeatherReport:
    def __init__(self, lat, long, api_key=api_key):
        self.lat = lat
        self.long = long
        self.api_key = api_key
        self.forecast_url = f'https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={long}&appid={self.api_key}'
        self.current_url = f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={long}&appid={self.api_key}'
    
    def __kelvin_to_celsius(self, kelvin):
        return kelvin - 273.15
    
    def __get_weather_data(self, url):
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print("Failed to retrieve data. Status code:", response.status_code)
            return None
        
    def __get_key_value(self, data):
        times = [entry['dt_txt'][:16] for entry in data['list']]
        temperatures = [self.__kelvin_to_celsius(entry['main']['temp']) for entry in data['list']]
        humidities = [entry['main']['humidity'] for entry in data['list']]
        pressures = [entry['main']['pressure'] for entry in data['list']]
        weather_types = [entry['weather'][0]['main'] for entry in data['list']]
        icons = [{"icon":entry['weather'][0]['icon'],"value":entry['weather'][0]['description']} for entry in data['list']]
        windspeeds = [entry['wind']['speed'] for entry in data['list']]
        rain_data = [entry.get('rain', {}).get('1h', 0) for entry in data['list']]
        return times, temperatures, humidities, pressures, weather_types, icons, windspeeds, rain_data
    
    def __figure_style(self,times):
        figsize = (max(len(times) * 0.5, 10), 5)
        return figsize
    
    def __chart_buf(self,cid,plot_func):
        buf = BytesIO()
        plot_func()
        plt.tight_layout()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        html_img_tag = f'<img src="cid:{cid}"><br>'
        return html_img_tag, buf

    def __create_temperature_chart(self, times, temperatures):
        def plot():
            plt.figure(figsize=self.__figure_style(times))
            plt.plot(times, temperatures, label='Temperature (°C)', color='red')
            plt.xlabel('Time')
            plt.ylabel('Temperature (°C)')
            plt.title('Temperature Forecast')
            plt.xticks(rotation=45)
            plt.legend()
        html_img_tag, buf = self.__chart_buf("temp_chart",plot)
        return html_img_tag,buf

    def __create_humidity_chart(self, times, humidities):
        def plot():
            plt.figure(figsize=self.__figure_style(times))
            plt.plot(times, humidities, label='Humidity (%)', color='blue')
            plt.xlabel('Time')
            plt.ylabel('Humidity (%)')
            plt.title('Humidity Forecast')
            plt.xticks(rotation=45)
            plt.legend()
        html_img_tag, buf = self.__chart_buf("humidity_chart",plot)
        return html_img_tag,buf

    def __create_pressure_chart(self, times, pressures):
        def plot():
            plt.figure(figsize=self.__figure_style(times))
            plt.plot(times, pressures, label='Pressure (hPa)', color='green')
            plt.xlabel('Time')
            plt.ylabel('Pressure (hPa)')
            plt.title('Pressure Forecast')
            plt.xticks(rotation=45)
            plt.legend()
        html_img_tag, buf = self.__chart_buf("pressure_chart",plot)
        return html_img_tag,buf

    def __create_rain_prediction_chart(self, times, rain_data):
        def plot():
            plt.figure(figsize=self.__figure_style(times))
            plt.plot(times, rain_data, label='Rain Prediction (mm)', color='purple')
            plt.xlabel('Time')
            plt.ylabel('Rain Prediction (mm)')
            plt.title('Rain Prediction Forecast')
            plt.xticks(rotation=45)
            plt.legend()
        html_img_tag, buf = self.__chart_buf("rain_chart",plot)
        return html_img_tag,buf
    
    def __create_windspeed_chart(self, times, wind_speeds):
        def plot():    
            plt.figure(figsize=self.__figure_style(times))
            plt.plot(times, wind_speeds, label='Wind Speed (m/s)', color='orange')
            plt.xlabel('Time')
            plt.ylabel('Wind Speed (m/s)')
            plt.title('Wind Speed Forecast')
            plt.xticks(rotation=45)
            plt.legend()
        html_img_tag, buf = self.__chart_buf("windspeed_chart",plot)
        return html_img_tag,buf

    def __create_weather_type_chart(self, times, icons):
        def plot():
            plt.figure(figsize=self.__figure_style(times))
            plt.xlim(-0.5, len(times) - 0.5)
            plt.ylim(0, 0.2)
            for i, icon_data in enumerate(icons):
                try:
                    icon_url = f"https://openweathermap.org/img/wn/{icon_data['icon']}@2x.png"
                    response = requests.get(icon_url)
                    img = Image.open(BytesIO(response.content)).convert("RGBA")

                    imagebox = OffsetImage(img, zoom=0.35)
                    ab = AnnotationBbox(imagebox, (i, 0.1), frameon=False)
                    plt.gca().add_artist(ab)

                    plt.text(i, 0.12, icon_data['value'], ha='center', va='center', fontsize=7, color='orange', rotation=90)
                except Exception as e:
                    print(f"Error loading icon {icon_data['icon']}: {e}")
            plt.xlabel('Time')
            plt.ylabel('Weather type')
            plt.title('Weather type Forecast')
            plt.xticks(range(len(times)), times, rotation=45, ha='right', fontsize=8)
        html_img_tag, buf = self.__chart_buf("weather_type_chart",plot)
        return html_img_tag,buf

    def __create_weather_table(self, forecast_data):
        table = [["Time", "Temparature", "Weather type", "Rain", "Wind Speed"]]
        for entry in forecast_data['list']:
            time = entry['dt_txt'][:16]   
            temp = f"{self.__kelvin_to_celsius(entry['main']['temp']):.1f}°C"
            icon = entry['weather'][0]['description']
            rain = f"{entry.get('rain', {}).get('1h', 0)} mm"
            wind = f"{entry['wind']['speed']} m/s"
            table.append([time, temp, icon, rain, wind])
        print(table)
        def plot(table):
            fig, ax = plt.subplots(figsize=(12, 0.3 * len(table)))
            ax.axis('off')
            table = ax.table(cellText=table,loc='center',cellLoc='center',colWidths=[0.2] * len(table[0]))
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1, 1.5)
        html_img_tag, buf = self.__chart_buf("weather_table",lambda: plot(table))
        return html_img_tag, buf
    

    def __create_combined_chart(self, times, temperatures, humidities, pressures, wind_speeds, rain_data):
        def plot():
            plt.figure(figsize=self.__figure_style(times))
            plt.plot(times, temperatures, label='Temperature (K)', color='red')
            plt.plot(times, humidities, label='Humidity (%)', color='blue')
            plt.plot(times, pressures, label='Pressure (hPa)', color='green')
            plt.plot(times, wind_speeds, label='Wind Speed (m/s)', color='purple')
            plt.plot(times, rain_data, label='Rain Prediction (mm)', color='orange')
            plt.xlabel('Time')
            plt.ylabel('Values')
            plt.title('Combined Weather Data Trends')
            plt.xticks(rotation=45)
            plt.legend()
        html_img_tag, buf = self.__chart_buf("combined_chart",plot)
        return html_img_tag,buf
    
    def __create_alert_table(self, times):
        table = [["Time", "event", "description"]]
        alerts = self.__get_weather_data(self.forecast_url).get('alerts', [])
        if alerts:
            for i,alert in enumerate(alerts):
                time = times[i]
                event = alert['event']
                description = alert['description']
                table.append([time, event, description])
        else:
            print('No weather alerts for this location.')
            table.append(["N/A", "No Alerts", "There are no weather alerts for this location."])
        col_widths = []
        num_cols = len(table[0])
        for col_index in range(num_cols):
            max_len = max(len(str(row[col_index])) for row in table)
            col_widths.append(max_len / 30)
        def plot(table):
            fig, ax = plt.subplots(figsize=(12, 0.6 * len(table)))
            ax.axis('off')
            table = ax.table(cellText=table,loc='center',cellLoc='center',colWidths=col_widths)
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1, 1.5)
        html_img_tag, buf = self.__chart_buf("alert_table",lambda: plot(table))
        return html_img_tag, buf
        
    def get_forecast_report(self):
        forecast_data = self.__get_weather_data(self.forecast_url)
        forecast_html = ""
        forecast_html += "<h2>Weather Forecast</h2>"
        forecast_images = []
        if forecast_data:
            times, temperatures, humidities, pressures, weather_types, icons, windspeeds, rain_data = self.__get_key_value(forecast_data)
            chart_generators = [
                ("temp_chart", lambda: self.__create_temperature_chart(times, temperatures)),
                ("humidity_chart", lambda: self.__create_humidity_chart(times, humidities)),
                ("pressure_chart", lambda: self.__create_pressure_chart(times, pressures)),
                ("windspeed_chart", lambda: self.__create_windspeed_chart(times, windspeeds)),
                ("rain_chart", lambda: self.__create_rain_prediction_chart(times, rain_data)),
                ("weather_type_chart", lambda: self.__create_weather_type_chart(times, icons)),
                ("combined_chart", lambda: self.__create_combined_chart(times, temperatures, humidities, pressures, windspeeds, rain_data)),
                ("weather_table", lambda: self.__create_weather_table(forecast_data)),
                ("alert_table", lambda: self.__create_alert_table(times))
            ]
            for cid, chart_func in chart_generators:
                img_html, img_buf = chart_func()
                forecast_html += f"<h3>{cid.replace('_', ' ').title()}</h3>{img_html}"
                forecast_images.append((cid, img_buf))   
        return forecast_html,forecast_images

    def get_current_report(self):
        current_data = self.__get_weather_data(self.current_url)
        current_html = ""
        if current_data:
            current_html += "<h2>Current Weather</h2>"
            current_html += f"<p><strong>Temperature:</strong> {current_data['main']['temp']} °C</p>"
            current_html += f"<p><strong>Humidity:</strong> {current_data['main']['humidity']} %</p>"
            current_html += f"<p><strong>Pressure:</strong> {current_data['main']['pressure']} hPa</p>"
            current_html += f"<p><strong>Weather:</strong> {current_data['weather'][0]['description'].title()}</p>"
            current_html += f"<p><strong>Wind Speed:</strong> {current_data['wind']['speed']} m/s</p>"
            current_html += f"<p><strong>Rain:</strong> {current_data.get('rain', {}).get('1h', 0)} mm</p>"
            alerts = current_data.get('alerts', [])
            current_html += f"<p><strong>Alert:</strong> {alerts[0]['event'] if alerts else 'No alerts'}</p>"
        return current_html   
    

class EmailSender:
    def __init__(self, recipient_email,lat,lon):
        self.weather_report = WeatherReport(lat, lon)
        self.recipient_email = recipient_email
        self.forecast_html,self.forecast_images = self.weather_report.get_forecast_report()
        self.current_html = self.weather_report.get_current_report()
        self.body = f"<html><body>{self.current_html}<hr>{self.forecast_html}</body></html>"
        self.subject = subject
        self.smtp_server_name = smtp_server_name
        self.login = login
        self.password = password
        self.sender_email = login

    def __select_smtp(self,smtp_server_name):
        if smtp_server_name == 'gmail':
            self.smtp_server = 'smtp.gmail.com'
            self.smtp_port = 587
        elif smtp_server_name == 'yahoo':
            self.smtp_server = 'smtp.mail.yahoo.com'
            self.smtp_port = 587
        elif smtp_server_name == 'outlook':
            self.smtp_server = 'smtp-mail.outlook.com'
            self.smtp_port = 587     
        else:
            raise ValueError("Unsupported SMTP server. Please use 'gmail', 'yahoo', or 'outlook'.")
        return self.smtp_server, self.smtp_port

    def send_email(self):
        msg = MIMEMultipart("related")
        msg['From'] = self.sender_email
        msg['To'] = self.recipient_email
        msg['Subject'] = self.subject
        
        alt_part = MIMEMultipart("alternative")
        alt_part.attach(MIMEText(self.body, "html"))
        msg.attach(alt_part)

        for cid, img_buf in self.forecast_images:
            img_buf.seek(0)
            img = MIMEImage(img_buf.read())
            print(f"{cid} size: {img_buf.getbuffer().nbytes} bytes")
            img.add_header("Content-ID", f"<{cid}>")
            img.add_header("Content-Disposition", "inline", filename=f"{cid}.png")
            msg.attach(img)
        smtp_server,smtp_port = self.__select_smtp(self.smtp_server_name)

        with smtplib.SMTP(smtp_server,smtp_port) as server:
            server.starttls()
            server.login(self.login, self.password)
            server.sendmail(self.sender_email, self.recipient_email, msg.as_string())
            print('Email sent successfully!')


def lambda_handler(event, context):
    if 'body' not in event or not event['body']:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing event body.'})
        }
    
    try:
        payload = json.loads(event['body'])
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Malformed JSON in body.'})
        }
    
    required_fields = ['recipient_email', 'lat', 'lon']
    missing = [field for field in required_fields if field not in payload or not payload[field]]

    if missing:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f'Missing or empty fields: {", ".join(missing)}'})
        }
    
    recipient_email = payload.get('recipient_email')
    lat = payload.get('lat')
    lon = payload.get('lon')

    if not is_valid_email(recipient_email):
        return {
            'statusCode': 400,
            'body': 'Invalid request: recipient_email must be valid.'
        }

    if not is_valid_lat_lon(lat, lon):
        return {
            'statusCode': 400,
            'body': 'Invalid request: Both lat and lon must be valid coordinates.'
        }

    email_sender = EmailSender(recipient_email, lat, lon)
    email_sender.send_email()

    return {
        'statusCode': 200,
        'body': 'Email sent successfully!'
    }

# #default values for testing
# bangalore_lat = 12.9716
# bangalore_lon = 77.5946
# default_recipient_email = "mohitkgupta22@gmail.com"

# lat = input("Enter latitude: ")
# if not lat:
#     lat = bangalore_lat
#     print(f"No input provided. Using default latitude: {lat}")
# lon = input("Enter longitude: ")
# if not lon:
#     lon = bangalore_lon
#     print(f"No input provided. Using default longitude: {lon}")
# recipient_email = input("Enter recipient email: ")
# if not recipient_email:
#     recipient_email = default_recipient_email
#     print(f"No input provided. Using default email: {recipient_email}")

# lambda_handler({"body":json.dumps({
#     'recipient_email': recipient_email,
#     'lat': lat,
#     'lon': lon})
# }, None)