# similarity_calculator.py

import itertools
from sentence_transformers import SentenceTransformer, util

MODEL = SentenceTransformer('all-mpnet-base-v2')

def calculate_pairwise_similarity(responses):
    all_similarity_scores = []
    for response in responses:
        task_responses = [
            {"SKU": response["SKU"], "GTIN": response["GTIN"], "Task": response["Task"], "Model": model, "Response": resp}
            for model, resp in response.items()
            if model not in ["SKU", "GTIN", "Task"] and resp != "NA"
        ]

        valid_responses = [resp for resp in task_responses if resp["Response"] != "NA"]

        if len(valid_responses) > 1:
            responses_text = [resp["Response"] for resp in valid_responses]
            embeddings = MODEL.encode(responses_text, convert_to_tensor=True)

            cosine_scores = util.pytorch_cos_sim(embeddings, embeddings)
            for i in range(len(valid_responses)):
                for j in range(i + 1, len(valid_responses)):
                    score = cosine_scores[i][j].item()
                    all_similarity_scores.append({
                        "SKU": valid_responses[i]["SKU"],
                        "GTIN": valid_responses[i]["GTIN"],
                        "Task": valid_responses[i]["Task"],
                        "Model_1": valid_responses[i]["Model"],
                        "Response_1": valid_responses[i]["Response"],
                        "Model_2": valid_responses[j]["Model"],
                        "Response_2": valid_responses[j]["Response"],
                        "Similarity_Score": score
                    })
    return all_similarity_scores
