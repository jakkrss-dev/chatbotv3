from google import genai
from pydantic import BaseModel, Field
from backend.config import client, generate_with_fallback, CHAT_MODEL
from backend.rag.sql.sql_tool import execute_sql_query

SCHEMA_INFO = """
Database Schema:

1. customers (customer_id, name, region, segment)
2. products (product_id, name, category, price)
3. sales (sale_id, customer_id, product_id, qty, sale_date)
4. books (book_id, title, author, category, price, published_date)

Relationships:
- sales.customer_id = customers.customer_id
- sales.product_id = products.product_id
"""

def ask_sql(question: str, chat_history: str = ""):
    prompt_context = f"""
{chat_history}
You are a helpful data analyst. Convert the following natural language question into a PostgreSQL query.
Here is the schema information:
{SCHEMA_INFO}

If you need to query the database to answer the user's question, call the provided tool to execute the query.
Then, use the results from the query to answer the user's question in a clear, concise manner.

If the user asks for a graph, chart, or plot, and the query results are suitable (e.g., a list of categories and values), 
you MUST also provide a "chart_config" in your final response as a JSON block.
The JSON block should look like this:
```json
{{
  "type": "chart",
  "chart_type": "bar", 
  "x_axis": "column_name_for_x",
  "y_axis": "column_name_for_y",
  "title": "Chart Title"
}}
```
Supported chart_types: bar, line, area, pie.

User Question: {question}
"""
    
    # We will pass a callable tool to google-genai
    def run_sql_db(query: str) -> str:
        """Executes a SELECT query on the PostgreSQL database and returns the result."""
        result = execute_sql_query(query)
        if isinstance(result, dict) and "error" in result:
             return f"Error executing query: {result['error']}"
        # Keep as list of dicts for internal use if we want, but LLM needs string
        import json
        return json.dumps(result)
        
    response = generate_with_fallback(
        contents=prompt_context,
        config=genai.types.GenerateContentConfig(
            tools=[run_sql_db],
            temperature=0.0
        )
    )
    
    tool_trace = []
    chart_data = None
    last_sql_result = None
    
    for part in response.candidates[0].content.parts:
        if part.function_call:
            func_name = part.function_call.name
            args = part.function_call.args
            
            tool_trace.append({"step": f"Generating SQL", "query": args.get("query")})
            
            if func_name == "run_sql_db":
                sql_result_str = run_sql_db(args.get("query"))
                import json
                try:
                    last_sql_result = json.loads(sql_result_str)
                except:
                    last_sql_result = sql_result_str
                
                tool_trace.append({"step": "Executing SQL", "result": sql_result_str[:200] + "..." if len(sql_result_str) > 200 else sql_result_str})
                
                # Send back the result to the LLM
                response2 = generate_with_fallback(
                    contents=[
                        prompt_context,
                        response.candidates[0].content,
                        genai.types.Part.from_function_response(
                            name=func_name,
                            response={"result": sql_result_str}
                        )
                    ]
                )
                
                answer = response2.text
                
                # Try to extract chart config if present
                if "```json" in answer:
                    try:
                        import re
                        match = re.search(r"```json\s*(\{.*?\})\s*```", answer, re.DOTALL)
                        if match:
                            config = json.loads(match.group(1))
                            if config.get("type") == "chart" and last_sql_result:
                                chart_data = {
                                    "config": config,
                                    "data": last_sql_result
                                }
                                # Remove the JSON block from the text answer for cleaner UI
                                answer = answer.replace(match.group(0), "").strip()
                    except Exception as e:
                        print(f"Error parsing chart config: {e}")

                return answer, tool_trace, chart_data

    # If no tool was called, or after processing
    return response.text, tool_trace, None
