git remote add origin https://github.com/crazydelta/newproject.gitimport os
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    url = request.form['url'].strip()
    fields = request.form['fields'].strip()
    save_directory = request.form['directory'].strip()

    if not url:
        flash("Error: URL field is empty.", 'error')
        return redirect(url_for('index'))

    if not save_directory:
        flash("Error: Save directory field is empty.", 'error')
        return redirect(url_for('index'))

    if not os.path.isdir(save_directory):
        flash(f"Error: Directory '{save_directory}' does not exist.", 'error')
        return redirect(url_for('index'))

    try:
        html = fetch_html(url)
    except Exception as e:
        flash(f"Failed to load page. Error: {e}", 'error')
        return redirect(url_for('index'))

    data = parse_html(html, fields)
    save_to_csv(data, save_directory)
    flash(f"CSV file saved to: {os.path.join(save_directory, 'scraped_data.csv')}", 'success')

    return redirect(url_for('index'))

def fetch_html(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def parse_html(html, fields):
    soup = BeautifulSoup(html, 'html.parser')
    data = {}

    if not fields:
        data['Content'] = soup.get_text(separator='\n', strip=True).split('\n')
    else:
        field_sets = [field.strip().split(',') for field in fields.split('|')]
        data = {f'Field {i+1}': [] for field_set in field_sets for i in range(len(field_set))}

        for field_set, field_indices in zip(field_sets, data.values()):
            for i, field in enumerate(field_set):
                tag, attr, value = field.split(':')
                elements = soup.find_all(tag, attrs={attr: value})
                if elements:
                    field_indices.extend(element.get_text(strip=True) for element in elements)
                else:
                    field_indices.append("N/A")

    return data

def save_to_csv(data, save_directory):
    df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in data.items()]))
    os.makedirs(save_directory, exist_ok=True)
    csv_file_path = os.path.join(save_directory, 'scraped_data.csv')
    df.to_csv(csv_file_path, index=False, encoding='utf-8')

if __name__ == "__main__":
    app.run(debug=True)