from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from bs4 import BeautifulSoup
import pandas as pd
from typing import Union
import os, time
from datetime import date, datetime
from config import flags

pd.set_option('mode.chained_assignment', None)

selenium_url = os.getenv("SELENIUM_URL", "http://selenium-firefox:4444/wd/hub")
print(f"Selenium url: {selenium_url}")

def fetch_fdisk_table() -> Union[pd.DataFrame, None]:
    try:
        print("Starting Fdisk Fetch")

        options = Options()
        options.add_argument("--headless")

        driver: webdriver.Remote = None
        for i in range(30):
            try:
                driver = webdriver.Remote(
                    command_executor=selenium_url,
                    options=options,
                )
                break
            except WebDriverException as e:
                print(f"Waiting for Selenium... ({i+1}/30)")
                time.sleep(2)
        else:
            raise Exception("Selenium server never became ready!")

        fdisk_username = os.environ.get("FDISK_USERNAME")
        fdisk_password = os.environ.get("FDISK_PASSWORD")
        fdisk_instanz = os.environ.get("FDISK_INSTANZNUMMER")

        print('Credentials read')
        if (fdisk_username == None or fdisk_password == None or fdisk_instanz == None):
            raise Exception("Fdisk credentials not provided")


        df = None
        driver.get("https://app.fdisk.at/fdisk/module/vws/logins/logins.aspx")

        # Fill in login form
        loginE = driver.find_element(By.ID,'login')
        loginE.clear()
        loginE.send_keys(fdisk_username)

        passwordE = driver.find_element(By.ID,'password')
        passwordE.clear()
        passwordE.send_keys(fdisk_password)
        driver.find_element(By.ID, 'Submit2').click()

        # Now Logged in and call site, which contains the table
        url = 'https://app.fdisk.at/fdisk/module/kvw/karriere/AngemeldeteKurseLFKDOList.aspx?' + \
                f'instanzennummer_person={fdisk_instanz}' + \
                '&ordnung=kursbeginn%2Ckursartenbez%2Czuname%2Cvorname' + \
                '&orderType=ASC' + \
                '&search=1' + \
                '&anzeige_count=ALLE'
        print(f'Table url: {url}')
        
        driver.get(url)

        # Scraping table
        table_kurse = driver.find_element(By.XPATH, '/html/body/table[2]/tbody/tr[2]/td[1]')
        soup = BeautifulSoup(table_kurse.get_attribute('innerHTML'), 'html.parser')
        table = soup.select("table")[0]

        # Preparing data
        tabledata = pd.read_html(str(table))[0]

        # Remove unneded lines
        df = tabledata.dropna(axis=0, how='all')
        df.drop(df.tail(2).index, inplace=True)
        df.dropna(axis=1, how='all', inplace=True)

        # Data Cleaning
        # Set Column Labels and remove them from the data
        df.columns = df.iloc[0:1].to_numpy()[0]
        df = df.iloc[1:]

        # Remove not needed columns in result table
        df.drop(labels=['Anwesenheitsstatus', 'Leistungsart', 'Bemerkung', "durchführende Instanz"], inplace=True,
                axis=1)

        # Rename the couse title column name
        df.rename(columns={'Kursart (Kurzbez.)': 'Kursbez.'}, inplace=True)
        # Change the location name of the NÖ Feuerwehr- und Sicherheitszentrum to NÖFSZ
        df.loc[df['Ort'] == 'Tulln, NÖ Feuerwehr- und Sicherheitszentrum', 'Ort'] = 'NÖFSZ'

        df['Ort'] = df['Ort'].str.replace('Feuerwehrhaus', 'Fwh.', regex=False)
        df['Ort'] = df['Ort'].str.replace('Feuerwehr', 'Fw.', regex=False)

        # Just display the first- and lastname (remove rank and number)
        df['Name'] = df['Name'].apply(lambda x: x[:x.find(',')])

        # Remove lines where booking is already rejected by the system
        if flags.REMOVE_DECLINED_COURSES:
            df.drop(df[(df['Teilnehmerstatus'] == 'Abgelehnt vom System') | (
                    df['Teilnehmerstatus'] == 'Abgelehnt Veranstalter')].index, inplace=True)

        # Drop the end date column
        df.drop(labels='Kursende', axis=1, inplace=True)

        # just show courses of the future
        if flags.REMOVE_PAST_COURSES:
            df['sort'] = (pd.to_datetime(df['Kursbeginn'], format='%d.%m.%Y %H:%M'))
            df = df[df['sort'].dt.date >= date.today()]
            df.drop(labels='sort', inplace=True, axis=1)

        if flags.WRITE_FDISK_TABLE_TO_FILE:
            print(datetime.now().strftime("[%d-%b-%Y %H:%M:%S]"), "Successfully written table to file")
            df.to_excel('out.xlsx', index=False)

    except Exception as ex:
        print("There was an error while fetching data. The program didn't succeed!")
        print(ex)
    finally:
        driver.quit()

    print("Ended Fdisk Fetch")
    return df
