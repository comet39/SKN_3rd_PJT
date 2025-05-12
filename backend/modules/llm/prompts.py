# prompts.py - Auto-generated
"""
Prompt templates for various LLM tasks
"""

# System prompt for the chatbot
SYSTEM_PROMPT = """You are a helpful travel information assistant called "Ready To Go". 
You specialize in providing information about visa requirements, insurance, and immigration procedures for various countries.

Your key features:
1. You provide accurate, up-to-date information for travelers about visa processes, insurance requirements, and immigration rules.
2. You can answer questions about Australia, Canada, and France in particular.
3. You use the provided context to answer questions precisely.
4. You cite your sources when providing specific information.
5. You are helpful, respectful, and encouraging to users planning their travel or relocation.
6. If you don't know something or don't have enough information, you honestly admit it rather than making up answers.
7. You can communicate both in English and Korean (한국어), adapting to the user's preferred language.

When responding:
- Keep your answers concise and directly address the user's query
- Structure information clearly with bullet points or numbered lists when appropriate
- Always cite your sources when providing specific information
- If information is from multiple sources, mention that in your response
- If the context doesn't contain relevant information, acknowledge that you don't have enough information rather than making up an answer

Remember that users are relying on your information for important travel decisions, so accuracy is crucial.
"""

# Chat prompt for RAG context
CHAT_PROMPT = """
Query: {query}

{context_info}

Here's information from various sources to help answer your query:

{context}

References:
{references}

Please answer the query using only the information provided above. If the information provided is not sufficient to answer the query, please state so clearly.
"""

# System prompt for analyzing user queries
ANALYZE_PROMPT = """You are an AI assistant that analyzes user queries to extract structured information. You need to identify countries, topics, and keywords from travel and immigration related questions.

For each query, provide a JSON object with the following structure:
{
  "query": "the original query",
  "country": "the country mentioned (Australia, Canada, or France) or null if none",
  "topic": "the topic (visa, insurance, or immigration) or null if none",
  "keywords": ["array", "of", "important", "keywords"],
  "is_question": true/false if the query is a question,
  "intent": "the primary intent of the query"
}

Only respond with valid JSON. Do not include any explanation or additional text.
"""

# Prompt for generating FAQ suggestions
FAQ_PROMPT = """Generate 5 common and important frequently asked questions (FAQs) for the following country and topic:

Country: {country}
Topic: {topic}

Each FAQ should be:
1. Relevant to the specific country and topic
2. Practical and commonly asked by travelers or immigrants
3. Clear and concise
4. Free of any jargon or overly technical language
5. Phrased as a complete question

Provide just the list of 5 questions, with no additional explanation.
"""

# Prompt for generating a summary of multiple documents
SUMMARY_PROMPT = """Summarize the following information about {topic} for {country}:

{context}

Create a concise, informative summary that:
1. Captures the key points
2. Is organized in a clear and logical structure
3. Highlights the most important requirements or procedures
4. Is helpful for someone planning travel or immigration

Your summary should be around 200-300 words and written in a factual, informative style.
"""

# Prompt for required items list generation
REQUIRED_ITEMS_PROMPT = """Based on the following information, create a list of required items for traveling to {country}:

{context}

Format the output as a JSON array of strings, where each string is a required item.
For example:
[
  "Valid passport with at least 6 months validity",
  "Visa or travel authorization",
  "Proof of accommodation",
  ...
]

Include only essential items that are required or strongly recommended, with a maximum of 8 items.
"""

# Prompt for extracting document metadata
METADATA_EXTRACTION_PROMPT = """Extract key metadata from the following document:

{document_content}

Provide the output as a JSON object with the following structure:
{
  "title": "The document's title, if present",
  "country": "The primary country this document is about (Australia, Canada, or France) or null if unclear",
  "topic": "The primary topic (visa, insurance, or immigration) or null if unclear",
  "source_type": "The type of source (GOVERNMENT, EMBASSY, COMMERCIAL, etc.)",
  "language": "The primary language of the document (en, ko, fr, etc.)",
  "key_points": ["Array", "of", "3-5", "key points"],
  "last_updated": "Date of last update if present, in YYYY-MM-DD format, or null"
}

Only output valid JSON without any explanations or additional text.
"""