/*
DROP TABLE IF EXISTS entreprises;
CREATE TABLE entreprises(
    siren TEXT PRIMARY KEY,
    denominationUniteLegale TEXT,
    activitePrincipaleUniteLegale TEXT,
    trancheEffectifsUniteLegale TEXT,
    etatAdministratifUniteLegale TEXT,
    economieSocialeSolidaireUniteLegale TEXT,
    categorieEntreprise TEXT,
    categorieJuridiqueUniteLegale TEXT,
    nomenclatureActivitePrincipaleUniteLegale TEXT
);


COPY entreprises(
    siren,
    denominationUniteLegale,
    activitePrincipaleUniteLegale,
    trancheEffectifsUniteLegale,
    etatAdministratifUniteLegale,
    economieSocialeSolidaireUniteLegale,
    categorieEntreprise,
    categorieJuridiqueUniteLegale,
    nomenclatureActivitePrincipaleUniteLegale
)

FROM 'C:\Program Files\PostgreSQL\17\data\StockUniteLegale_4colonnes.csv'
DELIMITER ','
CSV HEADER;


DROP TABLE IF EXISTS mergeactivite;
CREATE TABLE mergeactivite(
    activitePrincipaleUL TEXT PRIMARY KEY,
	sous_secteur TEXT, 
	secteur_division TEXT
);

COPY mergeactivite(
	activitePrincipaleUL,
	sous_secteur, 
	secteur_division
)
	
FROM 'C:\Program Files\PostgreSQL\17\data\denominationactiviteNAF.csv'
DELIMITER ','
CSV HEADER;


DELETE FROM entreprises
WHERE LENGTH(siren) <> 9;

ALTER TABLE entreprises RENAME COLUMN denominationUniteLegale TO trancheEffectifsUL;
ALTER TABLE entreprises RENAME COLUMN etatAdministratifUniteLegale TO nom_entreprise;
ALTER TABLE entreprises RENAME COLUMN trancheEffectifsUniteLegale TO etatAdministratifUL; 
ALTER TABLE entreprises RENAME COLUMN activitePrincipaleUniteLegale TO categorieE; 
ALTER TABLE entreprises RENAME COLUMN categorieEntreprise TO activitePrincipaleUL; 
ALTER TABLE entreprises RENAME COLUMN categorieJuridiqueUniteLegale TO nomenclatureActivitePrincipaleUL; 
ALTER TABLE entreprises RENAME COLUMN nomenclatureActivitePrincipaleUniteLegale TO economieSocialeSolidaireUL; 
ALTER TABLE entreprises RENAME COLUMN economieSocialeSolidaireUniteLegale TO categorieJuridiqueUL; 



DELETE FROM entreprises
WHERE etatAdministratifUL = 'C';

DELETE FROM entreprises
WHERE categorieJuridiqueUL NOT LIKE '5%';

DELETE FROM entreprises_fusion
WHERE LEFT(activitePrincipaleUL, 2) IN ('64', '68', '82', '84', '98','66','70','65','66');

# Attention appliquer les delete à "entreprises_fusion" et non pas à "entreprises"

DELETE FROM entreprises
WHERE categorieE IS NULL;

DROP TABLE IF EXISTS entreprises_bu;
CREATE TABLE entreprises_bu AS
SELECT * FROM entreprises;

DROP TABLE IF EXISTS entreprises_fusion;

CREATE TABLE entreprises_fusion AS
SELECT e.siren,
       e.trancheEffectifsUL,
       e.categorieE,
       e.activitePrincipaleUL,
       e.nom_entreprise,
       e.etatAdministratifUL,
       e.categorieJuridiqueUL,
       e.economieSocialeSolidaireUL,
       e.nomenclatureActivitePrincipaleUL,
       m.sous_secteur,
       m.secteur_division
FROM entreprises e
LEFT JOIN mergeactivite m
       ON e.activitePrincipaleUL = m.activitePrincipaleUL;

SELECT COUNT(nom_entreprise) AS nb_valeurs
FROM entreprises_fusion;


SELECT * FROM entreprises_fusion
Where LEFT(activitePrincipaleUL, 2) = '65' 
LIMIT 10

*/

