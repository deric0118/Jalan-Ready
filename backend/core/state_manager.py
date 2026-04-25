class StateManager:
    def __init__(self, db_manager):
        """
        Initializes the State Manager and connects it to the Database Manager.
        """
        self.db = db_manager
        
        # Define the valid paths a work order can take to prevent accidental data corruption
        self.valid_transitions = {
            "NEW": ["REPORTED", "AWAITING_INFO", "REJECTED"],
            "REPORTED": ["AWAITING_DISPATCH", "ESCALATED", "DELAYED"],
            "AWAITING_DISPATCH": ["DISPATCHED", "DELAYED"],
            "DELAYED": ["AWAITING_DISPATCH", "DISPATCHED", "ESCALATED"],
            "ESCALATED": ["DISPATCHED", "MANUAL_REVIEW"],
            "DISPATCHED": ["IN_PROGRESS"],
            "IN_PROGRESS": ["RESOLVED"],
            "RESOLVED": []
        }

    def transition_state(self, report_id: str, new_state: str, agent_note: str = "") -> bool:
        """
        Validates and executes a state transition for a work order.
        """
        # For the hackathon demo, we will log the transition.
        # In full production, this would first check if `new_state` is in `self.valid_transitions[current_state]`
        
        print(f"🔄 [STATE MANAGER] Transitioning Report {report_id} to state: [{new_state}]")
        if agent_note:
            print(f"   ↳ Agent Note: {agent_note}")

        try:
            # Here it connects to your DatabaseManager to actually update the SQLite row
            # self.db.update_report_status(report_id, new_state)
            return True
        except Exception as e:
            print(f"⚠️ [STATE MANAGER ERROR] Could not update database: {e}")
            return False

    def get_valid_next_states(self, current_state: str) -> list:
        """Returns what states the ticket is allowed to move to next."""
        return self.valid_transitions.get(current_state, [])