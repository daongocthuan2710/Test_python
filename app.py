from flask import Flask, request, jsonify
import io
import logging
import pandas as pd
import math

filename = "sales_data.csv"
# Global variable to hold the DataFrame in memory
in_memory_data = None

logging.basicConfig(
    filename='debug.log',
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

app = Flask(__name__)

@app.route('/')
def index():
    return "Welcome"

@app.route('/upload', methods=['POST'])
def upload_csv():
    global in_memory_data

    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected for uploading'}), 400

    try:
        stream = io.StringIO(file.read().decode('utf-8'))
        df = pd.read_csv(stream, parse_dates=['date'])
        in_memory_data = df

        return jsonify({
            'message': 'File uploaded and stored in memory successfully.',
            'num_rows': len(df),
            'columns': list(df.columns)
        }), 200

    except Exception as e:
        return jsonify({'error': f'Failed to process CSV file: {str(e)}'}), 500

@app.route('/sales/', methods=['GET'])
def get_filtered_sales():
    global in_memory_data

    # If no data has been uploaded yet
    if in_memory_data is None:
        return jsonify({'error': 'No CSV data in memory. Please upload first.'}), 400
    
    df = in_memory_data.copy()

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    region = request.args.get('region')

    if start_date:
        df = df[df['date'] >= pd.to_datetime(start_date)]

    if end_date:
        df = df[df['date'] <= pd.to_datetime(end_date)]

    if region:
        df = df[df['region'] == region]

    # Returns total sales, average sales, and count of transactions for the given date range and region
    df['sales'] = df['price'] * df['quantity']

    total_sales = float(df['sales'].sum()) if len(df) > 0 else 0.0
    average_sales = float(df['sales'].mean() if len(df) > 0 else 0.0)
    count_transactions = len(df)

    # Add pagination for large CSV files
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    total_records = len(df)
    paginated_df = df.iloc[start_idx:end_idx]
    paginated_df['date'] = paginated_df['date'].dt.strftime('%m/%d/%Y')

    data = paginated_df.to_dict(orient='records')
    total_pages = math.ceil(total_records / limit) if limit > 0 else 1

    return jsonify({
        'total_sales': total_sales,
        'average_sales': average_sales,
        'count_transactions': count_transactions,
        'page': page,
        'limit': limit,
        'total_pages': total_pages,
        'data': data
    }), 200


if __name__ == '__main__':
    app.run(debug=True)
