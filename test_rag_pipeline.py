
import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000"

def log(msg, status="INFO"):
    print(f"[{status}] {msg}")

def check_step(response, step_name):
    if 200 <= response.status_code < 300:
        log(f"{step_name}: SUCCESS")
        return True
    else:
        log(f"{step_name}: FAILED (Status {response.status_code})")
        log(response.text, "ERROR")
        return False

def run_e2e_test():
    # 1. Create Persona
    log("Step 1: Creating Persona...")
    persona_payload = {
        "age": 28,
        "gender": "female",
        "occasion": "birthday",
        "relationship": "friend",
        "budget": "25-50"
    }
    
    response = requests.post(f"{BASE_URL}/build-persona", json=persona_payload)
    if not check_step(response, "Create Persona"): return
    
    # Check response structure
    resp_json = response.json()
    persona_id = resp_json.get("id") if isinstance(resp_json, dict) else resp_json
    log(f"Persona ID: {persona_id}")
    
    # 2. Get Questions
    log("Step 2: Getting Questions...")
    response = requests.get(f"{BASE_URL}/personas/{persona_id}/questions")
    if not check_step(response, "Get Questions"): return
    
    # Questions response in controller returns List[SuggestedQuestion] directly, NOT {questions: []}
    # Checking src/questions/models.py would be wise, but assuming list based on controller return type hint
    questions = response.json()
    if isinstance(questions, dict) and 'questions' in questions:
        questions = questions.get("questions", [])

    if not questions:
        log("No questions received!", "ERROR")
        return
        
    log(f"Received {len(questions)} questions")
    
    # 3. Answer Questions
    log("Step 3: Answering Questions...")
    answers_payload = {
        "answers": []
    }
    
    # Create mock answers for the received questions
    # We'll just pick the first choice for each question or a simple text
    for q in questions:
        # q should have a 'choices' list if it's following the model
        choice = q.get("choices", ["Default Choice"])[0]
        
        answers_payload["answers"].append({
            "question_id": q["id"],
            "answer_choice": choice # Changed from answer_text to answer_choice
        })
    
    response = requests.post(f"{BASE_URL}/questions/answers", json=answers_payload)
    if not check_step(response, "Submit Answers"): return
    
    # 4. Get Recommendations (RAG)
    log("Step 4: Getting Recommendations (this may take a few seconds)...")
    start_time = time.time()
    # Controller requires POST
    response = requests.post(f"{BASE_URL}/personas/{persona_id}/recommendations")
    duration = time.time() - start_time
    
    if not check_step(response, "Get Recommendations"): return
    log(f"Recommendations received in {duration:.2f} seconds")
    
    recommendations = response.json()
    
    # 5. Validate Results
    log("Step 5: Validating Results...")
    
    # Allow for both list of products or a wrapped object depending on implementation
    if isinstance(recommendations, dict):
         # It might be in a 'recommendations' key or similar, inspect:
         print(json.dumps(recommendations, indent=2))
         recs_list = recommendations.get('recommendations', [])
    elif isinstance(recommendations, list):
        recs_list = recommendations
    else:
        recs_list = []

    if not recs_list:
        log("No recommendations list found in response", "WARN")
        return

    first_rec = recs_list[0]
    # Check for fields present in GiftRecommendation model
    is_real_product = "title" in first_rec and "purchase_links" in first_rec
    has_confidence = "confidence_score" in first_rec
    
    if is_real_product and len(first_rec["purchase_links"]) > 0:
        log("SUCCESS: Recommendations contain real product data")
        log(f"Sample: {first_rec['title']} - {first_rec['price_range']}")
    else:
        log("WARNING: Recommendations do NOT look like real products", "WARN")
        
    log("Test Complete.")

if __name__ == "__main__":
    try:
        run_e2e_test()
    except Exception as e:
        log(f"Test failed with exception: {e}", "ERROR")
