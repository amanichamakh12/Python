# Étape 1 : Construction de l'environnement
FROM python:3.9-slim as builder

WORKDIR /app

# Copie des fichiers nécessaires
COPY requirements.txt ./
COPY api/fastApi.py ./
COPY app/dashApp.py ./
COPY . .

# Installation des dépendances
RUN pip install --user --no-cache-dir -r requirements.txt


# Installation explicite d'uvicorn
RUN pip install --no-cache-dir uvicorn

# Copie et installation des autres dépendances

RUN pip install --no-cache-dir -r requirements.txt


# Assure que les scripts Python sont dans le PATH
ENV PATH=/root/.local/bin:$PATH

# Ports exposés (les mappings réels sont dans docker-compose)
EXPOSE 8000 8060

# Commande par défaut (sera écrasée par docker-compose)
CMD ["python", "--version"]