from fastapi import FastAPI, Request, Form, HTTPException, Depends, Cookie
from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
    PlainTextResponse,
    JSONResponse,
)
from transformers import AutoModelForCausalLM, AutoTokenizer
from fastapi.templating import Jinja2Templates
from pathlib import Path
import logging
import torch
from typing import List, Dict, Optional
from .basedatos import (
    register_user,
    verify_user,
    create_ejercicio_table,
    get_ejercicios_for_user,
    add_ejercicio_data,
    get_ejercicio_data,
    delete_ejercicio,  
)
from datetime import datetime

app = FastAPI()

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

model = None
tokenizer = None
MODEL_NAME = "R2E-Gym/R2EGym-14B-Agent"

async def get_current_user_id(
    request: Request, user_id: Optional[str] = Cookie(default=None)
) -> Optional[int]:
    if user_id is None:
        return None
    return int(user_id)

def load_model():
    global model, tokenizer
    if model is None:
        logger.info(f"Cargando modelo: {MODEL_NAME}...")
        try:
            tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
            model = AutoModelForCausalLM.from_pretrained(
                MODEL_NAME,
                device_map="auto",
                torch_dtype=torch.bfloat16,
                low_cpu_mem_usage=True,
            )
            tokenizer.pad_token = tokenizer.eos_token
            logger.info(f"Modelo {MODEL_NAME} cargado exitosamente")

            if torch.cuda.is_available():
                device_name = torch.cuda.get_device_name(
                    0
                )  
                logger.info(f"GPU disponible: {device_name}")
            else:
                logger.warning("No se detectó GPU. Se usará la CPU.")

        except Exception as e:
            logger.error(f"Error cargando modelo {MODEL_NAME}: {str(e)}")
            raise


@app.middleware("http")
async def validate_requests(request: Request, call_next):
    try:
        if "host" not in request.headers:
            return PlainTextResponse("Missing Host header", status_code=400)
        return await call_next(request)
    except Exception as e:
        logger.error(f"Invalid request: {str(e)}")
        return PlainTextResponse("Bad Request", status_code=400)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def show_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def handle_login(
    request: Request, email: str = Form(...), password: str = Form(...)
):
    try:
        user_id, is_valid = verify_user(
            email, password
        )  
        if not is_valid:
            return templates.TemplateResponse(
                "login.html", {"request": request, "error": "Credenciales incorrectas"}
            )
        response = RedirectResponse(url="/dashboard", status_code=303)
        response.set_cookie(
            key="user_id", value=str(user_id)
        )  
        return response
    except Exception as e:
        logger.error(f"Error en login: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@app.get("/register", response_class=HTMLResponse)
async def show_register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register")
async def handle_register(
    request: Request,
    nombre: str = Form(...),
    apellidos: str = Form(...),
    altura: int = Form(...),
    peso: float = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
):
    try:
        if password != password_confirm:
            return templates.TemplateResponse(
                "register.html",
                {"request": request, "error": "Las contraseñas no coinciden"},
            )

        if not register_user(nombre, apellidos, altura, peso, email, password):
            return templates.TemplateResponse(
                "register.html",
                {"request": request, "error": "El correo ya está registrado"},
            )

        return RedirectResponse(url="/login", status_code=303)
    except Exception as e:
        logger.error(f"Error en registro: {str(e)}")
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Error en el registro. Intente nuevamente."},
        )


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request, user_id: Optional[int] = Depends(get_current_user_id)
):
    if user_id is None:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/modelo", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})


@app.post("/modelo/generate")
async def generate_response(user_input: str = Form(...)):
    try:
        load_model()
        if tokenizer is None or model is None:
            return {"response": "El modelo no se ha cargado correctamente."}

        inputs = tokenizer(user_input, return_tensors="pt", padding=True, truncation=True).to(model.device)
        input_ids = inputs.input_ids
        attention_mask = inputs.attention_mask

        with torch.no_grad():
            outputs = model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                max_new_tokens=200,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )

        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        if user_input in response:
            response = response.replace(user_input, "").strip()

        print(f"Raw response from model: {response}")  
        return {"response": response}
    except Exception as e:
        logger.error(f"Error generando respuesta: {str(e)}")
        return {"response": "Lo siento, ocurrió un error. Por favor intenta nuevamente."}


@app.get("/ejercicios", response_class=HTMLResponse)
async def ejercicios_page(
    request: Request, user_id: Optional[int] = Depends(get_current_user_id)
):
    if user_id is None:
        return RedirectResponse(url="/login", status_code=303)
    ejercicios = get_ejercicios_for_user(user_id)
    return templates.TemplateResponse(
        "ejercicios.html",
        {"request": request, "ejercicios": ejercicios, "user_id": user_id},
    )


@app.post("/ejercicios/create")
async def create_ejercicio(
    request: Request,
    nombre_ejercicio: str = Form(...),
    user_id: Optional[int] = Depends(get_current_user_id),
):
    if user_id is None:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    if create_ejercicio_table(user_id, nombre_ejercicio):
        return RedirectResponse(url="/ejercicios", status_code=303)
    else:
        raise HTTPException(status_code=500, detail="Error al crear el ejercicio")


@app.post("/ejercicios/add_data")
async def add_data_to_ejercicio(
    request: Request,
    nombre_ejercicio: str = Form(...),
    series: int = Form(...),
    repeticiones: int = Form(...),
    peso_maximo: float = Form(...),
    user_id: Optional[int] = Depends(get_current_user_id),
):
    if user_id is None:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    fecha = datetime.now().strftime("%Y-%m-%d")
    if add_ejercicio_data(
        user_id, nombre_ejercicio, series, repeticiones, peso_maximo, fecha
    ):
        return JSONResponse({"message": "Datos añadidos correctamente"}, status_code=200)
    else:
        raise HTTPException(status_code=500, detail="Error al añadir los datos")


@app.get("/ejercicios/{nombre_ejercicio}/data", response_class=JSONResponse)
async def get_data_for_ejercicio(
    request: Request,
    nombre_ejercicio: str,
    user_id: Optional[int] = Depends(get_current_user_id),
):
    if user_id is None:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    data = get_ejercicio_data(user_id, nombre_ejercicio)
    return JSONResponse(data)


@app.post("/ejercicios/delete")
async def delete_ejercicio_route(
    request: Request,
    nombre_ejercicio: str = Form(...),
    user_id: Optional[int] = Depends(get_current_user_id),
):
    if user_id is None:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    if delete_ejercicio(user_id, nombre_ejercicio):
        return JSONResponse({"message": "Ejercicio eliminado correctamente"}, status_code=200)
    else:
        raise HTTPException(status_code=500, detail="Error al eliminar el ejercicio")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        server_header=False,
        date_header=False,
        http="h11",
        timeout_keep_alive=60,
        log_level="info",
    )