# 🔢 Module 11 – Calculation API

## 🗂️ Project Overview

This project builds on the previous FastAPI application by introducing a Calculation model that stores and manages arithmetic operations using SQLAlchemy, Pydantic, and PostgreSQL.

The application allows users to submit arithmetic calculations, validates input data, and stores calculation records in the database. It also includes automated testing and a CI/CD pipeline through GitHub Actions.

## 🛠️ Features

- **Calculation Model:** Uses SQLAlchemy to define and manage calculation records.
- **Pydantic Schemas:** Validates incoming calculation data and structures API responses.
- **Arithmetic Operations:** Supports addition, subtraction, multiplication, and division.
- **Input Validation:** Checks calculation inputs and prevents invalid operations, including division by zero.
- **PostgreSQL Database:** Stores calculation records and supports database integration testing.
- **Automated Testing:** Includes unit, integration, and end-to-end tests using pytest.
- **Docker:** Uses Docker and Docker Compose to build and run the application.
- **CI/CD Pipeline:** GitHub Actions automatically runs tests, builds the Docker image, scans it for vulnerabilities using Trivy, and pushes the image to Docker Hub.

## 💻 Technologies Used

- Python 3.11
- FastAPI
- SQLAlchemy
- Pydantic
- PostgreSQL
- Pytest
- Playwright
- Docker and Docker Compose
- GitHub Actions
- Trivy
- Docker Hub

## 📝 Calculation Model

The Calculation model represents arithmetic operations stored in the database.

The model includes:

| Field | Description |
|---|---|
| `id` | Unique calculation identifier |
| `a` | First operand |
| `b` | Second operand |
| `type` | Type of arithmetic operation |
| `result` | Result of the calculation |
| `user_id` | Optional reference to an associated user |

The application validates calculation inputs before processing operations. Division by zero is rejected to prevent invalid calculations.

## ⚙️ Installation and Setup

### Prerequisites

- Python 3.11
- Docker Desktop
- Git

### 1. Clone the Repository

```bash
git clone git@github.com:mab263/module11_is601.git
cd module11_is601
```

### 2. Build and Start the Application

Build the Docker containers:

```bash
docker compose build
```

Start the application:

```bash
docker compose up -d
```

### 3. Run the Tests

Run the test suite inside the application container:

```bash
docker compose exec web pytest -q --no-cov
```

To run tests with coverage:

```bash
docker compose exec web pytest --cov=. --cov-report=term-missing
```

The project includes unit, integration, and end-to-end tests to verify calculation functionality, database interactions, and application behavior.

## 🐳 Docker Hub

The Docker image is published to Docker Hub:

**Repository:** https://hub.docker.com/r/mab263/module11_is601

Pull the image:

```bash
docker pull mab263/module11_is601:latest
```

Run the image:

```bash
docker run --rm -p 8000:8000 mab263/module11_is601:latest
```

## GitHub Actions – CI/CD

The project uses GitHub Actions to automate the testing and deployment process.

The workflow includes two main jobs:

1. **Tests:** Runs the unit, integration, and end-to-end tests using a PostgreSQL service.
2. **Build, Scan, and Push:** Builds the Docker image, scans it for security vulnerabilities using Trivy, and pushes the image to Docker Hub when changes are pushed to the `main` branch.

Docker Hub credentials are stored securely in GitHub repository secrets.

## Reflection

This assignment provided additional experience working with SQLAlchemy models, Pydantic validation, PostgreSQL, and automated testing. It also helped strengthen my understanding of Docker and CI/CD workflows. Troubleshooting issues with dependencies, Docker builds, and GitHub Actions was challenging, but it helped me become more comfortable identifying errors and working through them. Overall, this project helped me better understand how different parts of a backend application work together, from validating user input to storing data and deploying an application.