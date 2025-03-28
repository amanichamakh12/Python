from fastapi import FastAPI
import pandas as pd
#from scrappin import scrap_data 
import importlib.util
import subprocess


app = FastAPI()
EXCEL_FILE_PATH = "C:/Users/user/webScrapping/python/annonces.xlsx"

@app.get("/AllAnnonces")
async def root():
    try:
        df = pd.read_excel(EXCEL_FILE_PATH)
        df = df.fillna("")

        data = df.to_dict(orient="records")

        return {"data": data}
    except Exception as e:
        return {"error": str(e)}
    
@app.post("/scrape")
async def scrape():
    try:
        # Exécuter le script de scraping via subprocess
        result = subprocess.run(["python", "C:/Users/user/webScrapping/scrappin.py"], capture_output=True, text=True)
        
        # Vérifier si l'exécution du script s'est bien déroulée
        if result.returncode == 0:
            return {"message": "Scraping terminé avec succès"}
        else:
            return {"error": f"Erreur lors de l'exécution du script : {result.stderr}"}
    except Exception as e:
        return {"error": f"Une erreur s'est produite : {str(e)}"}