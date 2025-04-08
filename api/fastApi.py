from fastapi import FastAPI
import pandas as pd
#from scrappin import scrap_data 
import importlib.util
import subprocess
import os
from fastapi.middleware.cors import CORSMiddleware
import json

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app = FastAPI()
Annoncesfile_in_docker = "/app/annonces.json"#pour tester dans docker
jsonFile="C:/Users/user/Downloads/Python/annonces.json"#pour tester localement

@app.get("/AllAnnonces")
async def root():
    try:
        df = pd.read_json(Annoncesfile_in_docker)
        #df=pd.read_json(jsonFile)#pour tester localement
        df = df.fillna("")

        data = df.to_dict(orient="records")

        return {"data": data}
    except Exception as e:
        return {"error": str(e)}
    
#@app.post("/scrape")
#async def scrape():
 #   try:
  #      # Exécuter le script de scraping via subprocess
   #     result = subprocess.run(["python", "C:/Users/user/Downloads/Python/api/scrappin.py"], capture_output=True, text=True)
    #    
       # Vérifier si l'exécution du script s'est bien déroulée
      #  if result.returncode == 0:
        #    return {"message": "Scraping terminé avec succès"}
        #else:
        #    return {"error": f"Erreur lors de l'exécution du script : {result.stderr}"}
    #except Exception as e:
     #   return {"error": f"Une erreur s'est produite : {str(e)}"}