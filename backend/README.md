# 🏆 Goal Management API

A powerful API for managing goals, tracking progress, and staying motivated with QR code-based access and user authentication. Perfect for productivity apps and personal development tools.

---

## 🎥 Demo

📌 *Demo link or GIF placeholder here*

---

## 📖 API Reference

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
