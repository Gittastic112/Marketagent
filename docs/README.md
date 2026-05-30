# Market Intelligence Engine Documentation

This folder contains the consolidated documentation for the Market Intelligence Engine. The documents are numbered in reading order.

## 00. Current State & Known Issues
**[00-current-state.md](file:///Users/mananmaheshwari/Documents/Codex/Market%20Intelligence%20App/market-intelligence-md-files%20copy/docs/00-current-state.md)**
The single source of truth for what currently works, what is mocked, what is missing, and the prioritized backlog of known issues.

## 01. Product Brief
**[01-product-brief.md](file:///Users/mananmaheshwari/Documents/Codex/Market%20Intelligence%20App/market-intelligence-md-files%20copy/docs/01-product-brief.md)**
The core product vision, scope, and definition of the intelligence engine.

## 02. Architecture
**[02-architecture.md](file:///Users/mananmaheshwari/Documents/Codex/Market%20Intelligence%20App/market-intelligence-md-files%20copy/docs/02-architecture.md)**
Technical architecture, stack decisions, and system constraints.

## 03. Database Schema
**[03-database-schema.md](file:///Users/mananmaheshwari/Documents/Codex/Market%20Intelligence%20App/market-intelligence-md-files%20copy/docs/03-database-schema.md)**
Overview of the SQLAlchemy models and relationships.

## 04. Data Sources & Ingestion
**[04-data-sources-and-ingestion.md](file:///Users/mananmaheshwari/Documents/Codex/Market%20Intelligence%20App/market-intelligence-md-files%20copy/docs/04-data-sources-and-ingestion.md)**
Rules for ingestion pipelines (SEC, RSS), handling stale data, and maintaining source provenance.

## 05. Scoring Framework
**[05-scoring-framework.md](file:///Users/mananmaheshwari/Documents/Codex/Market%20Intelligence%20App/market-intelligence-md-files%20copy/docs/05-scoring-framework.md)**
The deterministic formulas for Credibility, Novelty, Impact, and Portfolio Priority scores.

## 06. Security Threat Model
**[06-security-threat-model.md](file:///Users/mananmaheshwari/Documents/Codex/Market%20Intelligence%20App/market-intelligence-md-files%20copy/docs/06-security-threat-model.md)**
Security boundaries, untrusted input handling, and strict rules around API keys.

## 07. Local Development Guide
**[07-local-development.md](file:///Users/mananmaheshwari/Documents/Codex/Market%20Intelligence%20App/market-intelligence-md-files%20copy/docs/07-local-development.md)**
How to configure `.env`, run Docker Compose, and troubleshoot local issues.

## 08. Execution Runbook
**[08-execution-runbook.md](file:///Users/mananmaheshwari/Documents/Codex/Market%20Intelligence%20App/market-intelligence-md-files%20copy/docs/08-execution-runbook.md)**
The strict phase-by-phase implementation checklist and validation commands for building out the new architecture.

## 09. Beginner Glossary
**[09-beginner-glossary.md](file:///Users/mananmaheshwari/Documents/Codex/Market%20Intelligence%20App/market-intelligence-md-files%20copy/docs/09-beginner-glossary.md)**
Definitions of financial and technical terms used across the project.

## 10. Design Brief
**[10-design-brief.md](file:///Users/mananmaheshwari/Documents/Codex/Market%20Intelligence%20App/market-intelligence-md-files%20copy/docs/10-design-brief.md)**
The guiding North Star document detailing the frontend overhaul and backend API envelope refactoring.

---

### Archive
The `archive/` folder contains deprecated plans, historical rationale, and old prompts that should no longer be referenced.
