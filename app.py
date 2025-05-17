from flask import Flask, render_template, request
from ebay_scraper import search_ebay

app = Flask(__name__)

# Route for the homepage with search bar
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        search_query = request.form['search_query']
        print(f"Search Query: {search_query}")  # Debugging: Print search query
        items = search_ebay(search_query)
        for item in items:
            item['Price'] = "{:.2f}".format(item['Price'])
        #print(f"Found items: {items}")  # Debugging: Print found items
        return render_template('index.html', items=items)
    return render_template('index.html', items=None)


if __name__ == "__main__":
    app.run(debug=True)

