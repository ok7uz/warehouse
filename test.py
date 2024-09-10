import asyncio
import aiohttp

async def download_page(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            content = await response.text()
            print(f"Downloaded from {url}")

async def main():
    urls = ["https://example.com", "https://example.org", "https://example.net"]
    tasks = [download_page(url) for url in urls]
    await asyncio.gather(*tasks)

# asyncio dasturini ishga tushirish
asyncio.run(main())
