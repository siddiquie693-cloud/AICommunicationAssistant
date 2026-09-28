# AICommunicationAssistant

AICommunicationAssistant is a multilingual AI communication platform that helps users understand, generate, and manage communication across conversational AI, WhatsApp, and phone-call assistant workflows.

The project combines a Python/Django backend, AI provider abstractions, speech services, WhatsApp integration, a React Native mobile application, automated testing, Docker, and AWS ECS/Fargate deployment.

## Project Status

**Phase 32: Complete**

The final project checkpoint was completed and pushed to `main`.

* Final commit: `c9bd429`
* Branch: `main`
* Backend: Django + Django REST Framework
* Database: PostgreSQL
* Mobile: React Native / Expo
* Deployment: AWS ECS Fargate + Application Load Balancer
* AI: Provider-based architecture with Gemini and Mock providers
* Testing: Backend, AI, authentication, conversation, messaging, STT, TTS, WhatsApp, and mobile QA completed

## Core Features

### AI Conversations

* Create and manage conversations
* Send user messages
* Generate AI responses
* Maintain conversation history
* Configurable conversation memory
* System prompts
* Streaming AI responses
* Target-language responses
* Provider abstraction for AI models

### Multilingual Communication

The platform supports configurable user language preferences for communication and voice workflows.

User preferences include:

* Preferred language
* Voice language
* Timezone

### Speech-to-Text

The AI layer provides a provider-based speech-to-text architecture.

Features include:

* Speech-to-text service abstraction
* Provider factory
* Mock provider for testing
* Production provider configuration
* API integration
* Error handling

### Text-to-Speech

The project includes a provider-based text-to-speech architecture.

Features include:

* TTS service abstraction
* Provider factory
* Gemini TTS integration
* Mock TTS provider
* Configurable TTS model
* Configurable voice
* Audio response handling
* API integration

### WhatsApp Assistant

The application includes a WhatsApp communication workflow.

Implemented components include:

* WhatsApp provider abstraction
* Meta WhatsApp Cloud API provider
* Mock WhatsApp provider
* Webhook verification
* Incoming message parsing
* User lookup through WhatsApp phone number
* Conversation integration
* Outgoing message handling
* Provider error handling

### Phone Call Assistant

The mobile application includes a Phone Call Assistant interface.

Implemented functionality includes:

* Phone number input
* Phone number validation
* Call state UI
* Connecting state
* Language controls
* AI suggested response UI
* Copy suggested response
* Use suggested response
* Notifications
* Navigation

The actual telephony provider/backend call connection is **not yet connected**. The application intentionally displays:

> Phone calling is not connected yet.

when a valid phone number is submitted.

## Architecture

```text
                         ┌──────────────────────┐
                         │   React Native App   │
                         │      / Expo          │
                         └──────────┬───────────┘
                                    │
                                    │ REST / Streaming
                                    ▼
                         ┌──────────────────────┐
                         │    Django / DRF      │
                         │      Backend         │
                         └──────────┬───────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
       Authentication        Conversations          Messaging
              │                     │                     │
              │                     ▼                     ▼
              │              AI Conversation        WhatsApp
              │                  Service             Service
              │                     │
              │                     ▼
              │                AI Service
              │                     │
              │       ┌─────────────┼─────────────┐
              │       │             │             │
              ▼       ▼             ▼             ▼
           Users    AI Provider    STT           TTS
                       Factory    Factory       Factory
                         │           │             │
                         ▼           ▼             ▼
                      Gemini      Providers      Gemini
                       / Mock       / Mock       / Mock

                                    │
                                    ▼
                              PostgreSQL
```

## Technology Stack

### Backend

* Python 3.11
* Django 5.2
* Django REST Framework 3.18
* PostgreSQL
* JWT authentication
* Django Channels / WebSocket support
* Daphne
* HTTPX

### AI

* Google Gemini
* Gemini TTS
* AI provider abstraction
* Mock AI provider
* Prompt management
* Conversation memory
* Translation services
* Speech-to-text
* Text-to-speech

### Mobile

* React Native
* Expo
* JavaScript
* REST API integration
* Streaming response handling
* Local session/storage handling
* Network state handling
* Notification UI

### Infrastructure

* Docker
* AWS ECS Fargate
* AWS Application Load Balancer
* AWS security groups
* AWS target groups
* PostgreSQL
* Environment-based configuration
* ECS secrets

## Repository Structure

```text
AICommunicationAssistant/
│
├── .github/
│
├── ai/
│   ├── phone/
│   ├── prompts/
│   ├── providers/
│   ├── retrieval/
│   ├── services/
│   ├── speech_to_text/
│   ├── text_to_speech/
│   ├── translation/
│   └── whatsapp/
│
├── backend/
│   ├── config/
│   ├── conversations/
│   ├── core/
│   ├── knowledge/
│   ├── users/
│   ├── manage.py
│   └── requirements.txt
│
├── docs/
│
├── infrastructure/
│
├── mobile/
│   └── src/
│
├── scripts/
│
└── tests/
    ├── ai/
    └── conversations/
```

## AI Provider Architecture

The AI layer is designed around provider abstraction rather than coupling the application directly to one model provider.

The architecture contains:

```text
AIProvider
    │
    ├── GeminiProvider
    ├── OpenAIProvider
    └── MockAIProvider
```

The provider factory selects the configured provider.

This allows application services to work with an abstract AI interface rather than depending directly on Gemini or another vendor.

The same architectural approach is used for:

* AI
* Speech-to-text
* Text-to-speech
* WhatsApp

This makes the system easier to test and extend.

## Conversation Flow

A typical AI conversation follows this flow:

```text
User enters message
        │
        ▼
Mobile application
        │
        ▼
Django API
        │
        ▼
Conversation service
        │
        ├── Load conversation history
        │
        ├── Apply memory limit
        │
        ├── Apply system prompt
        │
        └── Send request to AI service
                    │
                    ▼
              Provider Factory
                    │
                    ▼
               AI Provider
                    │
                    ▼
               AI Response
                    │
                    ▼
             Save Message
                    │
                    ▼
             Stream to Mobile
```

The conversation system uses a dedicated system prompt:

```text
You are a helpful AI communication assistant.
Answer clearly, accurately, and naturally.
Maintain context from the conversation history.
```

## Authentication

The backend provides authenticated user workflows using JWT-based authentication.

Implemented authentication functionality includes:

* User registration/login infrastructure
* JWT access/refresh tokens
* Authenticated API access
* User profile
* User preferences
* Language preferences
* Session handling
* Password management
* Email verification infrastructure

## API Areas

The backend exposes APIs covering areas including:

````text
/api/auth/
/api/conversations/
/api/health/
/api/
/```

Important communication endpoints include:

```text
/api/conversations/
/api/conversations/<id>/messages/
/api/conversations/<id>/messages/stream/
/api/conversations/<id>/messages/
/api/text-to-speech/
/api/speech-to-text/
/```

WhatsApp functionality is exposed through dedicated webhook/provider workflows.

The exact endpoint configuration should be treated as the source of truth in the Django URL configuration.

## Streaming

AI responses can be streamed rather than waiting for the entire response before sending data to the mobile application.

The architecture separates:

```text
Request
  ↓
AI service
  ↓
Provider streaming
  ↓
Backend streaming response
  ↓
Mobile UI
````

Provider failures are handled without exposing raw provider exceptions directly to the client.

## Error Handling

The project uses dedicated exceptions and structured error handling across provider layers.

Examples include:

* AI provider errors
* Speech-to-text provider errors
* Text-to-speech provider errors
* WhatsApp provider errors
* WhatsApp webhook errors
* API validation errors

The provider abstraction prevents vendor-specific errors from leaking throughout the application.

## Testing

The project includes extensive automated testing across the backend and AI layers.

Final verified test groups include:

| Area           | Tests |
| -------------- | ----: |
| Backend        |   143 |
| AI             |   192 |
| Authentication |    53 |
| Conversations  |   149 |
| Messaging      |    16 |
| Speech-to-Text |     5 |
| Text-to-Speech |     7 |
| WhatsApp       |    20 |

All listed automated test groups passed during final QA.

Mobile functionality was additionally verified manually through the Expo application.

## Mobile QA

The following mobile workflows were manually verified:

### Authentication

* Login
* API connectivity
* Profile retrieval
* Language retrieval

### Home

* Home screen loading
* Navigation
* Conversation access
* WhatsApp access
* Phone Call Assistant access

### Conversations

* Conversation list
* Conversation creation
* Message history
* AI message flow
* Streaming request flow

### WhatsApp

* WhatsApp screen
* Recipient input
* Message input
* Language selection
* Send/action workflow
* History
* Navigation

### Phone Call Assistant

* Screen opening
* Recipient input
* Validation
* Call action
* Connecting state
* Language controls
* AI suggestion UI
* Copy action
* Navigation

The phone calling provider itself remains unconnected.

## Docker

The project includes production-oriented Docker configuration for the backend.

Dockerization was completed as part of the final production preparation phases.

The deployment architecture is designed to run the backend as a containerized service.

## AWS Deployment

The production environment uses:

```text
Internet
   │
   ▼
Application Load Balancer
   │
   ▼
Target Group
   │
   ▼
ECS Fargate Task
   │
   ▼
Django / Daphne
```

Verified AWS components include:

* ECS Fargate
* ECS production cluster
* Fargate task
* Application Load Balancer
* Target group
* Security groups
* Health checks
* ECS secrets

The production ECS task was verified as:

```text
RUNNING
HEALTHY
```

The ALB target was also verified as healthy.

## Production Health Check

The production health endpoint is:

```text
/api/health/
```

It returns:

```json
{
  "status": "ok",
  "service": "AI Communication Assistant",
  "version": "0.1.0"
}
```

The production HTTP health check was successfully verified during final deployment QA.

## Security

The project uses ECS secret references for sensitive production values such as:

* Django secret key
* Database password
* Gemini API key
* WhatsApp access token
* WhatsApp verification token

The production Django debug setting was verified as disabled.

The ECS task is not directly exposed on its application port; access is restricted through the ALB security group.

### Production hardening still pending

The current production ALB does not yet have:

* A custom production domain
* ACM TLS certificate
* HTTPS listener
* HTTPS redirect
* HSTS enforcement
* Secure session cookies
* Secure CSRF cookies
* Restricted `ALLOWED_HOSTS`

These should be configured after a real production domain and TLS certificate are available.

## Environment Configuration

The application uses environment-based configuration rather than hard-coding production secrets.

Examples of configuration areas include:

```text
DJANGO_DEBUG
DJANGO_SECRET_KEY
ALLOWED_HOSTS

AI_PROVIDER
GEMINI_MODEL

SPEECH_TO_TEXT_PROVIDER

TEXT_TO_SPEECH_PROVIDER
GEMINI_TTS_MODEL
GEMINI_TTS_VOICE

DB_NAME
DB_USER
DB_PASSWORD
DB_HOST
DB_PORT

WHATSAPP_PROVIDER
WHATSAPP_API_VERSION
WHATSAPP_PHONE_NUMBER_ID
WHATSAPP_ACCESS_TOKEN
WHATSAPP_VERIFY_TOKEN

PHONE_PROVIDER
```

Sensitive values should never be committed to Git.

## Local Development

### 1. Clone the repository

```bash
git clone https://github.com/siddiquie693-cloud/AICommunicationAssistant.git
cd AICommunicationAssistant
```

### 2. Create and activate the Python environment

From the project root:

```bash
python -m venv .venv
```

Windows:

```cmd
call .venv\Scripts\activate.bat
```

### 3. Install backend dependencies

```cmd
cd backend
pip install -r requirements.txt
```

### 4. Configure environment variables

Create the required environment configuration for local development.

Do not commit secrets.

### 5. Run migrations

```cmd
python manage.py migrate --settings=config.settings
```

### 6. Start the backend

Because the `ai` package is located at the repository root, local development from the `backend` directory may require:

```cmd
set PYTHONPATH=..
python manage.py runserver 0.0.0.0:8000
```

### 7. Run tests

From the `backend` directory:

```cmd
python manage.py test --settings=config.settings
```

## Mobile Development

The mobile application is located in:

```text
mobile/
```

Install the mobile dependencies and start the Expo development server according to the project's package configuration.

For local network development, configure the mobile API base URL to point to the development machine's reachable LAN address.

Example:

```text
EXPO_PUBLIC_API_BASE_URL=http://<development-machine-ip>:8000
```

Production builds must use a secure HTTPS API endpoint.

## Known Limitations

### Phone Telephony

The Phone Call Assistant UI is implemented, but an actual telephony provider has not yet been connected.

### Gemini Quota

The production/development AI workflow depends on the configured Gemini quota. During final mobile QA, Gemini rate-limit responses were observed. The backend correctly handled provider failure, but a provider fallback strategy could improve resilience.

### HTTPS

The deployed ALB currently operates through HTTP. A real domain and ACM certificate are required before enabling full HTTPS production hardening.

## Engineering Highlights

This project demonstrates practical experience with:

* Python backend development
* Django
* Django REST Framework
* PostgreSQL
* REST API design
* JWT authentication
* WebSockets
* Streaming responses
* AI/LLM integration
* Provider abstraction
* Prompt management
* Conversation memory
* Multilingual AI workflows
* Speech-to-text
* Text-to-speech
* WhatsApp integration
* React Native
* Expo
* Docker
* AWS ECS Fargate
* AWS Application Load Balancer
* Cloud deployment
* Automated testing
* Production debugging
* Error handling
* Environment-based configuration

## Future Improvements

Potential future improvements include:

* Real telephony provider integration
* HTTPS and custom production domain
* AI provider fallback
* Improved AI quota handling
* Voice-first conversations
* Call transcription
* Call summaries
* Conversation analytics
* More communication providers
* Advanced agent workflows
* Production monitoring and observability
* Improved AI response recovery and retry handling

## Project Repository

GitHub:

https://github.com/siddiquie693-cloud/AICommunicationAssistant

## Final Project Checkpoint

The final Phase 32 release preparation was completed with:

```text
Commit:
c9bd429 chore: complete phase 32 final QA and release preparation

Branch:
main

Status:
Clean working tree

Remote:
origin/main
```

Phase 32 is the final phase of the original project roadmap.

## Author

**Shahil Siddiquie**

GitHub:

https://github.com/siddiquie693-cloud
