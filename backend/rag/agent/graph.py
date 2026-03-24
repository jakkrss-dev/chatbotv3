from backend.config import generate_with_fallback, CHAT_MODEL
from backend.rag.retriever_pgvector import search_documents
from backend.rag.sql.function_calling_sql import ask_sql
from google import genai

def route_intent(question: str, chat_history: str = "") -> str:
    """Classifies if a question is meant for DOCUMENTS, SQL_DB, GENERAL, or MIXED."""
    prompt = f"""
{chat_history}
Classify the user's question into one of the following categories:
- DOCUMENTS: if the question refers to specific facts, manuals, PDF contents, or uploaded data.
- SQL_DB: if asking about database-style queries like sales, quantities, books (e.g., titles, authors), or specific business data.
- GENERAL: if it's a greeting, a general knowledge question (e.g. world history, science, coding), or casual talk.
- MIXED: if it combines both.

User Question: {question}

Reply with ONLY ONE WORD (DOCUMENTS, SQL_DB, GENERAL, or MIXED).
"""
    response = generate_with_fallback(
        prompt=prompt,
        config=genai.types.GenerateContentConfig(temperature=0.0)
    )
    return response.text.strip().upper()

def evaluate_context(question: str, context: str) -> dict:
    """Evaluates the retrieved context against the question."""
    prompt = f"""
Evaluate the following context based on the user's question.
Assign a score from 0 to 2 for Relevance and Sufficiency.
Relevance:
- 0: Not relevant
- 1: Partially relevant
- 2: Highly relevant
Sufficiency:
- 0: Cannot answer the question
- 1: Partially answers the question
- 2: Fully answers the question

Question: {question}
Context: {context}

Return JSON strictly in this format: {{"relevance": int, "sufficiency": int}}
"""
    response = generate_with_fallback(
        prompt=prompt,
        config=genai.types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.0
        )
    )
    import json
    try:
        return json.loads(response.text)
    except Exception:
        return {"relevance": 0, "sufficiency": 0}

def generate_answer_from_docs(question: str, context: str, chat_history: str = "") -> str:
    """Answers using context primarily, but allows general knowledge fallback."""
    prompt = f"""
{chat_history}
You are a helpful and knowledgeable assistant. 
Answer the user's Question.

Rules:
1. If the provided Context (from documents) contains the answer, use it and prioritize it.
2. If the Context is irrelevant or insufficient, use your broad internal knowledge to provide a high-quality, helpful response.
3. Keep the conversation natural. Don't over-explain if you are using your own knowledge vs the documents unless specifically asked.
4. IMPORTANT: Always cite the sources (filenames) used from the context at the end of your response or in brackets [Source: filename].

Context: 
{context}

Question: {question}
"""
    response = generate_with_fallback(
        prompt=prompt,
        config=genai.types.GenerateContentConfig(temperature=0.3)
    )
    return response.text

def generate_general_answer(question: str, chat_history: str = "") -> tuple[str, list]:
    """Generates a high-quality general purpose answer, using Web Search if needed."""
    from backend.rag.agent.web_search_tool import search_web
    prompt = f"""
{chat_history}
You are a helpful assistant. Answer the user's question. 
If the user asks for current events, specific facts, or external information that you don't confidently know, you MUST use the search_web tool to search the internet.
If you use information from the web search, you MUST provide the URLs as references at the end of your response.
User Question: {question}
"""
    response = generate_with_fallback(
        prompt=prompt,
        config=genai.types.GenerateContentConfig(
            temperature=0.7,
            tools=[search_web]
        )
    )
    
    tool_trace = []
    
    for part in response.candidates[0].content.parts:
        if part.function_call:
            func_name = part.function_call.name
            args = part.function_call.args
            
            if func_name == "search_web":
                query = args.get("query") or question
                tool_trace.append({"step": "Web Search", "query": query})
                search_result = search_web(query)
                
                response2 = generate_with_fallback(
                    contents=[
                        prompt,
                        response.candidates[0].content,
                        genai.types.Part.from_function_response(
                            name=func_name,
                            response={"result": search_result}
                        )
                    ],
                    config=genai.types.GenerateContentConfig(temperature=0.7)
                )
                return response2.text, tool_trace
                
    return response.text, tool_trace

def process_chat(question: str, mode: str = "auto", session_id: str = "default_user", max_iterations: int = 2):
    from backend.rag.agent.memory import get_formatted_history, add_to_history
    
    chat_history = get_formatted_history(session_id)
    
    tool_trace = []
    citations = []
    chart_data = None
    
    if mode == "sql":
        tool_trace.append({"step": "Mode: SQL"})
        answer, sql_trace, chart_data = ask_sql(question, chat_history)
        tool_trace.extend(sql_trace)
        add_to_history(session_id, question, answer)
        return answer, citations, tool_trace, chart_data
        
    elif mode == "rag":
        tool_trace.append({"step": "Mode: Document RAG"})
        
        # Retrieval
        docs = search_documents(question)
        context = "\n\n".join([f"Source: {d['metadata'].get('filename', 'Unknown')} (Chunk {d['chunk_index']})\n{d['content']}" for d in docs])
        citations.extend([{"doc_id": d["doc_id"], "chunk": d["chunk_index"], "score": d["score"]} for d in docs])
        
        tool_trace.append({"step": "Retrieved Docs", "count": len(docs)})
        
        answer = generate_answer_from_docs(question, context, chat_history)
        tool_trace.append({"step": "Generated Answer"})
        add_to_history(session_id, question, answer)
        return answer, citations, tool_trace, None

    # Auto Agentic RAG Pipeline
    tool_trace.append({"step": "Mode: Auto Agentic RAG"})
    
    # 1. Route Intent
    intent = route_intent(question, chat_history)
    tool_trace.append({"step": f"Intent Routing", "result": intent})
    
    if intent == "SQL_DB":
        answer, sql_trace, chart_data = ask_sql(question, chat_history)
        tool_trace.extend(sql_trace)
        add_to_history(session_id, question, answer)
        return answer, citations, tool_trace, chart_data
        
    elif intent == "GENERAL":
        tool_trace.append({"step": "General Knowledge Routing"})
        answer, web_trace = generate_general_answer(question, chat_history)
        if web_trace:
            tool_trace.extend(web_trace)
        add_to_history(session_id, question, answer)
        return answer, citations, tool_trace, None

    elif intent == "DOCUMENTS" or intent == "MIXED":
        tool_trace.append({"step": "Retrieving Documents"})
        docs = search_documents(question)
        context = "\n\n".join([f"Source: {d['metadata'].get('filename', 'Unknown')}\n{d['content']}" for d in docs])
        
        if docs:
            citations.extend([{"doc_id": d["doc_id"], "chunk": d["chunk_index"], "score": d["score"]} for d in docs])
            tool_trace.append({"step": f"Context Found ({len(docs)} chunks)"})
        else:
            tool_trace.append({"step": "No relevant documents found, using general knowledge fallback"})
            
        answer = generate_answer_from_docs(question, context, chat_history)
        add_to_history(session_id, question, answer)
        return answer, citations, tool_trace, None
        
    # Default fallback for any other cases
    answer, web_trace = generate_general_answer(question, chat_history)
    if web_trace:
        tool_trace.extend(web_trace)
    add_to_history(session_id, question, answer)
    return answer, citations, tool_trace, None
