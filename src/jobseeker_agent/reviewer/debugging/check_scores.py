from jobseeker_agent.reviewer.analyze_reviews import load_and_merge_data

def check_scores(generation_id: int):
    # for each sample, check that the value in the "score" field is equal to the sum of the scores in the "evaluation_grid" field.
    data = load_and_merge_data(generation_id)
    for item in data:
        score = item["score"]
        evaluation_grid = item["evaluation_grid"]
        evaluation_grid_score = sum(criterion["score"] for criterion in evaluation_grid)
        print(f"Score: {score}, Evaluation Grid Score: {evaluation_grid_score}")
        if score != evaluation_grid_score:
            print(f"Score mismatch for job ID {item['id']}: {score} != {evaluation_grid_score}")


if __name__ == "__main__":
    generation_id = 4
    check_scores(generation_id)