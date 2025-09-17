# PrepForge - AI-Powered Test Prep Platform

## Overview

PrepForge is a comprehensive AI-powered adaptive learning platform designed for standardized test preparation. It supports multiple exam types (GMAT, GRE, MCAT, USMLE, NCLEX, LSAT, IELTS, TOEFL, PMP, CFA, ACT, SAT). The platform generates unlimited, never-repeated multiple-choice questions tailored to individual user performance and provides intelligent explanations for enhanced learning. PrepForge aims to provide an advanced, adaptive, and accessible test preparation experience.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Flask with Jinja2 templating
- **Styling**: CSS with Bootstrap components, Inter font family
- **JavaScript**: Vanilla JS with MathJax for mathematical content rendering
- **Responsive Design**: Mobile-first approach
- **Color Scheme**: Primary: #4169e1 (Royal Blue); Background: #121212 (Black headers), #eae6dc (Beige), #FAF9F6 (Off-white); Accent: #d4a859 (Gold)

### Backend Architecture
- **Framework**: Flask with SQLAlchemy ORM
- **Database**: PostgreSQL (Neon)
- **Authentication**: Flask-Login with persistent sessions
- **Payment Processing**: Stripe integration
- **AI Integration**: xAI (Grok) for question generation and explanation, previously OpenAI.
- **Caching**: Local SQLite cache for question serving and Redis for rate limiting.

### Key Components

#### User Management System
- User registration, authentication, and profile management.
- Admin role-based access control.
- Subscription management with free trial (20 questions/day) and premium (unlimited/rate-limited) tiers.

#### Question Management System
- **4-Tier Availability System**: Ensures continuous question availability across all 13 exam types using JSON files, emergency AI generation, background batch generation, and personalized adaptive generation.
- **Question Caching**: Utilizes a `CachedQuestion` table for immediate access.
- **Adaptive Difficulty**: Dynamically adjusts question difficulty based on user performance, with intelligent prompts for the AI generator.
- **Guaranteed Availability**: Multiple fallback systems prevent practice interruption.

#### Practice Session Management
- Manages practice session state, provides immediate answer validation with explanations, tracks user progress, and includes an Answer Contest System for incorrect answers.

#### Subscription Gate System
- Protects API routes with rate limiting based on user subscription plan (free: 20 questions/day, pro: 10 questions/minute).
- Utilizes Redis with PostgreSQL fallback for high-performance rate limiting.

#### Adaptive Question System
- Tracks user performance in a PostgreSQL table, adjusts question difficulty based on scores (<40% easy, 40-70% medium, >70% hard).
- Enhances AI generator prompts with user context and performance data.

## External Dependencies

### Payment Processing
- **Stripe**: Handles subscription management and payment processing with embedded checkout using @stripe/stripe-js, including webhook handling for plan updates.

### AI Services
- **xAI (Grok)**: Primary AI service for generating multiple-choice questions and explanations.
- **OpenAI API**: Previously used for question generation and explanation.

### Database Services
- **Neon PostgreSQL**: Main relational database for all application data.
- **SQLite**: Used for local caching of questions for offline operation.
- **Redis**: Used for high-performance rate limiting in the subscription gate system.

### Content Delivery & UI
- **MathJax CDN**: Renders mathematical content.
- **Google Fonts**: Provides the Inter font family.
- **Font Awesome**: Supplies icons for UI elements.