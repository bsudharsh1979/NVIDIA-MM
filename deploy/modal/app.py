import modal

image = modal.Image.debian_slim(python_version="3.12").pip_install_from_requirements("services/api/requirements.txt")
app = modal.App("modality-twin-academy-api")


@app.function(image=image, timeout=60 * 30)
@modal.asgi_app()
def fastapi_app():
    import sys
    from pathlib import Path

    sys.path.append(str(Path("/root")))
    from app.main import app as inner

    return inner
