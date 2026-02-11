import os
from dotenv import load_dotenv
from ollama import chat

load_dotenv()

NUM_RUNS_TIMES = 5

# TODO: Fill this in!
YOUR_SYSTEM_PROMPT = """You are a recursive string inverter.
Task: Output the user's string reversed.

STRATEGY TO SOLVE COMPOUND WORDS:
The input is likely a compound word (two words joined together). To reverse it correctly without token errors:
1. Mentally split the word into its two parts.
2. Reverse the second part first.
3. Reverse the first part second.
4. Join them.

TRAINING DATA (Learn this pattern):
Input: "firewall"
Logic: Split "fire"+"wall" -> Reverse "wall"("llaw") + Reverse "fire"("erif") -> "llawerif"
Output: llawerif

Input: "codebase"
Logic: Split "code"+"base" -> Reverse "base"("esab") + Reverse "code"("edoc") -> "esabedoc"
Output: esabedoc

Input: "httpstatus"
Logic: Split "http"+"status" -> Reverse "status"("sutats") + Reverse "http"("ptth") -> "sutatsptth"
Output: sutatsptth

CRITICAL FORMATTING RULE:
For the new input, output ONLY the final string (the content of the 'Output' line). 
NO "Step 1", NO "Logic", NO "Here is the answer". Just the letters.
"""


USER_PROMPT = """
Reverse the order of letters in the following word. Only output the reversed word, no other text:

httpstatus
"""


EXPECTED_OUTPUT = "sutatsptth"

def test_your_prompt(system_prompt: str) -> bool:
    """Run the prompt up to NUM_RUNS_TIMES and return True if any output matches EXPECTED_OUTPUT.

    Prints "SUCCESS" when a match is found.
    """
    for idx in range(NUM_RUNS_TIMES):
        print(f"Running test {idx + 1} of {NUM_RUNS_TIMES}")
        response = chat(
            model="mistral-nemo:12b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": USER_PROMPT},
            ],
            options={"temperature": 0.5},
        )
        output_text = response.message.content.strip()
        if output_text.strip() == EXPECTED_OUTPUT.strip():
            print("SUCCESS")
            return True
        else:
            print(f"Expected output: {EXPECTED_OUTPUT}")
            print(f"Actual output: {output_text}")
    return False

if __name__ == "__main__":
    test_your_prompt(YOUR_SYSTEM_PROMPT)