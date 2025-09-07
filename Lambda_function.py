import urllib.request
import os
from datetime import datetime, timedelta, timezone
import boto3
import json

def lambda_handler(event, context):
    # Fetch environment variables
    sport_data_api_key = os.getenv("SPORTS_DATA_API_KEY")  # Make sure you set this in Lambda
    sns_arn = os.getenv("SNS_TOPIC_ARN")                   # Set this too
    region = os.environ["AWS_REGION"]                      # Auto set by Lambda runtime

    sns_client = boto3.client("sns", region_name=region)

    def get_game_data():
        utc_now = datetime.now(timezone.utc)
        # SportsData.io expects date in UTC (YYYY-MM-DD)
        today_date = utc_now.strftime("%Y-%m-%d")

        try:
            print(f"Fetching game data for {today_date}")
            url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{today_date}"
            
            # Add API key in header (correct way)
            req = urllib.request.Request(url, headers={"Ocp-Apim-Subscription-Key": sport_data_api_key})
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())

            print("API Response:", data)
            return data  # This should be a list of game dicts
        except Exception as e:
            print(f"Error while fetching game data: {e}")
            return []  # Return empty list instead of None to avoid iteration errors

    def format_game_data(game):
        if not game:
            return None

        status = game.get("Status", "Unknown")
        away_team = game.get("AwayTeam", "Unknown")
        home_team = game.get("HomeTeam", "Unknown")
        final_score = f"{game.get('AwayTeamScore', 'N/A')}-{game.get('HomeTeamScore', 'N/A')}"
        start_time = game.get("DateTime", "Unknown")
        channel = game.get("Channel", "Unknown")

        # Format quarters
        quarters = game.get("Quarters", [])
        quarter_scores = ', '.join([
            f"Q{q['Number']}: {q.get('AwayScore', 'N/A')}-{q.get('HomeScore', 'N/A')}" 
            for q in quarters
        ])

        base_message = f"Game Status: {status}\n{away_team} vs {home_team}\nChannel: {channel}\n"

        if status == "Final":
            return base_message + f"Final Score: {final_score}\nStart Time: {start_time}\nQuarter Scores: {quarter_scores}\n"
        elif status == "InProgress":
            last_play = game.get("LastPlay", "N/A")
            return base_message + f"Current Score: {final_score}\nLast Play: {last_play}\n"
        elif status == "Scheduled":
            return base_message + f"Start Time: {start_time}\n"
        else:
            return base_message + "Details are unavailable at the moment.\n"

    def publish_to_sns(message):
        try:
            response = sns_client.publish(
                TopicArn=sns_arn,
                Message=message,
                Subject="NBA Game Day Notification"
            )
            print("Published message to SNS topic successfully.")
            print("MessageId:", response.get("MessageId"))
        except Exception as e:
            print(f"Error while publishing to SNS: {e}")

    # Fetch games
    game_data = get_game_data()

    if game_data and len(game_data) > 0:
        messages = [format_game_data(game) for game in game_data if game]
        final_message = "\n---\n".join([m for m in messages if m])
    else:
        # Fallback message if no games or API fails
        final_message = "NBA Alert System is working, but no games are available today."

    publish_to_sns(final_message)