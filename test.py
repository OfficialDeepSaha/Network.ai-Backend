import asyncio
from datetime import datetime
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from models import User, Agent, Document, ConnectionRequest
from schemas import UserUpdate, ConnectionStatus, ActionEnum
import utils
from decision_engine import DecisionEngine
from engagement_module import EngagementModule
import logging

app = FastAPI()
logger = logging.getLogger("uvicorn.error")

# Initialize DecisionEngine and EngagementModule
decision_engine = DecisionEngine()
engagement_module = EngagementModule()

# Background task to continuously run AI agents
async def run_ai_agents(db: Session):
    while True:
        agents = db.query(Agent).all()
        for agent in agents:
            await process_agent(agent, db)
        await asyncio.sleep(60)  # Check every minute

# Process individual agent actions
async def process_agent(agent: Agent, db: Session):
    user = db.query(User).filter(User.id == agent.user_id).first()
    if not user:
        logger.error(f"User not found for agent {agent.id}")
        return

    # Get agent's next action
    next_action = decision_engine.get_next_action(agent, user)
    
    if next_action == ActionEnum.SEND_CONNECTION_REQUEST:
        await send_connection_request(agent, db)
    elif next_action == ActionEnum.INITIATE_CONVERSATION:
        await initiate_conversation(agent, db)
    elif next_action == ActionEnum.PROVIDE_RECOMMENDATION:
        await provide_recommendation(agent, db)
    
    # Update agent's state
    agent.last_active = datetime.utcnow()
    agent.next_action = next_action
    db.commit()

# AI agent actions
async def send_connection_request(agent: Agent, db: Session):
    recommendations = get_recommendations(agent.user_id, db)
    if recommendations:
        target_user_id = recommendations[0]['id']  # Send to the top recommendation
        connection_request = ConnectionRequest(
            sender_id=agent.user_id,
            receiver_id=target_user_id,
            status=ConnectionStatus.PENDING,
            action=ActionEnum.CONNECTION_REQUEST
        )
        db.add(connection_request)
        db.commit()
        logger.info(f"Agent {agent.id} sent a connection request to user {target_user_id}")

async def initiate_conversation(agent: Agent, db: Session):
    # Find a connected user
    connection = db.query(ConnectionRequest).filter(
        (ConnectionRequest.sender_id == agent.user_id) | (ConnectionRequest.receiver_id == agent.user_id),
        ConnectionRequest.status == ConnectionStatus.ACCEPTED
    ).first()
    
    if connection:
        other_user_id = connection.receiver_id if connection.sender_id == agent.user_id else connection.sender_id
        message = engagement_module.generate_conversation_starter(agent, other_user_id)
        # Here you would typically send this message through your messaging system
        logger.info(f"Agent {agent.id} initiated a conversation with user {other_user_id}: {message}")

async def provide_recommendation(agent: Agent, db: Session):
    user = db.query(User).filter(User.id == agent.user_id).first()
    recommendation = engagement_module.generate_recommendation(user)
    # Here you would typically send this recommendation to the user through your notification system
    logger.info(f"Agent {agent.id} provided a recommendation to user {user.id}: {recommendation}")

# Modified user update function
@app.post("/update_user/")
async def update_user(user: UserUpdate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user.user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        # Update user details
        for field, value in user.dict(exclude_unset=True).items():
            setattr(db_user, field, value)

        # Generate new embeddings
        user_profile_text = f"Education: {db_user.education}\nExperience: {db_user.experience}\nGoals: {db_user.goal}"
        user_embedding = utils.generate_embeddings(user_profile_text)
        if user_embedding:
            db_user.embedding = user_embedding
        else:
            logger.error(f"Failed to generate embeddings for user {user.user_id}")

        # Create or update agent
        agent = db.query(Agent).filter(Agent.user_id == user.user_id).first()
        if not agent:
            agent = Agent(user_id=user.user_id, state="initial")
            db.add(agent)
        
        agent.last_active = datetime.utcnow()
        db.commit()

        # Trigger immediate agent processing
        background_tasks.add_task(process_agent, agent, db)

        return {"message": "User details updated and agent activated"}

    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating user details")

# Startup event to begin running AI agents
@app.on_event("startup")
async def startup_event():
    db = next(get_db())
    asyncio.create_task(run_ai_agents(db))

# Main execution
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)












#New code    

@app.post("/auto_generate_connections/")
def auto_generate_connections(user_id: int, db: Session = Depends(get_db)):
    """
    Auto-generates connection requests based on recommendations, using a decision engine to filter connections.
    """

    # Fetch recommendations using the embeddings-based recommendation system
    recommendations = get_recommendations(user_id, db)

    # Fetch user details for the main user
    main_user = db.query(User).filter(User.id == user_id).first()

    # Calculate the embedding for the main user
    main_user_embedding = utils.generate_embeddings(f"{main_user.education} {main_user.experience} {main_user.goal}")

    # Process recommendations with the decision engine
    for rec in recommendations:
        target_user_id = rec['id']  # This is the recommended user
        
        # Fetch the target user's details and embeddings
        target_user = db.query(User).filter(User.id == target_user_id).first()
        target_user_embedding = utils.generate_embeddings(f"{target_user.education} {target_user.experience} {target_user.goal}")

        # Advanced decision-making criteria
        if decision_engine(main_user, main_user_embedding, target_user, target_user_embedding, db):
            # Check if a connection request already exists from the recommended user to the main user
            existing_request = db.query(ConnectionRequest).filter(
                ConnectionRequest.sender_id == target_user_id,  # Reversed sender
                ConnectionRequest.receiver_id == user_id,  # Reversed receiver
                ConnectionRequest.status == ConnectionStatus.PENDING
            ).first()

            if not existing_request:
                # The recommended user (target_user_id) sends the connection request to the main user (user_id)
                connection_request = ConnectionRequest(
                    sender_id=target_user_id,  # Reversed sender
                    receiver_id=user_id,  # Reversed receiver
                    status=ConnectionStatus.PENDING,
                    action=ActionEnum.CONNECTION_REQUEST
                )
                db.add(connection_request)
                db.commit()

                # Notify the main user that a connection request has been received from the recommended user
                utils.notify_user_of_connection_request(user_id)

    return {"status": "Auto-generated connection requests from recommendations sent to main user"}


def decision_engine(main_user, main_user_embedding, target_user, target_user_embedding, db: Session) -> bool:
    """
    A more advanced decision engine that evaluates multiple criteria before allowing connection requests.
    Returns True if a connection request should be generated.
    """
    
    # 1. Similarity Score
    similarity_score = utils.calculate_similarity(main_user_embedding, target_user_embedding)

    # 2. Mutual Interest Check (e.g., overlap in goals or experience)
    mutual_interest = check_mutual_interest(main_user, target_user)
    
    # 3. Activity Score (Recency of activity like login or posts)
    activity_score = calculate_activity_score(target_user, db)

    # 4. Trust Score (Based on accepted/rejected requests, feedback ratings, etc.)
    trust_score = calculate_trust_score(target_user, db)

    # 5. External Data Influence (GitHub/Twitter activity similarity)
    external_influence_score = calculate_external_influence(main_user, target_user)

    # 6. Compatibility Score (Combined evaluation of similarity, interests, activity, etc.)
    compatibility_score = (0.4 * similarity_score +
                           0.2 * mutual_interest +
                           0.15 * activity_score +
                           0.15 * trust_score +
                           0.1 * external_influence_score)

    # Apply a threshold to determine whether to generate a connection request
    THRESHOLD = 0.75  # Example threshold
    return compatibility_score >= THRESHOLD


def check_mutual_interest(main_user, target_user) -> float:
    """
    Check if the target user and main user have overlapping interests (goals, experience, etc.).
    Returns a mutual interest score between 0 and 1.
    """
    # Compare interests, goals, or experience for mutual interest
    mutual_goals = set(main_user.goal.split()).intersection(set(target_user.goal.split()))
    mutual_experience = set(main_user.experience.split()).intersection(set(target_user.experience.split()))
    mutual_interests_score = (len(mutual_goals) + len(mutual_experience)) / 2.0  # Example weighting
    return mutual_interests_score / max(len(main_user.goal.split()), len(main_user.experience.split()), 1)


def calculate_activity_score(user, db: Session) -> float:
    """
    Calculate an activity score based on the user's recent activity (e.g., last login, last post).
    Returns a score between 0 and 1.
    """
    # Fetch user's last login or last activity timestamp
    last_activity = user.last_login or user.last_post or user.last_contribution or datetime.min
    days_since_last_activity = (datetime.utcnow() - last_activity).days
    activity_score = max(1 - (days_since_last_activity / 30), 0)  # Score decreases with inactivity over 30 days
    return activity_score


def calculate_trust_score(user, db: Session) -> float:
    """
    Calculate a trust score based on the user's interaction history (accepted/rejected requests, feedback).
    Returns a score between 0 and 1.
    """
    # Calculate trust score based on accepted/rejected connection requests
    accepted_requests = db.query(ConnectionRequest).filter(
        ConnectionRequest.sender_id == user.id, 
        ConnectionRequest.status == ConnectionStatus.ACCEPTED
    ).count()

    rejected_requests = db.query(ConnectionRequest).filter(
        ConnectionRequest.sender_id == user.id, 
        ConnectionRequest.status == ConnectionStatus.REJECTED
    ).count()

    total_requests = accepted_requests + rejected_requests
    if total_requests == 0:
        return 1.0  # Default trust score if no prior requests

    trust_score = accepted_requests / total_requests  # Ratio of accepted to total requests
    return trust_score


def calculate_external_influence(main_user, target_user) -> float:
    """
    Calculate an influence score based on external data like GitHub or Twitter activity.
    Returns a score between 0 and 1.
    """
    # Fetch and compare GitHub activity
    main_github_activity = fetch_github_data(main_user.github_handle)
    target_github_activity = fetch_github_data(target_user.github_handle)

    # Compare activity similarity (example: comparing the types of contributions)
    if main_github_activity and target_github_activity:
        similarity = utils.calculate_similarity(main_github_activity, target_github_activity)
        return similarity

    return 0.0  # No influence score if GitHub data is unavailable



@app.get("/recommendations/")
def get_recommendations(user_id: int, db: Session = Depends(get_db)):
    # Fetch current user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Fetch all connection requests related to the user
    connections = db.query(ConnectionRequest).filter(
        (ConnectionRequest.sender_id == user_id) | 
        (ConnectionRequest.receiver_id == user_id)
    ).filter(
        ConnectionRequest.status.in_([ConnectionStatus.ACCEPTED, ConnectionStatus.REJECTED])
    ).all()

    connected_user_ids = set()
    for conn in connections:
        if conn.sender_id == user_id:
            connected_user_ids.add(conn.receiver_id)
        else:
            connected_user_ids.add(conn.sender_id)

    # Include all users except those in the connected_user_ids set and the current user
    other_users = db.query(User).filter(User.id != user_id).filter(
        User.id.notin_(connected_user_ids)
    ).all()

    # Generate embeddings for the other users
    user_profile_text = f"Education: {user.education}\nExperience: {user.experience}\nGoals: {user.goal}"
    user_embedding = utils.generate_embeddings(user_profile_text)

    other_user_profiles = [
        f"Education: {other_user.education}\nExperience: {other_user.experience}\nGoals: {other_user.goal}"
        for other_user in other_users
    ]

    other_user_embeddings = utils.batch_generate_embeddings(other_user_profiles)
    recommendations = []

    # Calculate similarity and create recommendations with similarity score
    for other_user, other_user_embedding in zip(other_users, other_user_embeddings):
        similarity_score = utils.calculate_similarity(user_embedding, other_user_embedding)
        recommendations.append({
            'id': other_user.id,
            'name': other_user.name,
            'similarity_score': similarity_score
        })

    return recommendations
