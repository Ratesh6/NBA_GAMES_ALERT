# NBA_GAMES_ALERT
USING AWS SNS LAMBDA AND EVENTBRIDGE

EventBridge (Every 10 mins)
           |
           v
      Lambda Function
           |
           v
   Fetch NBA Data from API
           |
           v
       Process Data
           |
     -----------------
     |               |
Games Today?       No Games
     |               |
     v               v
Prepare Score Msg  Prepare "No games today" Msg
           |
           v
Publish to SNS Topic
           |
           v
 Users receive Email/SMS
