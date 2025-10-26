
# Shopify App Services Documentation

## Docker Setup

This application can be run using Docker for easy deployment and development.

### Prerequisites

- Docker
- Docker Compose

### Quick Start

1. **Clone the repository and navigate to the project directory**

   ```bash
   cd shopify-app
   ```

2. **Create environment file**

   ```bash
   cp .env.example .env
   # Edit .env with your actual configuration values
   ```

3. **Build and run with Docker Compose**

   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - Frontend: `http://localhost:5173`
   - Backend API: `http://localhost:8000`
   - API Documentation: `http://localhost:8000/docs`

### Services

- **frontend**: React application served by Vite
- **backend**: FastAPI application
- **postgres**: PostgreSQL database
- **redis**: Redis cache/message broker
- **celery**: Background task worker

### Development

For development with hot reloading:

```bash
# Run all services
docker-compose up

# Run specific service
docker-compose up backend
docker-compose up frontend

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop services
docker-compose down
```

### Using the Docker Helper Script

A helper script `docker-helper.sh` is provided for easier Docker management:

```bash
# Setup environment (Unix/Linux/macOS)
./docker-helper.sh setup

# Start all services
./docker-helper.sh start

# View logs
./docker-helper.sh logs

# Stop services
./docker-helper.sh stop
```

**Note for Windows users**: The helper script requires Unix-like commands. You can either:

- Use it with WSL (Windows Subsystem for Linux)
- Run the Docker commands directly with `docker-compose`

### Environment Variables

Copy `.env.example` to `.env` and configure the following variables:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `OPENAI_API_KEY`: OpenAI API key
- `SHOPIFY_API_KEY`: Shopify app API key
- `SHOPIFY_API_SECRET`: Shopify app API secret
- And other service-specific configurations

## Privacy & Compliance

- [Privacy Policy](frontend/public/privacy-policy.md)
- [Data Retention Policy](DATA_RETENTION_POLICY.md)

## Table of Contents

1. [Shopify Service (`shopify_service.py`)](#shopify-service-shopify_servicepy)
2. [A/B Testing Service (`ab_testing_service.py`)](#ab-testing-service-ab_testing_servicepy)
3. [Analytics Service (`analytics_service.py`)](#analytics-service-analytics_servicepy)

---
This document provides an overview of the core services in the Shopify application, detailing their features and responsibilities.

1. [Shopify Service (`shopify_service.py`)](#shopify-service-shopify_servicepy)
2. [A/B Testing Service (`ab_testing_service.py`)](#ab-testing-service-ab_testing_servicepy)
3. [Analytics Service (`analytics_service.py`)](#analytics-service-analytics_servicepy)

---

## Shopify Service (`shopify_service.py`)

This service acts as the primary interface between our application, the Shopify API, and the OpenAI API for content generation. It handles all logic related to product data management and AI-powered description creation.

### Key Features

#### 1. Shopify Store Integration

- **Product Fetching**: `fetch_products` retrieves a complete list of products from a user's Shopify store, automatically handling API pagination.
- **Order Fetching**: `fetch_orders_for_product` retrieves all orders associated with a specific product, which is crucial for revenue attribution.
- **Product Updates**: `save_description` and `bulk_save_descriptions` push updated product descriptions back to Shopify.

#### 2. AI-Powered Content Generation

- **Standard Generation**: `generate_description` creates multiple unique product descriptions based on product details, keywords, and user-defined parameters (tone, style, length).
- **Image-Based Generation**: `generate_description_from_image` uses OpenAI's Vision model to generate descriptions from a product image URL.
- **URL-Based Generation**: `generate_description_from_url` scrapes content from a given URL and rewrites it to create a new, unique product description.
- **Variant Regeneration**: `regenerate_variant` takes user feedback on an existing description to generate an improved version.

#### 3. Advanced Content Tools

- **Brand Voice Adherence**: The service dynamically constructs prompts that incorporate the user's defined brand voice, ensuring all generated content is consistent in tone and vocabulary.
- **Feature-to-Benefit Transformation**: `transform_feature_to_benefit` uses AI to convert technical product features into customer-centric benefits.
- **Bulk Find and Replace**: `bulk_find_and_replace` allows merchants to perform a case-insensitive, whole-word search and replace across all or a filtered subset of their product descriptions.

#### 4. SEO and Optimization

- **Integrated SEO Analysis**: After generating a description, the service calls the `SEOService` to perform an on-the-fly SEO analysis and generate AI-powered improvement suggestions.
-
- **Metadata Generation**: The AI is prompted to return not just the description but also relevant keywords, a meta title, and a meta description.

---

## A/B Testing Service (`ab_testing_service.py`)

This service provides a comprehensive framework for running, managing, and analyzing A/B tests for product descriptions. It supports standard A/B tests, multi-arm bandit (MAB) tests, and personalized testing with user segmentation.

### A/B Testing Service Key Features

#### 1. Test Management

- **CRUD Operations**: Full support for creating, updating, retrieving, and deleting A/B tests (`create_ab_test`, `delete_ab_test`, etc.).
- **Lifecycle Management**: Functions to `start_test`, `pause_test`, and `end_test`, which can be triggered manually or via a scheduler.
- **Automated Scheduling**: `schedule_ab_tests` automatically starts and stops tests based on their configured start and end times.

### 2. Advanced Variant Assignment

- **Thompson Sampling (Multi-Arm Bandit)**: `assign_variant_thompson_sampling` dynamically allocates more traffic to better-performing variants over time, maximizing conversions even while a test is running.
- **Personalized Testing (Segmentation)**:
- Assigns variants based on visitor context (e.g., location, referral source) using `get_assigned_variant_for_segment`.
- Tracks performance metrics (impressions, conversions, revenue) for each segment individually.

#### 3. Statistical Analysis and Winner Declaration

- **Rich Analytics**: `get_analysis_results` provides a complete statistical breakdown of a test, including:
- Conversion rates, confidence intervals, and revenue per visitor (RPV).
- Bayesian probabilities (e.g., "probability that Variant B beats A").
- P-values and T-tests for statistical significance.
- **Automated Winner Detection**: `get_winner` uses a Sequential Probability Ratio Test (SPRT) to determine if a variant is a statistically significant winner as soon as enough data is collected.
- **Segment-Specific Winners**: `get_winners_by_segment` identifies which variants perform best for specific customer segments.
- **Auto-Promotion**: Running tests can be configured to automatically promote the winning variant, updating the main product description on Shopify without manual intervention.

#### 4. Metrics Tracking

- **Efficient Data Collection**: `record_impression` and `record_conversion` methods capture performance data. Metrics are batched and flushed to the database periodically using `flush_metrics` to reduce database load.
- **Revenue Tracking**: Records revenue for each conversion, enabling analysis of Average Order Value (AOV) and Revenue Per Visitor (RPV).

---

## Analytics Service (`analytics_service.py`)

This service focuses on providing merchants with actionable insights into their product and A/B test performance. It translates raw data into clear, revenue-focused metrics and proactive alerts.

### Analytics Service Key Features

#### 1. Performance Dashboards

- **Description Performance**: `get_description_performance` analyzes A/B test variants, showing conversion rates, confidence intervals, lift over baseline, and estimated revenue impact.
- **Revenue Attribution**: `get_revenue_attribution` connects to Shopify order data to calculate the total revenue generated by a specific product.
- **Timeline Analysis**: `get_product_timeline_performance` shows trends in product views and adds-to-cart over a given period.
- **Team and Category Performance**: `get_team_performance` and `get_category_performance` provide aggregated views to identify high-performing team members and product categories.

#### 2. Proactive & Actionable Alerts

- **Automated Monitoring**: `check_for_actionable_alerts` runs checks across the entire product catalog to identify key business opportunities and risks.
- **Types of Alerts**:
  - **Opportunity Alert**: Flags high-traffic products that don't have an A/B test running.
  - **Winner Alert**: Notifies the merchant when a variant in an A/B test becomes a statistically significant winner.
  - **Underperformance Alert**: Flags variants with sufficient traffic but a very low conversion rate.

#### 3. Advanced Statistical Calculations

- **Reliable Confidence Intervals**: Uses the Wilson score interval (`_calculate_confidence_interval`), which is more accurate for small sample sizes and extreme conversion rates.
- **Significance Testing**: Implements Z-tests (`_is_winner_statistically_significant`) and calculates p-values to help merchants make data-driven decisions.

#### 4. SEO Integration

- **Centralized Analysis**: Leverages the `SEOService` to perform SEO analysis on product content.
- **AI-Powered Suggestions**: Uses OpenAI to generate concrete, actionable suggestions for improving a product's SEO score based on the analysis results.
