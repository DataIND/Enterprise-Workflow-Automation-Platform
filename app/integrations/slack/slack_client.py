import requests


class SlackClient:

    @staticmethod
    def send_message(webhook_url, message):

        return requests.post(webhook_url, json={"text": message})
