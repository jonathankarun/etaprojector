import requests
from datetime import datetime, timedelta
from twilio.rest import Client

# Constants (replace these with your actual API keys)
GOOGLE_MAPS_API_KEY = 'YOUR_GOOGLE_MAPS_API_KEY'
TWILIO_ACCOUNT_SID = 'YOUR_TWILIO_ACCOUNT_SID'
TWILIO_AUTH_TOKEN = 'YOUR_TWILIO_AUTH_TOKEN'
TWILIO_PHONE_NUMBER = 'YOUR_TWILIO_PHONE_NUMBER'

def get_route_info(origin, destination):
    """
    Fetch optimal route and traffic information between origin and destination using Google Maps API.
    Returns:
        dict: Information including duration, traffic delay, and best route.
    """
    url = 'https://maps.googleapis.com/maps/api/directions/json'
    params = {
        'origin': origin,
        'destination': destination,
        'key': GOOGLE_MAPS_API_KEY,
        'departure_time': 'now',  # 'now' gives live traffic data
        'traffic_model': 'best_guess'
    }
    response = requests.get(url, params=params)
    data = response.json()
    
    try:
        route = data['routes'][0]['legs'][0]
        duration = route['duration']['text']
        duration_in_traffic = route['duration_in_traffic']['text']
        traffic_delay = (route['duration_in_traffic']['value'] - route['duration']['value']) / 60  # in minutes
        
        return {
            'duration': duration,
            'duration_in_traffic': duration_in_traffic,
            'traffic_delay': traffic_delay,
            'start_address': route['start_address'],
            'end_address': route['end_address']
        }
    except (IndexError, KeyError):
        return {"error": "Unable to retrieve route information"}

def get_optimal_departure_time(desired_arrival_time, route_duration_in_minutes):
    """
    Calculate the optimal time to leave to arrive at the desired time.
    Returns:
        datetime: The best time to leave to reach on time.
    """
    return desired_arrival_time - timedelta(minutes=route_duration_in_minutes)

def send_eta_notification(route_info, departure_time, recipient_phone):
    #Send an ETA notification using Twilio with route and traffic info.

    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    message = (f"Optimal Route from {route_info['start_address']} to {route_info['end_address']}:\n"
               f"Travel Time: {route_info['duration']} (In traffic: {route_info['duration_in_traffic']})\n"
               f"Traffic Delay: ~{int(route_info['traffic_delay'])} minutes\n"
               f"Best Time to Leave: {departure_time.strftime('%I:%M %p')}")
    
    sms = client.messages.create(
        body=message,
        from_=TWILIO_PHONE_NUMBER,
        to=recipient_phone
    )
    print(f"Notification sent: {sms.sid}")

# Main function to calculate route, traffic, and send ETA notification
def eta_projector(origin, destination, desired_arrival_time, recipient_phone):

    route_info = get_route_info(origin, destination)
    if 'error' in route_info:
        print(route_info['error'])
        return
    
    route_duration_in_minutes = int(route_info['duration_in_traffic'].split()[0])
    departure_time = get_optimal_departure_time(desired_arrival_time, route_duration_in_minutes)
    
    # Send notification with all details
    send_eta_notification(route_info, departure_time, recipient_phone)

# Example usage
origin_address = "123 Main St, Albany, New York"
destination_address = "456 Elm St, New York City, New York"
desired_arrival = datetime.now() + timedelta(hours=2)  # Desired arrival in 2 hours
recipient_phone_number = "+1234567890"

eta_projector(origin_address, destination_address, desired_arrival, recipient_phone_number)
