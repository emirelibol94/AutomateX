from dataclasses import dataclass, field
from typing import List, Optional, Any

@dataclass
class Action:
    type: str  # CLICK, TYPE, WAIT, LAUNCH_APP, ASSERT_EXISTS, etc.
    params: dict = field(default_factory=dict)
    description: str = ""
    id: str = ""
    # v63: Advanced parameters
    match_index: int = 0
    offset: tuple = (0, 0)

@dataclass
class Scenario:
    name: str
    description: str
    actions: List[Action] = field(default_factory=list)
    id: Optional[int] = None # v70: Add ID for tracking changes
    variables: dict = field(default_factory=dict) # v167.17: Scenario-level variables

    def add_action(self, action: Action):
        self.actions.append(action)

    def as_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "variables": self.variables, # v167.17
            "actions": [
                {
                    "type": a.type, 
                    "params": a.params, 
                    "description": a.description, 
                    "id": a.id,
                    "match_index": a.match_index,
                    "offset": a.offset
                }
                for a in self.actions
            ]
        }

    @staticmethod
    def from_dict(data: dict):
        scenario = Scenario(
            name=data["name"], 
            description=data.get("description", ""),
            variables=data.get("variables", {}) # v167.17
        )
        for action_data in data.get("actions", []):
            scenario.add_action(Action(
                type=action_data["type"],
                params=action_data.get("params", {}),
                description=action_data.get("description", ""),
                id=action_data.get("id", ""),
                match_index=action_data.get("match_index", 0),
                offset=tuple(action_data.get("offset", (0, 0)))
            ))
        return scenario
