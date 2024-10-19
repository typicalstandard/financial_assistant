from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PyQt5.QtCore import QThread, pyqtSignal


class Parser(QThread):
    progress = pyqtSignal(int)
    resultReady = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self, password, phone, df):
        super().__init__()
        self.password = password
        self.phone = phone
        self.df = df

    def run(self):
        mcc_from_site = dict()
        options = Options()
        options.add_argument("-headless")

        try:
            with webdriver.Firefox(options=options) as driver:
                wait = WebDriverWait(driver, 10)
                self.login(driver, wait)
                self.navigate_to_history(driver, wait)
                self.extract_mcc_codes(driver, wait, mcc_from_site)
                self.resultReady.emit(mcc_from_site)
        except Exception as e:
            self.error_occurred.emit(str(e))
            self.exit()

    def login(self, driver, wait):
        driver.get("https://insnc.by/")
        user_name = wait.until(EC.presence_of_element_located((By.NAME, 'phone')))
        user_name.send_keys(self.phone, Keys.RETURN)
        user_password = wait.until(EC.presence_of_element_located((By.NAME, 'password')))
        user_password.send_keys(self.password, Keys.RETURN)

    def navigate_to_history(self, driver, wait):
        history = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@href='/history']")))
        history.click()

    def extract_mcc_codes(self, driver, wait, mcc_from_site):
        x = 100 / len(self.df)
        self.s = [0]
        for i in self.df:
            next_term = self.s[-1] + x
            self.s.append(next_term)
            self.progress.emit(int(next_term))
            try:
                shopping_list = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@data-test-id='historyCell']")))
                original_text = shopping_list.text
                search = wait.until(EC.element_to_be_clickable((By.NAME, 'searchText')))
                search.send_keys(i, Keys.RETURN)
                check = wait.until_not(
                    EC.text_to_be_present_in_element((By.XPATH, "//button[@data-test-id='historyCell']"),
                                                     original_text))
                if check:
                    updated_shopping_list = wait.until(
                        EC.element_to_be_clickable((By.XPATH, "//button[@data-test-id='historyCell']")))
                    updated_shopping_list.click()
                self.parse_side_panel(wait, mcc_from_site, i)
                search.clear()
            except Exception as e:
                mcc_from_site[i] = 0
                search.clear()
                self.error_occurred.emit(f"Error processing {i}: {str(e)}")

    def parse_side_panel(self, wait, mcc_from_site, i):
        try:
            side_panel = wait.until(EC.visibility_of_element_located((
                By.XPATH, "//div[@class='history-details-side-panel_mainContent__gnt+e']"))).text.split()
            if side_panel[13].isdigit():
                mcc_from_site[i] = side_panel[13]
            else:
                mcc_from_site[i] = 0
        except Exception as e:
            mcc_from_site[i] = 0
            self.error_occurred.emit(f"Error parsing side panel for {i}: {str(e)}")
