# TaskBubble 🎨 — Team Task Manager

A clean, upbeat, and fully functional team task management web app built with Flask, PostgreSQL, and Bootstrap 5.

🌐 **Live Demo**: [https://taskmanager-6q51.onrender.com](https://taskmanager-6q51.onrender.com)

---

## ✨ Features

- **Role-Based Access Control** — Admins see and manage everything. Members see only their own projects and tasks.
- **Authentication** — Secure JWT-based login and signup with bcrypt password hashing.
- **Project Management** — Any user can create projects. Admins can view all projects across the platform.
- **Task Management** — Create tasks with title, description, priority, due date, and status. Update or delete anytime.
- **Live Dashboard** — Real stats pulled from the database — total projects, tasks, completion rate, overdue count.
- **Team Members** — Admins can add members to any project by User ID.
- **Responsive UI** — Works on desktop and mobile. Clean white + indigo + rose theme throughout.

---

## 🔐 Test Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@test.com | admin12365 |
| Member | test@test.com | 123456 |

> To get Admin access, sign up with `admin@test.com`. Any other email gets Member role.

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python + Flask + SQLAlchemy |
| Database | PostgreSQL |
| Auth | JWT + bcrypt |
| Frontend | HTML5 + Bootstrap 5 + Vanilla JS |
| Deployment | Render |

---

## 📁 Project Structure
taskmanager/
├── backend/
│   └── app.py          # All routes, models, auth, RBAC
├── indexing.html        # Login / Signup page
├── home.html            # Landing page
├── projects.html        # Projects list
├── project-detail.html  # Task board for a project
├── dashbord.html        # Dashboard (role-aware)
├── Procfile             # Gunicorn start command
├── requirements.txt     # Python dependencies
└── README.md

---

## ⚙️ Run Locally

**1. Clone the repo**
```bash
git clone https://github.com/Priyanshu0-0/taskmanager.git
cd taskmanager
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Set up environment variables**

Create a `.env` file in the root:
DATABASE_URL=sqlite:///taskmanager.db
JWT_SECRET=your-secret-key

**4. Run the app**
```bash
python -m backend.app
```

**5. Open in browser**
http://127.0.0.1:5000

---

## 🔌 API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/signup` | No | Register new user |
| POST | `/api/login` | No | Login and get JWT |
| GET | `/api/projects` | Yes | List projects (role-aware) |
| POST | `/api/projects` | Yes | Create a project |
| POST | `/api/projects/:id/members` | Admin | Add member to project |
| GET | `/api/projects/:id/tasks` | Yes | List tasks in project |
| POST | `/api/projects/:id/tasks` | Yes | Create a task |
| PUT | `/api/tasks/:id` | Yes | Update task status |
| DELETE | `/api/tasks/:id` | Yes | Delete a task |


## 🚀 Deployment

Deployed on **Render** with a PostgreSQL database plugin.

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn --chdir backend app:app --bind 0.0.0.0:$PORT`
- Environment variables set via Render dashboard: `DATABASE_URL`, `JWT_SECRET`


## 👥 Team

Built by **Priyanshu** as a full-stack assignment submission.
