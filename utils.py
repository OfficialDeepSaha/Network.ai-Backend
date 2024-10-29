from hashlib import sha256
import logging
import os
from fastapi import logger
import numpy as np
import openai
from functools import lru_cache
from sklearn.metrics.pairwise import cosine_similarity

from schemas import ConversationHistory

openai.api_key = "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"



logger = logging.getLogger("uvicorn.error")


def save_document(file, user_id):
    # Save file to local storage
    file_path = f"documents/user_{user_id}/{file.filename}"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())
    return file_path




def hash_password(password: str) -> str:
    return sha256(password.encode()).hexdigest()




def notify_user_of_connection_request(receiver_id: int):
    print(f"Notified user {receiver_id} of a new connection request")


def notify_user_of_approval(sender_id: int):
    # Notify the sender that their connection request has been approved
    print(f"Notified user {sender_id} that their connection request has been approved")





def generate_response(prompt: str, context: str = "") -> str:
    """Generate a response using OpenAI API based on the given prompt."""
    full_prompt = f"{context}\nUser: {prompt}\nAI:"
    response = openai.Completion.create(
        engine="gpt-4",  # Choose appropriate model
        prompt=full_prompt,
        max_tokens=150,
        temperature=0.7,
    )
    return response.choices[0].text.strip()

def evaluate_outcome(conversation_history: list) -> str:
    """Evaluate the outcome based on conversation history."""
    # Example logic: look for mutual interest keywords
    for message in conversation_history:
        if "mutual interest" in message.message:
            return "mutual interests identified"
    return "no mutual interests found"

def log_conversation(conversation_id: int, sender_id: int, receiver_id: int, message: str, db):
    """Log each message in the conversation."""
    conversation_log = ConversationHistory(
        conversation_id=conversation_id,
        sender_id=sender_id,
        receiver_id=receiver_id,
        message=message,
    )
    db.add(conversation_log)
    db.commit()
