# streaming-platform

A modular research platform for **Adaptive Stream Learning / Online Machine Learning** built with a microservices architecture.

## Overview

This repository is the root workspace for the ASLP project. It provides the foundation for multiple independent services that communicate through REST APIs and a message broker.

## Planned Structure

- `docs/` — architecture and implementation documentation
- `services/` — microservice implementations
- `shared-sdk/` — reusable Python package used by all services
- `scripts/` — helper scripts for setup and lifecycle operations
- `docker/` — Docker and compose assets

## Current Status

- Foundation files: in progress
- Shared SDK: in progress
- Configuration Service: in progress
- Other services: planned

## Development Principles

- Modular by design
- Loose coupling between services
- Centralized configuration
- REST API first
- Research-friendly and extensible

## Getting Started

At this stage the repository contains the foundation for development, but the service runtime is not yet complete.

The next step is to complete the foundation scripts and Docker files, then continue with the Configuration Service.

## Notes

This repository is intended for iterative development. Each milestone should be completed before moving to the next one.
