import asyncio
import pandas as pd
from playwright.async_api import async_playwright

class WBParser:
    def __init__(self):
        self.url = "https://www.wildberries.ru/catalog/elektronika/smartfony-i-telefony/all-smartphones"

    async def get_data(self):
        async with async_playwright() as p:
            # запуск браузера
            browser = await p.chromium.launch(headless=True) # headless=True чтобы не вылетало окно
            context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
            page = await context.new_page()
            
            print(f"🔗 Переход на {self.url}...")
            await page.goto(self.url, wait_until="networkidle")
            
            # чуть скроллим, чтобы товары прогрузились
            await page.mouse.wheel(0, 3000)
            await asyncio.sleep(2)

            # собираем товары с помощью селекторов
            products = []
            # ищем карточки по разным возможным признакам
            cards = await page.query_selector_all("article, .product-card, .j-card-item")
            
            for card in cards:
                try:
                    # пробуем найти название через разные селекторы
                    name_el = await card.query_selector(".product-card__name, .brand-name, .goods-name")
                    price_el = await card.query_selector(".price__lower-price, .wallet-price, .price__main")
                    brand_el = await card.query_selector(".product-card__brand, .brand-name")
                    
                    if name_el and price_el:
                        name_text = await name_el.inner_text()
                        price_text = await price_el.inner_text()
                        brand_text = await brand_el.inner_text() if brand_el else "—"
                        
                        products.append({
                            'Бренд': brand_text.strip(),
                            'Название': name_text.replace("/", "").strip(),
                            'Цена': price_text.replace("\xa0", "").replace(" ", "").replace("₽", "").strip()
                        })
                except Exception:
                    continue
            if not products:
                print("⚠️ WB заблокировал доступ. Использую демо-данные для проверки Excel...")
                products = [
                    {'Бренд': 'Apple', 'Название': 'iPhone 15', 'Цена': '95000'},
                    {'Бренд': 'Samsung', 'Название': 'Galaxy S24', 'Цена': '85000'},
                    {'Бренд': 'Xiaomi', 'Название': 'Redmi Note 13', 'Цена': '25000'}
                ]    

            await browser.close()
            return products

    def save_to_excel(self, data, filename="Result.xlsx"):
        df = pd.DataFrame(data)
        df.to_excel(filename, index=False)
        print(f"Готово! Собрано товаров: {len(data)}")
        print(f"Данные сохранены в {filename}")

async def main():
    parser = WBParser()
    print("Запуск асинхронного браузера...")
    
    data = await parser.get_data()
    
    if data:
        parser.save_to_excel(data)
    else:
        print("Не удалось найти товары на странице.")

if __name__ == "__main__":
    asyncio.run(main())