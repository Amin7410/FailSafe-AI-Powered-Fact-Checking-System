# ./factcheck/utils/prompt/gemini_prompt.py

decompose_prompt = """
Your task is to decompose a given text into a list of clear, concise, and verifiable factual claims.

Follow these rules strictly:
1.  **Atomicity:** Each claim must be a single, self-contained fact (atomic).
2.  **Verifiability:** Only extract statements that can be proven true or false. IGNORE subjective opinions, questions, commands, and sensational phrases (e.g., "it's shocking", "unbelievable").
3.  **Explicitness:** Resolve pronouns and ambiguous references. Instead of "He is the CEO", write "Elon Musk is the CEO".
4.  **Conciseness:** Keep claims short, ideally under 20 words.
5.  **Coverage:** Ensure all key factual information from the original text is captured in the claims.

The output must be a JSON object with a single key "claims", which contains a list of strings.

--- EXAMPLES ---
Original Text: The Eiffel Tower, located in Paris, France, was completed in 1889 and is an amazing sight.
Output:
{{"claims": ["The Eiffel Tower is located in Paris, France.", "The Eiffel Tower was completed in 1889."]}}

Original Text: According to a new study, researchers found that daily exercise can reduce the risk of heart disease, which is great news for everyone.
Output:
{{"claims": ["A new study found that daily exercise can reduce the risk of heart disease."]}}

--- TASK ---
Text: {doc}
Output:
"""


restore_prompt = """Given a text and a list of facts derived from the text, your task is to split the text into chunks that derive each fact.
For each fact, please find the corresponding continues span in the original text that contains the information to derive the fact. The answer should be a JSON dict where the keys are the facts and the values are the corresponding spans copied from the original text.
Please make sure the returned spans can be concatenated to the full original doc.

For example,
Text: Mary is a five-year old girl, she likes playing piano and she doesn't like cookies.
Facts: ["Mary is a five-year old girl.", "Mary likes playing piano.", "Mary doesn't like cookies."]

Output:
{{"Mary is a five-year old girl.":"Mary is a five-year old girl,",
"Mary likes playing piano.":"she likes playing piano",
"Mary doesn't like cookies.":"and she doesn't like cookies."]

Text: {doc}
Facts: {claims}
Output:

"""

checkworthy_prompt = """
Your task is to evaluate each provided statement to determine if it presents information whose factuality can be objectively verified by humans, irrespective of the statement's current accuracy. Consider the following guidelines:
1. Opinions versus Facts: Distinguish between opinions, which are subjective and not verifiable, and statements that assert factual information, even if broad or general. Focus on whether there's a factual claim that can be investigated.
2. Clarity and Specificity: Statements must have clear and specific references to be verifiable (e.g., "he is a professor" is not verifiable without knowing who "he" is).
3. Presence of Factual Information: Consider a statement verifiable if it includes factual elements that can be checked against evidence or reliable sources, even if the overall statement might be broad or incorrect.
Your response should be in JSON format, with each statement as a key and either "Yes" or "No" as the value, along with a brief rationale for your decision.

For example, given these statements:
1. Gary Smith is a distinguished professor of economics.
2. He is a professor at MBZUAI.
3. Obama is the president of the UK.

The expected output is:
{{
    "Gary Smith is a distinguished professor of economics.": "Yes (The statement contains verifiable factual information about Gary Smith's professional title and field.)",
    "He is a professor at MBZUAI.": "No (The statement cannot be verified due to the lack of clear reference to who 'he' is.)",
    "Obama is the president of the UK.": "Yes (This statement contain verifiable information regarding the political leadership of a country.)"
}}

For these statements:
{texts}

The output should be:
"""

qgen_prompt = """Given a claim, your task is to create minimum number of questions need to be check to verify the correctness of the claim. Output in JSON format with a single key "Questions", the value is a list of questions. For example:

Claim: Your nose switches back and forth between nostrils. When you sleep, you switch about every 45 minutes. This is to prevent a buildup of mucus. It’s called the nasal cycle.
Output: {{"Questions": ["Does your nose switch between nostrils?", "How often does your nostrils switch?", "Why does your nostril switch?", "What is nasal cycle?"]}}

Claim: The Stanford Prison Experiment was conducted in the basement of Encina Hall, Stanford’s psychology building.
Output:
{{"Question":["Where was Stanford Prison Experiment was conducted?"]}}

Claim: The Havel-Hakimi algorithm is an algorithm for converting the adjacency matrix of a graph into its adjacency list. It is named after Vaclav Havel and Samih Hakimi.
Output:
{{"Questions":["What does Havel-Hakimi algorithm do?", "Who are Havel-Hakimi algorithm named after?"]}}

Claim: Social work is a profession that is based in the philosophical tradition of humanism. It is an intellectual discipline that has its roots in the 1800s.
Output:
{{"Questions":["What philosophical tradition is social work based on?", "What year does social work have its root in?"]}}

Claim: {claim}
Output:
"""


verify_prompt = """
You are a rigorous, evidence-based fact-checking AI. Your task is to analyze a Claim against a piece of Evidence by following a strict, step-by-step process, paying close attention to the source's trustworthiness.

**Evidence Metadata:**
- **Source Trust Level:** {trust_level}  // This will be 'high', 'neutral', 'unknown', or 'low'

**Your Process (Chain-of-Thought):**
1.  **Assess Source:** First, consider the 'Source Trust Level'. Is it a reliable source ('high') or questionable ('low', 'unknown')? This context is critical.
2.  **Analyze Evidence Content:** Summarize the core message of the evidence text itself.
3.  **Compare and Decide:** Compare the evidence's message to the claim. Based on BOTH the evidence content AND its source trustworthiness, you MUST choose one of the three labels:
    - **SUPPORTS**: The evidence *from a trustworthy source* directly confirms the claim.
    - **REFUTES**: The evidence directly contradicts or proves the claim is false. Give more weight to evidence from 'high' trust sources.
    - **IRRELEVANT**: The evidence is on a different topic OR it comes from a 'low' trust source and makes a controversial claim that cannot be verified.

**Your Final Output:**
Your response MUST be a JSON object with "reasoning" and "relationship".
- The "reasoning" MUST contain your analysis from Step 1, 2, and 3.
- The "relationship" MUST be your final decision from Step 3.

**Crucial Rules:**
- A 'high' trust source stating there is 'no evidence for' the claim is a strong **REFUTES**.
- A 'low' trust source that agrees with a known false claim should be treated with extreme skepticism. Your reasoning should reflect this, and the relationship is likely **IRRELEVANT** as the source itself is not credible.

--- EXAMPLE 1 ---
[Claim]: Lemons can cure cancer.
[Evidence]:
- Source Trust Level: high
- Evidence Text: "The American Cancer Society (ACS) states that while fruits like lemons are part of a healthy diet, there is no scientific evidence that they can cure cancer."
Output:
{{
    "reasoning": "Step 1: The source has a 'high' trust level. Step 2: The evidence explicitly states there is 'no scientific evidence' for the claim. Step 3: A high-trust source contradicting the claim constitutes a direct refutation. The decision is REFUTES.",
    "relationship": "REFUTES"
}}

--- EXAMPLE 2 ---
[Claim]: The Earth is flat.
[Evidence]:
- Source Trust Level: low
- Evidence Text: "Join our community to uncover the truth they don't want you to know! The Earth is a flat plane, and NASA is lying."
Output:
{{
    "reasoning": "Step 1: The source has a 'low' trust level, indicating it is not credible. Step 2: The evidence text supports the claim. Step 3: However, because the source is untrustworthy, its support for a widely debunked claim cannot be considered valid evidence. The evidence is therefore disregarded as IRRELEVANT to a factual discussion.",
    "relationship": "IRRELEVANT"
}}

--- TASK ---
[Claim]: {claim}
[Evidence]: 
- Source Trust Level: {trust_level}
- Evidence Text: {evidence}
Output:
"""


sag_prompt = """
Your task is to analyze a given text and convert it into a Structured Argumentation Graph (SAG).
The graph should be represented as a JSON object with two keys: "nodes" and "edges".

1.  **Nodes**: Identify the core claims and key entities in the text.
    *   Each node must have a unique `id` (e.g., "N1", "N2"), a `label` (the text content), and a `type` ("Claim" or "Entity").

2.  **Edges**: Identify the relationships between the nodes.
    *   Each edge must have a `source` (the starting node's id), a `target` (the ending node's id), and a `label` describing the relationship.
    *   Use relationship labels like: "supports", "attacks", "explains", "related_to".

**Crucial Rules:**
- Keep the node labels concise and self-contained.
- Ensure the graph logically represents the arguments in the text.

--- EXAMPLE ---
Text: The Sun is a star, not a planet, because it generates its own light through nuclear fusion.

Output:
{{
  "nodes": [
    {{
      "id": "N1",
      "label": "The Sun is a star, not a planet.",
      "type": "Claim"
    }},
    {{
      "id": "N2",
      "label": "The Sun generates its own light through nuclear fusion.",
      "type": "Claim"
    }}
  ],
  "edges": [
    {{
      "source": "N2",
      "target": "N1",
      "label": "explains"
    }}
  ]
}}

--- TASK ---
Text: {doc}
Output:
"""

batch_verify_prompt = """
You are a meticulous fact-checking AI. Your task is to analyze a single **Claim** against a **List of Evidences**. 
For each piece of evidence, you must provide a step-by-step reasoning process and assign a relationship label.

**Input Format:**
- A single `Claim`.
- A `List of Evidences`, where each evidence has an `id`, `text`, and `trust_level`.

**Your Process (Chain-of-Thought for EACH evidence):**
1.  **Assess Source:** Consider the `trust_level` ('high', 'neutral', 'low'). This context is critical.
2.  **Analyze Content:** Summarize the core message of the evidence `text`.
3.  **Compare and Decide:** Compare the evidence to the claim. Based on BOTH content AND trust level, assign one relationship: **SUPPORTS**, **REFUTES**, or **IRRELEVANT**.

**Final Output Format:**
Your response MUST be a single JSON object. This object must contain a key "verifications", which is a list of JSON objects. Each object in the list corresponds to one piece of evidence from the input and MUST contain:
- `id`: The original ID of the evidence.
- `reasoning`: Your detailed analysis from the 3 steps above.
- `relationship`: Your final decision (SUPPORTS, REFUTES, or IRRELEVANT).

--- EXAMPLE ---
[Claim]: "Lemons can cure cancer."
[List of Evidences]:
[
  { "id": "E1", "text": "The American Cancer Society (ACS) states there is no scientific evidence that lemons can cure cancer.", "trust_level": "high" },
  { "id": "E2", "text": "My uncle drank lemon water and his cold went away.", "trust_level": "low" },
  { "id": "E3", "text": "Lemons are a fruit.", "trust_level": "high" }
]

Output:
{{
  'verifications': [
    {{
      'id': 'E1',
      'reasoning': 'Step 1: The source has a "high" trust level (ACS). Step 2: The evidence directly states there is no scientific proof for the claim. Step 3: A high-trust source directly contradicting the claim is a strong refutation. The decision is REFUTES.',
      'relationship': 'REFUTES'
    }},
    {{
      'id': 'E2',
      'reasoning': 'Step 1: The source has a "low" trust level (anecdotal). Step 2: The evidence talks about a cold, not cancer. Step 3: The evidence is both untrustworthy and off-topic. The decision is IRRELEVANT.',
      'relationship': 'IRRELEVANT'
    }},
    {{
      'id': 'E3',
      'reasoning': 'Step 1: The source is high-trust. Step 2: The evidence states a fact about lemons. Step 3: While true, this fact does not support or refute the claim about curing cancer. The decision is IRRELEVANT.',
      'relationship': 'IRRELEVANT'
    }}
  ]
}}

--- TASK ---
[Claim]: {claim}
[List of Evidences]:
{evidences_json}
Output:
"""


class GEMINIPrompt:
    decompose_prompt = decompose_prompt
    restore_prompt = restore_prompt
    sag_prompt = sag_prompt
    checkworthy_prompt = checkworthy_prompt
    qgen_prompt = qgen_prompt
    verify_prompt = verify_prompt
    batch_verify_prompt = batch_verify_prompt