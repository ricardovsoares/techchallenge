import os
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


def build_driver() -> webdriver.Chrome:
    options = Options()

    headless = os.getenv("SELENIUM_HEADLESS", "true").lower() == "true"
    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--remote-debugging-port=9222")

    # 1) CHROME_BIN (preferência), mas sem “matar” local se estiver inválida
    chrome_bin = os.getenv("CHROME_BIN")
    if chrome_bin and os.path.exists(chrome_bin):
        options.binary_location = chrome_bin
    else:
        # auto-detect (Linux/macOS/Windows via PATH)
        for candidate in ["google-chrome", "chrome", "chromium", "chromium-browser"]:
            p = shutil.which(candidate)
            if p:
                options.binary_location = p
                break
        else:
            # candidatos comuns (podem não existir)
            if os.name == "nt":
                for p in [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                ]:
                    if os.path.exists(p):
                        options.binary_location = p
                        break

    # 2) CHROMEDRIVER (preferência)
    chromedriver = os.getenv("CHROMEDRIVER")
    if chromedriver and os.path.exists(chromedriver):
        return webdriver.Chrome(service=Service(chromedriver), options=options)

    # auto-detect driver no PATH
    chromedriver = shutil.which("chromedriver")
    if chromedriver:
        return webdriver.Chrome(service=Service(chromedriver), options=options)

    # 3) fallback para DEV local: Selenium Manager (Selenium 4.6+)
    return webdriver.Chrome(options=options)
