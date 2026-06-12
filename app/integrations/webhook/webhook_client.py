import requests


class WebhookClient:

    @staticmethod
    def post(url, payload):

        return requests.post(url, json=payload)
