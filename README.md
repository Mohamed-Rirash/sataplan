# 🎯 SataPlan: Goal Management Platform

## 🌟 Overview

SataPlan is a powerful goal management application designed to help users track, manage, and achieve their personal and professional objectives. Leveraging modern web technologies, SataPlan provides an intuitive and secure platform for goal setting and progress tracking.

## ✨ Features

- 🚀 Goal Creation and Management
- 📊 Progress Tracking
- 🔐 Secure User Authentication
- 🔍 Goal Search and Filtering
- 📱 Responsive Web Interface
- 🖼️ Intuitive User Experience

## 🛠️ Tech Stack

- **Backend**: Python, FastAPI
- **Authentication**: JWT (JSON Web Tokens)
- **Database**: SQLAlchemy (with SQLite/PostgreSQL)
- **Frontend**: To be developed

## 🚦 Prerequisites

- Python 3.8+
- pip
- Virtual environment (recommended)

## 🔧 Installation

1. Clone the repository:
```bash
git clone https://github.com/Mohamed-Rirash/sataplan.git
cd sataplan
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## 🏃 Running the Application

1. Navigate to the backend directory:
```bash
cd backend
```

2. Start the FastAPI server:
```bash
uvicorn main:app --reload
```

## 📡 API Endpoints

### Goals Management

- `POST /goals/add`: Create a new goal
- `GET /goals/allgoals`: Retrieve all goals
- `GET /goals/goal/{goal_id}`: Retrieve a specific goal

### 🎯 Goals

#### ➕ Create a New Goal
```http
POST /goals/add

Request Body:

{
  "name": "Goal Name",
  "description": "Goal Description"
}

Responses:

    201 Created: Goal added successfully.
    422 Unprocessable Entity: Validation error.
```

#### 📜 Retrieve All Goals
```http
GET /goals/allgoals
```

| Parameter | Type | Description |
|-----------|------|-------------|
| offset    | int  | Pagination offset (default: 0). |
| limit     | int  | Number of goals per request. |

#### 🔍 Retrieve a Specific Goal
```http
GET /goals/goal/{goal_id}
```

| Parameter | Type | Description |
|-----------|------|-------------|
| goal_id   | int  | Required. Goal ID. |

#### ✏️ Update a Goal
```http
PATCH /goals/update/{goal_id}
```

#### 🗑️ Delete a Goal
```http
DELETE /goals/delete/{goal_id}
```

### 💡 Motivations

#### ➕ Add Motivation to a Goal
```http
POST /motivations/{goal_id}
```

Request Body:

{
  "quote": "Stay motivated!",
  "link": "https://example.com/"
}

#### 🔍 Retrieve Motivations for a Goal
```http
GET /motivations/{goal_id}
```

#### 🗑️ Delete a Motivation
```http
DELETE /motivations/{motivation_id}
```

### 📷 QR Code Management

#### 🆕 Generate QR Code for a Goal
```http
GET /qrcode/generate-permanent-qr/{goal_id}
```

#### 🔐 Verify Goal Access via QR Code
```http
POST /qrcode/verify-goal-access
```

| Parameter | Type | Description |
|-----------|------|-------------|
| goal_id   | int  | Required. Goal ID. |
| password   | string | Required. Goal password. |

#### 👀 View Goal Using QR Code
```http
GET /qrcode/view-goal
```

| Parameter | Type | Description |
|-----------|------|-------------|
| token     | string | Required. Access token |

### 🔎 Live Search

```http
GET /search/live-search
```

Description:
Retrieve live search results for goals and motivations.

### 👤 User Profile Management

#### 🆕 Create User Profile
```http
POST /user/create-profile
```

Request Body:

{
  "firstname": "John",
  "lastname": "Doe",
  "bio": "A passionate developer."
}

#### 🔍 Retrieve User Profile
```http
GET /user/me
```

#### ✏️ Update User Profile
```http
PUT /user/update-profile
```

Request Body:

{
  "firstname": "John",
  "lastname": "Doe",
  "bio": "An experienced software engineer."
}

### 🚀 Features

- ✅ User Authentication & Authorization
- ✅ Goal Tracking & Management
- ✅ Motivational Quotes Integration
- ✅ QR Code-Based Goal Access
- ✅ Live Search Functionality
- ✅ Secure Token-Based API

### 🛠 Installation

Install dependencies using uv (Python package manager).

```bash
uv pip install -r requirements.txt
```

### 🔑 Environment Variables
generate a secret key using the command below and add it to the .env file
```python
python -c "import secrets; print(secrets.token_hex(32))"
```

Create a .env file and add the following:

```
AUTH_SECRET_KEY=your secret key # secret key to sign the tokens generate it using the command aboce
ALGORITHM=HS256 # algorithm used to sign the token
QR_CODE_URL=http://localhost:5173/private
CORS_ALLOW_ORIGINS=http://localhost:5173 #your cors url
DATABASE_URL=sqlite:///db.sqlite #your database url
```

### 🏃‍♂️ Run Locally

Clone the project

```bash
git clone https://github.com/Mohamed-Rirash/sataplan.git
cd sataplan/backend
```
create venv
```bash
uv venv
```
activate venv
```bash
source .venv/bin/activate
```
add dependencies
```bash
uv sync
```

Start the server

```bash
fastapi dev
```

Open the Swagger UI:

[http://localhost:8000/api/docs](http://localhost:8000/api/docs)

### 🖼 Screenshots
![alt text](image-1.png)
![alt text](image.png)
![alt text](image-2.png)


### 🏗 Tech Stack

- Backend: FastAPI, PostgreSQL
- Authentication: OAuth2 JWT Tokens
- QR Code: QR Code Generator
- frontend: next.js

### 📜 License

MIT

### 🤝 Contact & Support

For any issues, feel free to open an issue on GitHub or contact the maintainer.

## 🔒 Authentication

User authentication is implemented using JWT tokens. Register and login endpoints are available to manage user access.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.

## 📞 Contact

Mohamed Rirash - [Your Email or LinkedIn]

Project Link: [https://github.com/Mohamed-Rirash/sataplan](https://github.com/Mohamed-Rirash/sataplan)
