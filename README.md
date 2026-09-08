# 🤖 LangGraph + FastAPI Chatbot

Un backend de agente conversacional construido con **FastAPI**, **LangChain**, **LangGraph** y **Pydantic**. Incluye memoria persistente multi-turno (`MemorySaver`), invocación de herramientas (`@tool`), streaming Server-Sent Events (SSE) y una interfaz web interactiva integrada.

---

## 📁 Estructura del Proyecto

El núcleo del agente está organizado en `app/agent/`:

```
Chatbot/
├── .env                  # Variables de entorno (claves API, ajustes)
├── .env.example          # Plantilla de configuración
├── .gitignore            # Archivos ignorados por Git
├── README.md             # Documentación del proyecto
├── requirements.txt      # Dependencias de Python
├── app/
│   ├── __init__.py
│   ├── config.py         # Configuración con Pydantic Settings
│   ├── main.py           # Servidor FastAPI, CORS y UI interactiva
│   ├── agent/            # Módulo del Agente LangGraph
│   │   ├── __init__.py
│   │   ├── state.py      # Define el estado del grafo (AgentState)
│   │   ├── tools.py      # Herramientas que el agente puede invocar
│   │   ├── graph.py      # Definición de nodos y bordes con LangGraph
│   │   └── main.py       # Ejecución del agente y modo interactivo de consola
│   ├── routers/          # Endpoints de la API FastAPI
│   │   ├── __init__.py
│   │   ├── health.py     # GET /health
│   │   └── chat.py       # POST /chat, POST /chat/stream, GET /chat/history/{thread_id}
│   └── schemas/          # Modelos y esquemas de validación Pydantic
│       ├── __init__.py
│       └── chat.py       # ChatRequest, ChatResponse, HealthResponse
└── tests/
    ├── __init__.py
    └── test_api.py       # Suite de pruebas automatizadas con pytest
```

---

## 🌟 Componentes de `app/agent/`

- **[app/agent/state.py](file:///c:/Users/APRENDIZ%20TARDE/Desktop/Chatbot/app/agent/state.py)**: Define `AgentState` con anotación `add_messages` para preservar el historial de la conversación.
- **[app/agent/tools.py](file:///c:/Users/APRENDIZ%20TARDE/Desktop/Chatbot/app/agent/tools.py)**: Define las herramientas invocables por el agente (calculadora matemática segura y consulta de hora/fecha actual).
- **[app/agent/graph.py](file:///c:/Users/APRENDIZ%20TARDE/Desktop/Chatbot/app/agent/graph.py)**: Ensambla el `StateGraph` de LangGraph, conecta el nodo del agente con las herramientas vía `ToolNode`, enruta con `should_continue` y compila con el checkpointer `MemorySaver`.
- **[app/agent/main.py](file:///c:/Users/APRENDIZ%20TARDE/Desktop/Chatbot/app/agent/main.py)**: Función `run_agent()` y modo consola interactivo (`python -m app.agent.main`).

---

## 🚀 Guía de Inicio Rápido

### 1. Activar el Entorno Virtual

**Windows (PowerShell):**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
source .venv/bin/activate
```

### 2. Configurar Variables de Entorno
Copia `.env.example` a `.env` y configura tu clave de OpenAI:
```env
OPENAI_API_KEY=sk-tu-clave-aqui
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.7
HOST=127.0.0.1
PORT=8000
DEBUG=True
```
*(Nota: Si no configuras la clave de OpenAI inmediatamente, el agente funcionará en **Modo Demostración** indicándote los pasos).*

### 3. Ejecutar el Agente

#### Opción A: Servidor Web FastAPI
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- **Demo Web**: [http://127.0.0.1:8000/demo](http://127.0.0.1:8000/demo)
- **Documentación Swagger**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

#### Opción B: Modo Consola Interactivo
```bash
python -m app.agent.main
```

---

## 📡 Endpoints de la API

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/` | Estado del servicio y enlaces de navegación |
| `GET` | `/health` | Chequeo de salud y estado de OpenAI |
| `GET` | `/demo` | Interfaz web de chat interactiva en el navegador |
| `POST` | `/chat` | Enviar mensaje con memoria de sesión (`thread_id`) |
| `POST` | `/chat/stream` | Streaming de respuestas en tiempo real (Server-Sent Events) |
| `GET` | `/chat/history/{thread_id}` | Historial completo de mensajes para una sesión |
| `GET` | `/docs` | Documentación interactiva Swagger UI |

---

## 🧪 Ejecutar Pruebas Automatizadas

```bash
pytest -v
```
