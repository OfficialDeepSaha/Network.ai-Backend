from sqlalchemy.orm import Session
from models import Feedback, User  # Import Feedback model
from utils import generate_embeddings, calculate_similarity
import numpy as np


def retrain_model(db: Session):
    """
    Retrain the recommendation model based on user feedback.

    This will use the feedback to either reinforce or penalize similarities
    between users based on the rating and feedback text.
    """
    
    # 1. Fetch all feedback from the database
    feedback_data = db.query(Feedback).all()

    if not feedback_data:
        print("No feedback available for training.")
        return {"message": "No feedback available for training"}

    print(f"Found {len(feedback_data)} feedback entries.")

    for feedback in feedback_data:
        # 2. Get the user who provided feedback
        user_id = feedback.user_id
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            continue  # Skip if user is not found

        # 3. Recalculate user's embedding based on feedback text (or refine it)
        user_profile_text = f"Education: {user.education}\nExperience: {user.experience}\nGoals: {user.goal}"
        user_embedding = generate_embeddings(user_profile_text)

        # 4. Find the target user(s) that the feedback is referring to (e.g., recommended connections)
        # In a real-world scenario, you'd link feedback to specific interactions or connections
        # For this example, we assume feedback refers to a recommended user
        target_users = db.query(User).filter(User.id != user_id).all()

        for target_user in target_users:
            target_user_profile_text = f"Education: {target_user.education}\nExperience: {target_user.experience}\nGoals: {target_user.goal}"
            target_user_embedding = generate_embeddings(target_user_profile_text)

            # 5. Calculate similarity between the users
            similarity_before = calculate_similarity(user_embedding, target_user_embedding)

            # 6. Adjust similarity based on feedback rating
            if feedback.rating >= 4:  # Positive feedback
                # Strengthen the similarity if the feedback is positive
                similarity_adjustment = 0.1 * feedback.rating
            else:  # Negative feedback
                # Penalize similarity if feedback is negative
                similarity_adjustment = -0.1 * (5 - feedback.rating)

            # 7. Apply adjustment to the similarity score (in practice, you'd refine embeddings, not just similarity)
            new_similarity = similarity_before + similarity_adjustment
            new_similarity = np.clip(new_similarity, 0, 1)  # Ensure similarity is between 0 and 1

            # (Optional) Store adjusted similarity back in the database or use it in future recommendations
            print(f"Adjusted similarity for {user.name} and {target_user.name}: {similarity_before} -> {new_similarity}")

    # 8. Finalize model retraining process
    print("Model retraining completed based on feedback.")
    return {"message": "Model retrained successfully"}
