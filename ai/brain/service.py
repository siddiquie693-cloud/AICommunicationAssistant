from ai.android.service import AndroidActionEngine
from ai.android.types import AndroidActionRequest
from ai.brain.types import BrainPipelineResult, BrainRequest
from ai.context.service import ContextEngine
from ai.intent.service import IntentEngine
from ai.memory.service import MemoryEngine
from ai.planner.service import ActionPlanner
from ai.safety.service import SafetyEngine
from people.services import PersonIdentityResolver
from django.db import models

class NIRABrain:
    """
    Top-level orchestration boundary for NIRA AI.

    The Brain coordinates understanding, context, planning,
    safety evaluation, and authorized Android execution.
    """

    def __init__(
        self,
        ai_service,
        *,
        intent_engine: IntentEngine | None = None,
        context_engine: ContextEngine | None = None,
        action_planner: ActionPlanner | None = None,
        safety_engine: SafetyEngine | None = None,
        android_action_engine: AndroidActionEngine | None = None,
        person_identity_resolver=None,
    ):
        self.ai_service = ai_service
        self.intent_engine = intent_engine
        self.context_engine = context_engine
        self.action_planner = action_planner
        self.safety_engine = safety_engine
        self.android_action_engine = android_action_engine
        self.person_identity_resolver = (
            person_identity_resolver
            or PersonIdentityResolver
        )

    def think(
        self,
        request: BrainRequest,
        *,
        system_prompt: str | None = None,
        messages: list[dict[str, str]] | None = None,
    ) -> str:
        """
        Process a structured request through the configured AI service.
        """
        if not isinstance(request, BrainRequest):
            raise TypeError("request must be a BrainRequest.")

        return self.ai_service.generate_response(
            request.text,
            system_prompt=system_prompt,
            messages=messages,
        )

    def process(
        self,
        request: BrainRequest,
        *,
        person=None,
        conversation=None,
    ) -> BrainPipelineResult:
        """
        Process a request through the complete NIRA action pipeline.

        The pipeline is:

        Request
        -> Intent
        -> Context
        -> Action Plan
        -> Safety
        -> Android Execution
        """
        if not isinstance(request, BrainRequest):
            raise TypeError("request must be a BrainRequest.")

        if self.intent_engine is None:
            raise ValueError("Intent Engine is not configured.")

        if self.context_engine is None:
            raise ValueError("Context Engine is not configured.")

        if self.action_planner is None:
            raise ValueError("Action Planner is not configured.")

        if self.safety_engine is None:
            raise ValueError("Safety Engine is not configured.")

        if self.android_action_engine is None:
            raise ValueError(
                "Android Action Engine is not configured."
            )

        intent = self.intent_engine.detect(request)

        if person is None:
            recipient = intent.parameters.get("recipient")
            context_user = getattr(
                self.context_engine.builder,
                "user",
                None,
            )

            if (
                recipient 
                and self.person_identity_resolver is not None
                and isinstance(context_user, models.Model)
            ):
                
                person = self.person_identity_resolver.resolve(
                    user=context_user,
                    name=recipient,
                )

        if person is None and conversation is None:
            context = self.context_engine.build(request)
        else:    
            context = self.context_engine.build(
                request,
                person=person,
                conversation=conversation,
            )

        action_plan = self.action_planner.plan(intent)

        safety_results = []
        action_results = []

        for action in action_plan.actions:
            safety_request = action.parameters.get(
                "_safety_request"
            )

            if safety_request is None:
                raise ValueError(
                    "Planned action is missing a SafetyRequest."
                )

            safety_result = self.safety_engine.evaluate(
                safety_request
            )

            safety_results.append(safety_result)

            if safety_result.decision.value != "allow":
                continue

            android_request = AndroidActionRequest(
                action_name=action.name,
                parameters=action.parameters,
            )

            action_result = self.android_action_engine.execute(
                android_request
            )

            action_results.append(action_result)

        return BrainPipelineResult(
            intent=intent,
            context=context,
            action_plan=action_plan,
            safety_results=safety_results,
            action_results=action_results,
        )