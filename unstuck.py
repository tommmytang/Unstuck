import os
import json
import cohere
from tavily import TavilyClient

# --- Configuration ---
# Fallback to hardcoded keys if environment variables aren't set (replace for testing if needed)
COHERE_KEY = os.getenv("COHERE_API_KEY", "KYrrefNlqXGEs6hZzaX0mSqyrW7EYLfBmhdB7YVA")
TAVILY_KEY = os.getenv("TAVILY_API_KEY", "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")

MAX_QUESTIONS = 3
MODEL_NAME = "command-a-03-2025"  # Updated to the current active stable model

class UnstuckAgent:
    def __init__(self):
        self.co = cohere.Client(COHERE_KEY)
        self.tavily = TavilyClient(api_key=TAVILY_KEY)
        self.chat_history = []
        self.target_item = ""
        self.products = []

    def run_intake(self):
        print("\n=============================================")
        print("   [VERSION 2: FACTOR RANKING ACTIVE]        ")
        print("=============================================\n")
        print("=== PHASE 1: DIAGNOSTIC ===")
        self.target_item = input("What are you trying to buy, but overthinking? \n> ")
        
        self.chat_history.append({"role": "USER", "message": f"I want to buy: {self.target_item}"})

        for i in range(MAX_QUESTIONS):
            prompt = (
                "You are an efficient personal shopper. Look at the chat history and ask ONE "
                "direct, targeted question to narrow down the user's preferences (e.g., budget, "
                "dealbreakers, style). Do not offer options yet. Just ask the question."
            )
            
            response = self.co.chat(
                message=prompt,
                chat_history=self.chat_history,
                model=MODEL_NAME,
                temperature=0.3
            )
            
            question = response.text
            self.chat_history.append({"role": "CHATBOT", "message": question})
            
            user_answer = input(f"\n[Unstuck] {question}\n> ")
            self.chat_history.append({"role": "USER", "message": user_answer})
            
        print("\n[Unstuck] Got it. I have enough information. Let me do the hunting...")

    def generate_options(self):
        print("\n=== PHASE 2: CURATION ===")
        query_prompt = "Based on our chat history, write a highly specific Google search query to find the best products for this user. Output ONLY the search query text."
        query_response = self.co.chat(message=query_prompt, chat_history=self.chat_history, model=MODEL_NAME)
        search_query = query_response.text.strip(' "')
        
        print(f"[*] Running Tavily Search: '{search_query}'...")
        
        tavily_results = self.tavily.search(query=search_query, search_depth="advanced", max_results=5)
        context = json.dumps(tavily_results.get("results", []))

        json_prompt = f"""
        You are a strict parser. Review this raw search data: {context}
        Extract exactly 5 distinct products that fit the user's preferences from the chat history.
        Return ONLY valid JSON in this exact format, with no markdown formatting or extra text:
        [
            {{"id": 1, "name": "Product A", "price": "$100", "reason": "Why it fits"}},
            ...
        ]
        """
        
        options_response = self.co.chat(
            message=json_prompt, 
            chat_history=self.chat_history,
            model=MODEL_NAME,
            temperature=0.1
        )
        
        clean_json = options_response.text.replace("```json", "").replace("```", "").strip()
        
        try:
            self.products = json.loads(clean_json)
        except json.JSONDecodeError:
            print("[!] Error parsing JSON from Cohere. Raw output:")
            print(clean_json)
            exit()

    def run_ranking(self):
        print("\n=== PHASE 3: FACTOR RANKING ===")
        print("[*] Analyzing products to find key differences...")
        
        factor_prompt = f"""
        Look at these products: {json.dumps(self.products)}. 
        Identify exactly 4 key differentiating factors or features (e.g., Price, Durability, Weight, Aesthetics, Battery Life) that vary between these specific items. 
        Return ONLY a comma-separated list of the 4 factors. No intro, no outro.
        """
        
        factor_response = self.co.chat(message=factor_prompt, model=MODEL_NAME, temperature=0.1)
        factors_string = factor_response.text.strip()
        
        print("\nTo calculate your perfect Top 3, please rank these factors from MOST important to LEAST important:")
        print(f"Factors to rank: {factors_string}")
        print("\nType them out in order, separated by commas (e.g., Price, Weight, Aesthetics, Durability)")
        
        user_ranking = input("> ")
        
        print("\n[*] Scoring products based on your priorities...")
        
        scoring_prompt = f"""
        Here is the original list of products: {json.dumps(self.products)}
        The user ranked their priorities from most to least important as follows: {user_ranking}.
        Evaluate each product against these ranked priorities. Calculate a comprehensive score for each.
        Return EXACTLY the top 3 highest-scoring products in this JSON format, updating the "reason" to explain why it scored high based on their ranking:
        [
            {{"id": 1, "name": "Product A", "price": "$100", "reason": "Scored highest because..."}},
            ...
        ]
        Return ONLY valid JSON.
        """
        
        scoring_response = self.co.chat(message=scoring_prompt, model=MODEL_NAME, temperature=0.1)
        clean_json = scoring_response.text.replace("```json", "").replace("```", "").strip()
        
        try:
            self.products = json.loads(clean_json)
            print("\n*** YOUR TOP 3 MATCHES ***")
            for p in self.products:
                print(f"[{p['id']}] {p['name']} | {p['price']}")
                print(f"    -> {p['reason']}\n")
        except json.JSONDecodeError:
            print("[!] Error parsing ranking JSON from Cohere. Raw output:")
            print(clean_json)
            exit()

    def find_deals(self):
        print("\n=== PHASE 4: THE DEAL BOUNTY ===")
        final_product = self.products[0]['name'] 
        print(f"[*] Selecting the #1 Ranked Match: {final_product}")
        print(f"[*] Hunting for the best active deals and links...")
        
        deal_query = f"{final_product} best price discount buy online"
        deal_results = self.tavily.search(query=deal_query, search_depth="basic")
        
        for result in deal_results.get("results", [])[:3]:
            print(f"\n- Vendor: {result['title']}")
            print(f"  Link: {result['url']}")
            
        print("\n[Unstuck] You're done overthinking. Buy it and close the tab.")

if __name__ == "__main__":
    agent = UnstuckAgent()
    agent.run_intake()
    agent.generate_options()
    agent.run_ranking()
    agent.find_deals()