
from django.db import models
from dataclasses import replace
from secrets import token_urlsafe

from ai.android.service import AndroidActionEngine
from ai.android.types import AndroidActionRequest
from ai.brain.types import (
    BrainPipelineResult,
    BrainRequest,
    PendingActionConfirmation,
)
from ai.android.types import AndroidActionRequest, AndroidActionResult
from ai.planner.types import PlannedAction

from ai.context.service import ContextEngine
from ai.intent.service import IntentEngine
from ai.memory.service import MemoryEngine
from ai.planner.service import ActionPlanner
from ai.safety.service import SafetyEngine
from ai.safety.request_builder import ActionSafetyRequestBuilder
from ai.android.registry import ActionRegistry
from people.services import PersonIdentityResolver
from ai.android.registry_types import ActionDefinition
from ai.safety.types import SafetyLevel


class NIRABrain:
    """
    Top-level orchestration boundary for NIRA AI.

    The Brain coordinates understanding, context, validation,
    planning, safety evaluation, and authorized Android execution.
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
        action_registry: ActionRegistry | None = None,
        person_identity_resolver=None,
        safety_request_builder=None,
        confirmation_store=None,
    ):
        self.ai_service = ai_service
        self.intent_engine = intent_engine
        self.context_engine = context_engine
        self.action_planner = action_planner
        self.action_registry = action_registry or ActionRegistry()
        self._register_default_actions()
        self.safety_engine = safety_engine
        self.android_action_engine = android_action_engine
        self.confirmation_store = confirmation_store
        self.person_identity_resolver = (
            person_identity_resolver
            or PersonIdentityResolver
        )
        self.safety_request_builder = (
            safety_request_builder or ActionSafetyRequestBuilder()
        )

    def _register_default_actions(self) -> None:
        definitions = (
            ActionDefinition(
                name="open_app",
                required_parameters=("app",),
                parameter_types={"app": str},
                risk_level=SafetyLevel.LOW,
            ),
            ActionDefinition(
                name="navigate",
                required_parameters=("location",),
                parameter_types={"location": str},
                risk_level=SafetyLevel.LOW,
            ),
            ActionDefinition(
                name="play_media",
                required_parameters=("request",),
                parameter_types={"request": str},
                risk_level=SafetyLevel.LOW,
            ),
            ActionDefinition(
                name="create_reminder",
                required_parameters=("request",),
                parameter_types={"request": str},
                risk_level=SafetyLevel.MEDIUM,
            ),
            ActionDefinition(
                name="send_message",
                required_parameters=("recipient",),
                optional_parameters=("request", "content"),
                parameter_types={
                    "recipient": str,
                    "request": str,
                    "content": str,
                },
                risk_level=SafetyLevel.HIGH,
            ),
            ActionDefinition(
                name="call_person",
                required_parameters=("recipient",),
                parameter_types={"recipient": str},
                risk_level=SafetyLevel.HIGH,
            ),
        )

        for definition in definitions:
            if self.action_registry.get(definition.name) is None:
                self.action_registry.register(definition)
    
    def approve_action(self, *, user, confirmation_id):
        """
        Approve and execute a pending action after fresh safety validation.

        A confirmation can be consumed only once.
        """

        if user is None or not user.is_authenticated:
            raise ValueError("An authenticated user is required.")

        if self.confirmation_store is None:
            raise ValueError("Confirmation Store is not configured.")

        if self.safety_engine is None:
            raise ValueError("Safety Engine is not configured.")

        if self.android_action_engine is None:
            raise ValueError("Android Action Engine is not configured.")

        # First, resolve the pending confirmation.
        record = self.confirmation_store.resolve(
            user=user,
            confirmation_id=confirmation_id,
            approved=True,
        )

        if record is None:
            return AndroidActionResult(
                success=False,
                action_name="confirmation",
                message="Confirmation not found or no longer pending.",
            )

        if record.status != record.Status.APPROVED:
            return AndroidActionResult(
                success=False,
                action_name=record.action_name,
                message="Confirmation has expired.",
            )

        # Consume approval before any execution attempt.
        consumed_record = self.confirmation_store.consume_approved(
            user=user,
            confirmation_id=confirmation_id,
        )

        if consumed_record is None:
            return AndroidActionResult(
                success=False,
                action_name=record.action_name,
                message="Confirmation expired or has already been consumed.",
            )

        # Revalidate the stored action.
        planned_action = PlannedAction(
            name=consumed_record.action_name,
            parameters=consumed_record.parameters,
        )

        registry_result = self.action_registry.validate(
            planned_action.name,
            planned_action.parameters,
        )

        if not registry_result.is_valid:
            return AndroidActionResult(
                success=False,
                action_name=planned_action.name,
                message="Action validation failed: "
                + "; ".join(registry_result.errors),
            )

        validated_action = replace(
            planned_action,
            parameters=registry_result.validated_parameters,
        )

        # Perform a fresh safety evaluation.
        safety_request = self.safety_request_builder.build(
            validated_action
        )

        safety_result = self.safety_engine.evaluate(safety_request)

        if safety_result.decision.value != "allow":
            return AndroidActionResult(
                success=False,
                action_name=validated_action.name,
                message="Execution blocked by safety engine: "
                + safety_result.reason,
            )

        # Execute only after all checks pass.
        android_request = AndroidActionRequest(
            action_name=validated_action.name,
            parameters=registry_result.validated_parameters,
        )

        return self.android_action_engine.execute(android_request)
            
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
        user=None,
        person=None,
        conversation=None,
    ) -> BrainPipelineResult:
        """
        Process a request through the complete NIRA action pipeline.

        Request
        -> Context
        -> Intent Detection
        -> Intent Validation
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

        if person is None and conversation is None:
            context = self.context_engine.build(request)
        else:
            context = self.context_engine.build(
                request,
                person=person,
                conversation=conversation,
            )

        validation_result = (
            self.intent_engine.detect_with_validation(
                request,
                context=context,
            )
        )

        intent = validation_result.intent

        # Stop invalid intents before planning or execution.
        if not validation_result.is_valid:
            return BrainPipelineResult(
                intent=intent,
                context=context,
                action_plan=None,
                safety_results=[],
                action_results=[],
                validation_result=validation_result,
            )

        if self.action_planner is None:
            raise ValueError("Action Planner is not configured.")

        if self.safety_engine is None:
            raise ValueError("Safety Engine is not configured.")

        if self.android_action_engine is None:
            raise ValueError(
                "Android Action Engine is not configured."
            )

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

                if person is not None:
                    context = self.context_engine.build(
                        request,
                        person=person,
                        conversation=conversation,
                    )
        clarification_method = getattr(
            type(self.action_planner),
            "plan_with_clarification",
            None,
        )

        if callable(clarification_method):
            action_plan = self.action_planner.plan_with_clarification(intent)
        else:
            action_plan = self.action_planner.plan(intent)

        if action_plan.requires_clarification:
            return BrainPipelineResult(
                intent=intent,
                context=context,
                action_plan=action_plan,
                safety_results=[],
                action_results=[],
                validation_result=validation_result,
            )

        safety_results = []
        action_results = []
        registry_errors = []
        pending_confirmations = []

        for action in action_plan.actions:
            registry_result = self.action_registry.validate(
                action.name,
                action.parameters,
            )

            if not registry_result.is_valid:
                registry_errors.extend(registry_result.errors)
                continue

            validated_action = replace(
                action,
                parameters=registry_result.validated_parameters,
            )

            safety_request = self.safety_request_builder.build(validated_action)

            safety_result = self.safety_engine.evaluate(
                safety_request
            )

            safety_results.append(safety_result)

            decision = safety_result.decision.value

            if decision == "confirm":
                if self.confirmation_store is None:
                    raise ValueError("Confirmation Store is required for pending actions.")

                if user is None or not user.is_authenticated:
                    raise ValueError(
                        "An authenticated user is required for action confirmation."
                    )

            if decision == "confirm":
                if self.confirmation_store is None:
                    raise ValueError(
                        "Confirmation Store is required for pending actions."
                    )

                if user is None or not user.is_authenticated:
                    raise ValueError(
                        "An authenticated user is required for action confirmation."
                    )

                pending_confirmation = PendingActionConfirmation(
                    confirmation_id=token_urlsafe(32),
                    action_name=action.name,
                    parameters=registry_result.validated_parameters,
                    reason=safety_result.reason,
                )

                self.confirmation_store.create_pending(
                    user=user,
                    confirmation=pending_confirmation,
                )

                pending_confirmations.append(pending_confirmation)
                break

            if decision != "allow":
                continue

            android_request = AndroidActionRequest(
                action_name=action.name,
                parameters=registry_result.validated_parameters,
            )

            action_result = self.android_action_engine.execute(android_request)

            action_results.append(action_result)

        if registry_errors:
            action_plan = replace(
                action_plan,
                errors=action_plan.errors + tuple(registry_errors),
            )    

        return BrainPipelineResult(
            intent=intent,
            context=context,
            action_plan=action_plan,
            safety_results=safety_results,
            action_results=action_results,
            validation_result=validation_result,
            pending_confirmations=pending_confirmations,
        )
