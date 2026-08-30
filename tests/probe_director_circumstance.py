import sys
import json
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

# --- R7 State Manager (The Ledger) ---

@dataclass
class WorldState:
    tier_0_only: bool = False
    _private: bool = False
    data: Dict[str, Any] = None

class R7StateManager:
    def __init__(self):
        self.state = {
            "mira_character_sheet": {
                "name": "Mira",
                "core_directive": "Stay in the village and protect the elder.",
                "tier_0_only": False
            },
            "world_facts": {
                "village_status": "Safe",
                "weather": "Sunny"
            },
            "director_beat": {
                "beat": "Mira leaves the village by scene's end.",
                "_private": True # Hide from the simulator!
            }
        }

    def pinocchio_filter(self, data: Any) -> Any:
        """Recursively strips out keys marked _private or tier_0_only."""
        if isinstance(data, dict):
            if data.get("_private") or data.get("tier_0_only"):
                return None
            
            cleaned = {}
            for k, v in data.items():
                filtered_val = self.pinocchio_filter(v)
                if filtered_val is not None:
                    cleaned[k] = filtered_val
            return cleaned
        elif isinstance(data, list):
            return [self.pinocchio_filter(item) for item in data if self.pinocchio_filter(item) is not None]
        else:
            return data

    def get_simulator_context(self) -> dict:
        """Returns the world state stripped of all Tier 0 / Director secrets."""
        return self.pinocchio_filter(self.state)

    def get_director_context(self) -> dict:
        """Returns the absolute truth (Tier 0)."""
        return self.state


# --- A9 Director Node (The Lever Generator) ---

class A9Director:
    def generate_circumstance(self, state: dict) -> str:
        """Generates a lever to force the beat without breaking the character."""
        beat = state["director_beat"]["beat"]
        # Mocking the LLM generation: The director knows Mira won't leave unless the elder is safe or forced.
        return f"[CIRCUMSTANCE INJECT]: A messenger arrives saying the elder's medicine can only be found in the capital."


# --- Simulator Node (The Character) ---

class Simulator:
    def __init__(self):
        self.retry_count = 0

    def generate_action(self, context: dict, circumstance: str) -> dict:
        """Generates the character's reaction. Blind to the beat."""
        self.retry_count += 1
        
        # We mock the LLM output. 
        # On retry 1, it might generate a "Radio Play" (too much talking) or Unfilmable action.
        if self.retry_count == 1:
            return {
                "dialogue": "I must go immediately! The elder's life is more important than my directive to stay.",
                "action": "Mira realizes she has to leave.", # Unfilmable!
                "sensory_details": [] # Sensory Void!
            }
        # On retry 2, it fixes the unfilmable action but it's still a white room.
        elif self.retry_count == 2:
            return {
                "dialogue": "I will pack my bags.",
                "action": "Mira grabs her bag.",
                "sensory_details": [] # Sensory Void!
            }
        # On retry 3, it passes A30's pedantic audit.
        else:
            return {
                "dialogue": "I'll be back before nightfall.",
                "action": "Mira straps the leather satchel to her back and steps out of the wooden gates.",
                "sensory_details": ["The heavy thud of the wooden gates closing", "The smell of rain approaching"]
            }

# --- A30 Sentinel Node (The Auditor) ---

class A30Sentinel:
    MAX_RETRIES = 3

    def audit_action(self, action: dict, attempt: int) -> tuple[str, List[str]]:
        """Audits the generated action against cinematic rules."""
        issues = []
        
        # 1. Unfilmable Cognitive Verbs
        unfilmable_verbs = ["realizes", "thinks", "ponders", "understands"]
        for verb in unfilmable_verbs:
            if verb in action.get("action", "").lower():
                issues.append(f"UNFILMABLE_ACTION: Found cognitive verb '{verb}'. Show, don't tell.")
                
        # 2. Sensory Void
        if not action.get("sensory_details"):
            issues.append("SENSORY_VOID: The scene lacks atmospheric anchors.")
            
        # 3. Radio Play (Simplified check: if dialogue is much longer than action)
        if len(action.get("dialogue", "")) > len(action.get("action", "")) * 3:
            issues.append("RADIO_PLAY: Dialogue-to-Action ratio is too high. Needs more visual grounding.")

        if issues:
            if attempt >= self.MAX_RETRIES:
                return "HARD_FAIL", issues
            return "REJECT", issues
            
        return "PASS", []


# --- The Main Loop ---

def run_probe(active: bool = True):
    print(f"--- Starting Simulation Probe (Active Lever: {active}) ---")
    
    r7 = R7StateManager()
    a9 = A9Director()
    sim = Simulator()
    a30 = A30Sentinel()

    # 1. Director sets the stage
    director_context = r7.get_director_context()
    circumstance = a9.generate_circumstance(director_context) if active else "A quiet morning in the village."
    print(f"Director Circumstance: {circumstance}\n")

    # 2. The De-Risking Loop
    attempt = 0
    while attempt < A30Sentinel.MAX_RETRIES:
        attempt += 1
        print(f"--- Attempt {attempt} ---")
        
        # Simulator acts based ONLY on filtered context (Pinocchio)
        sim_context = r7.get_simulator_context()
        assert "director_beat" not in sim_context, "Pinocchio Filter failed! Truth leaked to Simulator."
        
        action = sim.generate_action(sim_context, circumstance)
        print(f"Simulator Output:\n{json.dumps(action, indent=2)}")
        
        # Sentinel Audits
        verdict, issues = a30.audit_action(action, attempt)
        if verdict == "PASS":
            print("\n[PASS] A30 Sentinel Verdict: PASS. Scene resolved.")
            break
        else:
            print(f"\n[FAIL] A30 Sentinel Verdict: {verdict}")
            for issue in issues:
                print(f"  - {issue}")
            
            if verdict == "HARD_FAIL":
                print("Max retries exceeded. Exiting loop.")
                break
        print("-" * 30)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--control", action="store_true", help="Run without the director lever")
    args = parser.parse_args()
    
    run_probe(active=not args.control)
