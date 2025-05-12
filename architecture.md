# weather-report

## FOR AWS Deplyment:

1. API Gateway
The public entry point. When a user wants a weather update, they hit this API with their email and location.

2. Lambda Function
It does three things:

Takes input (lat, lon, email)

Fetches weather from an external API (like OpenWeatherMap)

Sends a formatted email with the forecast. (using SMTP server, gmail/yahoo/outlook)

3. SSM Parameter Store
All our secrets — like the weather API key and email details — are stored securely here, so they’re not hardcoded anywhere.

4. GitHub + CI/CD
We keep our code in GitHub, and anytime we push updates, our CI/CD pipeline automatically deploys the new Lambda code — no manual zipping or uploading needed.


## Additional services can we used:
1. EventBridge
Each user can have a scheduled rule (like “every day at 7am”) that triggers the Lambda for their location/email.

2. Email Service (like SES)
We can use it for email delivery. Lambda hands it off to SES or another email provider to send.

