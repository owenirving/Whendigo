# Whendigo

**Whendigo** is a real-time, group scheduling web app inspired by [When2Meet](https://when2meet.com), built to make group coordination fast, easy, and intuitive.

> Built with **Flask**, **MySQL**, **JavaScript**, **Socket.IO**, **Docker**, and **Jinja**.

---

## Features

- **Secure user authentication**  
  Robust login and registration system with encrypted details using scrypt.
  
- **Event creation & invitation**  
  Users can create events, set a date and time range, and invite others via email, even if they haven't signed up yet.
  
- **Interactive availability grid**  
  Intuitive click-and-drag grid UI for users to input their availability.
  
- **Heatmap visualization**  
  Real-time, color-based visualization of full group availability.
  
- **Best time calculation**  
  Automatically calculates and displays the most optimal meeting time based on the time when the most users are free.
  
- **Live synchronization**  
  Built with Socket.IO for seamless real-time updates across all users.

---

## Tech Stack

| Layer | Tool/Framework |
|-------|----------------|
| **frontend** | HTML, CSS, JavaScript, Jinja |
| **Backend** | Flask, Socket.IO, Python-dotenv, hashlib |
| **Database** | MySQL |
| **Deployment** | Docker, Google Cloud |

---

## Local Development
```bash
# Clone the repository
git clone https://github.com/owenirving/whendigo.git
cd whendigo

# Add your .env file and configure DB_SALT, SECRET_KEY, and ENCRYPTION_KEY

# Build and run container
docker-compose up --build
```

## Future Improvements
- Email notifications
- Admin dashboard for analytics

