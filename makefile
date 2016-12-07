init:
	conda config --add channels conda-forge
	conda create -n planes python=3.5 basemap pandas jupyter seaborn geopy lxml html5lib BeautifulSoup4 matplotlib nltk scikit-learn gensim