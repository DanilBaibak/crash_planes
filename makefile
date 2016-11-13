init:
	conda config --add channels conda-forge
	conda create -n planes python=3.5 basemap pandas jupyter geopy lxml html5lib BeautifulSoup4