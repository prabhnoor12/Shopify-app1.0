# Data Retention Policy

## Overview

This document outlines the data retention policies for the Shopify SaaS application in compliance with GDPR (General Data Protection Regulation) and CCPA (California Consumer Privacy Act) requirements.

## Retention Periods by Data Type

### 1. User Account Data

- **Data Types**: Email, hashed password, account creation/update timestamps
- **Retention Period**: Indefinite (until account deletion)
- **Legal Basis**: Contract performance, legitimate interest
- **Rationale**: Required for account functionality and user identification

### 2. Session Data

- **Data Types**: Session tokens, IP addresses, user agents, login timestamps
- **Retention Period**: 30 days after session expiration
- **Legal Basis**: Legitimate interest (security)
- **Rationale**: Security monitoring and fraud prevention

### 3. Audit Logs

- **Data Types**: User actions, IP addresses, user agents, event details
- **Retention Period**: 7 years
- **Legal Basis**: Legal obligation (GDPR Article 30)
- **Rationale**: Required for legal compliance and dispute resolution

### 4. Usage Analytics

- **Data Types**: Feature usage counts, API call logs, performance metrics
- **Retention Period**: 2 years
- **Legal Basis**: Legitimate interest
- **Rationale**: Service improvement and analytics

### 5. User Feedback

- **Data Types**: User-submitted feedback, ratings, comments
- **Retention Period**: 3 years
- **Legal Basis**: Legitimate interest
- **Rationale**: Product improvement and quality assurance

### 6. Temporary Data

- **Data Types**: Cache data, temporary files, API responses
- **Retention Period**: 24-72 hours
- **Legal Basis**: Service performance
- **Rationale**: Application functionality

## Data Deletion Procedures

### Automatic Deletion

- Session data: Automatically deleted 30 days after expiration
- Temporary data: Automatically deleted within 24-72 hours
- Expired tokens: Immediately upon expiration

### Manual/User-Initiated Deletion

- User account deletion: All associated data anonymized/deleted within 30 days
- GDPR data deletion requests: Processed within 30 days
- Data export requests: Provided within 30 days

### Legal Holds

- Data subject to legal holds or investigations may be retained beyond normal periods
- Legal department must be notified of any retention extensions

## Implementation

### Automated Cleanup Jobs

- Daily: Clean expired sessions and temporary data
- Weekly: Review and clean old analytics data
- Monthly: Audit log rotation (move to long-term storage after 1 year)
- Quarterly: Full data retention audit

### Manual Processes

- User account deletion requests
- GDPR/CCPA data subject requests
- Legal hold management

## Monitoring and Auditing

### Retention Compliance Checks

- Monthly automated audits of data retention
- Quarterly manual reviews
- Annual comprehensive audit

### Metrics Tracked

- Data volume by retention category
- Deletion success rates
- Compliance violation incidents
- User data request processing times

## Contact Information

For questions about data retention or to request data deletion:

- Email: `privacy@yourcompany.com`
- Data Protection Officer: `dpo@yourcompany.com`

## Policy Updates

This policy will be reviewed annually or when significant changes to data processing occur.

Last Updated: October 19, 2025
