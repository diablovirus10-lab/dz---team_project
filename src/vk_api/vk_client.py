"""VK client wrapper."""

class VKClient:
    def __init__(self, token):
        self.token = token

    def send_message(self, user_id, text, keyboard=None):
        """Send a message through VK API."""
        raise NotImplementedError("VKClient.send_message must be implemented")

    def receive_updates(self):
        """Receive updates from VK API."""
        raise NotImplementedError("VKClient.receive_updates must be implemented")
