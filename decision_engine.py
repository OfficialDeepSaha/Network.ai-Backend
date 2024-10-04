# decision_engine.py

from datetime import datetime, timedelta
import random
from typing import Dict, List
import openai
from requests import Session
from engagement_module import EngagementModule
from models import Agent, GroupChat, User
from schemas import ConnectionRequest
from background_task_manager import TaskManager  # Custom module for managing background tasks

class DecisionEngine:
    def __init__(self, db: Session, task_manager: TaskManager):
        self.db = db
        self.engagement_module = EngagementModule(db)
        self.task_manager = task_manager

    def run_background_decisions(self):
        """Continuously run decision-making tasks in the background for all active agents."""
        agents = self.db.query(Agent).filter(Agent.is_active == True).all()
        for agent in agents:
            self.task_manager.add_task(self.make_decision, agent.id)

    def make_decision(self, agent_id: int) -> Dict:
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise ValueError("Agent not found")

        user = self.db.query(User).filter(User.id == agent.user_id).first()
        if not user:
            raise ValueError("User not found")

        # Analyze user's recent activity, sentiment, and goals
        recent_activity = self.analyze_recent_activity(user.id)
        engagement_score = self.calculate_engagement_score(user.id)
        user_sentiment = self.analyze_user_sentiment(user.id)
        user_goal = user.goal  # Goal-oriented decision-making

        # Decision logic based on user's goal and sentiment
        if engagement_score < 0.3:
            return self.suggest_engagement_boosting_action(agent, user, user_sentiment, user_goal)
        elif len(recent_activity.get('new_connections', [])) > 3:
            return self.initiate_group_discussion(agent, user, user_sentiment)
        elif random.random() < 0.2:  # 20% chance to try something new
            return self.propose_new_activity(agent, user, user_sentiment, user_goal)
        else:
            return self.default_action(agent, user)

    def analyze_recent_activity(self, user_id: int) -> Dict:
        week_ago = datetime.utcnow() - timedelta(days=7)
        new_connections = self.db.query(ConnectionRequest).filter(
            ConnectionRequest.sender_id == user_id,
            ConnectionRequest.created_at > week_ago
        ).all()
        
        recent_chats = self.db.query(GroupChat).filter(
            GroupChat.members.any(id=user_id),
            GroupChat.created_at > week_ago
        ).all()

        return {
            'new_connections': new_connections,
            'recent_chats': recent_chats
        }

    def calculate_engagement_score(self, user_id: int) -> float:
        activity = self.analyze_recent_activity(user_id)
        connection_score = len(activity['new_connections']) * 0.1
        chat_score = len(activity['recent_chats']) * 0.2
        return min(connection_score + chat_score, 1.0)

    def analyze_user_sentiment(self, user_id: int) -> str:
        """Implement sentiment analysis to adjust decisions based on mood."""
        # Hypothetical method: fetch recent chats or social activity
        recent_messages = self.fetch_recent_messages(user_id)
        sentiments = [self.get_sentiment_analysis(msg.content) for msg in recent_messages]

        positive_score = sum(1 for sentiment in sentiments if sentiment == 'positive')
        negative_score = sum(1 for sentiment in sentiments if sentiment == 'negative')

        if positive_score > negative_score:
            return "positive"
        elif negative_score > positive_score:
            return "negative"
        else:
            return "neutral"

    def get_sentiment_analysis(self, text: str) -> str:
        """Calls a sentiment analysis API to evaluate text sentiment."""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an AI assistant analyzing sentiment."},
                    {"role": "user", "content": f"Analyze the sentiment of this message: {text}"}
                ]
            )
            return response.choices[0].message.content.strip().lower()
        except Exception as e:
            print(f"Sentiment analysis failed: {e}")
            return "neutral"

    def suggest_engagement_boosting_action(self, agent: Agent, user: User, sentiment: str, goal: str) -> Dict:
        suggestions = self.engagement_module.suggest_connections(agent.id)
        if suggestions:
            return {
                "action": "suggest_connections",
                "message": self.generate_connection_suggestion_message(user, suggestions[0], sentiment, goal),
                "suggestions": suggestions[:3]
            }
        else:
            return self.propose_new_activity(agent, user, sentiment, goal)

    def initiate_group_discussion(self, agent: Agent, user: User, sentiment: str) -> Dict:
        recent_connections = self.analyze_recent_activity(user.id)['new_connections']
        if len(recent_connections) >= 3:
            participants = [user.id] + [conn.receiver_id for conn in recent_connections[:3]]
            topic = self.generate_discussion_topic(participants)
            return {
                "action": "initiate_group_chat",
                "participants": participants,
                "topic": topic,
                "message": f"I've initiated a group chat on '{topic}' with your recent connections. Join in!"
            }
        else:
            return self.default_action(agent, user)

    def propose_new_activity(self, agent: Agent, user: User, sentiment: str, goal: str) -> Dict:
        activities = [
            "join_event", "share_article", "take_survey", "contribute_to_discussion"
        ]
        chosen_activity = random.choice(activities)
        return {
            "action": chosen_activity,
            "message": self.generate_activity_proposal_message(chosen_activity, user, sentiment, goal)
        }

    def default_action(self, agent: Agent, user: User) -> Dict:
        return {
            "action": "check_notifications",
            "message": "I've checked your notifications. Everything seems up to date!"
        }

    def generate_connection_suggestion_message(self, user: User, suggestion: Dict, sentiment: str, goal: str) -> str:
        prompt = f"Generate a friendly message suggesting that {user.name} connect with {suggestion['name']} based on their similarity score of {suggestion['similarity']}. " \
                 f"The user's mood is {sentiment} and their goal is {goal}. Keep it brief and engaging."
        return self.generate_message_with_ai(prompt)

    def generate_activity_proposal_message(self, activity: str, user: User, sentiment: str, goal: str) -> str:
        prompt = f"Generate a brief, engaging message proposing that {user.name} {activity.replace('_', ' ')}. " \
                 f"The user's mood is {sentiment} and their goal is {goal}. Make it sound exciting and beneficial."
        return self.generate_message_with_ai(prompt)

    def generate_message_with_ai(self, prompt: str) -> str:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an AI assistant helping to generate engaging messages for a professional networking platform."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating AI message: {e}")
            return "I have a suggestion for you, but I'm having trouble putting it into words right now. Let's try something new!"
