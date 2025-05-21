import os
import json
from time import sleep
import zstandard as zstd
import io

import pandas as pd

import requests
from seleniumwire import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.remote.webelement import WebElement



def main():
	options = Options()
	options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
	
	driver = webdriver.Firefox(options=options)
	
	driver.get('https://www.rarewhisky101.com/indices')
	driver.implicitly_wait(1)
	
	res = driver.find_elements(By.CSS_SELECTOR, "[class*='lg:px-4']")
	
	to_visit = []
	for res in res:
		link = res.get_attribute("href")
		name = res.find_elements(By.CSS_SELECTOR, "[class*='font-medium']")[0].text
		# print(name, link)
		to_visit.append((name, link))
	
	for name, link in to_visit:
		# Remove Prev page data
		driver.requests.clear()
		
		print(name, link)
		os.makedirs(os.path.join('data', 'Corporate'), exist_ok=True)
		driver.get(link)
		driver.implicitly_wait(1)
		select = driver.find_elements(By.CSS_SELECTOR, "[class*='fi-select-input']")[0]
		select = Select(select)
		select.select_by_value("all")
		sleep(1)
		
		body = None
		for request in driver.requests:
			if request.response and request.url == "https://www.rarewhisky101.com/livewire/update":
				# print(request.response.headers)
				# print(f"Status: {request.response.status_code}")
				body = request.response.body
				dctx = zstd.ZstdDecompressor()
		
		json_str = "{}"
		with dctx.stream_reader(io.BytesIO(body)) as reader:
			decompressed = reader.read()
			try:
				json_str = decompressed.decode("utf-8")
			except UnicodeDecodeError:
				print("Decompressed but not valid UTF-8 text.")
		
		json_dict = json.loads(json_str)
		try:
			data = json_dict['components'][0]['effects']['dispatches'][0]['params']['data']['datasets'][0]['data']
			labels = json_dict['components'][0]['effects']['dispatches'][0]['params']['data']['labels']
			
			data = {
				'values': data,
				'year': labels
			}
		except Exception as e:
			print(e)
			box_chart = driver.find_elements(By.CSS_SELECTOR, "[class*='fi-section-content']")[0]
			box_chart = box_chart.find_element(By.TAG_NAME, "div")
			box_chart = box_chart.find_element(By.TAG_NAME, "div")
			chart = box_chart.find_element(By.TAG_NAME, "div")
			
			str_json = str(chart.get_attribute("x-data")[60:-115])
			str_json = str_json.replace('\\u0022', '"')
			
			json_data = json.loads(str_json)
			data = {
				'values': json_data["datasets"][0]["data"],
				'year': json_data["labels"]
			}
		
		pd.DataFrame.from_dict(data).to_csv(f"data/Corporate/{name}.csv", index=False)
				
		
		# pd.DataFrame.from_dict(data).to_csv(f"data/Corporate/{name}.csv", index=False)
	
	driver.quit()


if __name__ == '__main__':
	main()
