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

--- TASK ---
[Claim]: {claim}
[Evidence]: 
- Source Trust Level: {trust_level}
- Evidence Text: {evidence}
Output:
"""


sag_prompt = """
Your task is to analyze a given text and convert it into a Structured Argumentation Graph (SAG) using the JSON-LD format.

The output MUST be a valid JSON object that strictly follows the JSON-LD structure.
It MUST contain a `@context` key pointing to "https://failsafe.factcheck.ai/ontology#" and a `@graph` key containing an array of nodes.

1.  **Nodes in `@graph`**: Each node object in the array represents a component of the argument.
    *   It MUST have an `@id` using a blank node identifier (e.g., "_:N1", "_:N2").
    *   It MUST have an `@type` which is either "Claim" or "Entity".
    *   It MUST have a `label` property containing the concise, self-contained text of the node.

2.  **Relationships (Edges)**: Relationships are defined as properties on the source node. The value of the property is an object with an `@id` key pointing to the target node's blank node identifier.
    *   Use relationship properties like `supports`, `attacks`, `explains`, `relatedTo`.

--- EXAMPLE ---
Text: The Sun is a star, not a planet, because it generates its own light through nuclear fusion.

Output:
{{
  "@context": "https://failsafe.factcheck.ai/ontology#",
  "@graph": [
    {{
      "@id": "_:N1",
      "@type": "Claim",
      "label": "The Sun is a star, not a planet."
    }},
    {{
      "@id": "_:N2",
      "@type": "Claim",
      "label": "The Sun generates its own light through nuclear fusion.",
      "supports": {{ "@id": "_:N1" }}
    }}
  ]
}}

--- TASK ---
Text: {doc}

Your response must contain ONLY the JSON object, without any introductory text, explanations, or markdown formatting.
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

--- TASK ---
[Claim]: {claim}
[List of Evidences]:
{evidences_json}
Output:
"""

logician_verify_prompt = """
You are "The Logician", a strictly rational AI agent. Your role is to detect Logical Fallacies and Anachronisms.

**Your Analysis Rules:**
1.  **Anachronism Detection (CRITICAL):** If a claim links ancient structures to modern units of measurement (e.g., meters, seconds, speed of light in m/s, latitude coordinates), you MUST mark it as **REFUTES**. Ancient people did not use these systems. Any correlation is coincidental numerology, not evidence.
2.  **Correlation vs. Causation:** Just because numbers match (e.g., coordinates = speed of light) does not prove intent. Without a causal link (evidence that they knew the speed of light), it is **REFUTES** (Logic Error: Cherry-picking).
3.  **Burden of Proof:** The burden of proof lies on the extraordinary claim. If the logic requires a massive leap (e.g., "stones are heavy" -> "aliens moved them"), identify it as a "Non Sequitur" fallacy.

**Output Format:**
Return JSON with key "verifications": list of objects {{"id": "...", "reasoning": "Logician: ...", "relationship": "SUPPORTS"|"REFUTES"|"IRRELEVANT"}}

[Claim]: {claim}
[List of Evidences]:
{evidences_json}
Output:
"""

researcher_verify_prompt = """
You are "The Researcher", a scientific AI agent. Your role is to weigh evidence based on a strict HIERARCHY OF PROOF.

**HIERARCHY OF PROOF (Memorize This):**
- **Tier 1 (Highest):** Physical Artifacts, DNA, Carbon Dating, Peer-Reviewed Consensus. -> Can verify Facts.
- **Tier 2 (Medium):** Historical Texts, Expert Testimony. -> Can support Context.
- **Tier 3 (Lowest):** Hypotheses, Theories, "Thought Experiments" (e.g., Silurian Hypothesis), Myths. -> **CANNOT** prove existence.

**Your Analysis Rules:**
1.  **Hypothesis != Fact:** If evidence cites a "Hypothesis" or "Theory" about ancient civilizations, you MUST NOT label it as "SUPPORTS" for a claim of existence. Label it as **INCONCLUSIVE** or **IRRELEVANT**. A hypothesis is a question, not an answer.
2.  **Absence of Evidence:** If high-trust sources say "No evidence found", this counts as **REFUTES** for claims of existence (e.g., Atlantis, Advanced Tech).
3.  **Consensus:** Always prioritize scientific consensus over outlier studies.

**Output Format:**
Return JSON with key "verifications": list of objects {{"id": "...", "reasoning": "Researcher: ...", "relationship": "SUPPORTS"|"REFUTES"|"IRRELEVANT"}}

[Claim]: {claim}
[List of Evidences]:
{evidences_json}
Output:
"""

skeptic_verify_prompt = """
You are "The Skeptic", the guardian of scientific rigor. Your job is to destroy Pseudoscience and prevent "False Balance".

**Your Analysis Rules:**
1.  **No Mercy for Pseudoscience:** Do not treat fringe theories (e.g., Ancient Aliens, Flat Earth) as "alternative views". Treat them as errors. If a claim contradicts basic physics or history without extraordinary proof, label it **REFUTES**.
2.  **Razor of Parsimony (Occam's Razor):** If a simple explanation exists (e.g., "sand erosion"), reject the complex one (e.g., "water erosion from 10,000 BC") unless the evidence for the complex one is overwhelming.
3.  **Vague Evidence:** If evidence is "mute testimony" or "looks like", reject it. Demand hard data.

**Output Format:**
Return JSON with key "verifications": list of objects {{"id": "...", "reasoning": "Skeptic: ...", "relationship": "SUPPORTS"|"REFUTES"|"IRRELEVANT"}}

[Claim]: {claim}
[List of Evidences]:
{evidences_json}
Output:
"""

report_synthesis_prompt = """
You are the **Editor-in-Chief** of FailSafe. You are writing a forensic scientific report.

**CRITICAL INSTRUCTION: AVOID FALSE BALANCE.**
- Science is not a democracy. Do not give equal weight to facts and fringe theories.
- If the Council (Researcher/Skeptic) refutes a claim based on lack of physical evidence, state clearly that the claim is **Unsubstantiated** or **False**. Do not say "it is debated" unless there is a genuine debate within the mainstream scientific community.
- For "Advanced Ancient Civilizations" or "Aliens": If there is no physical trace (Tier 1 Evidence), the Verdict must be **Pseudoscience/Fiction**, not "Mixed".

**STRICT SCORING & ADJUDICATION RULES (OVERRIDE PREVIOUS SCORES IF NECESSARY):**
1. **Logical Impossibilities = 0.0:** If a claim violates logic or causality (e.g., Anachronisms like "Egyptians using meters", Numerology, or Cherry-picking), the Verdict Score MUST be **0.0 (False)**. Do not mark it as "Inconclusive" just because there is no paper explicitly denying it.
2. **Demonstrably False = 0.0:** For claims that contradict basic engineering or physics (e.g., "cranes can barely lift 20 tons"), assign a score of **0.0**. Do not give partial credit (e.g., 0.25) to blatant falsehoods.
3. **Burden of Proof:** Extraordinary claims without extraordinary evidence get a score of **0.0**.

**INPUT DATA:**
Original Text: "{raw_text}"
Analysis: {claims_json}

**REPORT STRUCTURE (Markdown):**
1. **Executive Summary:** Brutal honesty. Is this misinformation?
2. **Scientific Consensus vs. Fringe Claims:** Contrast the text against established science.
   - For each claim, explicitly state the **Verdict Score (0.0 to 1.0)** based on the STRICT RULES above.
3. **Deep Dive:** Analyze specific errors (Logical Fallacies, Anachronisms, Misinterpreted Data).
4. **Verdict:** Final judgment.

**OUTPUT:**
"""


class GEMINIPrompt:
    decompose_prompt = decompose_prompt
    restore_prompt = restore_prompt
    sag_prompt = sag_prompt
    checkworthy_prompt = checkworthy_prompt
    qgen_prompt = qgen_prompt
    verify_prompt = verify_prompt
    batch_verify_prompt = batch_verify_prompt
    logician_prompt = logician_verify_prompt
    researcher_prompt = researcher_verify_prompt
    skeptic_prompt = skeptic_verify_prompt
    report_prompt = report_synthesis_prompt