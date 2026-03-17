"""
Data Factory Demand Intelligence Agent — Prototype
====================================================
Uses Mistral Agents API to automate the demand monitoring role
currently handled manually in Le Chat.

Prerequisites:
    pip install mistralai
    export MISTRAL_API_KEY="your-key"

This is a starting skeleton — flesh out after testing API access.
"""

from mistralai import Mistral
import os
import json
from datetime import datetime

# --- Configuration ---

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
OUTPUT_DIR = os.path.expanduser("~/dev/vilseckki-datafactory-app/demand-signals/")

AGENT_INSTRUCTIONS = """
You are the Demand Intelligence Agent for VilseckKI Data Factory.

Your job is to identify opportunities for synthetic dataset generation
that can be sold on Datarade and HuggingFace.

Focus areas:
1. German Mittelstand B2B data (ERP test data, SAP/Datev-compatible)
2. EU AI Act compliance test datasets
3. German healthcare / insurance dialogue data
4. Agricultural time-series (Bavaria + Tohoku/Hokkaido, Japan)
5. EHCP/SEND plans for UK special education (dissertation use)

For each opportunity, provide:
- Dataset name and description
- Target buyer persona
- Estimated record count
- Suggested price range (EUR)
- Column schema sketch
- Competitive landscape (what exists, what's missing)
- Confidence level (high / medium / low)

Output as structured JSON.
"""

SEARCH_QUERIES = [
    "synthetic data marketplace demand 2026",
    "Datarade most searched dataset categories",
    "EU AI Act training data requirements",
    "German SME test data needs",
    "HuggingFace dataset requests synthetic",
    "Bavarian AI Act Accelerator partner projects",
]


def create_demand_agent(client: Mistral) -> str:
    """Create the demand intelligence agent."""
    agent = client.beta.agents.create(
        model="mistral-large-latest",
        name="datafactory-demand-intel",
        instructions=AGENT_INSTRUCTIONS,
        tools=[
            {"type": "web_search"},
            {"type": "code_interpreter"},
        ],
    )
    return agent.id


def run_demand_scan(client: Mistral, agent_id: str) -> dict:
    """Execute a demand scan using the agent."""
    # Start a conversation
    conversation = client.beta.conversations.create(agent_id=agent_id)

    # Send the research prompt
    prompt = f"""
    Run a demand scan for synthetic dataset opportunities.

    Search for:
    {json.dumps(SEARCH_QUERIES, indent=2)}

    For each promising opportunity found, output structured JSON with the
    fields specified in your instructions.

    Date: {datetime.now().strftime('%Y-%m-%d')}
    """

    response = client.beta.conversations.append(
        conversation_id=conversation.id,
        message={"role": "user", "content": prompt},
    )

    return {
        "date": datetime.now().isoformat(),
        "conversation_id": conversation.id,
        "response": response.choices[0].message.content,
    }


def save_results(results: dict):
    """Save scan results to the demand-signals directory."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = f"scan-{datetime.now().strftime('%Y-%m-%d')}.json"
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Results saved to {filepath}")


if __name__ == "__main__":
    if not MISTRAL_API_KEY:
        print("Set MISTRAL_API_KEY environment variable first.")
        print("Get your key at: https://console.mistral.ai/api-keys")
        exit(1)

    client = Mistral(api_key=MISTRAL_API_KEY)

    print("Creating demand intelligence agent...")
    agent_id = create_demand_agent(client)
    print(f"Agent created: {agent_id}")

    print("Running demand scan...")
    results = run_demand_scan(client, agent_id)

    save_results(results)
    print("Done. Review results and convert promising leads to YAML configs.")
