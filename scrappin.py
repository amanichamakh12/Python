from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains 
from datetime import datetime, timedelta

import pandas as pd
import logging
import re
options = Options()
options.add_argument('--headless')  

service = Service("./chromedriver.exe")

driver = webdriver.Chrome(service=service, options=options)

logging.basicConfig(level=logging.INFO)


driver.get("https://www.tayara.tn/ads/c/Immobilier/?page=1")

wait = WebDriverWait(driver, 10)
annonces_elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//*[@id='__next']/div[3]/main/div[3]/div[3]/div[2]/div/article")))

annonces_data = []

def calculer_date(dure_publication):
    maintenant = datetime.now()  # Date actuelle
    match = re.search(r"(\d+)\s*(jour|heure|minute|day|hour|minute)s?", duree, re.IGNORECASE)
    
    if not match:
        return maintenant.strftime('%Y-%m-%d %H:%M:%S')  # Retourne la date actuelle si format inconnu
    
    nombre = int(match.group(1))  # Extrait le nombre
    unite = match.group(2).lower()  # Convertir en minuscule pour éviter les erreurs

    # Déterminer la durée à soustraire
    if "jour" in unite or "day" in unite:
        date_publication = maintenant - timedelta(days=nombre)
    elif "heure" in unite or "hour" in unite:
        date_publication = maintenant - timedelta(hours=nombre)
    elif "minute" in unite:
        date_publication = maintenant - timedelta(minutes=nombre)
    else:
        date_publication = maintenant  # Valeur par défaut

    return date_publication.strftime('%Y-%m-%d %H:%M:%S')  # Format lisible


for annonce in annonces_elements:

        lien = annonce.find_element(By.XPATH, ".//a").get_attribute("href")
        
        driver.execute_script("window.open(arguments[0]);", lien)
        driver.switch_to.window(driver.window_handles[1])  
        
        wait.until(EC.presence_of_element_located((By.XPATH, "//h1")))  
        
        # Extraire les informations de la page de détails
        titre = driver.find_element(By.XPATH, "//h1").text
        prix = driver.find_element(By.XPATH, "//data").text if driver.find_elements(By.XPATH, "//data") else "N/A"
        type_bien = driver.find_element(By.XPATH, "//div[contains(@class, 'flex')]//span[contains(text(), 'Type de transaction')]/following-sibling::span").text if driver.find_elements(By.XPATH, "//div[contains(@class, 'flex')]//span[contains(text(), 'Type de transaction')]/following-sibling::span") else "N/A"
        loc_details =driver.find_element(By.XPATH, "//div[contains(@class, 'flex items-center')]//span[contains(text(), ',')]").text if driver.find_elements(By.XPATH, "//div[contains(@class, 'flex items-center')]//span[contains(text(), ',')]") else "N/A"
        ville, duree = [x.strip() for x in loc_details.split(',')]
        superficie = driver.find_element(By.XPATH, "//div[contains(@class, 'flex')]//span[contains(text(), 'Superficie')]/following-sibling::span").text if driver.find_elements(By.XPATH, "//div[contains(@class, 'flex')]//span[contains(text(), 'Superficie')]/following-sibling::span") else "N/A"
        description = driver.find_element(By.XPATH, "//p[contains(@class, 'whitespace-pre-line')]").text
        afficher_numero=driver.find_element(By.XPATH, "//button[contains(., 'Afficher le numéro')] | //span[contains(., 'Afficher le numéro')]").click()
        numero = WebDriverWait(driver, 10).until(
    EC.visibility_of_element_located((By.XPATH, '//a[starts-with(@href, "tel:")]'))
).text
        date_exacte=calculer_date(duree)
       
    
        
        # Ajouter les informations de l'annonce à la liste
        annonces_data.append({
            "Titre": titre,
            "Prix": prix,
            "Type de bien": type_bien,
            "Localisation": ville,
            "Superficie": superficie,
            "Description": description,
            "Contact": numero,
            "Date de publication": date_exacte,
            "Lien": lien
        })

        logging.info(f"Annonce extraite:  {"titre:"+titre} ")
        logging.info(f"Annonce extraite:  {"prix:"+prix} ")
        logging.info(f"Annonce extraite:  {"type:"+type_bien}")
        logging.info(f"Annonce extraite:  {"localisation:"+ville}")
        logging.info(f"Annonce extraite:  {"superficie:"+superficie}")
        logging.info(f"Annonce extraite:  {"description:"+description}")
        logging.info(f"Annonce extraite:  {"contact:"+numero}")
        logging.info(f"Annonce extraite:  {"date de publication:"+date_exacte}")
        logging.info(f"Annonce extraite:  {"lien:"+lien}")
        logging.info(f" ******")

        driver.close()
        driver.switch_to.window(driver.window_handles[0])

   
df = pd.DataFrame(annonces_data)

df.to_excel("C:/Users/user/Downloads/Python/annonces.xlsx", index=False, engine='openpyxl')
logging.info("Données enregistrées en fichier Excel.")

driver.quit()