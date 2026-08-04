"""Core bot logic."""

class BotLogic:
    def __init__(self, database, vk_client, state_manager):
        self.database = database
        self.vk_client = vk_client
        self.state_manager = state_manager

    def handle_event(self, event):
        """Handle a single incoming event."""
        raise NotImplementedError("BotLogic.handle_event must be implemented")
