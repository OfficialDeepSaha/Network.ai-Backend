# engagement_module.py

from datetime import datetime, timedelta
from typing import Dict, List
from sqlalchemy.orm import Session
from models import GroupChat, GroupChatMessage, User, Agent
import utils

class EngagementModule:
    def __init__(self, db: Session):
        self.db = db

    def suggest_connections(self, agent_id: int) -> List[Dict]:
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise ValueError("Agent not found")

        user = self.db.query(User).filter(User.id == agent.user_id).first()
        if not user:
            raise ValueError("User not found")

        other_users = self.db.query(User).filter(User.id != user.id).all()
        user_profile_text = f"Education: {user.education}\nExperience: {user.experience}\nGoals: {user.goal}"
        user_embedding = utils.generate_embeddings(user_profile_text)

        other_user_profiles = [
            f"Education: {u.education}\nExperience: {u.experience}\nGoals: {u.goal}"
            for u in other_users
        ]
        other_user_embeddings = utils.batch_generate_embeddings(other_user_profiles)

        suggestions = []
        for other_user, embedding in zip(other_users, other_user_embeddings):
            similarity = utils.calculate_similarity(user_embedding, embedding)
            common_interests = self.find_common_interests(user, other_user)
            if similarity > 0.6 or common_interests:  # Lower threshold and consider common interests
                suggestions.append({
                    "id": other_user.id,
                    "name": other_user.name,
                    "similarity": similarity,
                    "common_interests": common_interests
                })

        return sorted(suggestions, key=lambda x: (x["similarity"], len(x["common_interests"])), reverse=True)

    def find_common_interests(self, user1: User, user2: User) -> List[str]:
        interests1 = set(user1.goal.lower().split()) if user1.goal else set()
        interests2 = set(user2.goal.lower().split()) if user2.goal else set()
        return list(interests1.intersection(interests2))

    def initiate_group_chat(self, agent_id: int, participants: List[int], topic: str) -> Dict:
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise ValueError("Agent not found")

        users = self.db.query(User).filter(User.id.in_(participants)).all()
        if len(users) < 2:
            raise ValueError("Not enough participants for a group chat")

        group_chat = GroupChat(name=f"Discussion: {topic}", created_at=datetime.utcnow())
        group_chat.members.extend(users)
        self.db.add(group_chat)
        self.db.commit()

        # Add an initial message to kick off the discussion
        initial_message = GroupChatMessage(
            chat_id=group_chat.id,
            sender_id=agent.user_id,
            content=f"Welcome to our discussion on {topic}! What are your thoughts on this subject?",
            created_at=datetime.utcnow()
        )
        self.db.add(initial_message)
        self.db.commit()

        return {
            "group_chat_id": group_chat.id,
            "topic": topic,
            "participants": [user.id for user in users]
        }

    def monitor_activity(self, agent_id: int) -> Dict:
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise ValueError("Agent not found")

        user = self.db.query(User).filter(User.id == agent.user_id).first()
        if not user:
            raise ValueError("User not found")

        week_ago = datetime.utcnow() - timedelta(days=7)
        
        recent_chats = self.db.query(GroupChat).filter(
            GroupChat.members.any(id=user.id),
            GroupChat.created_at > week_ago
        ).count()

        recent_messages = self.db.query(GroupChatMessage).filter(
            GroupChatMessage.sender_id == user.id,
            GroupChatMessage.created_at > week_ago
        ).count()

        return {
            "agent_id": agent.id,
            "user_id": user.id,
            "last_active": agent.last_active,
            "next_action": agent.next_action,
            "recent_chats_joined": recent_chats,
            "recent_messages_sent": recent_messages,
            "engagement_score": self.calculate_engagement_score(user.id)
        }

    def calculate_engagement_score(self, user_id: int) -> float:
        # This method is now implemented in the DecisionEngine class
        # Here we can add more sophisticated logic if needed
        pass