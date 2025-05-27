# 🚆 En_train_ame

**En_train_ame** es una aplicación web basada en aprendizaje automático, desarrollada con 🐍 **FastAPI** y desplegada en contenedores 🐳 **Docker**. Utiliza una base de datos **SQLite** para gestionar usuarios y un modelo de lenguaje preentrenado de 🤗 **Hugging Face** para tareas de NLP.

---

## 🧠 Tecnologías utilizadas

- 🚀 [FastAPI](https://fastapi.tiangolo.com/): framework web moderno y rápido.
- 🐍 Python 3.10+
- 🐳 Docker & Docker Compose
- 🗃️ SQLite3
- 🤗 Transformers (modelo preentrenado desde Hugging Face)
- 🌐 HTML/CSS/JS (para el frontend embebido)
- 🧪 Uvicorn (como servidor ASGI)

---

## 📁 Estructura del proyecto

```
En_train_ame/
│
├── app/
│ ├── main.py # Código principal de la API
│ ├── model/ # Carga del modelo de Hugging Face
│ └── templates/ # Archivos HTML
│
├── usuarios.db # Base de datos SQLite
├── Dockerfile # Imagen para Docker
├── docker-compose.yml # Orquestación de servicios
├── requirements.txt # Dependencias de Python
```


---

## 🔥 Endpoints disponibles

Estos endpoints se definen en `main.py` usando FastAPI:

| Método | Endpoint             | Descripción                                |
|--------|----------------------|--------------------------------------------|
| GET    | `/`                  | Página principal (formulario HTML)         |
| GET    | `/login`             | Formulario de inicio de sesión (HTML)      |
| POST   | `/login`             | Inicia sesión de usuario                   |
| GET    | `/register`          | Formulario de nuevo usuario (HTML)         |
| POST   | `/register`          | Registra un nuevo usuario                  |
| GET    | `/dashboard`         | Página de selección (HTML)                 |
| GET    | `/modelo`            | Página de chat (HTML)                      | 
| POST   | `/modelo/generate`   | Crea ua respuesta para la consulta         |
| GET    | `/ejercicios`        | Página para llevar registro de ejers()     |
| POST   | `/ejercicios/create` | Crea un nuevo registro y lo añade a db     |
| POST   |`/ejercicios/add_data`| Añade valores al registro y a la db        |
| GET    |`/ejercicios/{}/data` | Devuelve un json del ejercicio especificado|
| POST   |`/ejercicios/delete`  | Borra un registro existente, incluyendo db |




---

## 🛠️ Cómo usarlo

### 1️⃣ Clona el repositorio

```bash
git clone https://github.com/PlazzaA/En_train_ame.git
cd En_train_ame
```

### 2️⃣ (Opcional) Levanta el contenedor de docker
```
docker-compose up --build
```

### 3️⃣ Activa la app (Mediante docker o mediante uvicorn)
```
uvicorn app.main:app --reload --http h11
```

### 4️⃣ Accede a http://localhost:8000 en tu navegador favorito


