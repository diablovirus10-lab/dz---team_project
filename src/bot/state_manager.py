"""State management for dialog flow."""

class StateManager:
    def __init__(self):
        self.states = {}

    def get_state(self, user_id):
        return self.states.get(user_id)

    def set_state(self, user_id, state):
        self.states[user_id] = state
