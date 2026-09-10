# 🛍️ E-Commerce Chatbot

Un asistente conversacional de **tienda en línea** construido con **FastAPI**, **LangChain**, **LangGraph** y **Pydantic**. Permite a los clientes buscar productos, ver el catálogo, gestionar su carrito de compras, realizar pedidos y obtener respuestas sobre políticas de envío, devoluciones y atención al cliente mediante un agente con memoria multi-turno y herramientas invocables.

---

## 📁 Estructura del Proyecto

```
Chatbot/
├── .env                        # Variables de entorno (claves API, ajustes)
├── .env.example                # Plantilla de configuración
├── .gitignore                  # Archivos ignorados por Git
├── README.md                   # Documentación del proyecto
├── requirements.txt            # Dependencias de Python
├── app/
│   ├── __init__.py
│   ├── config.py               # Configuración con Pydantic Settings
│   ├── main.py                 # Servidor FastAPI, CORS y UI interactiva
│   ├── data/                   # Datos e-commerce
│   │   ├── __init__.py
│   │   ├── products.py         # Catálogo de productos simulado (24 productos)
│   │   └── knowledge_base.py   # Base de conocimientos: políticas y preguntas frecuentes
│   ├── agent/                  # Módulo del Agente LangGraph
│   │   ├── __init__.py
│   │   ├── state.py            # Define el estado del grafo (AgentState)
│   │   ├── tools.py            # Herramientas e-commerce que el agente puede invocar
│   │   ├── graph.py            # Definición de nodos y bordes con LangGraph
│   │   └── main.py             # Ejecución del agente y modo interactivo de consola
│   ├── routers/                # Endpoints de la API FastAPI
│   │   ├── __init__.py
│   │   ├── health.py           # GET /health
│   │   └── chat.py             # POST /chat, POST /chat/stream, GET /chat/history/{thread_id}
│   └── schemas/                # Modelos y esquemas de validación Pydantic
│       ├── __init__.py
│       └── chat.py             # ChatRequest, ChatResponse, HealthResponse
└── tests/
    ├── __init__.py
    └── test_api.py             # Suite de pruebas automatizadas con pytest
```

---

## 🛒 Herramientas E-Commerce

El agente dispone de un conjunto de herramientas para gestionar la experiencia de compra completa:

| Herramienta | Descripción |
|---|---|
| `search_catalog` | Busca productos por nombre, descripción o categoría. |
| `filter_products` | Filtra el catálogo por categoría y/o rango de precio. |
| `get_product_details` | Muestra la información completa de un producto por su ID. |
| `add_to_cart` | Añade productos al carrito de la sesión del usuario. |
| `view_cart` | Muestra el contenido actual del carrito y el total. |
| `remove_from_cart` | Elimina un producto del carrito por su ID. |
| `place_order` | Realiza el pedido con los productos del carrito y genera un ID de orden (`ORD-XXXX`). |
| `get_order_status` | Consulta el estado de un pedido existente. |
| `search_knowledge` | RAG sobre la base de conocimientos: envíos, devoluciones, pagos, soporte y promociones. |

### Catálogo de Productos

- **5 categorías**: Electrónica, Ropa, Hogar y Cocina, Deportes y Libros.
- **24 productos** simulados con `id`, `name`, `description`, `category`, `price` y `stock`.
- El carrito y los pedidos se almacenan **en memoria**, keyed por `thread_id` (sesión del usuario).

### Módulos de Datos

- **[app/data/products.py](file:///c:/Users/APRENDIZ%20TARDE/Desktop/Chatbot/app/data/products.py)**: Catálogo de productos y funciones `search_products()` / `get_product_by_id()`.
- **[app/data/knowledge_base.py](file:///c:/Users/APRENDIZ%20TARDE/Desktop/Chatbot/app/data/knowledge_base.py)**: Base de conocimientos con políticas de envío, devoluciones, pagos, pedidos, cuentas, contacto, productos y promociones.

---

## 🌟 Componentes de `app/agent/`

- **[app/agent/state.py](file:///c:/Users/APRENDIZ%20TARDE/Desktop/Chatbot/app/agent/state.py)**: Define `AgentState` con anotación `add_messages` para preservar el historial de la conversación.
- **[app/agent/tools.py](file:///c:/Users/APRENDIZ%20TARDE/Desktop/Chatbot/app/agent/tools.py)**: Define todas las herramientas e-commerce invocables por el agente.
- **[app/agent/graph.py](file:///c:/Users/APRENDIZ%20TARDE/Desktop/Chatbot/app/agent/graph.py)**: Ensambla el `StateGraph` de LangGraph, conecta el nodo del agente con las herramientas vía `ToolNode`, enruta con `should_continue` y compila con el checkpointer `MemorySaver`.
- **[app/agent/main.py](file:///c:/Users/APRENDIZ%20TARDE/Desktop/Chatbot/app/agent/main.py)**: Función `run_agent()` y modo consola interactivo (`python -m app.agent.main`).

---

## 🚀 Guía de Inicio Rápido

### 1. Activar el Entorno Virtual

##crear entoro
python -m venv .venv
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
*(Nota: Si no configuras la clave de OpenAI inmediatamente, el agente funcionará en **Modo Demostración**, mostrando una vista previa de las herramientas e-commerce).*

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
| `DELETE` | `/chat/history/{thread_id}` | Reiniciar el historial de una sesión |
| `GET` | `/chat/tools` | Listar todas las herramientas registradas del agente |
| `GET` | `/chat/graph` | Diagrama Mermaid del grafo de LangGraph |
| `GET` | `/docs` | Documentación interactiva Swagger UI |

---

## 🧪 Ejecutar Pruebas Automatizadas

```bash
pytest -v
```

---

## 🧩 Ejemplos de Uso

Prueba el asistente desde la UI (`/demo`) o la consola con mensajes como:

- "Muéstrame productos de electrónica"
- "Busca audífonos en el catálogo"
- "¿Cuál es el detalle del producto 3?"
- "Añade el producto 6 al carrito, cantidad 2"
- "Ver mi carrito de compras"
- "Quiero hacer el pedido"
- "¿Cuáles son sus políticas de devolución?"
- "¿Cuánto tarda el envío?"