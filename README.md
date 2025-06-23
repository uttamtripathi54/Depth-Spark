# 🌊 Depth Spark - 2D to 3D Image Converter 🔁

![GitHub last commit](https://img.shields.io/github/last-commit/uttamtripathi54/depth-spark?color=cyan)
![GitHub repo size](https://img.shields.io/github/repo-size/uttamtripathi54/depth-spark?color=teal)
![Python](https://img.shields.io/badge/Built%20With-Python-blue?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)

> **Depth Spark** is a free, web-based app that converts 2D images into **interactive 3D models** using AI. Designed with accessibility and simplicity in mind, this tool empowers creators, educators, and businesses to embrace 3D technology—without the steep learning curve.

---

## 🌟 Key Features

- 🖼️ Upload or paste a link to your 2D image (JPG/PNG/GIF)
- ⚙️ AI-powered 3D model generation
- 🔁 Export to `.GLB` format for real-time 3D viewing
- 🕹️ Built-in 3D model viewer (rotate, zoom, drag)
- 🚀 Fast and lightweight web app powered by **Flask**
- 🔐 Secure user authentication system
- 💡 Designed for **eCommerce**, **Education**, and **Marketing**

---

## 🧠 How It Works

```
📤 Upload Image  ─▶  🧠 AI-based Converter  ─▶  🧱 3D Model Generator  ─▶  🌐 Web Viewer + Download
```

---

## 🖥️ Demo

🌐 **Live Preview** (Coming Soon...)

> 👇 Here’s a glimpse of the user interface:

![Depth Spark UI Sample](https://your-image-link.com/sample-ui.gif)

---

## 🧩 Modules

| Module                     | Description                                                                 |
|---------------------------|-----------------------------------------------------------------------------|
| `UI Module`               | Clean, modern web interface for image upload and preview                    |
| `Image Handler`           | Validates input files and URLs                                              |
| `AI-Based Model Generator`| Converts 2D to 3D using integrated AI API (Falcon AI)                       |
| `3D Model Exporter`       | Saves models in `.glb` format                                               |
| `3D Viewer`               | Interactive viewer with pan, zoom, and rotate features                      |
| `Progress Tracker`        | Queue and progress status for batch conversions                             |
| `Error Handler`           | Friendly error messages and logs                                            |
| `Auth Module`             | User signup/login with hashed credentials                                   |
| `GLTF Viewer`             | Web renderer for real-time 3D display                                       |
| `API Integration`         | Connects with Falcon AI for conversion logic                                |

---

## 🛠️ Tech Stack

- **Frontend**: HTML, CSS, JavaScript, Anime Js
- **Backend**: Python, Flask
- **AI Integration**: Falcon AI API
- **3D Rendering**: Google's Model Viewer / GLTF Viewer
- **Database**: SQLAlchemy
- **Authentication**: Flask-Login

---

## 📂 Project Structure

```
depth-spark/
│
├── static/                  # CSS, JS, icons, Exported 3D models
├── templates/               # HTML templates
├── instance/                 # User Data, Contact Form Data
├── app.py                   # Main Flask app
├── model.py                  # Backend code, API Calling
└── requirements.txt         # Python dependencies
```

---

## 🚀 Getting Started

```bash
git clone https://github.com/uttamtripathi54/Depth-Spark.git
cd depth-spark
pip install -r requirements.txt
python app.py
```

> Open your browser and go to: `http://127.0.0.1:5000`

---

## 🙌 Team

👨‍💻 **Uttam Tripathi**  
👩‍💻 **Parul Sharma**

Final-year BCA students specializing in Data Science & AI.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 💬 Feedback

Have suggestions or ideas? Feel free to open an [Issue](https://github.com/uttamtripathi54/depth-spark/issues) or reach out on [LinkedIn](https://www.linkedin.com/in/uttam-tripathi-8421b2290)!

---

> _"Making 3D accessible to everyone—one click at a time."_ 🌍
