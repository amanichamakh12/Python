from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import logging

# Configurer ChromeOptions
options = Options()
options.add_argument('--headless')  # Si tu veux exécuter sans ouvrir le navigateur

service = Service("./chromedriver.exe")

driver = webdriver.Chrome(service=service, options=options)
print("je teste la push")

logging.basicConfig(level=logging.INFO)


driver.get("https://www.tayara.tn/ads/c/Immobilier/?page=1")

wait = WebDriverWait(driver, 10)
annonces_elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//*[@id='__next']/div[3]/main/div[3]/div[3]/div[2]/div/article")))

annonces_data = []

for annonce in annonces_elements:
    try:
        # Extraire le lien de l'annonce
        lien = annonce.find_element(By.XPATH, ".//a").get_attribute("href")
        
        # Ouvrir le lien dans un nouvel onglet
        driver.execute_script("window.open(arguments[0]);", lien)
        driver.switch_to.window(driver.window_handles[1])  # Passer à l'onglet de la page de détails
        
        # Attendre que la page de détails soit chargée
        wait.until(EC.presence_of_element_located((By.XPATH, "//h1")))  # Attendre que le titre soit chargé
        
        # Extraire les informations de la page de détails
        titre = driver.find_element(By.XPATH, "//h1").text
        prix = driver.find_element(By.XPATH, "//data").text if driver.find_elements(By.XPATH, "//data") else "N/A"
        
        # Type de bien
        type_bien = driver.find_element(By.XPATH, "//div[contains(@class, 'flex')]//span[contains(text(), 'Type de transaction')]/following-sibling::span").text if driver.find_elements(By.XPATH, "//div[contains(@class, 'flex')]//span[contains(text(), 'Type de transaction')]/following-sibling::span") else "N/A"
        # Localisation
        localisation = driver.find_element(By.XPATH, "//span[contains(@class, 'location')]").text if driver.find_elements(By.XPATH, "//span[contains(@class, 'location')]") else "N/A"
        
        # Superficie
        superficie = driver.find_element(By.XPATH, "//div[contains(@class, 'flex')]//span[contains(text(), 'Superficie')]/following-sibling::span").text if driver.find_elements(By.XPATH, "//div[contains(@class, 'flex')]//span[contains(text(), 'Superficie')]/following-sibling::span") else "N/A"
        # Description
        description = driver.find_element(By.XPATH, "//p[contains(@class, 'text-gray-700 font-semibold text-xl mb-4')]//p").text if driver.find_elements(By.XPATH, "//p[contains(@class, 'text-gray-700 font-semibold text-xl mb-4')]//p") else "N/A"        
        # Contact
        contact = driver.find_element(By.XPATH, "//a[contains(@class, 'text-gray-600')]").text if driver.find_elements(By.XPATH, "//a[contains(@class, 'text-gray-600')]") else "N/A"
        
        # Date de publication
        date_publication = driver.find_element(By.XPATH, "//span[contains(@class, 'date')]").text if driver.find_elements(By.XPATH, "//span[contains(@class, 'date')]") else "N/A"
        
        # Ajouter les informations de l'annonce à la liste
        annonces_data.append({
            "Titre": titre,
            "Prix": prix,
            "Type de bien": type_bien,
            "Localisation": localisation,
            "Superficie": superficie,
            "Description": description,
            "Contact": contact,
            "Date de publication": date_publication,
            "Lien": lien
        })

        logging.info(f"Annonce extraite:  {"titre:"+titre} ")

        logging.info(f"Annonce extraite:  {"prix:"+prix} ")
        logging.info(f"Annonce extraite:  {"type:"+type_bien}")
        logging.info(f"Annonce extraite:  {"localisation:"+localisation}")
        logging.info(f"Annonce extraite:  {"superficie:"+superficie}")
        logging.info(f"Annonce extraite:  {"description:"+description}")
        logging.info(f"Annonce extraite:  {"contact:"+contact}")
        logging.info(f"Annonce extraite:  {"date de publication:"+date_publication}")
        logging.info(f"Annonce extraite:  {"lien:"+lien}")
        logging.info(f" ******")

        driver.close()
        driver.switch_to.window(driver.window_handles[0])

    except Exception as e:
        logging.error(f"Erreur lors de l'extraction des données d'une annonce: {e}")
        if len(driver.window_handles) > 1:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])

df = pd.DataFrame(annonces_data)

df.to_excel("annonces.xlsx", index=False, engine='openpyxl')
logging.info("Données enregistrées en fichier Excel.")

driver.quit()