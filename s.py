from numpy import seterr
import scrapy
import json 
import pandas as pd
import psycopg2
from scrapy.exceptions import CloseSpider


def load_data_from_sql():
    # Connexion à la base
    conn = psycopg2.connect(
        host="localhost",       # ou l'adresse de ton serveur PostgreSQL
        database="LE GROS FICHIER EXCEL",
        user="postgres", 
        password="XXXXXX",     # cacher pour GITHUB 
        port=5432               # port par défaut PostgreSQL
    )
    
    # Requête SQL pour récupérer les colonnes
    query = """
    SELECT siren, nom_entreprise, sous_secteur, secteur_division,trancheeffectifsul
    FROM entreprises_fusion;
    """
    
    # Charger les données dans un DataFrame pandas
    df = pd.read_sql(query, conn)
    conn.close()
    
    sirens_gbl = df["siren"].astype(str).tolist()     # ajouter .astype(str) pour excel  convertir en listes deux colonnes excel pour ensuite alimenter le scraper 
    entreprises_gbl = df["nom_entreprise"].tolist()
    secteur_gbl = df["sous_secteur"].tolist()
    division_gbl = df["secteur_division"].tolist()
    treffectif_gbl = df["trancheeffectifsul"].tolist()

    return sirens_gbl, entreprises_gbl, secteur_gbl, division_gbl, treffectif_gbl 


sirens_gbl, entreprises_gbl, secteur_gbl, division_gbl, treffectif_gbl = load_data_from_sql()

class SSpider(scrapy.Spider):
    name = "s"
    allowed_domains = ["annuaire-entreprises.data.gouv.fr"]
    
    sirens = sirens_gbl    #définir les variables locales du spider à partir des variables globales qui contiennent les informations 
    entreprises = entreprises_gbl
    secteurs = secteur_gbl 
    divisions = division_gbl
    treffectifs = treffectif_gbl

    def start_requests(self):
        # Envoie une requête par siren, avec le nom en meta
        for siren, entreprise, secteur, division, treffectif in zip(self.sirens, self.entreprises, self.secteurs, self.divisions, self.treffectifs):
            url = f"https://data.economie.gouv.fr/api/records/1.0/search/?dataset=ratios_inpi_bce&q=siren%3A{siren}"
            yield scrapy.Request(url, callback=self.parse, meta={'siren': siren, 'entreprise': entreprise, 'secteur': secteur, 'division': division, 'treffectif': treffectif})
    
    def parse(self, response):  
        if response.status == 429:    
            raise CloseSpider('Received 429 Too Many Requests')   # le but c'est d'arreter le spider dès que la réponse 429 est atteinte mais ça marche pas encore 
        siren = response.meta['siren']
        entreprise = response.meta['entreprise']
        secteur = response.meta['secteur']
        division = response.meta['division']
        treffectif = response.meta['treffectif']


        js = json.loads(response.body)
        dat_yr = js.get("records", [])

        dat_yr = [     # filtre d'entreprises 
            i for i in dat_yr
            if i.get("fields", {}).get("date_cloture_exercice")  # année existe
            and len(i.get("fields", {}).get("date_cloture_exercice")) >= 4   #plus de 4 éléments (années)
            and 2016 <= int(i.get("fields", {}).get("date_cloture_exercice")[:4]) <= 2024  # année entre 2015 et 2024
            and i.get("fields", {}).get("chiffre_d_affaires") not in (0, None)  #  supprime les entreprise au CA=0 
        ]

    
        if len(dat_yr) < 3:  # ignorer les entreprises qui ont moins de 3 années de données suite au filtrage 
            return
        
        for i in dat_yr:
            index = i.get("fields", {})

            # Extraire les champs
            yr = index.get("date_cloture_exercice")
            rn = index.get("resultat_net")
            ca = index.get("chiffre_d_affaires")
            mb = index.get("marge_brute")
            ebe = index.get("ebe")
            ebit = index.get("ebit")
            caf_ca = index.get("caf_sur_ca")
            rcai_ca = index.get("resultat_courant_avant_impots_sur_ca")
            c_f_j = index.get("credit_fournisseurs_jours")
            r_s_j = index.get("rotation_des_stocks_jours")
            c_c_j = index.get("credit_clients_jours")
            bfr_CA = index.get("poids_bfr_exploitation_sur_ca")

            # Vérifier si une des valeurs essentielles est manquante (sauf treffectif qui peut rester vide)
            if None in [yr, rn, ca, mb, ebe, ebit, caf_ca, rcai_ca, c_f_j, r_s_j, c_c_j, bfr_CA]:
                continue   #  saute la ligne si au moins une valeur est nulle

            col = {
                'nom_entreprise': entreprise,
                'siren': siren,
                'sous_secteur': secteur,
                'secteur_division': division,
                'Annee': yr[:4],  # année formatée
                'treffectif': treffectif,  # peut rester None
                'RCAI_CA': rcai_ca,
                'RN_CA': round(rn*100/ca, 2) if ca else 0,
                'liqdt': index.get("ratio_de_liquidite"),
                'D_E': index.get("taux_d_endettement"),
                'CAF_CA': caf_ca,
                'MB_CA': round(mb*100/ca, 2) if ca else 0,
                'ebe': ebe,
                'ebit': ebit,
                'ca': ca,
                'rn': rn,
                'EBE_CA': round(ebe*100/ca, 2) if ca else 0,
                'EBIT_CA': round(ebit*100/ca, 2) if ca else 0,
                'CAF': round(caf_ca*ca/100, 2) if caf_ca and ca else 0,
                'c_f_j': c_f_j,
                'r_s_j': r_s_j,
                'c_c_j': c_c_j,
                'BFR_CA': bfr_CA,
            }
            yield col




"""     
 COMMANDE 
    scrapy runspider s.py -o resultats.csv -s FEED_EXPORT_ENCODING=utf-8-sig -s FEED_EXPORT_FIELDS_DELIMITER=";" -s JOBDIR=crawls/save1

"""

