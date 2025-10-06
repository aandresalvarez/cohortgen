"""
Interactive clarification module for Stage 1.

This module provides stateful, step-by-step clarification for cohort definitions.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)


class InteractiveClarificationSession:
    """
    Manages an interactive clarification session.
    
    This class wraps the clarification agent and maintains conversation state.
    """
    
    def __init__(self, run_id: str, initial_description: str):
        """
        Initialize a clarification session.
        
        Args:
            run_id: The run ID for this session
            initial_description: The user's initial cohort description
        """
        self.run_id = run_id
        self.initial_description = initial_description
        self.conversation_history: list[dict[str, str]] = []
        self.is_complete = False
        self.cohort_definition: Optional[Dict[str, Any]] = None
        
        # Import the clarification module
        from hitl_clarification_working import (
            agent, ClarificationDecision, CohortDefinition, 
            demographics_extractor, DemographicsExtraction
        )
        
        self.agent = agent
        self.ClarificationDecision = ClarificationDecision
        self.CohortDefinition = CohortDefinition
        self.demographics_extractor = demographics_extractor
        self.DemographicsExtraction = DemographicsExtraction
        
        # Track current state
        self.current_definition = CohortDefinition()
        self.question_count = 0
        self.max_questions = 5
        
        # Extract demographics first
        self._extract_initial_demographics()
        
        # Get first question
        self._get_next_question()
    
    def _extract_initial_demographics(self):
        """Extract demographics from initial description."""
        result = self.demographics_extractor.run_sync(
            self.initial_description
        )
        extracted = result.output
        
        demographics = {}
        if extracted.age:
            demographics["age"] = extracted.age
        if extracted.gender:
            demographics["gender"] = extracted.gender
        
        self.current_definition.demographics = demographics
        
        # Store time period separately if present
        self.time_period = extracted.time_period
    
    def _get_next_question(self):
        """Get the next clarification question from the agent."""
        # Build context for agent
        context = f"""
Initial Cohort Description: {self.initial_description}

Current Progress:
"""
        if self.current_definition.index_event:
            context += f"\n✓ Index Event: {self.current_definition.index_event}"
        if self.current_definition.inclusion_criteria:
            context += f"\n✓ Inclusion Criteria: {', '.join(self.current_definition.inclusion_criteria)}"
        if self.current_definition.exclusion_criteria:
            context += f"\n✓ Exclusion Criteria: {', '.join(self.current_definition.exclusion_criteria)}"
        if self.current_definition.observation_window:
            context += f"\n✓ Observation Window: {self.current_definition.observation_window}"
        if self.current_definition.demographics:
            context += f"\n✓ Demographics: {self.current_definition.demographics}"
        
        # Add conversation history
        if self.conversation_history:
            context += "\n\nConversation History:"
            for msg in self.conversation_history:
                context += f"\n{msg['role'].upper()}: {msg['content']}"
        
        context += f"\n\nQuestion count: {self.question_count}/{self.max_questions}"
        context += "\n\nDecide: ask another question or finish?"
        
        # Get agent decision
        result = self.agent.run_sync(context)
        decision: ClarificationDecision = result.output
        
        if decision.action == "finish" or self.question_count >= self.max_questions:
            # Session complete
            self.is_complete = True
            self.cohort_definition = decision.cohort_components.model_dump()
            
            # Add completion message
            self.conversation_history.append({
                "role": "assistant",
                "content": "✅ **Clarification complete!** I have all the information needed to define your cohort."
            })
        else:
            # Add question to history
            self.conversation_history.append({
                "role": "assistant",
                "content": decision.question
            })
            self.question_count += 1
            
            # Update current definition with any new components
            if decision.cohort_components:
                self.current_definition = decision.cohort_components
    
    def send_message(self, user_message: str) -> Tuple[Optional[str], bool, Optional[Dict[str, Any]]]:
        """
        Send a user message and get the next question.
        
        Args:
            user_message: The user's answer
            
        Returns:
            Tuple of (next_question, is_complete, cohort_definition)
        """
        if self.is_complete:
            return None, True, self.cohort_definition
        
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Get next question
        self._get_next_question()
        
        if self.is_complete:
            return None, True, self.cohort_definition
        else:
            # Return the last assistant message (the question)
            last_question = self.conversation_history[-1]["content"]
            return last_question, False, None
    
    def get_conversation_history(self) -> list[dict[str, str]]:
        """Get the complete conversation history."""
        return self.conversation_history.copy()
    
    def get_state(self) -> Dict[str, Any]:
        """Get the current session state for persistence."""
        return {
            "run_id": self.run_id,
            "conversation_history": self.conversation_history,
            "is_complete": self.is_complete,
            "cohort_definition": self.cohort_definition,
        }

