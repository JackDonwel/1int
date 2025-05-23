
# 🚀 Wakili Stamp Registration System API

This is the backend REST API built using Django and Django REST Framework. It manages stamp registration and verification.

---

## 📦 Base URL
```
http://tls.com/api/
```

---

## 📚 Endpoints Overview

### 🔐 Authentication
| Method | Endpoint            | Description              |
|--------|---------------------|--------------------------|
| POST   | `/auth/login/`      | Obtain auth token        |
| POST   | `/auth/register/`   | Register new user        |
| POST   | `/auth/logout/`     | Logout user              |

### 📝 Stamp Endpoints
| Method | Endpoint               | Description                    |
|--------|------------------------|--------------------------------|
| GET    | `/stamps/`             | List all stamps                |
| POST   | `/stamps/`             | Create new stamp               |
| GET    | `/stamps/<id>/`        | Get stamp by ID                |
| PUT    | `/stamps/<id>/`        | Update stamp                   |
| DELETE | `/stamps/<id>/`        | Delete stamp                   |

*(Add other endpoints as needed)*

---

## 🔑 Auth Instructions

This API uses **Token-based Authentication**.

- After login, include the token in your headers:
```http
Authorization: Token your_token_here
```

---

## 🔁 Sample Request (Using `curl`)

```bash
curl -X POST http://127.0.0.1:8000/auth/login/ \
-H "Content-Type: application/json" \
-d '{"username": "admin", "password": "password123"}'
```

---

## 🛠 Setup & Run Locally

```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo

# Create and activate virtual environment make sure it's outside the project eg my-project/1int-main
python3 -m venv env
source env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run server
python manage.py runserver
```

---

## 📫 Contact

For help or suggestions, reach out to:

- **Developer**: Jack Tuhoye Bombo
- **Email**: jdonwel@proton.me
- **LinkedIn**: [jack-tuhoye](https://linkedin.com/in/jack-tuhoye-366017307)
