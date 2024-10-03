# firebase.py
import firebase_admin
from firebase_admin import credentials, messaging

cred = credentials.Certificate(
    "utils/berchi-b12fb-firebase-adminsdk-1hcoo-9a6604967c.json"
)
firebase_admin.initialize_app(cred)


def send_push_notification(
    token: str, title: str, body: str, image: str = None, link: str = None
):
    print(image)
    # webpushFCMoptions=messaging.WebpushFCMOptions(link=link)
    # webpush=messaging.WebpushConfig(fcm_options=webpushFCMoptions)
    data = None
    if link or image:
        data = {}
    if link:
        data["link"] = link
    if image:
        data["image"] = image

    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body, image=image),
        token=token,
        data=data,
    )
    response = messaging.send(message)
    print("Successfully sent message:", response)
